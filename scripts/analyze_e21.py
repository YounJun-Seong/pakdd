"""Phase-6 E21 source length x evidence composition, analysis (docs/phase6_prereg.md, 2026-11-27).
Qwen3-14B, B = 200, truncation-free, target first. Competing = results/e21_qwen3-14b* (new); non-competing = the E19
`first` arm (committed verdicts). Outputs: results/e21/e21_summary.csv, e21_cells.csv, e21_report.md"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_e19 import LEAK7, load as load_e19  # noqa: E402
from analyze_lencontrol import fmt  # noqa: E402
from analyze_phase4 import boot_ci  # noqa: E402

M, B = "qwen3-14b", 200
LEVELS = (200, 500, 1000)
COMPS = ("competing", "noncompeting")
KEY = ["family", "sample_id", "mode", "level"]


def load():
    raw = pd.DataFrame([{k: r.get(k) for k in KEY + ["failed", "constructible", "source_tokens", "memory_tokens", "attempts"]}
                        for r in map(json.loads, open(f"results/e21_{M}.jsonl"))])
    for stem, col in (("ok", "elr"), ("mem", "wp")):
        s = pd.read_csv(f"results/e21_{M}_{stem}_scored.csv")
        assert not s.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any()
        raw = raw.merge(s[KEY + ["supported"]].rename(columns={"supported": col}), on=KEY, how="left", validate="1:1")
    raw["comp"] = "competing"
    e = load_e19(); e = e[e.arm == "first"].drop(columns="arm"); e["comp"] = "noncompeting"
    d = pd.concat([raw, e], ignore_index=True)
    d[["elr", "wp"]] = d[["elr", "wp"]].astype(float)
    return d, raw


def wide(d, col):
    bad = d[d.failed.astype(bool)].sample_id.unique()
    g = d[~d.sample_id.isin(bad)]
    return g.pivot_table(index="sample_id", columns=["comp", "mode", "level"], values=col, aggfunc="first").dropna() * 100


def contrasts(p):
    out = {}
    for tag, cell in (("G", lambda c, l: p[(c, "blind", l)] - p[(c, "aware", l)]), ("blind", lambda c, l: p[(c, "blind", l)]),
                      ("aware", lambda c, l: p[(c, "aware", l)])):
        for c in COMPS:
            for l in LEVELS:
                out[f"{tag}|cell ({c}, L={l})"] = cell(c, l)
            out[f"{tag}|LENGTH({c})"] = cell(c, 1000) - cell(c, 200)
            out[f"{tag}|step 200->500 ({c})"] = cell(c, 500) - cell(c, 200)
            out[f"{tag}|step 500->1000 ({c})"] = cell(c, 1000) - cell(c, 500)
        for l in LEVELS:
            out[f"{tag}|COMPOSITION(L={l})"] = cell("competing", l) - cell("noncompeting", l)
        out[f"{tag}|INTERACTION"] = out[f"{tag}|LENGTH(competing)"] - out[f"{tag}|LENGTH(noncompeting)"]
        out[f"{tag}|LENGTH pooled"] = (out[f"{tag}|LENGTH(competing)"] + out[f"{tag}|LENGTH(noncompeting)"]) / 2
    return out


def verdict(s):
    sig = lambda k: bool(s.loc[k, "hi"] < 0 or s.loc[k, "lo"] > 0)  # noqa: E731
    neg = lambda k: bool(s.loc[k, "hi"] < 0)  # noqa: E731
    both = neg("G|LENGTH(competing)") and neg("G|LENGTH(noncompeting)")
    v = ["length effect in both compositions" if both else
         "length effect NOT in both compositions (competing: " + ("yes" if neg("G|LENGTH(competing)") else "no")
         + ", non-competing: " + ("yes" if neg("G|LENGTH(noncompeting)") else "no") + ")"]
    v.append(f"composition changes the length effect (INTERACTION {s.loc['G|INTERACTION', 'est']:+.1f})" if sig("G|INTERACTION")
             else "composition does not detectably change the length effect")
    cs = [l for l in LEVELS if neg(f"G|COMPOSITION(L={l})")]
    v.append("competition-specific loss at " + ", ".join(map(str, cs)) if cs else "no competition-specific loss at any length")
    return "; ".join(v)


def main():
    Path("results/e21").mkdir(parents=True, exist_ok=True)
    d, raw = load()
    src = pd.DataFrame([{k: v for k, v in json.loads(l).items() if k != "blocks"} for l in open("data/longsource/e21_sources_v1.jsonl")])
    prim = set(src[src.constructible].sample_id)
    sets = {"primary (common cohort)": prim, "excluding the 7 E16 leak sources": prim - LEAK7, "all articles with both sources": set(src.sample_id)}
    md = ["# E21 Source length x evidence composition — analysis", "",
          f"Qwen3-14B, B = {B}, truncation-free, four writes + reader, judge-based outcomes, target finding first in every source.",
          "Competing = annotated findings added to the target (new chains); non-competing = filler prose (the E19 `first` arm).",
          "G = Blind − Aware. LENGTH(C) = G(1000, C) − G(200, C); COMPOSITION(L) = G(L, competing) − G(L, non-competing);",
          "INTERACTION = LENGTH(competing) − LENGTH(non-competing). `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples).", "",
          f"New chains: {len(raw)}; failed regenerations: {int(raw.failed.sum())}.", ""]
    g = src[src.constructible]
    mt = raw[(raw.family == "original") & raw.sample_id.isin(prim)].drop_duplicates(["sample_id", "level"]).groupby("level").source_tokens.mean()
    md += ["## Competing sources (primary set)", "", "| Level | Reference tokens | Model tokens | Competing findings | Blocks |", "|---|---|---|---|---|"]
    for l in LEVELS:
        x = g[g.level == l]
        md.append(f"| {l} | {x.n_tokens_ref.mean():.0f} [{x.n_tokens_ref.min()}, {x.n_tokens_ref.max()}] | {mt[l]:.0f} | {x.n_competitors.mean():.1f} | {x.n_blocks.mean():.1f} |")
    md.append("")
    rows, cells = [], []
    for fam in ("original", "matched"):
        df = d[d.family == fam]
        md += [f"## {fam} prompt{'s (primary)' if fam == 'original' else ' (secondary)'}", ""]
        dp = df[df.sample_id.isin(prim)]
        mem = dp.groupby(["comp", "mode", "level"]).memory_tokens.mean()
        att = dp.groupby(["comp", "mode", "level"]).attempts.apply(lambda x: np.mean([a[0] for a in x if isinstance(a, list) and a]))
        md += ["M4 length in model tokens (first-write attempts), Aware / Blind:", "", "| Composition | 200 | 500 | 1000 |", "|---|---|---|---|"]
        for c in COMPS:
            md.append(f"| {c} | " + " | ".join(f"{mem[(c, 'aware', l)]:.0f} ({att[(c, 'aware', l)]:.1f}) / {mem[(c, 'blind', l)]:.0f} ({att[(c, 'blind', l)]:.1f})" for l in LEVELS) + " |")
        md.append("")
        for col, lbl in (("elr", "ELR"), ("wp", "WP")):
            for sname, ids in sets.items():
                p = wide(df[df.sample_id.isin(ids)], col)
                C = contrasts(p)
                for k, v in C.items():
                    t = boot_ci(v.to_numpy())
                    rows.append(dict(family=fam, outcome=lbl, set=sname, n=len(p), estimand=k, est=t[0], lo=t[1], hi=t[2]))
                if not sname.startswith("primary"):
                    continue
                ci = lambda k: fmt(boot_ci(C[k].to_numpy()))  # noqa: E731
                md += [f"### {lbl}  (n = {len(p)})", "", "Cell rates (%), Aware / Blind, and G = Blind − Aware:", "",
                       "| Composition | L = 200 | L = 500 | L = 1000 | LENGTH = G(1000) − G(200) | Blind(1000) − Blind(200) |", "|---|---|---|---|---|---|"]
                for c in COMPS:
                    cs = []
                    for l in LEVELS:
                        gg = boot_ci(C[f"G|cell ({c}, L={l})"].to_numpy())
                        cs.append(f"{p[(c, 'aware', l)].mean():.1f} / {p[(c, 'blind', l)].mean():.1f}; G {fmt(gg)}")
                        cells.append(dict(family=fam, outcome=lbl, comp=c, level=l, n=len(p), aware=p[(c, "aware", l)].mean(),
                                          blind=p[(c, "blind", l)].mean(), G=gg[0], G_lo=gg[1], G_hi=gg[2]))
                    md.append(f"| {c} | " + " | ".join(cs) + f" | **{ci(f'G|LENGTH({c})')}** | {ci(f'blind|LENGTH({c})')} |")
                md.append("| COMPOSITION (competing − non-competing) | " + " | ".join(ci(f"G|COMPOSITION(L={l})") for l in LEVELS)
                          + f" | INTERACTION **{ci('G|INTERACTION')}** | {ci('blind|INTERACTION')} |")
                md += ["", "| Step (G) | competing | non-competing |", "|---|---|---|"]
                for nm in ("step 200->500", "step 500->1000"):
                    md.append(f"| {nm} | " + " | ".join(ci(f"G|{nm} ({c})") for c in COMPS) + " |")
                md.append("")
    S = pd.DataFrame(rows)
    S.round(3).to_csv("results/e21/e21_summary.csv", index=False)
    pd.DataFrame(cells).round(3).to_csv("results/e21/e21_cells.csv", index=False)
    md += ["## Reading rule (pre-registered)", ""]
    for fam in ("original", "matched"):
        for lbl in ("ELR", "WP"):
            for sname in sets:
                s = S[(S.family == fam) & (S.outcome == lbl) & (S.set == sname)].set_index("estimand")
                tagp = " (PRIMARY)" if (fam, lbl) == ("original", "ELR") and sname.startswith("primary") else ""
                md.append(f"- {fam}, {lbl}, {sname} (n = {int(s.n.iloc[0])}){tagp}: {verdict(s)}. "
                          f"LENGTH competing {fmt(tuple(s.loc['G|LENGTH(competing)', ['est', 'lo', 'hi']]))}, "
                          f"non-competing {fmt(tuple(s.loc['G|LENGTH(noncompeting)', ['est', 'lo', 'hi']]))}, "
                          f"INTERACTION {fmt(tuple(s.loc['G|INTERACTION', ['est', 'lo', 'hi']]))}.")
    Path("results/e21/e21_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
