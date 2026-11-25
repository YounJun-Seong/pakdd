"""Score chain outputs with the ICO claim classifier.

Reads results/chains_{model}.jsonl, classifies every step text against its ICO,
joins gold labels, and writes the long-format scoring table used for all
Gate 1 analysis:

results/scored_{model}.csv with columns
  sample_id, gold_label, model, depth, budget, step, role,
  direction, certainty, claim_label, supported,
  citation_present, citation_correct

supported := claim_label == gold_label (definitive claim matching gold).

Usage: score_chains.py --model qwen3-8b [--concurrency 32]
"""
import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from supdrift.classifier import classify
from supdrift.llm import LLMCache


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--concurrency", type=int, default=32)
    args = ap.parse_args()

    pilot = pd.read_json("data/pilot/pilot_v2.jsonl", lines=True)
    meta = pilot.set_index("sample_id")[
        ["intervention", "comparator", "outcome", "gold_label"]
    ].to_dict(orient="index")

    rows = []
    with open(f"results/chains_{args.model}.jsonl") as f:
        for line in f:
            rec = json.loads(line)
            if "error" not in rec:
                rows.append(rec)
    print(f"{len(rows)} step outputs to score")

    cache = LLMCache("cache/classifier_scoring.jsonl")
    sem = asyncio.Semaphore(args.concurrency)
    done = 0

    async def score(rec):
        nonlocal done
        m = meta[rec["sample_id"]]
        try:
            res = await classify(
                m["intervention"], m["comparator"], m["outcome"], rec["text"],
                cache=cache, sem=sem,
            )
        except Exception as e:
            print(f"EVAL_ERROR {rec['sample_id']} step{rec['step']}: {type(e).__name__}", flush=True)
            res = {"direction": "EVAL_ERROR", "certainty": "EVAL_ERROR",
                   "claim_label": "EVAL_ERROR"}
        done += 1
        if done % 500 == 0:
            print(f"{done}/{len(rows)} scored", flush=True)
        return {
            "sample_id": rec["sample_id"],
            "gold_label": m["gold_label"],
            "model": rec["model"],
            "depth": rec["depth"],
            "budget": rec["budget"],
            "step": rec["step"],
            "role": rec["role"],
            "direction": res["direction"],
            "certainty": res["certainty"],
            "claim_label": res["claim_label"],
            "supported": res["claim_label"] == m["gold_label"],
            "citation_present": rec["citation_present"],
            "citation_correct": rec["citation_correct"],
        }

    scored = await asyncio.gather(*[score(r) for r in rows])
    df = pd.DataFrame(scored)
    out = f"results/scored_{args.model}.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} rows)")


if __name__ == "__main__":
    asyncio.run(main())
