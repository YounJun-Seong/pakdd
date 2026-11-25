"""Score Gate 2 chain outputs with the FROZEN classifier against the target ICO.

Output: results/gate2_scored_{model}.csv
  sample_id, gold_label, model, mode, icoset, depth, budget, step, role,
  direction, certainty, claim_label, supported, citation_present, citation_correct

Usage: score_gate2.py --model qwen3-8b [--concurrency 24]
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
    ap.add_argument("--concurrency", type=int, default=24)
    args = ap.parse_args()

    meta = {}
    for line in open("data/gate2/gate2_v1.jsonl"):
        rec = json.loads(line)
        meta[rec["sample_id"]] = rec["target"]

    rows = [json.loads(l) for l in open(f"results/gate2_chains_{args.model}.jsonl")
            if '"error"' not in l]
    n0 = len(rows)
    # chains were generated on the candidate set; keep only verified targets
    rows = [r for r in rows if r["sample_id"] in meta]
    print(f"{len(rows)}/{n0} step outputs to score (verified targets only)")

    cache = LLMCache("cache/classifier_scoring.jsonl")  # shared with Gate 1 (frozen classifier)
    sem = asyncio.Semaphore(args.concurrency)
    done = 0

    async def score(rec):
        nonlocal done
        t = meta[rec["sample_id"]]
        try:
            res = await classify(t["intervention"], t["comparator"], t["outcome"],
                                 rec["text"], cache=cache, sem=sem)
        except Exception as e:
            print(f"EVAL_ERROR {rec['sample_id']} step{rec['step']}: {type(e).__name__}", flush=True)
            res = {"direction": "EVAL_ERROR", "certainty": "EVAL_ERROR",
                   "claim_label": "EVAL_ERROR"}
        done += 1
        if done % 500 == 0:
            print(f"{done}/{len(rows)} scored", flush=True)
        return {
            "sample_id": rec["sample_id"], "gold_label": t["gold_label"],
            "model": rec["model"], "mode": rec["mode"], "icoset": rec["icoset"],
            "depth": rec["depth"], "budget": rec["budget"],
            "step": rec["step"], "role": rec["role"],
            "direction": res["direction"], "certainty": res["certainty"],
            "claim_label": res["claim_label"],
            "supported": res["claim_label"] == t["gold_label"],
            "citation_present": rec["citation_present"],
            "citation_correct": rec["citation_correct"],
        }

    scored = await asyncio.gather(*[score(r) for r in rows])
    out = f"results/gate2_scored_{args.model}.csv"
    pd.DataFrame(scored).to_csv(out, index=False)
    print(f"wrote {out}")


if __name__ == "__main__":
    asyncio.run(main())
