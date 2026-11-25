"""Phase-4 generation driver (pre-registered in docs/phase4_prereg.md).

One generic enforced-budget chain serves every experiment: the seed material
(list of spans) and the cache key are what differ. Every intermediate step's
raw token count and whether it was truncated are recorded in the output row,
so compliance / forced-truncation are read straight from the results.

Subcommands (all: --model M [--concurrency N] [--limit N])
  plan                          print the number of chains / LLM calls per experiment
  pilot                         ① P60 subset, aware+blind / multi, B in {40,50,75,100,150}
  budget   --budgets 40,50,100  ① full 2x2 grid at each budget (25 = pure cache replay of
                                  the paper's extra_hard chains, incl. token counts)
  length   --budgets 25,50      ② single_filler / single_dup (needs data/phase4/materials.jsonl)
  position --budgets 25,50      ③ target first / middle / last
  kdose    --budgets 25,50      ⑤ K in 1..5 on subset A5 (needs materials.jsonl)
  depth3                        ⑥ depth-3 2x2 grid at B=25
  slots    --budgets 25,50      ⑧ blind_slots vs (existing) blind, multi
  seeds                         seed robustness: S100 subset, 2x2 grid, B in {25,50,150},
                                  seeds 143/244 (seed 42 = the ① rows); Qwen models

Output rows: results/phase4_{exp}_{model}.jsonl with
  text (final answer), memory (last intermediate), steps [{step, raw_tokens,
  truncated}], forced (any step truncated), plus the design columns.
Scoring: scripts/phase4_score.sh (finals and memories through the frozen evaluator).
"""
import argparse
import asyncio
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from supdrift.chain2 import (BLIND_SYSTEM, BLIND_USER, FINAL_ANSWER_TOKENS, FINAL_SYSTEM,
                             FINAL_USER, INTERMEDIATE_SYSTEM, INTERMEDIATE_USER,
                             citation_flags)
from supdrift.llm import LLMCache, chat, full_cache_key

MODELS = ["qwen3-8b", "qwen3-14b", "gpt-5.4-mini"]
PILOT_BUDGETS = [40, 50, 75, 100, 150]
LABELS = ["INCREASE", "NO_DIFFERENCE", "DECREASE"]

# ⑧ query-blind structured allocation: the MODEL writes one ultra-short slot per
# finding. Same hard cap as free-form blind; the only difference is the format.
SLOTS_SYSTEM = """You are one step in a multi-step biomedical research assistant pipeline.
You receive working notes about a clinical study. The specific question that a later
step will need to answer is not yet known.
Condense the notes for future use as one ultra-short slot per distinct finding, so that
every finding keeps its effect direction and statistical status.
Format, one line per finding: <outcome> | <intervention> vs <comparator> | up/down/none | sig/ns
Never strengthen a claim: write none and ns exactly when the notes report no significant difference.
Keep the source id if present. Output only the slot lines."""

SLOTS_USER = """Notes from the previous step:
{material}

Rewrite as slot lines for future use. Maximum length: {budget} tokens (about {words} words)."""

# Phase-5 P2-2 balanced compact memory: every finding gets one compact record;
# the instruction forbids omission, which free-form blind is free to do.
BALANCED_SYSTEM = """You are one step in a multi-step biomedical research assistant pipeline.
You receive working notes about a clinical study. The specific question that a later
step will need to answer is not yet known, so every finding may matter.
Preserve one compact record for EVERY finding in the notes. Do not omit any finding.
Format, one line per finding: <outcome>: <increase|decrease|no difference>, <significant|n.s.>
Keep the source id if present. Output only the records."""

BALANCED_USER = """Notes from the previous step:
{material}

Rewrite as one compact record per finding, omitting none. Maximum length: {budget} tokens (about {words} words)."""


# ----------------------------------------------------------------------------- data
def load_samples(path="data/gate2/gate2_v1.jsonl"):
    return [json.loads(l) for l in open(path)]


SEED_BUDGETS, EXTRA_SEEDS = [25, 50, 150], [143, 244]   # seed 42 already exists in ①


def pilot_subset(samples, per_label=20):
    """P60: first `per_label` articles per gold label in file order."""
    seen = {l: 0 for l in LABELS}
    out = []
    for s in samples:
        g = s["target"]["gold_label"]
        if seen[g] < per_label:
            seen[g] += 1
            out.append(s)
    return out


def load_materials():
    p = Path("data/phase4/materials.jsonl")
    if not p.exists():
        sys.exit("missing data/phase4/materials.jsonl — run scripts/build_phase4_materials.py")
    return {json.loads(l)["sample_id"]: json.loads(l) for l in open(p)}


def material_text(pmcid, spans):
    body = "\n".join(f"- {s}" for s in spans)
    return f"Excerpts from source article [PMC{pmcid}]:\n{body}"


def spans_original(sample, icoset):
    """Exactly chain2.seed_material's span list (same RNG, same order)."""
    spans = [sample["target"]["evidence"]]
    if icoset == "multi":
        spans = spans + [d["evidence"] for d in sample["distractors"]]
        random.Random(f"{sample['sample_id']}-order").shuffle(spans)
    return spans


def spans_meta(sample):
    """Phase-5 P2-4 Blind + Candidate Metadata: the multi material in the SAME
    per-article order as spans_original (a seeded shuffle of a list of equal
    length yields the same permutation), with each span carrying the identity
    of the comparison it was annotated for (intervention / comparator /
    outcome). No direction, no significance, and no indication of which
    candidate is the eventual target."""
    items = [(sample["target"], sample["target"]["evidence"])] + \
            [(d, d["evidence"]) for d in sample["distractors"]]
    random.Random(f"{sample['sample_id']}-order").shuffle(items)
    return items


def material_text_meta(pmcid, items):
    body = "\n".join(f"- [Intervention: {d['intervention']} | Comparator: {d['comparator']} | "
                     f"Outcome: {d['outcome']}] {s}" for d, s in items)
    return f"Excerpts from source article [PMC{pmcid}]:\n{body}"


def spans_position(sample, where):
    """Multi material with the target moved to first / middle / last; the
    distractors keep the relative order of the original shuffle."""
    spans = spans_original(sample, "multi")
    tgt = sample["target"]["evidence"]
    rest = [s for s in spans if s != tgt]
    k = len(rest) + 1
    idx = {"first": 0, "middle": k // 2, "last": k - 1}[where]
    return rest[:idx] + [tgt] + rest[idx:]


def spans_kdose(sample, pool, k):
    """Target + first (k-1) distractors of the per-article permutation `pool`
    (nested sets across k), shuffled per (article, k)."""
    spans = [sample["target"]["evidence"]] + [d["evidence"] for d in pool[: k - 1]]
    random.Random(f"{sample['sample_id']}-K{k}-order").shuffle(spans)
    return spans


def spans_control(sample, mat, cond):
    """② single_filler / single_dup: target + (K-1) control chunks, shuffled with
    the ORIGINAL per-article RNG so position statistics match multi."""
    chunks = mat["filler_chunks"] if cond == "single_filler" else mat["dup_chunks"]
    spans = [sample["target"]["evidence"]] + list(chunks)
    random.Random(f"{sample['sample_id']}-order").shuffle(spans)
    return spans


# ----------------------------------------------------------------------- tokenizers
def tokenizers():
    from transformers import AutoTokenizer
    import tiktoken
    qt = {"qwen3-8b": AutoTokenizer.from_pretrained("Qwen/Qwen3-8B-FP8"),
          "qwen3-14b": AutoTokenizer.from_pretrained("Qwen/Qwen3-14B-FP8")}
    gt = tiktoken.get_encoding("o200k_base")

    def enc(model, text):
        # disallowed_special=(): a generation can contain the literal string
        # "<|endoftext|>"; tiktoken must count it as text, not raise
        return (qt[model].encode(text, add_special_tokens=False) if model in qt
                else gt.encode(text, disallowed_special=()))

    def dec(model, ids):
        return qt[model].decode(ids) if model in qt else gt.decode(ids)

    return enc, dec


# ---------------------------------------------------------------------------- chain
async def chain(model, sample, spans, *, mode, budget, depth, cache, sem, enc, dec,
                exp, cond, legacy_keys=False, seed=42, material_override=None):
    """Enforced-budget chain of `depth` steps (depth-1 intermediate + final).
    legacy_keys=True reproduces run_extras.run_chain_hard's cache keys so the
    paper's 25-token chains are replayed from cache, not regenerated.
    material_override: a prebuilt M0 (P2-4 metadata material); prompts unchanged."""
    t = sample["target"]
    ico = {k: t[k] for k in ("intervention", "comparator", "outcome")}
    material = material_override or material_text(sample["pmcid"], spans)
    steps, forced = [], False

    for step in range(1, depth):
        words = int(budget * 0.75)
        if mode == "aware":
            system = INTERMEDIATE_SYSTEM
            user = INTERMEDIATE_USER.format(material=material, budget=budget, words=words, **ico)
        elif mode == "blind_slots":
            system = SLOTS_SYSTEM
            user = SLOTS_USER.format(material=material, budget=budget, words=words)
        elif mode == "blind_balanced":   # Phase-5 P2-2
            system = BALANCED_SYSTEM
            user = BALANCED_USER.format(material=material, budget=budget, words=words)
        elif mode == "blind_plural":     # Phase-6 E13 sensitivity: multi-trial wording, nothing else changed
            system = BLIND_SYSTEM.replace("about a clinical study", "about one or more clinical studies")
            assert system != BLIND_SYSTEM
            user = BLIND_USER.format(material=material, budget=budget, words=words)
        else:
            system = BLIND_SYSTEM
            user = BLIND_USER.format(material=material, budget=budget, words=words)
        if legacy_keys:
            key = full_cache_key(model, {"task": "hard_step", "sid": sample["sample_id"],
                                         "mode": mode, "icoset": cond, "budget": budget,
                                         "step": step, "material": material})
        else:
            key = full_cache_key(model, {"task": "p4_step", "exp": exp, "sid": sample["sample_id"],
                                         "mode": mode, "cond": cond, "budget": budget,
                                         "depth": depth, "step": step, "material": material,
                                         **({"seed": seed} if seed != 42 else {})})
        raw = (await chat(model, [{"role": "system", "content": system},
                                  {"role": "user", "content": user}],
                          cache=cache, cache_key=key, sem=sem,
                          temperature=0.7, seed=seed, max_tokens=budget * 2 + 64)).strip()
        ids = enc(model, raw)
        truncated = len(ids) > budget
        material = dec(model, ids[:budget]) if truncated else raw
        forced = forced or truncated
        steps.append({"step": step, "raw_tokens": len(ids), "truncated": truncated})

    memory = material
    user = FINAL_USER.format(material=memory, budget=FINAL_ANSWER_TOKENS,
                             words=int(FINAL_ANSWER_TOKENS * 0.75), **ico)
    if legacy_keys:
        key = full_cache_key(model, {"task": "extra_final", "sid": sample["sample_id"],
                                     "tag": f"hard{budget}-{mode}-{cond}", "material": memory})
    else:
        key = full_cache_key(model, {"task": "p4_final", "exp": exp, "sid": sample["sample_id"],
                                     "mode": mode, "cond": cond, "budget": budget,
                                     "depth": depth, "material": memory,
                                     **({"seed": seed} if seed != 42 else {})})
    text = (await chat(model, [{"role": "system", "content": FINAL_SYSTEM},
                               {"role": "user", "content": user}],
                       cache=cache, cache_key=key, sem=sem,
                       temperature=0.7, seed=seed,
                       max_tokens=FINAL_ANSWER_TOKENS * 2 + 64)).strip()
    return {"sample_id": sample["sample_id"], "exp": exp, "mode": mode, "cond": cond,
            "budget": budget, "depth": depth, "seed": seed, "n_spans": len(spans),
            "steps": steps, "n_truncated_steps": sum(s["truncated"] for s in steps),
            "forced": forced, "memory": memory, "text": text,
            **citation_flags(text, sample["pmcid"])}


# ----------------------------------------------------------------------------- jobs
def jobs_for(exp, samples, budgets, materials):
    """Yield (sample, spans, mode, cond, budget, depth, extra_cols, legacy)."""
    if exp == "pilot":
        for s in pilot_subset(samples):
            for b in PILOT_BUDGETS:
                for mode in ("aware", "blind"):
                    yield s, spans_original(s, "multi"), mode, "multi", b, 5, {}, False
    elif exp == "budget":
        for s in samples:
            for b in budgets:
                for mode in ("aware", "blind"):
                    for ico in ("single", "multi"):
                        yield s, spans_original(s, ico), mode, ico, b, 5, {}, True
    elif exp == "length":
        for s in samples:
            m = materials.get(s["sample_id"])
            if m is None:
                continue
            for b in budgets:
                for mode in ("aware", "blind"):
                    for cond in ("single_filler", "single_dup"):
                        if not m.get(cond.replace("single_", "") + "_chunks"):
                            continue
                        yield s, spans_control(s, m, cond), mode, cond, b, 5, {}, False
    elif exp == "position":
        for s in samples:
            for b in budgets:
                for mode in ("aware", "blind"):
                    for where in ("first", "middle", "last"):
                        yield s, spans_position(s, where), mode, where, b, 5, {}, False
    elif exp == "kdose":
        for s in samples:
            m = materials.get(s["sample_id"])
            if m is None or len(m.get("kpool", [])) < 4:
                continue
            for b in budgets:
                for mode in ("aware", "blind"):
                    for k in range(1, 6):
                        yield s, spans_kdose(s, m["kpool"], k), mode, f"K{k}", b, 5, {"K": k}, False
    elif exp == "seeds":
        # S100: first 34/33/33 articles per label (superset of P60); 2x2 grid x 3 budgets x 2 extra seeds
        for s in pilot_subset(samples, per_label=34)[:100]:
            for b in SEED_BUDGETS:
                for seed in EXTRA_SEEDS:
                    for mode in ("aware", "blind"):
                        for ico in ("single", "multi"):
                            yield s, spans_original(s, ico), mode, ico, b, 5, {"seed": seed}, False
    elif exp == "depth3":
        for s in samples:
            for mode in ("aware", "blind"):
                for ico in ("single", "multi"):
                    yield s, spans_original(s, ico), mode, ico, 25, 3, {}, False
    elif exp == "slots":
        for s in samples:
            for b in budgets:
                yield s, spans_original(s, "multi"), "blind_slots", "multi", b, 5, {}, False
    elif exp == "meta":   # Phase-5 P2-4: blind prompts, metadata-labelled M0, multi
        for s in samples:
            items = spans_meta(s)
            for b in budgets:
                yield (s, [sp for _, sp in items], "blind_meta", "multi", b, 5,
                       {"_material": material_text_meta(s["pmcid"], items)}, False)
    else:
        sys.exit(f"unknown exp {exp}")


def plan(samples, materials):
    print(f"{'exp':<10} {'chains/model':>12} {'LLM calls/model':>16}")
    for exp, budgets in [("pilot", PILOT_BUDGETS), ("budget", [40, 50, 100]),
                         ("length", [25, 50]), ("position", [25, 50]),
                         ("kdose", [25, 50]), ("depth3", [25]), ("slots", [25, 50]),
                         ("seeds", SEED_BUDGETS)]:
        js = list(jobs_for(exp, samples, budgets, materials or {}))
        calls = sum(j[5] for j in js)
        print(f"{exp:<10} {len(js):>12} {calls:>16}   (budgets {budgets})")


# ----------------------------------------------------------------------------- main
async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--model", default=None)
    ap.add_argument("--budgets", default=None, help="comma-separated")
    ap.add_argument("--concurrency", type=int, default=24)
    ap.add_argument("--limit", type=int, default=None, help="smoke test: first N samples")
    args = ap.parse_args()

    samples = load_samples()
    if args.limit:
        samples = samples[: args.limit]
    materials = load_materials() if args.cmd in ("length", "kdose") else None
    if args.cmd == "plan":
        mp = Path("data/phase4/materials.jsonl")
        plan(samples, load_materials() if mp.exists() else None)
        return
    if args.model not in MODELS:
        sys.exit(f"--model must be one of {MODELS}")
    budgets = [int(b) for b in args.budgets.split(",")] if args.budgets else None
    if args.cmd in ("budget", "length", "position", "kdose", "slots", "meta") and not budgets:
        sys.exit("--budgets required")

    enc, dec = tokenizers()
    sem = asyncio.Semaphore(args.concurrency)
    # ① at any budget shares the paper's hard-chain cache (25 replays, others extend it)
    cache = LLMCache(f"cache/extra_hard_{args.model}.jsonl" if args.cmd == "budget"
                     else f"cache/phase4_{args.model}.jsonl")
    Path("results").mkdir(exist_ok=True)
    out_path = f"results/phase4_{args.cmd}_{args.model}.jsonl"
    jobs = list(jobs_for(args.cmd, samples, budgets, materials))
    print(f"{args.cmd} {args.model}: {len(jobs)} chains", flush=True)

    rows, done, lock = [], 0, asyncio.Lock()

    async def one(job):
        nonlocal done
        s, spans, mode, cond, b, depth, extra, legacy = job
        r = await chain(args.model, s, spans, mode=mode, budget=b, depth=depth,
                        cache=cache, sem=sem, enc=enc, dec=dec, exp=args.cmd,
                        cond=cond, legacy_keys=legacy, seed=extra.get("seed", 42),
                        material_override=extra.get("_material"))
        r.update({k: v for k, v in extra.items() if not k.startswith("_")})
        async with lock:
            rows.append(r)
            done += 1
            if done % 200 == 0:
                print(f"  {done}/{len(jobs)}", flush=True)

    await asyncio.gather(*[one(j) for j in jobs])
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n_forced = sum(r["forced"] for r in rows)
    print(f"wrote {out_path}: {len(rows)} chains, forced truncation in {n_forced} "
          f"({n_forced / max(len(rows), 1):.1%})", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
