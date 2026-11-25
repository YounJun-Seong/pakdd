"""Validate the ICO claim classifier against Evidence Inference gold labels.

Feeds the classifier the GOLD evidence span for each pilot example; the derived
claim label should recover the dataset's gold effect label. This is the
zero-annotation sanity check that must pass before any SR curve is trusted.

Usage: validate_classifier.py [N]   (default: full pilot set)
"""
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from supdrift.classifier import CLASSIFIER_MODEL, classify
from supdrift.llm import LLMCache

CONCURRENCY = 16
OUT = Path("results/classifier_validation.jsonl")


async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else None
    pilot = pd.read_json("data/pilot/pilot_v2.jsonl", lines=True)
    if n:
        pilot = pilot.head(n)

    cache = LLMCache("cache/classifier_validation.jsonl")
    sem = asyncio.Semaphore(CONCURRENCY)

    async def run_one(rec):
        res = await classify(
            rec["intervention"], rec["comparator"], rec["outcome"], rec["evidence"],
            cache=cache, sem=sem,
        )
        return {
            "sample_id": rec["sample_id"],
            "gold_label": rec["gold_label"],
            "direction": res["direction"],
            "certainty": res["certainty"],
            "claim_label": res["claim_label"],
        }

    recs = pilot.to_dict(orient="records")
    results = await asyncio.gather(*[run_one(r) for r in recs])

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    df = pd.DataFrame(results)
    strict_acc = (df["claim_label"] == df["gold_label"]).mean()
    # direction-level accuracy ignores hedging (gold spans sometimes report
    # a direction with hedged language even when the label is definitive)
    dir_acc = (df["direction"] == df["gold_label"]).mean()

    print(f"model: {CLASSIFIER_MODEL}   n={len(df)}")
    print(f"strict accuracy (claim_label == gold): {strict_acc:.3f}")
    print(f"direction accuracy (direction == gold): {dir_acc:.3f}")

    # per-class P/R/F1 and macro-F1 over the 3 gold classes; UNCERTAIN /
    # NOT_MENTIONED predictions count as misses (recall loss)
    print("\nper-class metrics (claim_label vs gold):")
    f1s = {}
    for cls in ["INCREASE", "NO_DIFFERENCE", "DECREASE"]:
        tp = int(((df["claim_label"] == cls) & (df["gold_label"] == cls)).sum())
        fp = int(((df["claim_label"] == cls) & (df["gold_label"] != cls)).sum())
        fn = int(((df["claim_label"] != cls) & (df["gold_label"] == cls)).sum())
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1s[cls] = 2 * p * r / (p + r) if p + r else 0.0
        print(f"  {cls:<14} P={p:.3f} R={r:.3f} F1={f1s[cls]:.3f}")
    macro_f1 = sum(f1s.values()) / len(f1s)
    gate_a = "PASS" if macro_f1 >= 0.90 else "FAIL"
    print(f"macro-F1 = {macro_f1:.3f}  -> Gate A (>=0.90): {gate_a}")

    print("\nclaim_label distribution:", dict(Counter(df["claim_label"])))
    print("\nconfusion (rows=gold, cols=claim_label):")
    print(pd.crosstab(df["gold_label"], df["claim_label"]).to_string())

    # the confusion the user flagged as SR-threatening
    nd = df[df["gold_label"] == "NO_DIFFERENCE"]
    nd_to_unc = (nd["claim_label"] == "UNCERTAIN").mean()
    hedged = df[df["certainty"] == "HEDGED"]
    print(f"\nNO_DIFFERENCE -> UNCERTAIN rate: {nd_to_unc:.3f} "
          f"(hedged predictions overall: {len(hedged)}, "
          f"of which gold NO_DIFFERENCE: {int((hedged['gold_label']=='NO_DIFFERENCE').sum())})")

    print("\nconfusion (rows=gold, cols=direction):")
    print(pd.crosstab(df["gold_label"], df["direction"]).to_string())

    errs = df[df["direction"] != df["gold_label"]]
    print(f"\n{len(errs)} direction errors; first 10 sample_ids: {errs['sample_id'].head(10).tolist()}")


if __name__ == "__main__":
    asyncio.run(main())
