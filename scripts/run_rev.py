"""Phase-6 reviewer-requested experiments, generation (docs/phase6_prereg.md, 2026-11-21).

  bigbudget --model M [--budgets 256,512,1024]   E1: enforced 2x2 chains at larger budgets
  notrunc   --model M [--budgets 25,50]          E3b: truncation-free chains on the FULL cohort
                                                 (Phase-5 P0-2 protocol and cache; S100 replays)
  answers   --model M                            E5 / E2: natural-language target answers from
                                                 question-only, gold Oracle-All (untruncated) and
                                                 Model Oracle-All (M4 / M1) -> scored by the evaluator
  labels    --model M                            E4 (+E5, E2): direct label prediction from every memory;
                                                 no evaluator involved

Every row carries the target ICO and gold label (score_generic.py --self-ico).
Outputs: results/rev_{cmd}_{model}.jsonl (+ _mem.jsonl for the chain experiments).
"""
import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_phase4 import MODELS, chain, load_samples, material_text, spans_original, tokenizers  # noqa: E402
from run_phase5 import answer_from, notrunc_chain, oracle_memory  # noqa: E402
from supdrift.llm import LLMCache, chat, full_cache_key  # noqa: E402

BIG = [256, 512, 1024]
CELLS = [(m, c) for m in ("aware", "blind") for c in ("single", "multi")]
NO_NOTES = "(no working notes are available)"
MO_BUDGETS = [150, 256, 512, 1024]

LABEL_SYSTEM = """You are the final step of a multi-step biomedical research assistant pipeline.
Based on the working notes you receive, decide what they establish about the research question.
Answer with exactly one label:
Increase - the intervention significantly increased the outcome relative to the comparator
Decrease - the intervention significantly decreased the outcome relative to the comparator
No-Difference - there was no significant difference between the intervention and the comparator on the outcome
Uncertain - the notes do not establish any of the above for this question
Output only the label."""

LABEL_USER = """Research question: What is the effect of "{intervention}" compared with "{comparator}" on "{outcome}"?

Working notes:
{material}

Label:"""

# question-only forced guess: no notes, no Uncertain option (upper bound of memory-free answering)
GUESS_SYSTEM = """You are a biomedical research assistant. No study notes are available.
Give your best guess of what a randomized controlled trial found for the research question.
Answer with exactly one label:
Increase - the intervention significantly increased the outcome relative to the comparator
Decrease - the intervention significantly decreased the outcome relative to the comparator
No-Difference - there was no significant difference between the intervention and the comparator on the outcome
You must choose one of the three. Output only the label."""

GUESS_USER = """Research question: What is the effect of "{intervention}" compared with "{comparator}" on "{outcome}"?

Label:"""

LAB = [("NO_DIFFERENCE", r"no[\s\-_]*(significant\s+)?difference"), ("INCREASE", r"increase"),
       ("DECREASE", r"decrease"), ("UNCERTAIN", r"uncertain")]


def parse_label(raw):
    t = raw.strip().lower()
    hits = [(m.start(), lab) for lab, pat in LAB for m in [re.search(pat, t)] if m]
    return min(hits)[1] if hits else "UNPARSED"


def ico(s):
    t = s["target"]
    return {k: t[k] for k in ("prompt_id", "intervention", "comparator", "outcome", "gold_label")}


def dump(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {path}: {len(rows)} rows", flush=True)


def mem_rows(rows):
    return [{**{k: v for k, v in r.items() if k not in ("text", "steps", "memory")}, "text": r["memory"]}
            for r in rows if r.get("memory")]


def model_oracle(model, samples, enc):
    """sample_id -> {stage: (memory, n_tokens)}: the model's own independent candidate memories
    (P2-5b free-form chains), concatenated in the article's span order."""
    by = {}
    for r in map(json.loads, open(f"results/freeform_{model}.jsonl")):
        by.setdefault(r["sample_id"], []).append(r)
    out = {}
    for s in samples:
        cands = sorted(by[s["sample_id"]], key=lambda r: r["position"])
        assert len(cands) == 1 + len(s["distractors"])
        out[s["sample_id"]] = {}
        for stage in ("m4", "m1"):
            mem = "\n".join(f"- {c[stage]}" for c in cands)
            out[s["sample_id"]][stage] = (mem, len(enc(model, mem)))
    return out


class Runner:
    def __init__(self, args):
        self.model = args.model
        self.samples = load_samples()
        if args.limit:
            self.samples = self.samples[: args.limit]
        self.tag = "_smoke" if args.limit else ""
        self.enc, self.dec = tokenizers()
        self.sem = asyncio.Semaphore(args.concurrency)
        self.rows, self.done, self.lock = [], 0, asyncio.Lock()

    async def add(self, coro, total):
        r = await coro
        async with self.lock:
            self.rows.extend(r if isinstance(r, list) else [r])
            self.done += 1
            if self.done % 500 == 0:
                print(f"  {self.done}/{total}", flush=True)

    async def gather(self, jobs):
        print(f"{len(jobs)} jobs", flush=True)
        await asyncio.gather(*[self.add(j, len(jobs)) for j in jobs])
        order = {s["sample_id"]: i for i, s in enumerate(self.samples)}
        self.rows.sort(key=lambda r: (order[r["sample_id"]], str(r.get("source", "")), r.get("budget", 0),
                                      str(r.get("mode", "")), str(r.get("cond", ""))))

    # ------------------------------------------------------------------ E1
    async def bigbudget(self, budgets):
        cache = LLMCache(f"cache/rev_{self.model}.jsonl")

        async def one(s, b, mode, cond):
            r = await chain(self.model, s, spans_original(s, cond), mode=mode, budget=b, depth=5, cache=cache,
                            sem=self.sem, enc=self.enc, dec=self.dec, exp="bigbudget", cond=cond)
            r.update(ico(s))
            return r
        await self.gather([one(s, b, m, c) for s in self.samples for b in budgets for m, c in CELLS])
        dump(f"results/rev_bigbudget_{self.model}{self.tag}.jsonl", self.rows)
        dump(f"results/rev_bigbudget_{self.model}_mem{self.tag}.jsonl", mem_rows(self.rows))
        for b in budgets:
            g = [r for r in self.rows if r["budget"] == b]
            print(f"  B={b}: forced {sum(r['forced'] for r in g) / len(g):.1%}, mean realized length "
                  f"{sum(r['steps'][-1]['raw_tokens'] for r in g) / len(g):.0f} tokens", flush=True)

    # ------------------------------------------------------------------ E3b
    async def notrunc(self, budgets):
        cache = LLMCache(f"cache/phase5_{self.model}.jsonl")

        async def one(s, b, mode, cond):
            r = await notrunc_chain(self.model, s, spans_original(s, cond), mode, cond, b, cache, self.sem, self.enc)
            r.update(ico(s))
            return r
        await self.gather([one(s, b, m, c) for s in self.samples for b in budgets for m, c in CELLS])
        dump(f"results/rev_notrunc_{self.model}{self.tag}.jsonl", self.rows)
        ok = [r for r in self.rows if not r["failed"]]
        dump(f"results/rev_notrunc_{self.model}_ok{self.tag}.jsonl", [{k: v for k, v in r.items() if k != "memory"} for r in ok])
        dump(f"results/rev_notrunc_{self.model}_mem{self.tag}.jsonl", mem_rows(ok))
        for b in budgets:
            for m, c in CELLS:
                g = [r for r in self.rows if r["budget"] == b and r["mode"] == m and r["cond"] == c]
                print(f"  B={b} {m}/{c}: failed {sum(r['failed'] for r in g) / len(g):.1%}", flush=True)

    # ------------------------------------------------------------------ E5 / E2 answers
    async def answers(self):
        cache = LLMCache(f"cache/rev_{self.model}.jsonl")
        mo = model_oracle(self.model, self.samples, self.enc)

        async def one(s, source, memory, extra):
            text = await answer_from(self.model, s, memory, s["target"], cache, self.sem, f"rev-{source}")
            return {"sample_id": s["sample_id"], **ico(s), "source": source, **extra, "memory": memory, "text": text}
        jobs = []
        for s in self.samples:
            jobs.append(one(s, "question_only", NO_NOTES, {}))
            g = oracle_memory(s, "short", "oracle_all")
            jobs.append(one(s, "gold_oracle_all", g, {"n_tokens": len(self.enc(self.model, g))}))
            for stage in ("m4", "m1"):
                mem, n = mo[s["sample_id"]][stage]
                jobs.append(one(s, f"model_oracle_{stage}", mem, {"n_tokens": n}))
        await self.gather(jobs)
        dump(f"results/rev_answers_{self.model}{self.tag}.jsonl", self.rows)

    # ------------------------------------------------------------------ E4 labels
    async def labels(self):
        cache = LLMCache(f"cache/rev_{self.model}.jsonl")
        m = self.model
        ids = {s["sample_id"]: s for s in self.samples}

        async def one(s, source, memory, extra, guess=False):
            t = s["target"]
            q = {k: t[k] for k in ("intervention", "comparator", "outcome")}
            msgs = ([{"role": "system", "content": GUESS_SYSTEM}, {"role": "user", "content": GUESS_USER.format(**q)}]
                    if guess else
                    [{"role": "system", "content": LABEL_SYSTEM},
                     {"role": "user", "content": LABEL_USER.format(material=memory, **q)}])
            key = full_cache_key(m, {"task": "rev_guess" if guess else "rev_label", "sid": s["sample_id"],
                                     "pid": t["prompt_id"], "material": None if guess else memory})
            raw = (await chat(m, msgs, cache=cache, cache_key=key, sem=self.sem,
                              temperature=0.0, seed=42, max_tokens=8)).strip()
            pred = parse_label(raw)
            return {"sample_id": s["sample_id"], "source": source, **extra, "gold_label": t["gold_label"],
                    "label_raw": raw, "pred_label": pred, "correct": pred == t["gold_label"]}

        jobs = []
        # enforced chains: committed budgets + the new large budgets
        for path, src in ((f"results/phase4_budget_{m}.jsonl", "enforced"), (f"results/rev_bigbudget_{m}.jsonl", "enforced"),
                          (f"results/rev_notrunc_{m}.jsonl", "notrunc")):
            if not Path(path).exists():
                print(f"  (skipping {path}: not generated yet)", flush=True); continue
            for r in map(json.loads, open(path)):
                if r["sample_id"] in ids and r.get("memory"):
                    jobs.append(one(ids[r["sample_id"]], src, r["memory"],
                                    {"mode": r["mode"], "cond": r["cond"], "budget": r["budget"]}))
        mo = model_oracle(m, self.samples, self.enc)
        for s in self.samples:
            jobs.append(one(s, "question_only", NO_NOTES, {}))
            jobs.append(one(s, "question_only_guess", None, {}, guess=True))
            for cond in ("single", "multi"):
                jobs.append(one(s, "full_evidence", material_text(s["pmcid"], spans_original(s, cond)), {"cond": cond}))
            jobs.append(one(s, "gold_oracle_all", oracle_memory(s, "short", "oracle_all"), {}))
            jobs.append(one(s, "gold_oracle_target", oracle_memory(s, "short", "oracle_target"), {}))
            for stage in ("m4", "m1"):
                mem, n = mo[s["sample_id"]][stage]
                jobs.append(one(s, f"model_oracle_{stage}", mem, {"n_tokens": n}))
        await self.gather(jobs)
        dump(f"results/rev_labels_{m}{self.tag}.jsonl", self.rows)
        up = sum(r["pred_label"] == "UNPARSED" for r in self.rows)
        print(f"  unparsed labels: {up} / {len(self.rows)}", flush=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["bigbudget", "notrunc", "answers", "labels"])
    ap.add_argument("--model", required=True, choices=MODELS)
    ap.add_argument("--budgets", default=None)
    ap.add_argument("--concurrency", type=int, default=24)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    r = Runner(args)
    b = [int(x) for x in args.budgets.split(",")] if args.budgets else None
    if args.cmd == "bigbudget":
        await r.bigbudget(b or BIG)
    elif args.cmd == "notrunc":
        await r.notrunc(b or [25, 50])
    elif args.cmd == "answers":
        await r.answers()
    else:
        await r.labels()
    print(f"REV_DONE {args.cmd} {args.model}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
