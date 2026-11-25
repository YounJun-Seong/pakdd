"""Phase-6 E16 filler validation, analysis (docs/phase6_prereg.md, 2026-11-23).
Inputs: data/audit/e16_key.csv, e16_ratings_{A,B}.jsonl (LLM raters), results/e16/e16_filler_spans_all.csv,
results/e16/e16_leak_scored.csv (evaluator screen, optional), the E14 verdicts.
Outputs: results/e16/e16_rating_summary.csv, e16_sensitivity.csv, e16_flagged_items.csv, e16_report.md"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_lencontrol import BUDGETS, MODELS, fmt, load  # noqa: E402
from analyze_phase4 import boot_ci  # noqa: E402

FIELDS = ["finding", "background_claim", "target_relevance", "duplicates_evidence", "well_formed"]
POP = {"home_own": 679, "other_own": 2829, "borrowed": 674}


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan, np.nan)
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (100 * p, 100 * max(0, c - h), 100 * min(1, c + h))


def kappa(a, b):
    a, b = list(a), list(b); labs = sorted(set(a) | set(b)); n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(l) / n) * (b.count(l) / n) for l in labs)
    return po, (po - pe) / (1 - pe) if pe < 1 else np.nan


def components(d, col, b):
    g = d[d.budget == b]
    p = g.pivot_table(index="sample_id", columns=["mode", "cond"], values=col, aggfunc="first").dropna() * 100
    G = {c: p[("blind", c)] - p[("aware", c)] for c in ("single", "filler", "multi")}
    return len(p), boot_ci((G["filler"] - G["single"]).to_numpy()), boot_ci((G["multi"] - G["filler"]).to_numpy())


def main():
    K = pd.read_csv("data/audit/e16_key.csv")
    R = {}
    for r in "AB":
        p = Path(f"data/audit/e16_ratings_{r}.jsonl")
        if p.exists():
            d = pd.DataFrame([json.loads(l) for l in open(p) if l.strip()]).set_index("item_id")
            assert sorted(d.index) == sorted(K.item_id), r
            R[r] = d.loc[K.item_id].reset_index(drop=True)
    md = ["# E16 Filler validation — analysis", "",
          "Raters A and B are two independent LLM annotators (Claude sessions), blind to stratum and to every result; they are",
          "not human annotators. Codebook: `data/audit/CODEBOOK.md`. Sample: 100 filler spans (home_own 40 / other_own 30 / borrowed 30).", ""]
    A = pd.read_csv("results/e16/e16_filler_spans_all.csv"); P = pd.read_csv("results/e16/e16_target_position.csv")
    dpos = P.target_tokens_before_filler - P.target_tokens_before_long
    md += ["## 1. Deterministic checks (all 4,182 filler spans, 279 sources)", "",
           f"- Target slot identical in every source; reference tokens before the target, filler − long: mean {dpos.mean():+.1f}, max |diff| {dpos.abs().max():.0f}.",
           f"- Target sentence occurs more than once: filler {(P.target_occurrences_filler > 1).mean():.1%} of sources, E13 long source {(P.target_occurrences_long > 1).mean():.1%}"
           " (the original single-span source: once). Duplicates are exact copies carried by other candidates of the home article; in the long source the sentence can",
           "  also sit inside a longer competitor span, which the filler replaces.",
           f"- Lexical similarity to the gold evidence: max token Jaccard {A.jaccard_gold.max():.2f}, max ROUGE-L recall {A.rougeL_recall_gold.max():.2f}; statistical-marker regex hits {int(A.stat_marker.sum())} spans.",
           f"- Strata in the population: {A.stratum.value_counts().to_dict()}.", ""]
    rows, flagged = [], set()
    if R:
        def flags(d):
            contam = d.finding != "NONE"
            leak = (d.finding == "TARGET_RESULT") | (d.background_claim == "TARGET") | (d.target_relevance == "DIRECTION") | (d.duplicates_evidence == "YES")
            return dict(finding=contam, any_claim=contam | (d.background_claim != "NONE"), target_leak=leak,
                        topic_related=d.target_relevance != "NONE", broken_text=d.well_formed == "NO")
        F = {r: flags(d) for r, d in R.items()}
        views = dict(F)
        if len(R) == 2:
            views["both"] = {k: F["A"][k] & F["B"][k] for k in F["A"]}
            views["either"] = {k: F["A"][k] | F["B"][k] for k in F["A"]}
        md += ["## 2. Rated sample (% of spans, Wilson 95 % CI; weighted = population-weighted over the three strata)", "",
               "| Rater | Measure | home_own (n=40) | other_own (n=30) | borrowed (n=30) | weighted |", "|---|---|---|---|---|---|"]
        for v, fl in views.items():
            for k, x in fl.items():
                cell, wt = [], 0.0
                for st in POP:
                    m = (K.stratum == st).to_numpy(); w = wilson(int(x[m].sum()), int(m.sum()))
                    cell.append(f"{w[0]:.1f} [{w[1]:.1f}, {w[2]:.1f}]"); wt += w[0] * POP[st] / sum(POP.values())
                    rows.append(dict(rater=v, measure=k, stratum=st, n=int(m.sum()), k=int(x[m].sum()), pct=w[0], lo=w[1], hi=w[2]))
                w = wilson(int(x.sum()), len(x))
                rows.append(dict(rater=v, measure=k, stratum="all_unweighted", n=len(x), k=int(x.sum()), pct=w[0], lo=w[1], hi=w[2]))
                rows.append(dict(rater=v, measure=k, stratum="weighted", n=len(x), k=int(x.sum()), pct=wt, lo=np.nan, hi=np.nan))
                md.append(f"| {v} | {k} | {' | '.join(cell)} | {wt:.1f} (unweighted {w[0]:.1f} [{w[1]:.1f}, {w[2]:.1f}]) |")
        md.append("")
        if len(R) == 2:
            md += ["Inter-rater agreement: " + "; ".join(f"{f} {kappa(R['A'][f], R['B'][f])[0]:.1%} (kappa {kappa(R['A'][f], R['B'][f])[1]:.2f})" for f in FIELDS) + ".", ""]
        ev = views.get("either", list(views.values())[0])
        bad = K[ev["target_leak"].to_numpy() | ev["finding"].to_numpy()]
        out = bad[["item_id", "sample_id", "stratum", "text"]].copy()
        for r, d in R.items():
            for f in FIELDS + ["note"]:
                out[f"{f}_{r}"] = d.loc[bad.index, f].to_numpy() if f in d else ""
        out.to_csv("results/e16/e16_flagged_items.csv", index=False)
        flagged = set(K[ev["target_leak"].to_numpy()].sample_id)
        md += [f"Spans flagged by either rater as a finding or a target leak: {len(bad)} (listed in `e16_flagged_items.csv`); target leaks: {int(ev['target_leak'].sum())}.", ""]
    leak_ids = set()
    if Path("results/e16/e16_leak_scored.csv").exists():
        Lk = pd.read_csv("results/e16/e16_leak_scored.csv")
        assert not Lk.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any()
        leak_ids = set(Lk[Lk.claim_label != "NOT_MENTIONED"].sample_id)
        w, g = wilson(len(leak_ids), len(Lk)), wilson(int(Lk.supported.sum()), len(Lk))
        md += ["## 3. Evaluator leak screen (all 279 filler sources, target sentence removed)", "",
               f"- Any label other than Not-Mentioned: {len(leak_ids)} / {len(Lk)} = {w[0]:.1f} % [{w[1]:.1f}, {w[2]:.1f}]; labels: {Lk.claim_label.value_counts().to_dict()}.",
               f"- Gold label recovered without the target sentence: {int(Lk.supported.sum())} / {len(Lk)} = {g[0]:.1f} % [{g[1]:.1f}, {g[2]:.1f}].", ""]
        Lk[Lk.claim_label != "NOT_MENTIONED"][["sample_id", "gold_label", "claim_label", "direction", "certainty"]].to_csv("results/e16/e16_leak_sources.csv", index=False)
    dup = set(P[(P.target_occurrences_filler > 1) | (P.target_occurrences_long > 1)].sample_id)
    sens = []
    md += ["## 4. Sensitivity of the E14 decomposition (existing verdicts; LENGTH = Filler − Single, COMPETITION = Multi − Filler)", "",
           "| Model | Outcome | B | All 279: LENGTH | COMPETITION | excl. flagged/leak sources: n | LENGTH | COMPETITION | excl. repeated-target sources: n | LENGTH | COMPETITION |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        d, _ = load(m)
        for col, lbl in (("elr", "ELR"), ("wp", "WP")):
            for b in BUDGETS:
                n0, l0, c0 = components(d, col, b)
                n1, l1, c1 = components(d[~d.sample_id.isin(flagged | leak_ids)], col, b)
                n2, l2, c2 = components(d[~d.sample_id.isin(dup)], col, b)
                md.append(f"| {m} | {lbl} | {b} | {fmt(l0)} | {fmt(c0)} | {n1} | {fmt(l1)} | {fmt(c1)} | {n2} | {fmt(l2)} | {fmt(c2)} |")
                for tag, n, l, c in (("all", n0, l0, c0), ("excl_flagged_leak", n1, l1, c1), ("excl_repeated_target", n2, l2, c2)):
                    sens.append(dict(model=m, outcome=lbl, budget=b, subset=tag, n=n, length=l[0], length_lo=l[1], length_hi=l[2],
                                     competition=c[0], competition_lo=c[1], competition_hi=c[2]))
    md += ["", f"Excluded in the flagged/leak analysis: {len(flagged | leak_ids)} sources (rater target leaks {len(flagged)}, evaluator screen {len(leak_ids)}); "
               f"in the repeated-target analysis: {len(dup)} sources.", ""]
    pd.DataFrame(rows).round(2).to_csv("results/e16/e16_rating_summary.csv", index=False)
    pd.DataFrame(sens).round(2).to_csv("results/e16/e16_sensitivity.csv", index=False)
    Path("results/e16/e16_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
