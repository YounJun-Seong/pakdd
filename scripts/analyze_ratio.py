"""Phase-6 E13 compression-ratio experiment, analysis (docs/phase6_prereg.md, 2026-11-22).

Prints the pre-registered tables and writes results/ratio_summary.csv (one row per model x protocol x
budget x outcome) and results/ratio_design_summary.csv (truncation, realized ratio, Oracle-All fit).
Sections marked EXPLORATORY were not pre-registered.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_phase4 import boot_ci, did_boot  # noqa: E402

MODELS = ["qwen3-8b", "qwen3-14b", "gpt-5.4-mini"]
BUDGETS = [100, 200, 400, 800]
CELLS = [("aware", "single"), ("blind", "single"), ("aware", "multi"), ("blind", "multi")]   # multi == Long here
KEY = ["sample_id", "mode", "cond", "budget"]
DIR = {"INCREASE": "increase", "DECREASE": "decrease", "NO_DIFFERENCE": "no difference"}
SIG = {"INCREASE": "significant", "DECREASE": "significant", "NO_DIFFERENCE": "n.s."}
OUTCOMES = [("sup_final", "ELR"), ("sup_mem", "WP"), ("lab_ok", "judge-free ELR")]


def fmt(t):
    return f"{t[0]:+5.1f} [{t[1]:+5.1f}, {t[2]:+5.1f}]"


def jl(p):
    return [json.loads(l) for l in open(p)]


def have(*ps):
    return all(Path(p).exists() for p in ps)


def sig(t):
    return "*" if (t[1] > 0 or t[2] < 0) else " "


def per_article(d, col):
    piv = d.pivot_table(index="sample_id", columns=["mode", "cond"], values=col, aggfunc="first").dropna()
    return ((piv[("blind", "multi")] - piv[("aware", "multi")]) - (piv[("blind", "single")] - piv[("aware", "single")])) * 100


def load(m, proto):
    """One row per chain with verdicts where available. cond 'long' is renamed 'multi' for did_boot."""
    stem = f"results/ratio_{m}" if proto == "enforced" else f"results/ratio_notrunc_{m}"
    if not have(stem + ".jsonl"):
        return None
    rows = jl(stem + ".jsonl")
    keep = KEY + ["source_tokens", "target_pos", "forced", "failed"]
    df = pd.DataFrame([{k: r.get(k) for k in keep} for r in rows])
    if proto == "enforced":
        df["step_raw"] = [[s["raw_tokens"] for s in r["steps"]] for r in rows]
        df["failed"] = False
    else:
        df["step_raw"] = None
    fin_p = stem + ("_scored.csv" if proto == "enforced" else "_ok_scored.csv")
    for path, col in ((fin_p, "sup_final"), (stem + "_mem_scored.csv", "sup_mem")):
        if have(path):
            sc = pd.read_csv(path)
            assert not sc.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any(), path
            df = df.merge(sc[KEY + ["supported"]].rename(columns={"supported": col}), on=KEY, how="left", validate="1:1")
    lp = f"results/ratio_labels_{m}.jsonl"
    if have(lp):
        lab = pd.DataFrame(jl(lp))
        e = lab[lab.source == proto][KEY + ["correct"]].rename(columns={"correct": "lab_ok"}).astype({"budget": int})
        df = df.merge(e, on=KEY, how="left", validate="1:1")
    df["cond"] = df["cond"].replace({"long": "multi"})
    for c in ("sup_final", "sup_mem", "lab_ok"):
        if c in df:
            df[c] = df[c].astype(float)
    return df


def oracle_tokens(m, enc):
    out = {}
    for L in jl("data/longsource/longsource_v1.jsonl"):
        blocks = {}
        for c in L["candidates"]:
            blocks.setdefault(c["pmcid"], []).append(f"{c['outcome']}: {DIR[c['gold_label']]}, {SIG[c['gold_label']]}")
        txt = "\n\n".join(f"Findings from [PMC{p}]:\n" + "\n".join(v) for p, v in blocks.items())
        out[L["sample_id"]] = len(enc(m, txt))
    return pd.Series(out)


def design():
    print("E13 DESIGN CHECK — source length, forced truncation, realized ratio, Gold Oracle-All fit (enforced protocol)")
    from run_phase4 import tokenizers
    enc, _ = tokenizers()
    rows = []
    for m in MODELS:
        df = load(m, "enforced")
        if df is None:
            print(f"\n{m}: not generated"); continue
        orc = oracle_tokens(m, enc)
        src = df[df.cond == "multi"].drop_duplicates("sample_id").source_tokens
        print(f"\n{m}   long source {src.mean():.0f} tokens (model tokenizer; {src.min():.0f}–{src.max():.0f}); "
              f"Gold Oracle-All {orc.mean():.0f} tokens (p90 {orc.quantile(.9):.0f}, max {orc.max()})")
        for b in BUDGETS:
            d = df[(df.budget == b) & df["mode"].isin(["aware", "blind"])].copy()
            d["forced"] = d["forced"].astype(float)
            d["len"] = d["step_raw"].map(lambda s: min(s[-1], b))
            f = [d[(d["mode"] == mo) & (d.cond == c)].forced.mean() * 100 for mo, c in CELLS]
            ln = [d[(d["mode"] == mo) & (d.cond == c)]["len"].mean() for mo, c in CELLS]
            lm = d[d.cond == "multi"]
            rr = [(lm[lm["mode"] == mo]["len"] / lm[lm["mode"] == mo].source_tokens).mean() * 100 for mo in ("aware", "blind")]
            fit = (orc <= b).mean() * 100
            print(f"  B={b:<4} forced % A-S/B-S/A-L/B-L {f[0]:5.1f} {f[1]:5.1f} {f[2]:5.1f} {f[3]:5.1f} | memory tokens "
                  f"{ln[0]:4.0f} {ln[1]:4.0f} {ln[2]:4.0f} {ln[3]:4.0f} | realized ratio Long A/B {rr[0]:4.1f}% / {rr[1]:4.1f}% | Oracle-All fits {fit:5.1f}%")
            rows.append(dict(model=m, budget=b, nominal_ratio=b / 10, forced_AS=f[0], forced_BS=f[1], forced_AL=f[2], forced_BL=f[3],
                             mem_AS=ln[0], mem_BS=ln[1], mem_AL=ln[2], mem_BL=ln[3], realized_ratio_AL=rr[0], realized_ratio_BL=rr[1],
                             oracle_all_fit=fit, oracle_all_tokens=orc.mean(), source_tokens=src.mean()))
    pd.DataFrame(rows).to_csv("results/ratio_design_summary.csv", index=False)


def table(d, col):
    c4 = [d[(d["mode"] == mo) & (d.cond == c)][col].mean() * 100 for mo, c in CELLS]
    t = did_boot(d, col)
    am = d[(d["mode"] == "aware") & (d.cond == "multi")].set_index("sample_id")[col]
    bm = d[(d["mode"] == "blind") & (d.cond == "multi")].set_index("sample_id")[col]
    g = boot_ci((bm - am.reindex(bm.index)).dropna().to_numpy() * 100)
    return c4, t, g


def main_tables():
    rows, verdict = [], {}
    for proto, title in (("enforced", "ENFORCED PROTOCOL (primary)"), ("notrunc", "TRUNCATION-FREE PROTOCOL (regenerate, never cut)")):
        print(f"E13 {title} — cells A-S / B-S / A-L / B-L, n per cell = articles; * = 95% CI excludes 0")
        for m in MODELS:
            df = load(m, proto)
            if df is None:
                print(f"\n{m}: not generated"); continue
            df = df[df["mode"].isin(["aware", "blind"])]
            print(f"\n{m}")
            for col, lbl in OUTCOMES:
                if col not in df:
                    print(f"  {lbl}: not scored"); continue
                pa = {}
                for b in BUDGETS:
                    d = df[df.budget == b]
                    rec = dict(model=m, protocol=proto, budget=b, outcome=lbl)
                    if proto == "notrunc":
                        fail = [d[(d["mode"] == mo) & (d.cond == c)].failed.mean() * 100 for mo, c in CELLS]
                        okid = d.groupby("sample_id").failed.sum(); okid = okid[okid == 0].index
                        cc = d[d.sample_id.isin(okid)]
                        if cc[col].isna().any():
                            print(f"  {lbl} B={b}: not scored"); continue
                        c4, t, g = table(cc, col)
                        against = {("blind", "multi"): 1.0, ("aware", "single"): 1.0, ("aware", "multi"): 0.0, ("blind", "single"): 0.0}
                        imp = d.copy()
                        imp[col] = [against[(mo, c)] if f else v for mo, c, f, v in zip(imp["mode"], imp.cond, imp.failed, imp[col])]
                        tb = did_boot(imp, col)
                        print(f"  {lbl:<15} B={b:<4} {c4[0]:5.1f} {c4[1]:5.1f} {c4[2]:5.1f} {c4[3]:5.1f}  DiD {fmt(t[:3])}{sig(t)} (n={t[3]})  "
                              f"Blind−Aware|Long {fmt(g)}{sig(g)}  bound {fmt(tb[:3])}{sig(tb)}  failed % {fail[0]:.1f}/{fail[1]:.1f}/{fail[2]:.1f}/{fail[3]:.1f}")
                        rec.update(fail_AS=fail[0], fail_BS=fail[1], fail_AL=fail[2], fail_BL=fail[3], bound=tb[0], bound_lo=tb[1], bound_hi=tb[2])
                        pa[b] = per_article(cc, col)
                    else:
                        if d[col].isna().any():
                            print(f"  {lbl} B={b}: not scored"); continue
                        c4, t, g = table(d, col)
                        print(f"  {lbl:<15} B={b:<4} {c4[0]:5.1f} {c4[1]:5.1f} {c4[2]:5.1f} {c4[3]:5.1f}  DiD {fmt(t[:3])}{sig(t)} (n={t[3]})  "
                              f"Blind−Aware|Long {fmt(g)}{sig(g)}")
                        pa[b] = per_article(d, col)
                    rec.update(AS=c4[0], BS=c4[1], AL=c4[2], BL=c4[3], DiD=t[0], DiD_lo=t[1], DiD_hi=t[2], n=t[3],
                               BmA_long=g[0], BmA_long_lo=g[1], BmA_long_hi=g[2], present=bool(t[2] < 0))
                    rows.append(rec)
                    verdict[(proto, lbl, m, b)] = bool(t[2] < 0)
                if 100 in pa and 800 in pa:
                    j = pa[100].index.intersection(pa[800].index)
                    c = boot_ci((pa[100].loc[j] - pa[800].loc[j]).to_numpy())
                    print(f"  {lbl:<15} dose–response contrast DiD(100) − DiD(800): {fmt(c)}{sig(c)} (n={len(j)})")
                    rows.append(dict(model=m, protocol=proto, budget=-1, outcome=lbl + " DiD(100)-DiD(800)", DiD=c[0], DiD_lo=c[1], DiD_hi=c[2], n=len(j)))
        print()
    pd.DataFrame(rows).to_csv("results/ratio_summary.csv", index=False)
    print("READING RULE (ELR): present = enforced DiD < 0, CI excludes 0; robust = also in the truncation-free complete cases")
    for b in BUDGETS:
        pres = [m for m in MODELS if verdict.get(("enforced", "ELR", m, b))]
        rob = [m for m in pres if verdict.get(("notrunc", "ELR", m, b))]
        print(f"  B={b:<4} present in {len(pres)}/3 ({', '.join(pres) or '-'}); robust in {len(rob)}/3 ({', '.join(rob) or '-'})")


def refs():
    print("\nREFERENCES — untruncated long source (ratio 100 %), and the plural-wording sensitivity (enforced, Long, B=200)")
    for m in MODELS:
        out = [m]
        pa = f"results/ratio_answers_{m}_scored.csv"
        if have(pa):
            t = boot_ci(pd.read_csv(pa).supported.astype(float).to_numpy() * 100)
            out.append(f"full long source, judged answer ELR {t[0]:.1f} [{t[1]:.1f}, {t[2]:.1f}]")
        lp = f"results/ratio_labels_{m}.jsonl"
        if have(lp):
            lab = pd.DataFrame(jl(lp)); f = lab[lab.source == "full_long"]
            out.append(f"judge-free label from full long source {f.correct.mean() * 100:.1f}")
        print("  " + " | ".join(out))
        df = load(m, "enforced")
        if df is None:
            continue
        d = df[(df.budget == 200) & (df.cond == "multi")]
        for col, lbl in OUTCOMES:
            if col not in d or d[col].isna().any():
                continue
            p = d[d["mode"] == "blind_plural"].set_index("sample_id")[col]; b = d[d["mode"] == "blind"].set_index("sample_id")[col]
            a = d[d["mode"] == "aware"].set_index("sample_id")[col]
            c = boot_ci((p - b.reindex(p.index)).to_numpy() * 100); g = boot_ci((p - a.reindex(p.index)).to_numpy() * 100)
            print(f"      {lbl:<15} Blind {b.mean() * 100:5.1f}  Blind_plural {p.mean() * 100:5.1f}  plural − frozen {fmt(c)}{sig(c)}   "
                  f"Blind_plural − Aware {fmt(g)}{sig(g)}")


def explore():
    print("\nEXPLORATORY (not pre-registered) — enforced, Long, ELR by position of the target evidence in the source")
    for m in MODELS:
        df = load(m, "enforced")
        if df is None or "sup_final" not in df:
            continue
        d = df[(df.cond == "multi") & df["mode"].isin(["aware", "blind"])].copy()
        if d.sup_final.isna().any():
            continue
        d["third"] = pd.cut(d.target_pos.astype(float), [-1, 1 / 3, 2 / 3, 2], labels=["first", "middle", "last"])
        print(f"  {m}")
        for b in BUDGETS:
            s = []
            for th in ("first", "middle", "last"):
                x = d[(d.budget == b) & (d.third == th)]
                bl = x[x["mode"] == "blind"].set_index("sample_id").sup_final; aw = x[x["mode"] == "aware"].set_index("sample_id").sup_final
                c = boot_ci((bl - aw.reindex(bl.index)).to_numpy() * 100)
                s.append(f"{th} {fmt(c)}{sig(c)} (n={len(bl)})")
            print(f"    B={b:<4} Blind − Aware | Long: " + "   ".join(s))


if __name__ == "__main__":
    design(); print(); main_tables(); refs(); explore()
