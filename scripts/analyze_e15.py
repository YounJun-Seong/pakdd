"""Phase-6 E15 matched-prompt control, analysis (docs/phase6_prereg.md, 2026-11-23).
Matched-prompt cells (results/e15b{B}_{model}*) against the original-prompt cells of the same 279 articles
(E13 truncation-free Single / Multi, E14 Filler; committed verdicts).
Outputs: results/e15/e15_summary.csv, results/e15/e15_report.md      usage: analyze_e15.py [budget ...]"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_lencontrol import fmt, load as load_orig, scored  # noqa: E402
from analyze_phase4 import boot_ci  # noqa: E402

MODELS = ["qwen3-14b", "qwen3-8b"]
KEY = ["sample_id", "mode", "cond", "budget"]
CONDS = ("single", "filler", "multi")


def load_matched(m, b):
    raw = pd.DataFrame([{k: r.get(k) for k in KEY + ["failed", "source_tokens", "memory_tokens", "mean_attempts"]}
                        for r in map(json.loads, open(f"results/e15b{b}_{m}.jsonl"))])
    d = raw.merge(scored(f"results/e15b{b}_{m}_ok_scored.csv").rename(columns={"supported": "elr"}), on=KEY, how="left", validate="1:1")
    d = d.merge(scored(f"results/e15b{b}_{m}_mem_scored.csv").rename(columns={"supported": "wp"}), on=KEY, how="left", validate="1:1")
    d["mode"] = d["mode"].str.replace("_m", "", regex=False)
    d[["elr", "wp"]] = d[["elr", "wp"]].astype(float)
    return d


def wide(d, col, b):
    g = d[d.budget == b]
    bad = g[g.failed.astype(bool)].sample_id.unique()
    g = g[~g.sample_id.isin(bad)]
    return g.pivot_table(index="sample_id", columns=["mode", "cond"], values=col, aggfunc="first").dropna() * 100


def comps(p):
    G = {c: p[("blind", c)] - p[("aware", c)] for c in CONDS}
    return {"G_single": G["single"], "G_filler": G["filler"], "G_multi": G["multi"],
            "LENGTH": G["filler"] - G["single"], "COMPETITION": G["multi"] - G["filler"], "TOTAL": G["multi"] - G["single"]}


def main():
    budgets = [int(x) for x in sys.argv[1:]] or [200]
    Path("results/e15").mkdir(parents=True, exist_ok=True)
    rows = []
    md = ["# E15 Matched-prompt control — analysis", "",
          "Matched prompt: one system prompt and one instruction for both arms; the Aware arm only adds the question line.",
          "Original prompt: the committed E13 (Single, Multi) and E14 (Filler) truncation-free chains of the same articles.",
          "Judge-based outcomes; `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples). G = Blind − Aware.",
          "LENGTH = G_Filler − G_Single; COMPETITION = G_Multi − G_Filler; change = matched − original on the same articles.", ""]
    verdicts = []
    for b in budgets:
        for m in MODELS:
            if not Path(f"results/e15b{b}_{m}_mem_scored.csv").exists():
                md += [f"## {m}, B = {b}: not scored", ""]; continue
            dm, (do, _) = load_matched(m, b), load_orig(m)
            fail = dm.groupby(["mode", "cond"]).failed.mean() * 100
            mem = dm.groupby(["mode", "cond"]).memory_tokens.mean()
            att = dm.groupby(["mode", "cond"]).mean_attempts.mean()
            md += [f"## {m}, B = {b}", "",
                   "Failed regenerations (%): " + ", ".join(f"{mo}/{c} {fail[(mo, c)]:.1f}" for mo in ("aware", "blind") for c in CONDS) + ".",
                   "M4 length (model tokens): " + ", ".join(f"{mo}/{c} {mem[(mo, c)]:.0f}" for mo in ("aware", "blind") for c in CONDS)
                   + "; mean attempts per write: " + ", ".join(f"{mo}/{c} {att[(mo, c)]:.2f}" for mo in ("aware", "blind") for c in CONDS) + ".", ""]
            for col, lbl in (("elr", "ELR"), ("wp", "WP")):
                pm, po = wide(dm, col, b), wide(do, col, b)
                idx = pm.index.intersection(po.index); pm, po = pm.loc[idx], po.loc[idx]
                md += [f"### {lbl}  (n = {len(idx)})", "", "| Prompt | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |", "|---|---|---|---|---|---|---|"]
                for name, p in (("matched", pm), ("original", po)):
                    md.append(f"| {name} | " + " | ".join(f"{p[(mo, c)].mean():.1f}" for c in CONDS for mo in ("aware", "blind")) + " |")
                md.append("| matched − original | " + " | ".join(fmt(boot_ci((pm[(mo, c)] - po[(mo, c)]).to_numpy())) for c in CONDS for mo in ("aware", "blind")) + " |")
                cm, co = comps(pm), comps(po)
                md += ["", "| Estimand | Matched | Original | Matched − original |", "|---|---|---|---|"]
                for k in cm:
                    a, o, dlt = boot_ci(cm[k].to_numpy()), boot_ci(co[k].to_numpy()), boot_ci((cm[k] - co[k]).to_numpy())
                    md.append(f"| {k} | {'**' + fmt(a) + '**' if k == 'LENGTH' else fmt(a)} | {fmt(o)} | {fmt(dlt)} |")
                    rows.append(dict(model=m, budget=b, outcome=lbl, estimand=k, n=len(idx), matched=a[0], matched_lo=a[1], matched_hi=a[2],
                                     original=o[0], original_lo=o[1], original_hi=o[2], change=dlt[0], change_lo=dlt[1], change_hi=dlt[2]))
                    if k == "LENGTH":
                        retained = a[2] < 0; atten = dlt[1] > 0; large = atten and abs(a[0]) < 0.5 * abs(o[0])
                        v = ("retained" if retained else "not retained") + (", largely reduced" if large else (", attenuated" if atten else ""))
                        verdicts.append(f"- {m}, B = {b}, {lbl}: LENGTH matched {fmt(a)} vs original {fmt(o)}; change {fmt(dlt)} -> **{v}**")
                md.append("")
    pd.DataFrame(rows).round(3).to_csv("results/e15/e15_summary.csv", index=False)
    md += ["## Reading rule (pre-registered; primary = ELR, Qwen3-14B, B = 200)", ""] + verdicts
    Path("results/e15/e15_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
