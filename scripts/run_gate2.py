"""Run the Gate 2 grid for one model.

Conditions per sample:
  depth 1: mode "direct" x icoset {single, multi}          (budget-independent)
  depth 5: mode {aware, blind} x icoset {single, multi} x budget {50, 25}

= 2 + 8 chains (42 LLM calls) per sample.

Usage: run_gate2.py --model qwen3-8b [--n N] [--concurrency 32]
Output: results/gate2_chains_{model}.jsonl
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from supdrift.chain2 import run_chain2
from supdrift.llm import LLMCache

DEPTH_MAIN = 5
BUDGETS = [50, 25]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--input", default="data/gate2/gate2_v1.jsonl")
    args = ap.parse_args()

    samples = [json.loads(l) for l in open(args.input)]
    if args.n:
        samples = samples[: args.n]

    conditions = [("direct", "single", 1, 0), ("direct", "multi", 1, 0)] + [
        (mode, icoset, DEPTH_MAIN, b)
        for mode in ("aware", "blind") for icoset in ("single", "multi") for b in BUDGETS
    ]

    cache = LLMCache(f"cache/gate2_chains_{args.model}.jsonl")
    sem = asyncio.Semaphore(args.concurrency)
    out_path = Path(f"results/gate2_chains_{args.model}.jsonl")
    out_path.parent.mkdir(exist_ok=True)
    out_f = open(out_path, "w")
    lock = asyncio.Lock()
    done, total = 0, len(samples) * len(conditions)

    async def run_one(sample, mode, icoset, depth, budget):
        nonlocal done
        try:
            steps = await run_chain2(sample, model_name=args.model, mode=mode,
                                     icoset=icoset, depth=depth, budget=budget,
                                     cache=cache, sem=sem)
            err = None
        except Exception as e:
            steps, err = None, f"{type(e).__name__}: {e}"
        async with lock:
            base = {"sample_id": sample["sample_id"], "model": args.model,
                    "mode": mode, "icoset": icoset, "depth": depth, "budget": budget}
            if steps is None:
                out_f.write(json.dumps({**base, "error": err}) + "\n")
            else:
                for s in steps:
                    out_f.write(json.dumps({**base, **s}, ensure_ascii=False) + "\n")
            done += 1
            if done % 100 == 0:
                out_f.flush()
                print(f"{done}/{total} chains", flush=True)

    await asyncio.gather(*[run_one(s, *c) for s in samples for c in conditions])
    out_f.close()
    print(f"done: {total} chains -> {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
