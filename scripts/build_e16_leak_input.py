"""Phase-6 E16 evaluator leak screen, input (docs/phase6_prereg.md, 2026-11-23): each constructible filler source
with every occurrence of the target sentence removed, to be classified for the target question by the frozen
evaluator. Expected label: NOT_MENTIONED. Output: results/e16/e16_leak_input.jsonl"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_longsource import render  # noqa: E402
from run_phase4 import load_samples  # noqa: E402
from run_rev import ico  # noqa: E402

S = {s["sample_id"]: s for s in load_samples()}
n = 0
with open("results/e16/e16_leak_input.jsonl", "w") as out:
    for f in map(json.loads, open("data/longsource/longfiller_v1.jsonl")):
        if not f["constructible"]:
            continue
        s = S[f["sample_id"]]; tgt = s["target"]["evidence"]
        blocks = [{**b, "spans": [sp for sp in b["spans"] if not (b["sample_id"] == f["sample_id"] and sp == tgt)]} for b in f["blocks"]]
        blocks = [b for b in blocks if b["spans"]]
        text = render(blocks)
        assert tgt not in text
        out.write(json.dumps({"sample_id": f["sample_id"], **ico(s), "exp": "e16_leak", "text": text}, ensure_ascii=False) + "\n"); n += 1
print(f"wrote results/e16/e16_leak_input.jsonl: {n} sources")
