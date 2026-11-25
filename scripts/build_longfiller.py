"""E14 length-matched control for E13 (docs/phase6_prereg.md, 2026-11-22).

For every E13 long source, build a source of the same structure and length in which the target finding is the
ONLY finding: every other evidence span is replaced by non-finding prose from the same trial's article
(sentences from body sections before the Results, with any sentence that could carry a finding removed —
the Phase-4 filler definition), token-matched span by span (o200k_base). Block order, headers and the position
of the target span are unchanged. Sentences are never reused inside a source. When a trial's own prose is
insufficient, the remainder is taken from the other trials of the same source (flagged).

Output: data/longsource/longfiller_v1.jsonl  (sample_id, pmcid, blocks, n_tokens_ref, long_tokens_ref,
        n_filler_spans, n_borrowed_spans, constructible)
"""
import json
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_longsource import ntok, render  # noqa: E402
from build_phase4_materials import filler_sentences  # noqa: E402
from run_phase4 import load_samples  # noqa: E402

OUT = Path("data/longsource/longfiller_v1.jsonl")


def fill(want, pool):
    """Whole sentences from `pool` (list of [sentence, tokens], consumed) best-fitted to `want` tokens."""
    parts, have = [], 0
    while pool and have < want - 4:
        fits = [p for p in pool if p[1] <= want - have + 6]
        pick = max(fits, key=lambda p: p[1]) if fits else min(pool, key=lambda p: p[1])
        if not fits and have > 0 and abs(want - have) <= abs(want - have - pick[1]):
            break                                     # adding the shortest sentence would overshoot more than stopping
        pool.remove(pick); parts.append(pick[0]); have += pick[1]
    return " ".join(parts), have


def main():
    samples = {s["sample_id"]: s for s in load_samples()}
    longs = [json.loads(l) for l in open("data/longsource/longsource_v1.jsonl")]
    sent_cache = {}
    rows = []
    for L in longs:
        s = samples[L["sample_id"]]
        tgt = s["target"]["evidence"]
        rng = random.Random(f"{L['sample_id']}-filler")
        pools = {}
        for b in L["blocks"]:
            if b["pmcid"] not in sent_cache:
                sent_cache[b["pmcid"]] = [(x, ntok(x)) for x in filler_sentences(b["pmcid"])]
            p = [list(x) for x in sent_cache[b["pmcid"]]]
            rng.shuffle(p); pools[b["pmcid"]] = p
        blocks, n_fill, n_borrow, ok, carry = [], 0, 0, True, 0
        for b in L["blocks"]:
            spans = []
            for sp in b["spans"]:
                if b["sample_id"] == L["sample_id"] and sp == tgt:
                    spans.append(sp); continue
                want = max(12, ntok(sp) - carry)       # carry = tokens over (+) / under (-) so far: totals stay matched
                text, have = fill(want, pools[b["pmcid"]])
                if have < want - 10:                   # own prose exhausted: borrow from the other trials of this source
                    reserve = [p for k, v in pools.items() if k != b["pmcid"] for p in v]
                    more, got = fill(want - have, reserve)
                    used = set(more_s for more_s in [x[0] for x in [p for k, v in pools.items() for p in v]] if more and more_s in more)
                    for k in pools:                    # consume what was borrowed
                        pools[k] = [p for p in pools[k] if p[0] not in used]
                    text = (text + " " + more).strip(); have += got; n_borrow += 1
                if not text:
                    ok = False
                carry += have - ntok(sp)
                spans.append(text or sp); n_fill += 1
            blocks.append({"pmcid": b["pmcid"], "sample_id": b["sample_id"], "spans": spans})
        mat = render(blocks)
        assert tgt in mat
        rows.append({"sample_id": L["sample_id"], "pmcid": L["pmcid"], "blocks": blocks, "n_tokens_ref": ntok(mat),
                     "long_tokens_ref": L["n_tokens_ref"], "n_filler_spans": n_fill, "n_borrowed_spans": n_borrow,
                     "constructible": bool(ok and abs(ntok(mat) - L["n_tokens_ref"]) <= 0.05 * L["n_tokens_ref"])})
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n = np.array([r["n_tokens_ref"] for r in rows]); d = n - np.array([r["long_tokens_ref"] for r in rows])
    print(f"wrote {OUT}: {len(rows)} sources; constructible {sum(r['constructible'] for r in rows)}; tokens mean {n.mean():.0f} "
          f"(min {n.min()}, max {n.max()}); filler − long: mean {d.mean():+.1f}, p5 {np.percentile(d, 5):+.0f}, p95 {np.percentile(d, 95):+.0f}; "
          f"sources with a borrowed span {sum(r['n_borrowed_spans'] > 0 for r in rows)}; filler spans per source {np.mean([r['n_filler_spans'] for r in rows]):.1f}")


if __name__ == "__main__":
    main()
