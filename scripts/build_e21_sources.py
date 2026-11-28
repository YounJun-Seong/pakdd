"""Phase-6 E21 length x composition (docs/phase6_prereg.md, 2026-11-27): competing-finding sources. No generation.

For every article with an E14 filler source, build the COMPETING counterpart of the E19 `first` arm from the E13
long source (data/longsource/longsource_v1.jsonl): the home block is the first block, the target finding its first
bullet, and every other bullet is an annotated finding of the home trial or of another cohort trial.

  level 200 / 500   competing findings are tried in reading order (remaining home findings, then the other blocks in
                    their E13 order), whole findings only, until the rendered source reaches the level
                    (o200k_base reference tokens). A finding that keeps the source at or below the level is added;
                    one that overshoots is added only if the source stays within the upper tolerance and lands
                    closer to the level; otherwise it is skipped at this level. The 500 source extends the 200 one.
  level 1000        all findings of the E13 long source

Nested (200 within 500 within 1000). Nothing is rewritten or cut. Any bullet that is, contains or is contained in
the target sentence is dropped, so the target occurs exactly once. Rendering and block headers are those of E13.

The non-competing counterpart is the E19 `first` arm (data/longsource/e19_sources_v1.jsonl), unchanged.

Output: data/longsource/e21_sources_v1.jsonl (one row per article x level) and results/e21/e21_sources_summary.csv
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_e19_sources import LEVELS, TOL  # noqa: E402
from build_longsource import ntok, render  # noqa: E402
from run_phase4 import load_samples  # noqa: E402

OUT = Path("data/longsource/e21_sources_v1.jsonl")


def plan(L, tgt):
    """Home block first with the target as its first bullet; competitor queue in reading order."""
    home = L["blocks"][L["home_index"]]
    assert home["sample_id"] == L["sample_id"]
    clean = lambda sp: tgt not in sp and sp not in tgt  # noqa: E731
    order = [{"pmcid": home["pmcid"], "sample_id": home["sample_id"], "comp": [s for s in home["spans"] if clean(s)]}]
    order += [{"pmcid": b["pmcid"], "sample_id": b["sample_id"], "comp": [s for s in b["spans"] if clean(s)]}
              for i, b in enumerate(L["blocks"]) if i != L["home_index"]]
    dropped = sum(len(b["spans"]) for b in L["blocks"]) - sum(len(b["comp"]) for b in order)
    return order, dropped


def assemble(order, tgt, sel):
    """The target and the selected competitors (queue indices), in reading order."""
    blocks, q = [], 0
    for i, b in enumerate(order):
        take = [sp for j, sp in enumerate(b["comp"]) if q + j in sel]; q += len(b["comp"])
        spans = ([tgt] if i == 0 else []) + take
        if spans:
            blocks.append({"pmcid": b["pmcid"], "sample_id": b["sample_id"], "spans": spans})
    return blocks


def window(order, tgt, level, sel):
    """Extend the selection of the previous level. Findings are tried in reading order: one that keeps the source at
    or below the level is added; one that overshoots is added (and ends the scan) only if the source stays within
    the upper tolerance and lands closer to the level; otherwise it is skipped at this level."""
    total = sum(len(b["comp"]) for b in order)
    if level == 1000:
        return set(range(total))
    sel = set(sel); cur = ntok(render(assemble(order, tgt, sel)))
    for j in range(total):
        if cur >= level:
            break
        if j in sel:
            continue
        n = ntok(render(assemble(order, tgt, sel | {j})))
        if n <= level:
            sel.add(j); cur = n
        elif n <= TOL[level][1] and abs(n - level) < abs(cur - level):
            sel.add(j); cur = n
            break
    return sel


def main():
    samples = {s["sample_id"]: s for s in load_samples()}
    long = {json.loads(l)["sample_id"]: json.loads(l) for l in open("data/longsource/longsource_v1.jsonl")}
    filler_ok = {json.loads(l)["sample_id"] for l in open("data/longsource/longfiller_v1.jsonl") if json.loads(l)["constructible"]}
    e19 = pd.DataFrame([{k: v for k, v in json.loads(l).items() if k != "blocks"} for l in open("data/longsource/e19_sources_v1.jsonl")])
    e19_ok = set(e19[e19.constructible].sample_id)
    rows = []
    for sid in sorted(filler_ok):
        tgt = samples[sid]["target"]["evidence"]
        order, dropped = plan(long[sid], tgt)
        sel = set()
        for level in LEVELS:
            new = window(order, tgt, level, sel)
            assert sel <= new; sel = new; k = len(sel)                               # nested
            blocks = assemble(order, tgt, sel)
            mat = render(blocks)
            assert mat.count(tgt) == 1 and mat.find(tgt) == mat.find("- ") + 2, (sid, level)
            n, nt = ntok(mat), ntok(tgt)
            rows.append({"sample_id": sid, "pmcid": samples[sid]["pmcid"], "arm": "competing_first", "level": level, "blocks": blocks,
                         "n_tokens_ref": n, "tokens_before": ntok(mat[:mat.find(tgt)]), "target_tokens": nt,
                         "n_blocks": len(blocks), "n_competitors": k, "n_home_competitors": len(blocks[0]["spans"]) - 1,
                         "contiguous": bool(sel == set(range(k))),
                         "target_duplicates_dropped": dropped,
                         "in_tolerance": bool(TOL[level][0] <= n <= TOL[level][1] and k >= 1)})
    D = pd.DataFrame(rows)
    ok = D.groupby("sample_id").in_tolerance.all()
    D["competing_constructible"] = D.sample_id.map(ok)
    D["e19_constructible"] = D.sample_id.isin(e19_ok)
    D["constructible"] = D.competing_constructible & D.e19_constructible          # the common cohort of E21
    with open(OUT, "w") as fh:
        for r in D.to_dict("records"):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    Path("results/e21").mkdir(parents=True, exist_ok=True)
    q = lambda x: f"{x.mean():.1f} +- {x.std():.1f} [{x.min():.0f}, {x.max():.0f}]"  # noqa: E731
    C = D[D.constructible]
    S = C.groupby("level").agg(n=("sample_id", "size"), tokens=("n_tokens_ref", q), before=("tokens_before", q),
                               blocks=("n_blocks", "mean"), competitors=("n_competitors", "mean"),
                               home_competitors=("n_home_competitors", "mean")).reset_index()
    S.insert(0, "composition", "competing")
    f = e19[(e19.arm == "first") & e19.sample_id.isin(set(C.sample_id))]
    T = f.groupby("level").agg(n=("sample_id", "size"), tokens=("n_tokens_ref", q), before=("tokens_before", q),
                               blocks=("n_blocks", "mean"), filler_sentences=("n_filler_sentences", "mean")).reset_index()
    T.insert(0, "composition", "noncompeting (E19 first)")
    pd.concat([S, T]).round(2).to_csv("results/e21/e21_sources_summary.csv", index=False)
    print(pd.concat([S, T]).to_string(index=False))
    print(f"articles with a filler source: {D.sample_id.nunique()}; competing sources in tolerance at all levels: {int(ok.sum())}; "
          f"E19 primary set: {len(e19_ok)}; common cohort: {C.sample_id.nunique()}")
    print("out of tolerance by level:", D[~D.in_tolerance].groupby("level").size().to_dict())
    print("articles with a dropped target duplicate:", int((D.groupby('sample_id').target_duplicates_dropped.first() > 1).sum()),
          "(the target bullet itself counts as one dropped span)")


if __name__ == "__main__":
    main()
