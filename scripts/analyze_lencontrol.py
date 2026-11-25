"""Phase-6 E14 length-matched control, analysis (docs/phase6_prereg.md, 2026-11-22).
Combines the new Filler cells with the E13 truncation-free Single and Multi cells of the same articles.
Outputs: results/lenctrl_summary.csv, results/lenctrl_report.md"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_phase4 import boot_ci  # noqa: E402

MODELS = ["qwen3-8b", "qwen3-14b"]
BUDGETS = [100, 200, 400, 800]
KEY = ["sample_id", "mode", "cond", "budget"]


def jl(p):
    return [json.loads(l) for l in open(p)]


def fmt(t):
    return f"{t[0]:+.1f} [{t[1]:+.1f}, {t[2]:+.1f}]" + ("*" if (t[1] > 0 or t[2] < 0) else "")


def scored(p):
    d = pd.read_csv(p)
    assert not d.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any(), p
    return d[KEY + ["supported"]]


def load(m):
    raw = pd.DataFrame([{k: r.get(k) for k in KEY + ["failed", "source_tokens", "memory_tokens", "mean_attempts"]}
                        for r in jl(f"results/lenctrl_{m}.jsonl")])
    f = raw.merge(scored(f"results/lenctrl_{m}_ok_scored.csv").rename(columns={"supported": "elr"}), on=KEY, how="left", validate="1:1")
    f = f.merge(scored(f"results/lenctrl_{m}_mem_scored.csv").rename(columns={"supported": "wp"}), on=KEY, how="left", validate="1:1")
    e = pd.DataFrame([{k: r.get(k) for k in KEY + ["failed", "source_tokens"]} for r in jl(f"results/ratio_notrunc_{m}.jsonl")])
    e = e.merge(scored(f"results/ratio_notrunc_{m}_ok_scored.csv").rename(columns={"supported": "elr"}), on=KEY, how="left", validate="1:1")
    e = e.merge(scored(f"results/ratio_notrunc_{m}_mem_scored.csv").rename(columns={"supported": "wp"}), on=KEY, how="left", validate="1:1")
    e["cond"] = e.cond.replace({"long": "multi"})
    d = pd.concat([f, e[e.sample_id.isin(f.sample_id.unique())]], ignore_index=True)
    d[["elr", "wp"]] = d[["elr", "wp"]].astype(float)
    return d, raw


def main():
    rows = []
    md = ["# E14 Length-matched control for E13 — analysis", "",
          "Truncation-free protocol; judge-based outcomes; Single and Multi cells are the E13 chains of the same articles.",
          "Filler = same structure and length as the E13 long source, target finding kept, every other span replaced by",
          "non-finding prose from the same trials. `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples).", ""]
    for m in MODELS:
        if not Path(f"results/lenctrl_{m}_mem_scored.csv").exists():
            md.append(f"## {m}: not scored"); continue
        d, raw = load(m)
        n_art = d.sample_id.nunique()
        src = raw.groupby("cond").source_tokens.mean()
        md += [f"## {m}  (n = {n_art} articles; filler source {src['filler']:.0f} model tokens)", "",
               "Failed regenerations (filler cells): " + ", ".join(
                   f"B={b} aware {raw[(raw.budget == b) & (raw['mode'] == 'aware')].failed.mean() * 100:.1f}% / blind "
                   f"{raw[(raw.budget == b) & (raw['mode'] == 'blind')].failed.mean() * 100:.1f}%" for b in BUDGETS) + ".",
               "Blind/Filler memory tokens: " + ", ".join(
                   f"B={b} {raw[(raw.budget == b) & (raw['mode'] == 'blind')].memory_tokens.mean():.0f}" for b in BUDGETS) + ".", ""]
        for col, lbl in (("elr", "ELR"), ("wp", "WP")):
            md += [f"### {lbl}", "",
                   "| B | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi | Blind − Aware, Filler | LENGTH (Filler − Single) | COMPETITION (Multi − Filler) | E13 DiD (Multi − Single) |",
                   "|---|---|---|---|---|---|---|---|---|---|---|"]
            for b in BUDGETS:
                g = d[d.budget == b]
                bad = g[g.failed.astype(bool)].sample_id.unique()
                g = g[~g.sample_id.isin(bad)]
                p = g.pivot_table(index="sample_id", columns=["mode", "cond"], values=col, aggfunc="first").dropna() * 100
                G = {c: p[("blind", c)] - p[("aware", c)] for c in ("single", "filler", "multi")}
                gf, ln, cp, tot = (boot_ci(x.to_numpy()) for x in (G["filler"], G["filler"] - G["single"], G["multi"] - G["filler"], G["multi"] - G["single"]))
                cm = {(mo, c): p[(mo, c)].mean() for mo in ("aware", "blind") for c in ("single", "filler", "multi")}
                md.append(f"| {b} | {cm[('aware', 'single')]:.1f} | {cm[('blind', 'single')]:.1f} | {cm[('aware', 'filler')]:.1f} | {cm[('blind', 'filler')]:.1f} | "
                          f"{cm[('aware', 'multi')]:.1f} | {cm[('blind', 'multi')]:.1f} | {fmt(gf)} | {fmt(ln)} | **{fmt(cp)}** | {fmt(tot)} |")
                rows.append(dict(model=m, outcome=lbl, budget=b, n=len(p), **{f"{mo}_{c}": v for (mo, c), v in cm.items()},
                                 BmA_filler=gf[0], BmA_filler_lo=gf[1], BmA_filler_hi=gf[2],
                                 length=ln[0], length_lo=ln[1], length_hi=ln[2],
                                 competition=cp[0], competition_lo=cp[1], competition_hi=cp[2],
                                 e13_did=tot[0], e13_did_lo=tot[1], e13_did_hi=tot[2],
                                 competition_specific=bool(cp[2] < 0), length_driven=bool(ln[2] < 0)))
            md.append("")
    S = pd.DataFrame(rows)
    S.round(3).to_csv("results/lenctrl_summary.csv", index=False)
    if len(S):
        md += ["## Reading rule (pre-registered), ELR", ""]
        for b in BUDGETS:
            s = S[(S.outcome == "ELR") & (S.budget == b)]
            md.append(f"- B={b}: competition-specific in {int(s.competition_specific.sum())}/{len(s)} models "
                      f"({', '.join(s[s.competition_specific].model) or '-'}); length-driven in {int(s.length_driven.sum())}/{len(s)} "
                      f"({', '.join(s[s.length_driven].model) or '-'}).")
    Path("results/lenctrl_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
