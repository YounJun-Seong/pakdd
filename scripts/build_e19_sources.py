"""Phase-6 E19 length-position control (docs/phase6_prereg.md, 2026-11-23): sources. No generation, no scoring.

For every constructible E14 filler source (data/longsource/longfiller_v1.jsonl) build 3 position arms x 3 length
levels in which the target finding is the ONLY finding, occurs exactly once, and sits at a fixed position:

  first   the home block is the first block and the target its first bullet  (nothing but the header before it)
  middle  equal amounts of filler before and after the target                (relative position 0.5)
  last    the home block is the last block and the target its last bullet    (nothing after it)

  level 200 / 500   the filler nearest to the target, extended outward sentence by sentence until the rendered
                    source reaches the level (o200k_base reference tokens, the tokenizer of E13 / E14)
  level 1000        all filler material of the E14 source

The sources of one arm are NESTED (200 within 500 within 1000): a longer source only adds filler farther away from
the target. Filler text, block headers and the rendering are those of E14; nothing is rewritten. A filler bullet
at the edge of a window may be cut at a sentence boundary; a block without bullets is dropped. Other blocks keep
their E14 relative order; home filler bullets keep theirs.

Output: data/longsource/e19_sources_v1.jsonl (one row per article x arm x level) and
        results/e19/e19_sources_summary.csv
"""
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_audit_e16_e17 import STAT_RE  # noqa: E402
from build_longsource import ntok, render  # noqa: E402
from run_phase4 import load_samples  # noqa: E402

OUT = Path("data/longsource/e19_sources_v1.jsonl")
ARMS = ("first", "middle", "last")
LEVELS = (200, 500, 1000)
TOL = {200: (170, 230), 500: (425, 575), 1000: (850, 1100)}     # +-15 % of the level; 1000 = all material
CENTRE = (1 / 3, 2 / 3)                                           # middle arm: target centre in the middle third
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(])")


def sents(span):
    return [x for x in SPLIT.split(span) if x.strip()]


def assemble(order, tgt, home_id, take):
    """order: list of (block, side) in reading order; take[(pmcid, span_idx)] = list of kept sentences.
    The home block is [before bullets..., target, after bullets...]."""
    blocks = []
    for b, _ in order:
        spans = []
        for si, kind in b["slots"]:
            if kind == "target":
                spans.append(tgt)
            elif take.get((b["pmcid"], si)):
                spans.append(" ".join(take[(b["pmcid"], si)]))
        if spans:
            blocks.append({"pmcid": b["pmcid"], "sample_id": b["sample_id"], "spans": spans})
    return blocks


def plan(f, tgt, arm):
    """Reading order of blocks and, per side, the filler bullets ordered outward from the target."""
    home = next(b for b in f["blocks"] if b["sample_id"] == f["sample_id"])
    others = [b for b in f["blocks"] if b["sample_id"] != f["sample_id"]]
    hfill = [s for s in home["spans"] if s != tgt]                       # duplicates of the target are dropped
    cost = lambda b: ntok(render([{"pmcid": b["pmcid"], "spans": b["spans"]}]))  # noqa: E731
    if arm == "first":
        i, pre = 0, []
    elif arm == "last":
        i, pre = len(hfill), list(range(len(others)))
    else:                                                                # balance filler tokens around the target
        best = None
        oc = [cost(b) for b in others]; hc = [ntok(s) for s in hfill]
        for i_ in range(len(hfill) + 1):
            for r in range(len(others) + 1):
                for sub in itertools.combinations(range(len(others)), r):
                    before = sum(oc[j] for j in sub) + sum(hc[:i_])
                    after = sum(oc) - sum(oc[j] for j in sub) + sum(hc[i_:])
                    k = (abs(before - after), i_, sub)
                    if best is None or k < best:
                        best = k
        _, i, pre = best
    hb = {"pmcid": home["pmcid"], "sample_id": home["sample_id"], "fill": hfill,
          "slots": [(j, "fill") for j in range(i)] + [(-1, "target")] + [(j, "fill") for j in range(i, len(hfill))]}
    ob = [{"pmcid": b["pmcid"], "sample_id": b["sample_id"], "fill": b["spans"], "slots": [(j, "fill") for j in range(len(b["spans"]))]} for b in others]
    order = [(ob[j], "before") for j in pre] + [(hb, "home")] + [(ob[j], "after") for j in range(len(ob)) if j not in pre]
    # sentence queues, nearest to the target first
    before = [(hb["pmcid"], j, k, s) for j in reversed(range(i)) for k, s in reversed(list(enumerate(sents(hfill[j]))))]
    for j in reversed(list(pre)):
        for si in reversed(range(len(ob[j]["fill"]))):
            before += [(ob[j]["pmcid"], si, k, s) for k, s in reversed(list(enumerate(sents(ob[j]["fill"][si]))))]
    after = [(hb["pmcid"], j, k, s) for j in range(i, len(hfill)) for k, s in enumerate(sents(hfill[j]))]
    for j in range(len(ob)):
        if j not in pre:
            for si in range(len(ob[j]["fill"])):
                after += [(ob[j]["pmcid"], si, k, s) for k, s in enumerate(sents(ob[j]["fill"][si]))]
    return order, before, after


def window(order, before, after, tgt, home_id, level):
    """Extend outward from the target, always on the side that currently has fewer tokens (one-sided arms have one
    queue), until the rendered source reaches `level`; stop at the first sentence that would overshoot, unless it
    lands closer to the level."""
    take, nb, na = {}, 0, 0
    qb, qa = list(before), list(after)

    def add(q, side):
        p, si, k, s = q[0]
        t = dict(take); cur = list(t.get((p, si), []))
        t[(p, si)] = ([s] + cur) if side == "b" else (cur + [s])
        return t

    cur = ntok(render(assemble(order, tgt, home_id, take)))
    while qb or qa:
        first = "b" if (qb and (not qa or nb <= na)) else "a"
        done = True
        for side in (first, "a" if first == "b" else "b"):            # the lighter side first; the other side only if that overshoots
            q = qb if side == "b" else qa
            if not q:
                continue
            t = add(q, side); n = ntok(render(assemble(order, tgt, home_id, t)))
            if level != 1000 and n > level and abs(n - level) >= abs(cur - level):
                continue
            take = t
            if side == "b":
                nb += n - cur
            else:
                na += n - cur
            cur = n; q.pop(0); done = False
            break
        if done or (level != 1000 and cur >= level):
            break
    return assemble(order, tgt, home_id, take)


def main():
    samples = {s["sample_id"]: s for s in load_samples()}
    F = [json.loads(l) for l in open("data/longsource/longfiller_v1.jsonl")]
    rows = []
    for f in F:
        if not f["constructible"]:
            continue
        tgt = samples[f["sample_id"]]["target"]["evidence"]
        for arm in ARMS:
            order, before, after = plan(f, tgt, arm)
            prev = None
            for level in LEVELS:
                blocks = window(order, before, after, tgt, f["sample_id"], level)
                mat = render(blocks)
                assert mat.count(tgt) == 1, (f["sample_id"], arm, level)
                pos = mat.find(tgt)
                n, nb, nt = ntok(mat), ntok(mat[:pos]), ntok(tgt)
                fill = [x for b in blocks for sp in b["spans"] if sp != tgt for x in sents(sp)]
                if prev is not None:
                    assert set(prev) <= set(fill), (f["sample_id"], arm, level)       # nested
                prev = fill
                rows.append({"sample_id": f["sample_id"], "pmcid": f["pmcid"], "arm": arm, "level": level, "blocks": blocks,
                             "n_tokens_ref": n, "tokens_before": nb, "target_tokens": nt, "tokens_after": max(0, n - nb - nt),
                             "rel_centre": (nb + nt / 2) / n, "n_blocks": len(blocks), "n_filler_sentences": len(fill),
                             "stat_marker": any(bool(STAT_RE.search(sp)) for b in blocks for sp in b["spans"] if sp != tgt),
                             "in_tolerance": bool(TOL[level][0] <= n <= TOL[level][1] and len(fill) >= 1
                                                  and (arm != "middle" or CENTRE[0] <= (nb + nt / 2) / n <= CENTRE[1]))})
    D = pd.DataFrame(rows)
    ok = D.groupby("sample_id").in_tolerance.all()
    D["constructible"] = D.sample_id.map(ok)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as fh:
        for r in D.to_dict("records"):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    Path("results/e19").mkdir(parents=True, exist_ok=True)
    q = lambda x: f"{x.mean():.0f} [{x.min():.0f}, {x.max():.0f}]"  # noqa: E731
    S = D.groupby(["arm", "level"], sort=False).agg(n=("sample_id", "size"), in_tolerance=("in_tolerance", "sum"),
                                                     tokens=("n_tokens_ref", q), before=("tokens_before", q), after=("tokens_after", q),
                                                     rel_centre=("rel_centre", lambda x: f"{x.mean():.2f} [{x.min():.2f}, {x.max():.2f}]"),
                                                     blocks=("n_blocks", "mean"), filler_sentences=("n_filler_sentences", "mean"),
                                                     stat_marker=("stat_marker", "sum")).reset_index()
    S.round(2).to_csv("results/e19/e19_sources_summary.csv", index=False)
    print(S.to_string(index=False))
    print(f"articles: {D.sample_id.nunique()}; constructible in all 9 sources: {int(ok.sum())}; "
          f"out of tolerance by cell: {D[~D.in_tolerance].groupby(['arm', 'level']).size().to_dict()}")
    print("excluded:", sorted(ok[~ok].index))


if __name__ == "__main__":
    main()
