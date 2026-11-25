"""Phase-6 E19 length-position control, analysis (docs/phase6_prereg.md, 2026-11-23).
Qwen3-14B, B = 200, truncation-free; 3 position arms x 3 source lengths x Aware / Blind, original and matched prompts.
Outputs: results/e19/e19_summary.csv, results/e19/e19_cells.csv, results/e19/e19_report.md"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_e15 import load_matched  # noqa: E402
from analyze_lencontrol import fmt, load as load_orig  # noqa: E402
from analyze_phase4 import boot_ci  # noqa: E402

M, B = "qwen3-14b", 200
ARMS, LEVELS = ("first", "middle", "last"), (200, 500, 1000)
KEY = ["family", "sample_id", "mode", "arm", "level"]
LEAK7 = {"G2-0033", "G2-0046", "G2-0080", "G2-0085", "G2-0205", "G2-0214", "G2-0088"}   # E16: evaluator screen (6) + rated leak (1)


def load():
    raw = pd.DataFrame([{k: r.get(k) for k in KEY + ["failed", "constructible", "source_tokens", "memory_tokens", "mean_attempts", "attempts"]}
                        for r in map(json.loads, open(f"results/e19_{M}.jsonl"))])
    for stem, col in (("ok", "elr"), ("mem", "wp")):
        s = pd.read_csv(f"results/e19_{M}_{stem}_scored.csv")
        assert not s.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any()
        raw = raw.merge(s[KEY + ["supported"]].rename(columns={"supported": col}), on=KEY, how="left", validate="1:1")
    raw[["elr", "wp"]] = raw[["elr", "wp"]].astype(float)
    return raw


def wide(d, col):
    bad = d[d.failed.astype(bool)].sample_id.unique()
    g = d[~d.sample_id.isin(bad)]
    return g.pivot_table(index="sample_id", columns=["mode", "arm", "level"], values=col, aggfunc="first").dropna() * 100


def contrasts(p):
    """Per-article series of every pre-registered estimand (G = Blind - Aware; `_blind` = Blind cell rates alone)."""
    out = {}
    for tag, cell in (("G", lambda a, l: p[("blind", a, l)] - p[("aware", a, l)]), ("blind", lambda a, l: p[("blind", a, l)])):
        for a in ARMS:
            out[f"{tag}|LEN({a})"] = cell(a, 1000) - cell(a, 200)
            out[f"{tag}|step 200->500 ({a})"] = cell(a, 500) - cell(a, 200)
            out[f"{tag}|step 500->1000 ({a})"] = cell(a, 1000) - cell(a, 500)
        out[f"{tag}|LEN_pooled"] = sum(out[f"{tag}|LEN({a})"] for a in ARMS) / 3
        out[f"{tag}|step 200->500 pooled"] = sum(out[f"{tag}|step 200->500 ({a})"] for a in ARMS) / 3
        out[f"{tag}|step 500->1000 pooled"] = sum(out[f"{tag}|step 500->1000 ({a})"] for a in ARMS) / 3
        for other in ("last", "middle"):
            for l in LEVELS:
                out[f"{tag}|POS {other}-first (L={l})"] = cell(other, l) - cell("first", l)
            out[f"{tag}|POS_pooled {other}-first"] = sum(out[f"{tag}|POS {other}-first (L={l})"] for l in LEVELS) / 3
        out[f"{tag}|LEN(last) - LEN(first)"] = out[f"{tag}|LEN(last)"] - out[f"{tag}|LEN(first)"]
        out[f"{tag}|LEN(middle) - LEN(first)"] = out[f"{tag}|LEN(middle)"] - out[f"{tag}|LEN(first)"]
        for l in LEVELS:
            out[f"{tag}|level mean (L={l})"] = sum(cell(a, l) for a in ARMS) / 3
    return out


def verdict(S, fam, outcome, aset):
    s = S[(S.family == fam) & (S.outcome == outcome) & (S.set == aset)].set_index("estimand")
    sig = lambda k: bool(s.loc[k, "hi"] < 0 or s.loc[k, "lo"] > 0)  # noqa: E731
    v = []
    if s.loc["G|LEN_pooled", "hi"] < 0:
        arms = [a for a in ARMS if s.loc[f"G|LEN({a})", "hi"] < 0]
        v.append("length effect with position fixed" + (" (at every position)" if len(arms) == 3 else f" (CI excludes 0 in: {', '.join(arms) or 'no single arm'})"))
    else:
        v.append("NO length effect with position fixed (LEN_pooled CI includes 0)" if not sig("G|LEN_pooled") else "length effect of the opposite sign")
    g = [s.loc[f"G|level mean (L={l})", "est"] for l in LEVELS]
    v.append("graded" if (g[0] >= g[1] >= g[2] and s.loc["G|step 200->500 pooled", "est"] <= 0 and s.loc["G|step 500->1000 pooled", "est"] <= 0) else "not graded")
    k = "G|POS_pooled last-first"
    v.append(f"position effect (last − first {s.loc[k, 'est']:+.1f})" if sig(k) else "no position effect (last − first CI includes 0)")
    return "; ".join(v)


def main():
    Path("results/e19").mkdir(parents=True, exist_ok=True)
    raw = load()
    src = [json.loads(l) for l in open("data/longsource/e19_sources_v1.jsonl")]
    ref_tok = pd.DataFrame([{k: r[k] for k in ("sample_id", "arm", "level", "n_tokens_ref", "tokens_before", "tokens_after", "rel_centre", "constructible")} for r in src])
    prim = set(ref_tok[ref_tok.constructible].sample_id)
    sets = {"primary (all nine sources in tolerance)": prim, "excluding the 7 E16 leak sources": prim - LEAK7, "all articles": set(ref_tok.sample_id)}
    four = {"original": load_orig(M)[0], "matched": load_matched(M, B)}
    md = ["# E19 Length–position control — analysis", "",
          f"Qwen3-14B, B = {B}, truncation-free, four writes + reader, judge-based outcomes. Sources: the E14 filler material with the target",
          "at a fixed position (first / middle / last) and three nested lengths (200 / 500 / 1,000 reference tokens).",
          "G = Blind − Aware. LEN(arm) = G(1000) − G(200). POS = G(other arm) − G(first) at the same length. `*` = 95 % CI excludes 0",
          "(paired article bootstrap, 2,000 resamples). Negative LEN = the Blind − Aware penalty grows with source length.", "",
          f"Chains: {len(raw)}; failed regenerations: {int(raw.failed.sum())}.", ""]
    g = ref_tok[ref_tok.sample_id.isin(prim)].merge(raw[raw.family == "original"].drop_duplicates(["sample_id", "arm", "level"])[["sample_id", "arm", "level", "source_tokens"]],
                                                    on=["sample_id", "arm", "level"])
    md += ["## Sources (primary set)", "", "| Arm | Level | Reference tokens | Model tokens | Tokens before target | Tokens after target | Target centre (relative) |", "|---|---|---|---|---|---|---|"]
    for a in ARMS:
        for l in LEVELS:
            x = g[(g.arm == a) & (g.level == l)]
            md.append(f"| {a} | {l} | {x.n_tokens_ref.mean():.0f} [{x.n_tokens_ref.min()}, {x.n_tokens_ref.max()}] | {x.source_tokens.mean():.0f} | {x.tokens_before.mean():.0f} | {x.tokens_after.mean():.0f} | {x.rel_centre.mean():.2f} |")
    md.append("")
    rows, cells = [], []
    for fam in ("original", "matched"):
        d = raw[raw.family == fam]
        md += [f"## {fam} prompt{'s (primary)' if fam == 'original' else ' (secondary)'}", ""]
        dp = d[d.sample_id.isin(prim)]
        mem = dp.groupby(["mode", "arm", "level"]).memory_tokens.mean(); att = dp.groupby(["mode", "arm", "level"]).attempts.apply(lambda x: np.mean([a[0] for a in x if a]))
        md += ["M4 length in model tokens (first-write attempts), Aware / Blind:", "", "| Arm | 200 | 500 | 1000 |", "|---|---|---|---|"]
        for a in ARMS:
            md.append(f"| {a} | " + " | ".join(f"{mem[('aware', a, l)]:.0f} ({att[('aware', a, l)]:.1f}) / {mem[('blind', a, l)]:.0f} ({att[('blind', a, l)]:.1f})" for l in LEVELS) + " |")
        md.append("")
        for col, lbl in (("elr", "ELR"), ("wp", "WP")):
            for sname, ids in sets.items():
                p = wide(d[d.sample_id.isin(ids)], col)
                C = contrasts(p)
                for k, v in C.items():
                    t = boot_ci(v.to_numpy())
                    rows.append(dict(family=fam, outcome=lbl, set=sname, n=len(p), estimand=k, est=t[0], lo=t[1], hi=t[2]))
                if not sname.startswith("primary"):
                    continue
                md += [f"### {lbl}  (n = {len(p)})", "", "Cell rates (%), Aware / Blind, and G = Blind − Aware:", "",
                       "| Arm | L = 200 | L = 500 | L = 1000 | LEN = G(1000) − G(200) | Blind(1000) − Blind(200) |", "|---|---|---|---|---|---|"]
                for a in ARMS:
                    cs = []
                    for l in LEVELS:
                        gg = boot_ci((p[("blind", a, l)] - p[("aware", a, l)]).to_numpy())
                        cs.append(f"{p[('aware', a, l)].mean():.1f} / {p[('blind', a, l)].mean():.1f}; G {fmt(gg)}")
                        cells.append(dict(family=fam, outcome=lbl, arm=a, level=l, n=len(p), aware=p[("aware", a, l)].mean(), blind=p[("blind", a, l)].mean(), G=gg[0], G_lo=gg[1], G_hi=gg[2]))
                    md.append(f"| {a} | " + " | ".join(cs) + f" | **{fmt(boot_ci(C[f'G|LEN({a})'].to_numpy()))}** | {fmt(boot_ci(C[f'blind|LEN({a})'].to_numpy()))} |")
                md.append("| pooled | " + " | ".join("G " + fmt(boot_ci(C[f"G|level mean (L={l})"].to_numpy())) for l in LEVELS)
                          + f" | **{fmt(boot_ci(C['G|LEN_pooled'].to_numpy()))}** | {fmt(boot_ci(C['blind|LEN_pooled'].to_numpy()))} |")
                md += ["", "| Contrast (G) | first | middle | last | pooled |", "|---|---|---|---|---|"]
                for nm in ("step 200->500", "step 500->1000"):
                    md.append(f"| {nm} | " + " | ".join(fmt(boot_ci(C[f"G|{nm} ({a})"].to_numpy())) for a in ARMS) + f" | {fmt(boot_ci(C[f'G|{nm} pooled'].to_numpy()))} |")
                md += ["", "| Position contrast (G) | L = 200 | L = 500 | L = 1000 | pooled |", "|---|---|---|---|---|"]
                for other in ("last", "middle"):
                    md.append(f"| {other} − first | " + " | ".join(fmt(boot_ci(C[f"G|POS {other}-first (L={l})"].to_numpy())) for l in LEVELS)
                              + f" | {fmt(boot_ci(C[f'G|POS_pooled {other}-first'].to_numpy()))} |")
                md.append(f"| LEN(last) − LEN(first) | | | | {fmt(boot_ci(C['G|LEN(last) - LEN(first)'].to_numpy()))} |")
                md.append(f"| LEN(middle) − LEN(first) | | | | {fmt(boot_ci(C['G|LEN(middle) - LEN(first)'].to_numpy()))} |")
                # reference: target-only source and natural-position filler source of the same articles (not tested)
                f4 = four[fam]; f4 = f4[(f4.budget == B) & f4.sample_id.isin(p.index)]
                r4 = f4.pivot_table(index="sample_id", columns=["mode", "cond"], values=col, aggfunc="first").dropna() * 100
                md += ["", "Reference (same articles, existing verdicts; not part of the test): "
                       + "; ".join(f"{nm} {r4[('aware', c)].mean():.1f} / {r4[('blind', c)].mean():.1f}, G {fmt(boot_ci((r4[('blind', c)] - r4[('aware', c)]).to_numpy()))}"
                                   for nm, c in (("target-only source", "single"), ("E14 Filler (natural position)", "filler"))) + f" (n = {len(r4)}).", ""]
    S = pd.DataFrame(rows)
    S.round(3).to_csv("results/e19/e19_summary.csv", index=False)
    pd.DataFrame(cells).round(3).to_csv("results/e19/e19_cells.csv", index=False)
    md += ["## Reading rule (pre-registered; primary = ELR, original prompts, primary set)", ""]
    for sname in sets:
        md.append(f"**{sname}**")
        md.append("")
        for fam in ("original", "matched"):
            for lbl in ("ELR", "WP"):
                s = S[(S.family == fam) & (S.outcome == lbl) & (S.set == sname)].set_index("estimand")
                t = s.loc["G|LEN_pooled"]; q = s.loc["G|POS_pooled last-first"]
                md.append(f"- {fam}, {lbl} (n = {int(t.n)}): LEN_pooled {t.est:+.1f} [{t.lo:+.1f}, {t.hi:+.1f}]; "
                          + ", ".join(f"{a} {s.loc[f'G|LEN({a})', 'est']:+.1f} [{s.loc[f'G|LEN({a})', 'lo']:+.1f}, {s.loc[f'G|LEN({a})', 'hi']:+.1f}]" for a in ARMS)
                          + f"; POS_pooled last − first {q.est:+.1f} [{q.lo:+.1f}, {q.hi:+.1f}] -> **{verdict(S, fam, lbl, sname)}**")
        md.append("")
    Path("results/e19/e19_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
