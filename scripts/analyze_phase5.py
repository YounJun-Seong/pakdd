"""Phase-5 analysis (docs/phase5_prereg.md).

  trajectory   P1-1  WP by stage M0..M4 per cell; transition loss/recovery; GEE blind*multi*stage
  notrunc      P0-2  2x2 DiD without truncation vs enforced DiD on the same S100; compliance; position
  resample     P1-2  K-profile averaged over 5 candidate subsets; subset-seed variance
  oracle       P0-1  fit rate by K x B; Oracle-Target / Oracle-All / Model-Aware / Model-Blind SR;
                     Oracle EA vs Model-Blind EA (eligible ICOs primary)
  balanced     P2-2  blind_balanced vs free-form blind at B=50/150
Outputs: printed tables + results/phase5_{exp}_summary.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_phase4 import (MODELS, boot_ci, cell_table, did_boot, gee_interaction,  # noqa: E402
                            load_exp, load_hard25, print_cells)

S100_IDS = None


def s100_ids():
    global S100_IDS
    if S100_IDS is None:
        from run_phase4 import load_samples, pilot_subset
        S100_IDS = {s["sample_id"] for s in pilot_subset(load_samples(), per_label=34)[:100]}
    return S100_IDS


def gee(df, outcome, rhs, cluster="sample_id"):
    d = df.copy(); d["y"] = d[outcome].astype(int)
    return smf.gee(f"y ~ {rhs}", groups=cluster, data=d, family=sm.families.Binomial(),
                   cov_struct=sm.cov_struct.Exchangeable()).fit()


# ------------------------------------------------------------------ P1-1
def trajectory():
    print("P1-1 MEMORY TRAJECTORY — enforced 25, complete warrant (WP) by stage; n=294")
    rows = []
    for m in MODELS:
        p = Path(f"results/phase5_trajectory_{m}_scored.csv")
        if not p.exists():
            print(f"  {m}: not scored"); continue
        d = pd.read_csv(p)
        d["wp"] = d["supported"].astype(int)
        d["present"] = (d["direction"] != "NOT_MENTIONED").astype(int)
        d["dir_ok"] = (d["direction"] == d["gold_label"]).astype(int)
        d["asserted"] = (d["certainty"] == "ASSERTED").astype(int)
        src = d[d["mode"] == "source"].set_index(["sample_id", "cond"])
        print(f"\n{m}  (M0 = seed material: single {src.loc[(slice(None), 'single'), 'wp'].mean()*100:.1f}%, "
              f"multi {src.loc[(slice(None), 'multi'), 'wp'].mean()*100:.1f}% WP)")
        print(f"  {'cell':<14}" + "".join(f"{'M'+str(s):>8}" for s in range(5)) + "   transition loss M0>1 / 1>2 / 2>3 / 3>4   recovery")
        for mode in ["aware", "blind"]:
            for ico in ["single", "multi"]:
                g = d[(d["mode"] == mode) & (d["cond"] == ico)].pivot_table(index="sample_id", columns="step", values="wp")
                g[0] = src.loc[(slice(None), ico), "wp"].droplevel("cond").reindex(g.index)
                g = g[[0, 1, 2, 3, 4]].dropna()
                means = [g[s].mean() * 100 for s in range(5)]
                loss, rec = [], []
                for s in range(1, 5):
                    prev_ok = g[s - 1] == 1
                    loss.append(((g[s] == 0) & prev_ok).sum() / max(prev_ok.sum(), 1) * 100)
                    prev_bad = g[s - 1] == 0
                    rec.append(((g[s] == 1) & prev_bad).sum() / max(prev_bad.sum(), 1) * 100)
                total_loss = means[0] - means[4]
                first = means[0] - means[1]
                share = first / total_loss * 100 if total_loss > 0 else np.nan
                print(f"  {mode+'/'+ico:<14}" + "".join(f"{v:8.1f}" for v in means)
                      + f"   {loss[0]:4.1f} / {loss[1]:4.1f} / {loss[2]:4.1f} / {loss[3]:4.1f}%   "
                      f"{np.mean(rec[1:]):4.1f}%   share of loss at M0>M1: {share:.0f}%")
                for s in range(5):
                    rows.append({"model": m, "mode": mode, "cond": ico, "step": s, "WP": means[s],
                                 "loss_from_prev": np.nan if s == 0 else loss[s - 1],
                                 "recovery_from_prev": np.nan if s == 0 else rec[s - 1]})
                comp = d[(d["mode"] == mode) & (d["cond"] == ico)].groupby("step")[["present", "dir_ok", "asserted"]].mean() * 100
                print(f"  {'':<14}   present " + " ".join(f"{v:5.1f}" for v in comp["present"])
                      + " | direction ok " + " ".join(f"{v:5.1f}" for v in comp["dir_ok"])
                      + " | asserted " + " ".join(f"{v:5.1f}" for v in comp["asserted"]))
        dd = d[d["mode"] != "source"].copy()
        dd["blind"] = (dd["mode"] == "blind").astype(int); dd["multi"] = (dd["cond"] == "multi").astype(int)
        r = gee(dd, "wp", "blind * multi * C(step, Treatment(1))")
        ks = [k for k in r.params.index if k.startswith("blind:multi:C(step")]
        print("  GEE blind x multi x stage (ref M1): " + ", ".join(f"{k.split('[T.')[1][:-1]}: {r.params[k]:+.2f} (p={r.pvalues[k]:.2g})" for k in ks))
    pd.DataFrame(rows).to_csv("results/phase5_trajectory_summary.csv", index=False)


# ------------------------------------------------------------------ P0-2
def load_p5(exp, m):
    rows = [json.loads(l) for l in open(f"results/phase5_{exp}_{m}.jsonl")]
    df = pd.DataFrame([{k: v for k, v in r.items() if k not in ("memory", "text", "steps")} for r in rows])
    keys = ["sample_id", "mode", "cond", "budget"] + (["K", "subset_seed"] if "subset_seed" in df.columns else [])
    fin = pd.read_csv(f"results/phase5_{exp}_{m}_final_scored.csv")[keys + ["supported"]].rename(columns={"supported": "sup_final"})
    mem = pd.read_csv(f"results/phase5_{exp}_{m}_mem_scored.csv")[keys + ["supported"]].rename(columns={"supported": "sup_mem"})
    df = df.merge(fin, on=keys).merge(mem, on=keys)
    df[["sup_final", "sup_mem"]] = df[["sup_final", "sup_mem"]].astype(int)
    df["model"] = m
    if "forced" not in df:
        df["forced"] = False
    return df


def notrunc():
    print("P0-2 TRUNCATION-FREE ROBUSTNESS — S100, regenerate-until-compliant, never cut")
    ids = s100_ids(); rows = []
    for m in MODELS:
        if not Path(f"results/phase5_notrunc_{m}_final_scored.csv").exists():
            print(f"  {m}: not scored"); continue
        raw = pd.DataFrame([json.loads(l) for l in open(f"results/phase5_notrunc_{m}.jsonl")])
        df = load_p5("notrunc", m)
        print(f"\n{m}")
        for b in sorted(df["budget"].unique()):
            g = df[(df["budget"] == b) & (df["cond"].isin(["single", "multi"]))]
            rw = raw[(raw["budget"] == b) & (raw["cond"].isin(["single", "multi"]))]
            fail = rw.groupby(["mode", "cond"])["failed"].mean() * 100
            att = rw[~rw["failed"]].groupby(["mode", "cond"])["mean_attempts"].mean()
            first = rw[~rw["failed"]].explode("first_try_compliant").groupby(["mode", "cond"])["first_try_compliant"].mean() * 100
            print(f"  B={b}  failed% A/S {fail.get(('aware','single'),0):.0f} A/M {fail.get(('aware','multi'),0):.0f} "
                  f"B/S {fail.get(('blind','single'),0):.0f} B/M {fail.get(('blind','multi'),0):.0f} | mean attempts "
                  f"A/S {att.get(('aware','single'),np.nan):.1f} A/M {att.get(('aware','multi'),np.nan):.1f} "
                  f"B/S {att.get(('blind','single'),np.nan):.1f} B/M {att.get(('blind','multi'),np.nan):.1f} | first-try compliant% "
                  f"A/S {first.get(('aware','single'),np.nan):.0f} A/M {first.get(('aware','multi'),np.nan):.0f} "
                  f"B/S {first.get(('blind','single'),np.nan):.0f} B/M {first.get(('blind','multi'),np.nan):.0f}")
            out, _, _ = cell_table(g)
            print_cells(f"no-trunc B={b}", out, 0, 0)
            # enforced comparison on the same articles
            enf = load_hard25(m) if b == 25 else load_exp("budget", m).query("budget == @b")
            enf = enf[enf["sample_id"].isin(g["sample_id"].unique())]
            oute, fe, fbm = cell_table(enf)
            print_cells(f"enforced B={b} (same n)", oute, fe, fbm)
            for name in ["SR", "warrant"]:
                rows.append({"model": m, "budget": b, "outcome": name, "protocol": "no-trunc", **out[name]})
                rows.append({"model": m, "budget": b, "outcome": name, "protocol": "enforced", **oute[name]})
        # position arm at B=25
        pos = df[(df["budget"] == 25) & (df["cond"].isin(["first", "middle", "last"]))]
        if len(pos):
            for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
                piv = pos.pivot_table(index="sample_id", columns=["cond", "mode"], values=outcome, aggfunc="first").dropna()
                line = []
                for q in ["first", "middle", "last"]:
                    pen = (piv[(q, "blind")] - piv[(q, "aware")]).to_numpy(float) * 100
                    pm, lo, hi = boot_ci(pen); line.append(f"{q} {pm:+5.1f} [{lo:+5.1f},{hi:+5.1f}]")
                    rows.append({"model": m, "budget": 25, "outcome": name, "protocol": "no-trunc", "position": q, "penalty": pm, "lo": lo, "hi": hi})
                fl = ((piv[("first", "blind")] - piv[("first", "aware")]) - (piv[("last", "blind")] - piv[("last", "aware")])).to_numpy(float) * 100
                fm, flo, fhi = boot_ci(fl)
                print(f"  position B=25 {name:<8} blind penalty: " + "  ".join(line) + f"  | first-last {fm:+5.1f} [{flo:+5.1f},{fhi:+5.1f}] (n={len(piv)})")
            p4 = load_exp("position", m); p4 = p4[(p4["budget"] == 25) & (p4["sample_id"].isin(pos["sample_id"].unique()))]
            piv = p4.pivot_table(index="sample_id", columns=["cond", "mode"], values="sup_final", aggfunc="first").dropna()
            print("  enforced ③ on same articles, SR: " + "  ".join(f"{q} {(piv[(q,'blind')]-piv[(q,'aware')]).mean()*100:+5.1f}" for q in ["first", "middle", "last"]))
    pd.DataFrame(rows).to_csv("results/phase5_notrunc_summary.csv", index=False)


# ------------------------------------------------------------------ P1-2
def resample():
    print("P1-2 REPEATED CANDIDATE-SUBSET RANDOMIZATION — A5, B=50, K=2..5, 5 subsets (42 + 4 new)")
    rows = []
    for m in MODELS:
        if not Path(f"results/phase5_resample_{m}_final_scored.csv").exists():
            print(f"  {m}: not scored"); continue
        new = load_p5("resample", m)
        old = load_exp("kdose", m); old = old[old["budget"] == 50].copy(); old["subset_seed"] = 42
        old = old[old["K"] >= 2]
        df = pd.concat([new, old[new.columns.intersection(old.columns)]], ignore_index=True)
        print(f"\n{m}  n={df['sample_id'].nunique()} articles, subsets per (article,K): {df.groupby(['sample_id','K'])['subset_seed'].nunique().mean():.1f}")
        for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
            line = []
            for k in range(2, 6):
                gk = df[df["K"] == k]
                piv = gk.pivot_table(index=["sample_id", "subset_seed"], columns="mode", values=outcome, aggfunc="first").dropna()
                pen_art = (piv["blind"] - piv["aware"]).groupby(level="sample_id").mean().to_numpy(float) * 100
                pm, lo, hi = boot_ci(pen_art)
                per_seed = (piv["blind"] - piv["aware"]).groupby(level="subset_seed").mean() * 100
                rows.append({"model": m, "outcome": name, "K": k, "penalty": pm, "lo": lo, "hi": hi,
                             "seed_sd": per_seed.std(ddof=1), **{f"seed{s}": v for s, v in per_seed.items()}})
                line.append(f"K{k} {pm:+5.1f} [{lo:+5.1f},{hi:+5.1f}] (seed SD {per_seed.std(ddof=1):.1f})")
            print(f"  {name:<8} " + "  ".join(line))
            dd = df.copy(); dd["blind"] = (dd["mode"] == "blind").astype(int); dd["Kc"] = dd["K"] - 3.5
            r = gee(dd, outcome, "blind * Kc")
            print(f"  {name:<8} GEE (all subsets): blind x K {r.params['blind:Kc']:+.3f} (p={r.pvalues['blind:Kc']:.2g}); aware slope {r.params['Kc']:+.3f} (p={r.pvalues['Kc']:.2g})")
    pd.DataFrame(rows).to_csv("results/phase5_resample_summary.csv", index=False)


# ------------------------------------------------------------------ P0-1
def oracle():
    print("P0-1 ORACLE MULTI-WARRANT CAPACITY CONTROL")
    readable = None
    rp = Path("data/gate2/distractor_readability.jsonl")
    if rp.exists():
        rd = pd.read_json(rp, lines=True)
        readable = {(s, p) for s, p, ok in zip(rd["sample_id"], rd["prompt_id"], rd["readable"]) if ok}
    rows = []
    for m in MODELS:
        if not Path(f"results/phase5_oracle_{m}_scored.csv").exists():
            print(f"  {m}: not scored"); continue
        o = pd.read_csv(f"results/phase5_oracle_{m}_scored.csv")
        o["supported"] = o["supported"].astype(int)
        # n_ico was late-bound in the generator (always the last article's K); derive K from the data
        kmap = {json.loads(l)["sample_id"]: 1 + len(json.loads(l)["distractors"]) for l in open("data/gate2/gate2_v1.jsonl")}
        o["n_ico"] = o["sample_id"].map(kmap)
        print(f"\n{m}")
        # fit rate by K x B (short format, oracle_all)
        oa = o[(o["kind"] == "oracle_all") & (o["fmt"] == "short") & (o["role"] == "target")]
        fit = oa.groupby(["n_ico", "budget"])["fits"].mean().unstack() * 100
        fit.loc["all"] = oa.groupby("budget")["fits"].mean() * 100
        print("  Oracle-All (short) fit rate % by K x B:"); print(fit.round(0).to_string())
        of = o[(o["kind"] == "oracle_all") & (o["fmt"] == "full") & (o["role"] == "target")]
        print("  Oracle-All (full) fit rate % by B: " + "  ".join(f"B={b} {v:.0f}" for b, v in (of.groupby('budget')['fits'].mean()*100).items()))
        # target SR: oracle_target / oracle_all(short) / oracle_all(full) / model aware / model blind
        base = pd.concat([load_hard25(m), load_exp("budget", m).query("budget != 25")])
        bm = base[(base["cond"] == "multi")].groupby(["budget", "mode"])["sup_final"].mean().unstack() * 100
        print(f"  {'B':>4} {'Oracle-T':>9} {'Oracle-All':>11} {'(fit only)':>11} {'Oracle-All full':>15} {'Model-Aware':>12} {'Model-Blind':>12}")
        for b in sorted(o["budget"].unique()):
            ot = o[(o["kind"] == "oracle_target") & (o["budget"] == b) & (o["role"] == "target")]["supported"].mean() * 100
            oas = oa[oa["budget"] == b]; oall = oas["supported"].mean() * 100
            ofit = oas[oas["fits"]]["supported"].mean() * 100 if oas["fits"].any() else np.nan
            ofu = of[of["budget"] == b]["supported"].mean() * 100
            # paired comparison on the fit-only articles: model aware/blind SR on the SAME articles
            fit_ids = set(oas[oas["fits"]]["sample_id"])
            sub = base[(base["budget"] == b) & (base["cond"] == "multi") & (base["sample_id"].isin(fit_ids))]
            aw_fit = sub[sub["mode"] == "aware"]["sup_final"].mean() * 100 if len(sub) else np.nan
            bl_fit = sub[sub["mode"] == "blind"]["sup_final"].mean() * 100 if len(sub) else np.nan
            print(f"  {b:>4} {ot:9.1f} {oall:11.1f} {ofit:8.1f} (n={int(oas['fits'].sum()):3d}) {ofu:15.1f} {bm.loc[b,'aware']:12.1f} {bm.loc[b,'blind']:12.1f}"
                  f"   | fit-only articles: aware {aw_fit:5.1f} blind {bl_fit:5.1f}")
            rows.append({"model": m, "budget": b, "oracle_target": ot, "oracle_all": oall, "oracle_all_fit": ofit,
                         "n_fit": int(oas["fits"].sum()), "oracle_all_full": ofu, "model_aware": bm.loc[b, "aware"], "model_blind": bm.loc[b, "blind"],
                         "model_aware_fitsub": aw_fit, "model_blind_fitsub": bl_fit})
        # Expected answerability: oracle_all short (all ICOs) vs model blind (blind-ea)
        be_p = Path(f"results/phase5_blindea_{m}_scored.csv")
        be = pd.read_csv(be_p) if be_p.exists() else None
        print(f"  Expected Answerability (article-weighted; eligible ICOs):  {'B':>4} {'Oracle-All':>11} {'Model-Blind':>12}  | all ICOs: Oracle / Blind")
        for b in sorted(o["budget"].unique()):
            def ea(df):
                if df is None or df.empty:
                    return np.nan, np.nan
                d = df.copy(); d["supported"] = d["supported"].astype(int)
                allv = d.groupby("sample_id")["supported"].mean().mean() * 100
                if readable is not None:
                    elig = d[[(r == "target") or ((s, p) in readable) for r, s, p in zip(d["role"], d["sample_id"], d["prompt_id"])]]
                    return elig.groupby("sample_id")["supported"].mean().mean() * 100, allv
                return np.nan, allv
            oe, oa_all = ea(o[(o["kind"] == "oracle_all") & (o["fmt"] == "short") & (o["budget"] == b)])
            bee, be_all = ea(be[be["budget"] == b] if be is not None else None)
            print(f"  {'':<57} {b:>4} {oe:11.1f} {bee:12.1f}  | {oa_all:5.1f} / {be_all:5.1f}")
            rows[-len(sorted(o["budget"].unique())) + sorted(o["budget"].unique()).index(b)].update(
                {"oracle_EA_eligible": oe, "blind_EA_eligible": bee, "oracle_EA_all": oa_all, "blind_EA_all": be_all})
    pd.DataFrame(rows).to_csv("results/phase5_oracle_summary.csv", index=False)


# ------------------------------------------------------------------ P2-2
def balanced():
    print("P2-2 BALANCED COMPACT MEMORY vs free-form blind (multi)")
    for m in MODELS:
        if not Path(f"results/phase5_balanced_{m}_final_scored.csv").exists():
            print(f"  {m}: not scored"); continue
        bl = load_p5("balanced", m)
        base = load_exp("budget", m)
        for b, g in bl.groupby("budget"):
            ref = base[(base["budget"] == b) & (base["cond"] == "multi") & (base["mode"] == "blind")]
            j = g.merge(ref[["sample_id", "sup_final", "sup_mem", "forced"]], on="sample_id", suffixes=("_bal", "_free"))
            for o in ["sup_final", "sup_mem"]:
                d = (j[f"{o}_bal"].astype(float) - j[f"{o}_free"].astype(float)).to_numpy() * 100
                dm, lo, hi = boot_ci(d)
                print(f"  {m:<13} B={b:<4} {o:<9} free {j[f'{o}_free'].mean()*100:5.1f} balanced {j[f'{o}_bal'].mean()*100:5.1f}  "
                      f"delta {dm:+5.1f} [{lo:+5.1f},{hi:+5.1f}]  forced: free {j['forced_free'].mean()*100:.0f}% balanced {j['forced_bal'].mean()*100:.0f}%")




# ------------------------------------------------------------------ P0-2 diagnostics
def truncdiag():
    """Forced-truncation diagnostics per model x budget x cell, from the ① enforced
    chains (every step's raw length is recorded): chain-level forced rate,
    write-level truncation rate, mean pre-truncation length, tokens cut when cut,
    and the paired Aware/Multi vs Blind/Multi difference in chain-forced rate.
    Attempts: Phase-3 regeneration control (B=25, <=4 tries) and, when scored,
    the Phase-5 truncation-free arm (S100, adaptive, <=20 tries)."""
    print("P0-2 FORCED-TRUNCATION DIAGNOSTICS — enforced-cap ① chains, n=294 per cell")
    rows = []
    cells = [("aware", "single"), ("aware", "multi"), ("blind", "single"), ("blind", "multi")]
    for m in MODELS:
        df = load_exp("budget", m, need_scores=False)
        print(f"\n{m}   (per cell: chain-forced% | write-level truncated% | mean raw tok/step | mean tokens cut when cut)")
        for b in sorted(df["budget"].unique()):
            d = df[df["budget"] == b]
            parts = []
            for mode, ico in cells:
                g = d[(d["mode"] == mode) & (d["cond"] == ico)]
                steps = np.concatenate(g["step_raw"].tolist())
                over = steps[steps > b]
                cf = g["forced"].mean() * 100; wl = (steps > b).mean() * 100
                cut = (over - b).mean() if len(over) else 0.0
                parts.append(f"{mode[0].upper()}/{ico[0].upper()} {cf:3.0f}|{wl:3.0f}|{steps.mean():5.1f}|{cut:4.1f}")
                rows.append({"model": m, "budget": b, "mode": mode, "cond": ico, "chain_forced_pct": cf,
                             "write_truncated_pct": wl, "mean_raw_tokens": steps.mean(),
                             "mean_tokens_cut_when_cut": cut, "p90_raw_tokens": np.percentile(steps, 90)})
            am = d[(d["mode"] == "aware") & (d["cond"] == "multi")].set_index("sample_id")["forced"].astype(float)
            bm = d[(d["mode"] == "blind") & (d["cond"] == "multi")].set_index("sample_id")["forced"].astype(float)
            diff = (bm - am.reindex(bm.index)).dropna().to_numpy() * 100
            dm, lo, hi = boot_ci(diff)
            print(f"  B={b:<4} " + "  ".join(parts) + f"   | B/M − A/M chain-forced {dm:+5.1f} pp [{lo:+.1f},{hi:+.1f}]")
            rows[-1]["bm_minus_am_forced"] = dm; rows[-1]["bm_minus_am_lo"] = lo; rows[-1]["bm_minus_am_hi"] = hi
        # attempts: Phase-3 regeneration control at 25 (<=4 tries, then forced)
        rp = Path(f"results/extra_regen_{m}_scored.csv")
        if rp.exists():
            r = pd.read_csv(rp)
            t = r.groupby(["mode", "icoset"]).agg(tries=("tries", "mean"), forced=("forced", "mean"))
            print("  regen control B=25 (<=4 tries): " + "  ".join(
                f"{mo[0].upper()}/{ic[0].upper()} tries {v.tries/4:.2f}/step, still forced {v.forced*100:.0f}%"
                for (mo, ic), v in t.iterrows()))
        np_ = Path(f"results/phase5_notrunc_{m}.jsonl")
        if np_.exists():
            raw = pd.DataFrame([json.loads(l) for l in open(np_)])
            raw = raw[raw["cond"].isin(["single", "multi"])]
            for b, g in raw.groupby("budget"):
                ok = g[~g["failed"]]
                att = ok.groupby(["mode", "cond"])["mean_attempts"].mean()
                fail = g.groupby(["mode", "cond"])["failed"].mean() * 100
                print(f"  no-trunc arm S100 B={b} (adaptive, <=20 tries): " + "  ".join(
                    f"{mo[0].upper()}/{ic[0].upper()} {att.get((mo, ic), np.nan):.2f} tries/step, failed {fail.get((mo, ic), 0):.0f}%"
                    for mo, ic in cells))
    pd.DataFrame(rows).to_csv("results/phase5_truncdiag_summary.csv", index=False)


_CMDS = {"trajectory": trajectory, "notrunc": notrunc, "resample": resample,
         "oracle": oracle, "balanced": balanced, "truncdiag": truncdiag}
if __name__ == "__main__":
    _CMDS[sys.argv[1]]()
