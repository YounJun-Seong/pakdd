"""Prune Gate 2 candidates to targets the FROZEN evaluator grounds from the
gold span (classifier(gold span) == gold). Runs the frozen classifier v3; no
prompt/rule changes. Residual NOT_MENTIONED targets are dropped (same rationale
as the pilot's human-audited exclusions; a human audit of a sample of these is
scheduled with the Phase-4 annotation).

Output: data/gate2/gate2_v1.jsonl (verified, ~100 per label)
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from supdrift.classifier import classify
from supdrift.llm import LLMCache

N_PER_LABEL = 100
CONCURRENCY = 32


async def main():
    cands = [json.loads(l) for l in open("data/gate2/gate2_candidates.jsonl")]
    cache = LLMCache("cache/gate2_verify.jsonl")
    sem = asyncio.Semaphore(CONCURRENCY)

    async def check(rec):
        t = rec["target"]
        res = await classify(t["intervention"], t["comparator"], t["outcome"],
                             t["evidence"], cache=cache, sem=sem)
        return rec, res["claim_label"] == t["gold_label"]

    results = await asyncio.gather(*[check(r) for r in cands])
    kept, used = [], {"INCREASE": 0, "NO_DIFFERENCE": 0, "DECREASE": 0}
    for rec, ok in results:
        lab = rec["target"]["gold_label"]
        if ok and used[lab] < N_PER_LABEL:
            used[lab] += 1
            kept.append(rec)
    grounded = sum(1 for _, ok in results if ok)
    print(f"grounded targets: {grounded}/{len(cands)} ({grounded/len(cands):.1%})")
    print(f"kept (capped {N_PER_LABEL}/label): {used}")

    with open("data/gate2/gate2_v1.jsonl", "w") as f:
        for rec in kept:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"wrote data/gate2/gate2_v1.jsonl ({len(kept)} articles)")


if __name__ == "__main__":
    asyncio.run(main())
