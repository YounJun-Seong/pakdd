"""Merge parallel scoring shards (SUPDRIFT_SCORE_CACHE) into the canonical evaluator cache.
A key already present in the canonical cache is never overwritten; within the shards the first
write wins. Shards are renamed *.merged afterwards.   usage: merge_score_cache.py shard.jsonl [...]"""
import json
import os
import sys

CANON = "cache/classifier_scoring.jsonl"
seen = {json.loads(l)["key"] for l in open(CANON)}
added = skipped = 0
with open(CANON, "a") as out:
    for shard in sys.argv[1:]:
        for l in open(shard):
            k = json.loads(l)["key"]
            if k in seen:
                skipped += 1
                continue
            seen.add(k); out.write(l if l.endswith("\n") else l + "\n"); added += 1
        os.rename(shard, shard + ".merged")
print(f"merged {added} new keys into {CANON} ({skipped} already present); total {len(seen)}")
