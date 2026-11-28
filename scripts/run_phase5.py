"""Phase-5 driver (docs/phase5_prereg.md). Reuses the Phase-4 chain and helpers.

  trajectory --model M --budgets 25       P1-1: replay M1..M4 (+M0) of the ① chains from cache
  notrunc    --model M --budgets 25,50    P0-2: regenerate-until-compliant (<=20 tries), never truncate;
                                          S100 x 2x2 + position arm (multi, first/middle/last) at B=25
  resample   --model M --budget 50        P1-2: A5, K=2..5, subset seeds 143/244/345/446
  oracle     --model M --budgets 25,40,50,150   P0-1: Oracle-Target / Oracle-All readers + Oracle EA
  blind-ea   --model M --budgets 25,40,50,150   P0-1: Model-Blind EA from the ① blind/multi memories
  balanced   --model M --budgets 50,150   P2-2: blind_balanced chains, multi

Outputs: results/phase5_{exp}_{model}.jsonl. Scoring: scripts/phase5_score.sh.
"""
import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_phase4 import (BLIND_SYSTEM, BLIND_USER, FINAL_ANSWER_TOKENS, FINAL_SYSTEM,  # noqa: E402
                        FINAL_USER, INTERMEDIATE_SYSTEM, INTERMEDIATE_USER, MODELS,
                        chain, load_materials, load_samples, material_text, pilot_subset,
                        spans_kdose, spans_original, spans_position, tokenizers)
from supdrift.chain2 import citation_flags  # noqa: E402
from supdrift.llm import LLMCache, chat, full_cache_key  # noqa: E402

STRICTER = ("\nHARD LIMIT: your entire output must be at most {b} tokens "
            "(about {w} words). Be extremely terse; drop anything that does not fit.")
MAX_TRIES = 20
# Phase-6 E15 matched-prompt control (docs/phase6_prereg.md, 2026-11-23): ONE system prompt and ONE instruction for
# both arms; the Aware arm (`aware_m`) differs from the Blind arm (`blind_m`) only by the question line.
MATCHED_SYSTEM = """You are one step in a multi-step biomedical research assistant pipeline.
You receive working notes from the previous step about clinical research. A later step will answer a research question using only your notes.
Condense the notes for the next step, within the length limit.
Preserve the supporting evidence and source information as appropriate.
Output only the notes."""
MATCHED_Q = 'Research question: What is the effect of "{intervention}" compared with "{comparator}" on "{outcome}"?\n\n'
MATCHED_USER = """Notes from the previous step:
{material}

Condense these notes so a later step can use them. Maximum length: {budget} tokens (about {words} words)."""
RESAMPLE_SEEDS = [143, 244, 345, 446]
DIR_WORD = {"INCREASE": "increase", "DECREASE": "decrease", "NO_DIFFERENCE": "no difference"}
SIG_WORD = {"INCREASE": "significant", "DECREASE": "significant", "NO_DIFFERENCE": "n.s."}


def s100(samples):
    return pilot_subset(samples, per_label=34)[:100]


# ----------------------------------------------------------------- P1-1 replay
def replay_rows(model, sample, spans, mode, cond, budget, cache, enc, dec, legacy):
    """Reconstruct M1..M4 of an enforced chain from the cache; no generation."""
    t = sample["target"]
    ico = {k: t[k] for k in ("intervention", "comparator", "outcome")}
    material = material_text(sample["pmcid"], spans)
    rows = []
    for step in range(1, 5):
        if legacy:
            key = full_cache_key(model, {"task": "hard_step", "sid": sample["sample_id"],
                                         "mode": mode, "icoset": cond, "budget": budget,
                                         "step": step, "material": material})
        else:
            key = full_cache_key(model, {"task": "p4_step", "exp": "budget", "sid": sample["sample_id"],
                                         "mode": mode, "cond": cond, "budget": budget,
                                         "depth": 5, "step": step, "material": material})
        raw = cache._mem.get(key)
        if raw is None:
            raise KeyError(f"cache miss {model} {sample['sample_id']} {mode}/{cond} B={budget} step {step}")
        raw = raw.strip()
        ids = enc(model, raw)
        material = dec(model, ids[:budget]) if len(ids) > budget else raw
        rows.append({"sample_id": sample["sample_id"], "mode": mode, "cond": cond, "budget": budget,
                     "step": step, "raw_tokens": len(ids), "truncated": len(ids) > budget,
                     "text": material})
    return rows


# ----------------------------------------------------------------- P0-2 regen
async def notrunc_chain(model, sample, spans, mode, cond, budget, cache, sem, enc, material_override=None, n_writes=4,
                        base_seed=42):
    # base_seed != 42: Phase-6 E23 multi-seed replication (the seed enters the cache key; seed 42 keeps the old keys)
    sd = {} if base_seed == 42 else {"seed": base_seed}
    t = sample["target"]
    ico = {k: t[k] for k in ("intervention", "comparator", "outcome")}
    material = material_override or material_text(sample["pmcid"], spans)   # override: Phase-6 E13 long source
    attempts, compliant, instructed = [], [], []
    for step in range(1, n_writes + 1):          # n_writes = 1: Phase-6 E18 one-pass memory (same step-1 cache key)
        fitted = None
        for a in range(MAX_TRIES):
            # adaptive instruction: the INSTRUCTED budget shrinks 5 % per failed attempt
            # (never below 8 tokens); acceptance is always against the TRUE cap `budget`
            ib = max(8, round(budget * (1 - 0.05 * a)))
            words = max(6, int(ib * 0.75))
            extra = "" if a == 0 else STRICTER.format(b=ib, w=words)
            if mode in ("aware_m", "blind_m"):          # Phase-6 E15: identical prompt, question line in aware_m only
                system = MATCHED_SYSTEM + extra
                user = ((MATCHED_Q.format(**ico) if mode == "aware_m" else "")
                        + MATCHED_USER.format(material=material, budget=ib, words=words))
            elif mode == "aware":
                system = INTERMEDIATE_SYSTEM + extra
                user = INTERMEDIATE_USER.format(material=material, budget=ib, words=words, **ico)
            else:
                system = BLIND_SYSTEM + extra
                user = BLIND_USER.format(material=material, budget=ib, words=words)
            key = full_cache_key(model, {"task": "p5_notrunc_step", "sid": sample["sample_id"],
                                         "mode": mode, "cond": cond, "budget": budget,
                                         "step": step, "attempt": a, "instructed": ib,
                                         "material": material, **sd})
            raw = (await chat(model, [{"role": "system", "content": system},
                                      {"role": "user", "content": user}],
                              cache=cache, cache_key=key, sem=sem,
                              temperature=0.7, seed=base_seed + 100 * a,
                              max_tokens=budget * 2 + 64)).strip()
            if len(enc(model, raw)) <= budget:
                fitted = raw
                attempts.append(a + 1); compliant.append(a == 0); instructed.append(ib)
                break
        if fitted is None:
            return {"sample_id": sample["sample_id"], "exp": "notrunc", "mode": mode, "cond": cond,
                    "budget": budget, "depth": 5, "failed": True, "failed_step": step,
                    "attempts": attempts, "memory": None, "text": None}
        material = fitted
    memory = material
    user = FINAL_USER.format(material=memory, budget=FINAL_ANSWER_TOKENS,
                             words=int(FINAL_ANSWER_TOKENS * 0.75), **ico)
    key = full_cache_key(model, {"task": "p5_notrunc_final", "sid": sample["sample_id"],
                                 "mode": mode, "cond": cond, "budget": budget, "material": memory, **sd})
    text = (await chat(model, [{"role": "system", "content": FINAL_SYSTEM},
                               {"role": "user", "content": user}],
                       cache=cache, cache_key=key, sem=sem, temperature=0.7, seed=base_seed,
                       max_tokens=FINAL_ANSWER_TOKENS * 2 + 64)).strip()
    return {"sample_id": sample["sample_id"], "exp": "notrunc", "mode": mode, "cond": cond,
            "budget": budget, "depth": 5, "failed": False, "attempts": attempts,
            "instructed_budgets": instructed,
            "first_try_compliant": compliant, "mean_attempts": sum(attempts) / len(attempts),
            "forced": False, "memory": memory, "text": text, **citation_flags(text, sample["pmcid"])}


# ----------------------------------------------------------------- P0-1 oracle
def oracle_lines(sample, fmt):
    """(prompt_id, line) per ICO, in the same per-article order as the chains' spans."""
    prompts = [sample["target"]] + sample["distractors"]
    pairs = []
    for p in prompts:
        head = (p["outcome"] if fmt == "short"
                else f"{p['outcome']} [{p['intervention']} vs {p['comparator']}]")
        pairs.append((p["prompt_id"], f"{head}: {DIR_WORD[p['gold_label']]}, {SIG_WORD[p['gold_label']]}"))
    random.Random(f"{sample['sample_id']}-order").shuffle(pairs)
    return pairs


def oracle_memory(sample, fmt, kind):
    pairs = oracle_lines(sample, fmt)
    if kind == "oracle_target":
        pairs = [pl for pl in pairs if pl[0] == sample["target"]["prompt_id"]]
    return f"Findings from [PMC{sample['pmcid']}]:\n" + "\n".join(l for _, l in pairs)


async def answer_from(model, sample, memory, prompt, cache, sem, tag):
    user = FINAL_USER.format(material=memory, budget=FINAL_ANSWER_TOKENS,
                             words=int(FINAL_ANSWER_TOKENS * 0.75),
                             intervention=prompt["intervention"], comparator=prompt["comparator"],
                             outcome=prompt["outcome"])
    key = full_cache_key(model, {"task": "p5_read", "tag": tag, "sid": sample["sample_id"],
                                 "pid": prompt["prompt_id"], "material": memory})
    return (await chat(model, [{"role": "system", "content": FINAL_SYSTEM},
                               {"role": "user", "content": user}],
                       cache=cache, cache_key=key, sem=sem, temperature=0.7, seed=42,
                       max_tokens=FINAL_ANSWER_TOKENS * 2 + 64)).strip()


def ico_row(sample, p, role):
    return {"sample_id": sample["sample_id"], "role": role, "prompt_id": p["prompt_id"],
            "intervention": p["intervention"], "comparator": p["comparator"],
            "outcome": p["outcome"], "gold_label": p["gold_label"]}


# ------------------------------------------------------------------------ main
async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--model", required=True)
    ap.add_argument("--budgets", default=None)
    ap.add_argument("--budget", type=int, default=50)
    ap.add_argument("--concurrency", type=int, default=24)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    model = args.model
    samples = load_samples()
    if args.limit:
        samples = samples[: args.limit]
    budgets = [int(b) for b in args.budgets.split(",")] if args.budgets else None
    enc, dec = tokenizers()
    sem = asyncio.Semaphore(args.concurrency)
    out_path = f"results/phase5_{args.cmd.replace('-', '')}_{model}.jsonl"
    rows, lock, done = [], asyncio.Lock(), 0

    async def collect(coro, n_total):
        nonlocal done
        r = await coro
        async with lock:
            rows.extend(r if isinstance(r, list) else [r]); done += 1
            if done % 200 == 0:
                print(f"  {done}/{n_total}", flush=True)

    if args.cmd == "trajectory":
        cache = LLMCache(f"cache/extra_hard_{model}.jsonl")
        seen_src = set()
        for s in samples:
            for b in budgets or [25]:
                for mode in ("aware", "blind"):
                    for ico in ("single", "multi"):
                        spans = spans_original(s, ico)
                        rows.extend(replay_rows(model, s, spans, mode, ico, b, cache, enc, dec, legacy=(b == 25)))
                        if (s["sample_id"], ico, b) not in seen_src:   # M0 = seed material
                            seen_src.add((s["sample_id"], ico, b))
                            rows.append({"sample_id": s["sample_id"], "mode": "source", "cond": ico,
                                         "budget": b, "step": 0, "raw_tokens": len(enc(model, material_text(s["pmcid"], spans))),
                                         "truncated": False, "text": material_text(s["pmcid"], spans)})
        print(f"trajectory {model}: {len(rows)} memory rows replayed from cache")

    elif args.cmd == "notrunc":
        cache = LLMCache(f"cache/phase5_{model}.jsonl")
        jobs = []
        for s in s100(samples):
            for b in budgets:
                for mode in ("aware", "blind"):
                    for ico in ("single", "multi"):
                        jobs.append(notrunc_chain(model, s, spans_original(s, ico), mode, ico, b, cache, sem, enc))
            for mode in ("aware", "blind"):
                for where in ("first", "middle", "last"):
                    jobs.append(notrunc_chain(model, s, spans_position(s, where), mode, where, 25, cache, sem, enc))
        print(f"notrunc {model}: {len(jobs)} chains", flush=True)
        await asyncio.gather(*[collect(j, len(jobs)) for j in jobs])

    elif args.cmd == "resample":
        cache = LLMCache(f"cache/phase5_{model}.jsonl")
        mats = load_materials()
        jobs = []
        for s in samples:
            m = mats.get(s["sample_id"])
            if m is None or len(m.get("kpool", [])) < 4:
                continue
            for seed in RESAMPLE_SEEDS:
                pool = list(m["kpool"]); random.Random(f"{s['sample_id']}-K{seed}").shuffle(pool)
                for k in range(2, 6):
                    spans = [s["target"]["evidence"]] + [d["evidence"] for d in pool[: k - 1]]
                    random.Random(f"{s['sample_id']}-K{k}-s{seed}-order").shuffle(spans)
                    for mode in ("aware", "blind"):
                        async def one(s=s, spans=spans, mode=mode, k=k, seed=seed):
                            r = await chain(model, s, spans, mode=mode, budget=args.budget, depth=5,
                                            cache=cache, sem=sem, enc=enc, dec=dec, exp="resample",
                                            cond=f"K{k}")
                            r.update({"K": k, "subset_seed": seed}); return r
                        jobs.append(one())
        print(f"resample {model}: {len(jobs)} chains", flush=True)
        await asyncio.gather(*[collect(j, len(jobs)) for j in jobs])

    elif args.cmd == "oracle":
        cache = LLMCache(f"cache/phase5_{model}.jsonl")
        jobs = []
        for s in samples:
            prompts = [("target", s["target"])] + [("distractor", d) for d in s["distractors"]]
            for b in budgets:
                for kind, fmt, roles in [("oracle_target", "short", ["target"]),
                                         ("oracle_all", "short", ["target", "distractor"]),
                                         ("oracle_all", "full", ["target"])]:
                    mem_full = oracle_memory(s, fmt, kind)
                    ids = enc(model, mem_full)
                    fits = len(ids) <= b
                    mem = mem_full if fits else dec(model, ids[:b])
                    for role, p in prompts:
                        if role not in roles:
                            continue
                        async def one(s=s, p=p, role=role, kind=kind, fmt=fmt, b=b, mem=mem, fits=fits,
                                      ntok=len(ids), n_ico=len(prompts)):   # bind: closures are late-bound
                            text = await answer_from(model, s, mem, p, cache, sem, f"{kind}-{fmt}-{b}")
                            return {**ico_row(s, p, role), "exp": "oracle", "kind": kind, "fmt": fmt,
                                    "budget": b, "fits": fits, "oracle_tokens": ntok,
                                    "n_ico": n_ico, "memory": mem, "text": text}
                        jobs.append(one())
        print(f"oracle {model}: {len(jobs)} reads", flush=True)
        await asyncio.gather(*[collect(j, len(jobs)) for j in jobs])

    elif args.cmd == "blind-ea":
        cache = LLMCache(f"cache/phase5_{model}.jsonl")
        mem = {}
        for r in map(json.loads, open(f"results/phase4_budget_{model}.jsonl")):
            if r["mode"] == "blind" and r["cond"] == "multi":
                mem[(r["sample_id"], r["budget"])] = r["memory"]
        jobs = []
        for s in samples:
            prompts = [("target", s["target"])] + [("distractor", d) for d in s["distractors"]]
            for b in budgets:
                m = mem.get((s["sample_id"], b))
                if m is None:
                    continue
                for role, p in prompts:
                    async def one(s=s, p=p, role=role, b=b, m=m):
                        text = await answer_from(model, s, m, p, cache, sem, f"blindea-{b}")
                        return {**ico_row(s, p, role), "exp": "blindea", "kind": "model_blind",
                                "budget": b, "memory": m, "text": text}
                    jobs.append(one())
        print(f"blind-ea {model}: {len(jobs)} reads", flush=True)
        await asyncio.gather(*[collect(j, len(jobs)) for j in jobs])

    elif args.cmd == "balanced":
        cache = LLMCache(f"cache/phase5_{model}.jsonl")
        jobs = [chain(model, s, spans_original(s, "multi"), mode="blind_balanced", budget=b, depth=5,
                      cache=cache, sem=sem, enc=enc, dec=dec, exp="balanced", cond="multi")
                for s in samples for b in budgets]
        print(f"balanced {model}: {len(jobs)} chains", flush=True)
        await asyncio.gather(*[collect(j, len(jobs)) for j in jobs])
    else:
        sys.exit(f"unknown cmd {args.cmd}")

    Path("results").mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {out_path}: {len(rows)} rows", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
