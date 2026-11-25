"""Score any finals-style JSONL with the frozen classifier.

Rows may carry their own ICO/gold (answerability output) or reference the
gate2_v1 target (everything else).

Usage: score_generic.py --chains F --out CSV [--self-ico] [--concurrency 24]
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
    ap.add_argument("--chains", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--self-ico", action="store_true",
                    help="rows carry intervention/comparator/outcome/gold_label themselves")
    ap.add_argument("--concurrency", type=int, default=24)
    args = ap.parse_args()

    meta = {json.loads(l)["sample_id"]: json.loads(l)["target"]
            for l in open("data/gate2/gate2_v1.jsonl")}
    rows = [json.loads(l) for l in open(args.chains)]
    # one scoring process at a time: two concurrent writers judged the same items twice and left
    # conflicting duplicates in the cache (fixed 2026-09-29, scripts/build_canonical.py)
    # SUPDRIFT_SCORE_CACHE (2026-11-21): a parallel scorer writes to its own shard and only READS the
    # canonical cache, so two evaluator servers can be used at once without duplicate writes; shards are
    # merged afterwards by scripts/merge_score_cache.py (keys already in the canonical cache are kept).
    import fcntl
    import os
    canonical = "cache/classifier_scoring.jsonl"
    path = os.environ.get("SUPDRIFT_SCORE_CACHE", canonical)
    lock = open(path[:-6] + ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(f"another scoring process holds the lock of {path} — run scoring sequentially per cache")
    cache = LLMCache(path)
    if path != canonical:
        for line in open(canonical):
            rec = json.loads(line)
            cache._mem.setdefault(rec["key"], rec["response"])
    sem = asyncio.Semaphore(args.concurrency)
    done = 0

    async def score(rec):
        nonlocal done
        t = rec if args.self_ico else meta[rec["sample_id"]]
        try:
            res = await classify(t["intervention"], t["comparator"], t["outcome"],
                                 rec["text"], cache=cache, sem=sem)
        except Exception as e:
            print(f"EVAL_ERROR {rec.get('sample_id')}: {type(e).__name__}", flush=True)
            res = {"claim_label": "EVAL_ERROR", "direction": "EVAL_ERROR",
                   "certainty": "EVAL_ERROR"}
        done += 1
        if done % 500 == 0:
            print(f"{done}/{len(rows)} scored", flush=True)
        base = {k: v for k, v in rec.items() if k != "text"}
        base["gold_label"] = t["gold_label"]
        base["claim_label"] = res["claim_label"]
        base["direction"] = res["direction"]
        base["certainty"] = res["certainty"]
        base["supported"] = res["claim_label"] == t["gold_label"]
        return base

    scored = await asyncio.gather(*[score(r) for r in rows])
    df = pd.DataFrame(scored)
    # generations can contain NUL / CR characters, which the csv writer cannot
    # quote ("need to escape, but no escapechar set"); strip them, keep an escapechar
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].map(lambda v: v.replace("\x00", "").replace("\r", " ") if isinstance(v, str) else v)
    df.to_csv(args.out, index=False, escapechar="\\")
    n_err = sum(1 for r in scored if r["claim_label"] in ("EVAL_ERROR", "PARSE_ERROR"))
    print(f"wrote {args.out} ({len(scored)} rows, {n_err} dirty)")


if __name__ == "__main__":
    asyncio.run(main())
