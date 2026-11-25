"""Phase-4 analysis (docs/phase4_prereg.md). Every statistic here is what the
pre-registration names; nothing else is computed.

  pilot                 ① compliance / forced truncation per budget -> B_high
  budget                ① 2x2 cells per budget: SR + warrant DiD (bootstrap CI),
                          GEE blind*multi per budget, three-way blind*multi*log2B
  length                ② blind penalty per condition; multi - control contrasts
  position              ③ blind penalty per target position; balanced average
  kdose                 ⑤ SR/warrant over K, GEE blind*K slope
  depth                 ⑥ DiD at depth 1/3/5, GEE blind*multi*depth
  slots                 ⑧ blind_slots vs blind, multi

Inputs: results/phase4_{exp}_{model}.jsonl (+ _final_scored.csv, _mem_scored.csv).
Outputs: printed tables + results/phase4_{exp}_summary.csv
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

MODELS = ["qwen3-8b", "qwen3-14b", "gpt-5.4-mini"]
SEED, N_BOOT = 42, 2000


# ------------------------------------------------------------------ helpers
def boot_ci(per_article: np.ndarray, seed=SEED):
    rng = np.random.default_rng(seed)
    x = np.asarray(per_article, float)
    ms = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(N_BOOT)]
    return x.mean(), np.percentile(ms, 2.5), np.percentile(ms, 97.5)


def did_boot(df, outcome, seed=SEED):
    """DiD = (blind-aware | multi) - (blind-aware | single), paired by article.
    Returns pp with percentile bootstrap CI over articles."""
    piv = df.pivot_table(index="sample_id", columns=["mode", "cond"], values=outcome, aggfunc="first")
    piv = piv.dropna()
    d = ((piv[("blind", "multi")] - piv[("aware", "multi")])
         - (piv[("blind", "single")] - piv[("aware", "single")])).to_numpy(float) * 100
    m, lo, hi = boot_ci(d, seed)
    return m, lo, hi, len(d)


def gee_interaction(df, outcome, formula_rhs="blind * multi", extra_cols=None):
    d = df.copy()
    d["y"] = d[outcome].astype(int)
    d["blind"] = (d["mode"] == "blind").astype(int)
    d["multi"] = (d["cond"] == "multi").astype(int)
    if extra_cols:
        for k, v in extra_cols.items():
            d[k] = v(d)
    r = smf.gee(f"y ~ {formula_rhs}", groups="sample_id", data=d,
                family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
    return r


def load_exp(exp, model, need_scores=True):
    """Design rows joined with evaluator verdicts for final (sup_final) and
    last memory (sup_mem)."""
    rows = [json.loads(l) for l in open(f"results/phase4_{exp}_{model}.jsonl")]
    df = pd.DataFrame([{k: v for k, v in r.items() if k not in ("steps", "memory", "text")}
                       for r in rows])
    df["step_raw"] = [[s["raw_tokens"] for s in r["steps"]] for r in rows]
    df["n_steps"] = [len(r["steps"]) for r in rows]
    if not need_scores:
        return df
    keys = ["sample_id", "mode", "cond", "budget", "depth"] + (["seed"] if "seed" in df.columns else [])
    fin = pd.read_csv(f"results/phase4_{exp}_{model}_final_scored.csv")[keys + ["supported", "claim_label"]]
    mem = pd.read_csv(f"results/phase4_{exp}_{model}_mem_scored.csv")[keys + ["supported", "claim_label"]]
    df = df.merge(fin.rename(columns={"supported": "sup_final", "claim_label": "final_label"}), on=keys)
    df = df.merge(mem.rename(columns={"supported": "sup_mem", "claim_label": "mem_label"}), on=keys)
    df["model"] = model
    df[["sup_final", "sup_mem"]] = df[["sup_final", "sup_mem"]].astype(int)   # bools break "-"
    return df


def load_hard25(model):
    """The paper's enforced-25 grid (Fig. 2) in phase4 row format, with token
    counts replayed by `run_phase4.py budget --budgets 25`."""
    p = Path(f"results/phase4_budget_{model}.jsonl")
    if p.exists():
        df = load_exp("budget", model)
        return df[df["budget"] == 25]
    fin = pd.read_csv(f"results/extra_hard_{model}_scored.csv")
    mem = pd.read_csv(f"results/extra_hardmem_{model}_scored.csv")
    mem = mem[mem["step"] == 4]
    df = fin.rename(columns={"icoset": "cond", "supported": "sup_final"})[
        ["sample_id", "mode", "cond", "sup_final"]]
    df = df.merge(mem.rename(columns={"icoset": "cond", "supported": "sup_mem"})[
        ["sample_id", "mode", "cond", "sup_mem"]], on=["sample_id", "mode", "cond"])
    df["budget"], df["depth"], df["model"] = 25, 5, model
    df["forced"] = np.nan
    df[["sup_final", "sup_mem"]] = df[["sup_final", "sup_mem"]].astype(int)
    return df


def cell_table(df, label=""):
    """Four-cell SR/warrant table with penalties, DiD, GEE p, forced rate."""
    out = {}
    for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
        cells = df.groupby(["cond", "mode"])[outcome].mean() * 100
        did, lo, hi, n = did_boot(df, outcome)
        g = gee_interaction(df, outcome)
        out[name] = dict(
            S_aware=cells[("single", "aware")], S_blind=cells[("single", "blind")],
            M_aware=cells[("multi", "aware")], M_blind=cells[("multi", "blind")],
            pen_S=cells[("single", "blind")] - cells[("single", "aware")],
            pen_M=cells[("multi", "blind")] - cells[("multi", "aware")],
            DiD=did, DiD_lo=lo, DiD_hi=hi, n=n,
            gee_coef=g.params["blind:multi"], gee_p=g.pvalues["blind:multi"])
    forced = df["forced"].mean() * 100 if df["forced"].notna().any() else np.nan
    forced_bm = (df[(df["mode"] == "blind") & (df["cond"] == "multi")]["forced"].mean() * 100
                 if df["forced"].notna().any() else np.nan)
    return out, forced, forced_bm


def print_cells(tag, out, forced, forced_bm):
    for name in ["SR", "warrant"]:
        o = out[name]
        print(f"  {tag:<28} {name:<8} S {o['S_aware']:5.1f}/{o['S_blind']:5.1f} ({o['pen_S']:+5.1f}) "
              f"M {o['M_aware']:5.1f}/{o['M_blind']:5.1f} ({o['pen_M']:+5.1f})  "
              f"DiD {o['DiD']:+5.1f} [{o['DiD_lo']:+5.1f},{o['DiD_hi']:+5.1f}]  "
              f"GEE p={o['gee_p']:.2g}  forced all/BM {forced:4.0f}/{forced_bm:4.0f}%")


# ------------------------------------------------------------------ ① pilot
def pilot():
    print("① PILOT — chain-level forced truncation (any step raw > B) and natural "
          "step compliance, multi-ICO, P60")
    rows = []
    for m in MODELS:
        p = Path(f"results/phase4_pilot_{m}.jsonl")
        if not p.exists():
            print(f"  {m}: pilot not finished"); continue
        df = load_exp("pilot", m, need_scores=False)
        for (b, mode), g in df.groupby(["budget", "mode"]):
            steps = np.concatenate(g["step_raw"].tolist())
            over = steps[steps > b]
            rows.append({"model": m, "budget": b, "mode": mode, "n": len(g),
                         "forced_chain_%": g["forced"].mean() * 100,
                         "step_compliance_%": (steps <= b).mean() * 100,
                         "mean_raw_tokens": steps.mean(),
                         "p90_raw_tokens": np.percentile(steps, 90),
                         # severity: share of the raw text removed when a step IS truncated
                         "cut_frac_when_forced_%": ((over - b) / over).mean() * 100 if len(over) else 0.0})
    t = pd.DataFrame(rows)
    if t.empty:
        return
    print(t.pivot_table(index=["model", "mode"], columns="budget",
                        values="forced_chain_%").round(1).to_string())
    print("\nstep-level natural compliance (%):")
    print(t.pivot_table(index=["model", "mode"], columns="budget",
                        values="step_compliance_%").round(1).to_string())
    print("\nmean raw tokens per step:")
    print(t.pivot_table(index=["model", "mode"], columns="budget",
                        values="mean_raw_tokens").round(1).to_string())
    print("\ntruncation severity — % of a step's raw tokens removed, given it was truncated:")
    print(t.pivot_table(index=["model", "mode"], columns="budget",
                        values="cut_frac_when_forced_%").round(1).to_string())
    bm = t[t["mode"] == "blind"].pivot_table(index="model", columns="budget", values="forced_chain_%")
    ok = (bm <= 10).all(axis=0)
    passing = [b for b in bm.columns if ok[b]]
    print(f"\nBlind/Multi forced-truncation <= 10% in ALL models at budgets: {passing}")
    print(f"=> B_high = {min(passing) if passing else 'none <= 150 -> use 150 and report shortfall'}")
    t.to_csv("results/phase4_pilot_summary.csv", index=False)


# ------------------------------------------------------------------ ① budget
def budget():
    print("① BUDGET SWEEP — enforced cap, depth 5, n=294 paired articles")
    summary, frames = [], []
    for m in MODELS:
        print(f"\n{m}")
        parts = [load_hard25(m)]
        p = Path(f"results/phase4_budget_{m}_final_scored.csv")
        if p.exists():
            d = load_exp("budget", m)
            parts.append(d[d["budget"] != 25])
        df = pd.concat(parts, ignore_index=True)
        frames.append(df)
        for b, g in sorted(df.groupby("budget"), key=lambda kv: kv[0]):
            out, forced, forced_bm = cell_table(g)
            print_cells(f"B={b}", out, forced, forced_bm)
            for name in ["SR", "warrant"]:
                summary.append({"model": m, "budget": b, "outcome": name,
                                "forced_all": forced, "forced_blind_multi": forced_bm, **out[name]})
        if df["budget"].nunique() >= 3:
            for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
                g3 = gee_interaction(df, outcome, "blind * multi * logB",
                                     {"logB": lambda d: np.log2(d["budget"]) - np.log2(d["budget"]).mean()})
                k = "blind:multi:logB"
                print(f"  three-way blind x multi x log2(B) [{name}]: coef {g3.params[k]:+.3f} "
                      f"(SE {g3.bse[k]:.3f}), p={g3.pvalues[k]:.3g}  "
                      f"(positive = interaction shrinks as budget grows)")
    pd.DataFrame(summary).to_csv("results/phase4_budget_summary.csv", index=False)


# ------------------------------------------------------------------ ② length
def length():
    print("② LENGTH-MATCHED CONTROL — blind penalty by material condition")
    summary = []
    for m in MODELS:
        p = Path(f"results/phase4_length_{m}_final_scored.csv")
        if not p.exists():
            print(f"  {m}: not scored"); continue
        ctrl = load_exp("length", m)
        base = pd.concat([load_hard25(m)] + (
            [load_exp("budget", m).query("budget != 25")]
            if Path(f"results/phase4_budget_{m}_final_scored.csv").exists() else []))
        df = pd.concat([ctrl, base[base["budget"].isin(ctrl["budget"].unique())]], ignore_index=True)
        # restrict to articles that have every condition at that budget
        for b, g in df.groupby("budget"):
            have = g.groupby("sample_id")["cond"].nunique()
            g = g[g["sample_id"].isin(have[have == g["cond"].nunique()].index)]
            print(f"\n{m}  B={b}  n={g['sample_id'].nunique()} articles with all conditions")
            for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
                piv = g.pivot_table(index="sample_id", columns=["cond", "mode"], values=outcome, aggfunc="first")
                for cond in ["single", "single_filler", "single_dup", "multi"]:
                    if (cond, "blind") not in piv:
                        continue
                    a, bl = piv[(cond, "aware")].mean() * 100, piv[(cond, "blind")].mean() * 100
                    pen = ((piv[(cond, "blind")] - piv[(cond, "aware")]).to_numpy(float)) * 100
                    pm, plo, phi = boot_ci(pen)
                    summary.append({"model": m, "budget": b, "outcome": name, "cond": cond,
                                    "aware": a, "blind": bl, "penalty": pm, "pen_lo": plo, "pen_hi": phi})
                    print(f"  {name:<8} {cond:<14} aware {a:5.1f} blind {bl:5.1f}  penalty {pm:+5.1f} [{plo:+5.1f},{phi:+5.1f}]")
                for ctrl_cond in ["single_filler", "single_dup"]:
                    if (ctrl_cond, "blind") not in piv:
                        continue
                    d = (piv[("multi", "blind")] - piv[(ctrl_cond, "blind")]).to_numpy(float) * 100
                    dm, dlo, dhi = boot_ci(d)
                    print(f"  {name:<8} blind multi - {ctrl_cond:<13}: {dm:+5.1f} [{dlo:+5.1f},{dhi:+5.1f}]")
    pd.DataFrame(summary).to_csv("results/phase4_length_summary.csv", index=False)


# ------------------------------------------------------------------ ③ position
def position():
    print("③ TARGET POSITION — blind penalty by target position (multi)")
    summary = []
    for m in MODELS:
        p = Path(f"results/phase4_position_{m}_final_scored.csv")
        if not p.exists():
            print(f"  {m}: not scored"); continue
        df = load_exp("position", m)
        for b, g in df.groupby("budget"):
            print(f"\n{m}  B={b}")
            for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
                piv = g.pivot_table(index="sample_id", columns=["cond", "mode"], values=outcome, aggfunc="first").dropna()
                pens = {}
                for pos in ["first", "middle", "last"]:
                    pen = (piv[(pos, "blind")] - piv[(pos, "aware")]).to_numpy(float) * 100
                    pens[pos] = pen
                    pm, lo, hi = boot_ci(pen)
                    summary.append({"model": m, "budget": b, "outcome": name, "position": pos,
                                    "aware": piv[(pos, "aware")].mean() * 100,
                                    "blind": piv[(pos, "blind")].mean() * 100,
                                    "penalty": pm, "pen_lo": lo, "pen_hi": hi})
                    print(f"  {name:<8} {pos:<7} aware {piv[(pos, 'aware')].mean()*100:5.1f} "
                          f"blind {piv[(pos, 'blind')].mean()*100:5.1f}  penalty {pm:+5.1f} [{lo:+5.1f},{hi:+5.1f}]")
                bal = np.mean([pens[p] for p in pens], axis=0)
                bm, blo, bhi = boot_ci(bal)
                fl = pens["first"] - pens["last"]
                fm, flo, fhi = boot_ci(fl)
                print(f"  {name:<8} position-balanced penalty {bm:+5.1f} [{blo:+5.1f},{bhi:+5.1f}]; "
                      f"first - last {fm:+5.1f} [{flo:+5.1f},{fhi:+5.1f}]")
                gg = g.copy(); gg["y"] = gg[outcome].astype(int)
                gg["blind"] = (gg["mode"] == "blind").astype(int)
                gg["last"] = (gg["cond"] == "last").astype(int)
                r = smf.gee("y ~ blind * last", groups="sample_id", data=gg,
                            family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
                print(f"  {name:<8} GEE blind x last: coef {r.params['blind:last']:+.3f}, p={r.pvalues['blind:last']:.3g}")
    pd.DataFrame(summary).to_csv("results/phase4_position_summary.csv", index=False)


# ------------------------------------------------------------------ ⑤ K dose
def kdose():
    print("⑤ RANDOMIZED K — dose-response, subset A5")
    summary = []
    for m in MODELS:
        p = Path(f"results/phase4_kdose_{m}_final_scored.csv")
        if not p.exists():
            print(f"  {m}: not scored"); continue
        df = load_exp("kdose", m)
        for b, g in df.groupby("budget"):
            print(f"\n{m}  B={b}  n={g['sample_id'].nunique()} articles")
            for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
                line = []
                for k in range(1, 6):
                    gk = g[g["K"] == k]
                    a = gk[gk["mode"] == "aware"][outcome].mean() * 100
                    bl = gk[gk["mode"] == "blind"][outcome].mean() * 100
                    piv = gk.pivot_table(index="sample_id", columns="mode", values=outcome, aggfunc="first").dropna()
                    pm, lo, hi = boot_ci((piv["blind"] - piv["aware"]).to_numpy(float) * 100)
                    summary.append({"model": m, "budget": b, "outcome": name, "K": k, "aware": a,
                                    "blind": bl, "penalty": pm, "pen_lo": lo, "pen_hi": hi})
                    line.append(f"K{k} {a:4.1f}/{bl:4.1f} ({pm:+5.1f})")
                print(f"  {name:<8} " + "  ".join(line))
                gg = g.copy(); gg["y"] = gg[outcome].astype(int)
                gg["blind"] = (gg["mode"] == "blind").astype(int)
                gg["Kc"] = gg["K"] - 3
                r = smf.gee("y ~ blind * Kc", groups="sample_id", data=gg,
                            family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
                print(f"  {name:<8} GEE: aware slope/K {r.params['Kc']:+.3f} (p={r.pvalues['Kc']:.2g}); "
                      f"blind x K {r.params['blind:Kc']:+.3f} (p={r.pvalues['blind:Kc']:.2g})")
    pd.DataFrame(summary).to_csv("results/phase4_kdose_summary.csv", index=False)


# ------------------------------------------------------------------ ⑥ depth
def depth():
    print("⑥ DEPTH FACTORIAL — enforced 25")
    summary = []
    for m in MODELS:
        p = Path(f"results/phase4_depth3_{m}_final_scored.csv")
        if not p.exists():
            print(f"  {m}: depth 3 not scored"); continue
        d3 = load_exp("depth3", m)
        d5 = load_hard25(m)
        # depth 1 = nominal direct (budget-independent); aware == blind, no memory
        nom = pd.read_csv(f"results/gate2_scored_{m}.csv")
        d1 = nom[(nom["role"] == "final") & (nom["depth"] == 1)].copy()
        d1 = d1.rename(columns={"icoset": "cond", "supported": "sup_final"})[["sample_id", "cond", "sup_final"]]
        d1["sup_final"] = d1["sup_final"].astype(int)
        d1 = pd.concat([d1.assign(mode="aware"), d1.assign(mode="blind")])
        d1["depth"], d1["budget"], d1["model"], d1["sup_mem"], d1["forced"] = 1, 25, m, np.nan, np.nan
        print(f"\n{m}")
        for dd, g in [(1, d1), (3, d3), (5, d5)]:
            out, forced, forced_bm = cell_table(g) if dd != 1 else (None, np.nan, np.nan)
            if dd == 1:
                cells = g.groupby("cond")["sup_final"].mean() * 100
                print(f"  depth 1 (direct)   SR single {cells['single']:5.1f}  multi {cells['multi']:5.1f}  (aware==blind)")
                continue
            print_cells(f"depth {dd}", out, forced, forced_bm)
            for name in ["SR", "warrant"]:
                summary.append({"model": m, "depth": dd, "outcome": name, **out[name]})
        both = pd.concat([d3, d5], ignore_index=True)
        for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
            r = gee_interaction(both, outcome, "blind * multi * deep", {"deep": lambda d: (d["depth"] == 5).astype(int)})
            k = "blind:multi:deep"
            print(f"  three-way blind x multi x depth5 [{name}]: coef {r.params[k]:+.3f}, p={r.pvalues[k]:.3g}")
    pd.DataFrame(summary).to_csv("results/phase4_depth_summary.csv", index=False)


# ------------------------------------------------------------------ seeds
def seeds():
    print("SEED ROBUSTNESS — S100 subset, enforced cap, DiD per seed (42 = main run; "
          "for GPT-5.4-mini the seed is not honoured by the API, so 143/244 are independent re-runs)")
    rows = []
    for m in MODELS:
        if not all(Path(f"results/phase4_seeds_{m}_{s}_scored.csv").exists() for s in ("final", "mem")):
            print(f"  {m}: not scored"); continue
        sd = load_exp("seeds", m)
        s100 = set(sd["sample_id"])
        base = pd.concat([load_hard25(m), load_exp("budget", m).query("budget != 25")])
        base = base[base["sample_id"].isin(s100)].copy(); base["seed"] = 42
        allr = pd.concat([base[base["budget"].isin(sd["budget"].unique())], sd], ignore_index=True)
        for b, g in allr.groupby("budget"):
            for outcome, name in [("sup_final", "SR"), ("sup_mem", "warrant")]:
                dids = []
                for seed, gs in g.groupby("seed"):
                    d, lo, hi, n = did_boot(gs, outcome)
                    dids.append(d)
                    rows.append({"model": m, "budget": b, "outcome": name, "seed": seed, "DiD": d, "lo": lo, "hi": hi, "n": n})
                print(f"  {m:<10} B={b:<4} {name:<8} DiD by seed 42/143/244: "
                      + " / ".join(f"{x:+5.1f}" for x in dids) + f"   mean {np.mean(dids):+5.1f} ± SD {np.std(dids, ddof=1):.1f}")
    pd.DataFrame(rows).to_csv("results/phase4_seeds_summary.csv", index=False)


# ------------------------------------------------------------------ ⑧ slots
def slots():
    print("⑧ QUERY-BLIND SLOT ALLOCATION vs free-form blind (multi)")
    for m in MODELS:
        if not all(Path(f"results/phase4_slots_{m}_{s}_scored.csv").exists() for s in ("final", "mem")):
            print(f"  {m}: not scored"); continue
        sl = load_exp("slots", m)
        base = pd.concat([load_hard25(m)] + (
            [load_exp("budget", m).query("budget != 25")]
            if Path(f"results/phase4_budget_{m}_final_scored.csv").exists() else []))
        for b, g in sl.groupby("budget"):
            ref = base[(base["budget"] == b) & (base["cond"] == "multi") & (base["mode"] == "blind")]
            j = g.merge(ref[["sample_id", "sup_final", "sup_mem"]], on="sample_id", suffixes=("_slots", "_free"))
            for o in ["sup_final", "sup_mem"]:
                d = (j[f"{o}_slots"].astype(float) - j[f"{o}_free"].astype(float)).to_numpy() * 100
                dm, lo, hi = boot_ci(d)
                print(f"  {m:<13} B={b} {o:<9} free {j[f'{o}_free'].mean()*100:5.1f} slots {j[f'{o}_slots'].mean()*100:5.1f}  "
                      f"delta {dm:+5.1f} [{lo:+5.1f},{hi:+5.1f}]  slots forced {g['forced'].mean()*100:.0f}%")


if __name__ == "__main__":
    {"pilot": pilot, "budget": budget, "length": length, "position": position,
     "kdose": kdose, "depth": depth, "slots": slots, "seeds": seeds}[sys.argv[1]]()
