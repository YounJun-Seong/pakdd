"""Phase-6 E23 multi-seed replication of E14, analysis (docs/phase6_prereg.md, 2026-11-27).
Qwen3-14B, B = 200, truncation-free, Aware / Blind x Single / Filler / Multi. Seed 42 = the committed E13 / E14 chains;
seeds 143 / 244 / 345 / 446 = results/e23_qwen3-14b*.
Outputs: results/e23/e23_summary.csv, e23_cells.csv, e23_report.md"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_lencontrol import fmt, load as load_orig  # noqa: E402
from analyze_phase4 import N_BOOT, SEED, boot_ci  # noqa: E402

M, B = "qwen3-14b", 200
SEEDS = [42, 143, 244, 345, 446]
CONDS = ("single", "filler", "multi")
KEY = ["seed", "sample_id", "mode", "cond"]
EST = {"LENGTH (Filler − Single)": ("filler", "single"), "COMPETITION (Multi − Filler)": ("multi", "filler"),
       "E13 DiD (Multi − Single)": ("multi", "single")}


def load():
    d42, _ = load_orig(M)
    d42 = d42[d42.budget == B].assign(seed=42)[KEY + ["failed", "elr", "wp"]]
    meta = []
    for path, cc in ((f"results/ratio_notrunc_{M}.jsonl", {"single": "single", "long": "multi"}), (f"results/lenctrl_{M}.jsonl", {"filler": "filler"})):
        for r in map(json.loads, open(path)):
            if r["budget"] == B and r["cond"] in cc and not r["failed"]:
                meta.append(dict(seed=42, sample_id=r["sample_id"], mode=r["mode"], cond=cc[r["cond"]], attempts=r["attempts"], memory=r["memory"]))
    raw = [json.loads(l) for l in open(f"results/e23_{M}.jsonl")]
    new = pd.DataFrame([{**{k: r.get(k) for k in KEY + ["failed"]}} for r in raw])
    for stem, col in (("ok", "elr"), ("mem", "wp")):
        s = pd.read_csv(f"results/e23_{M}_{stem}_scored.csv")
        assert not s.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any()
        new = new.merge(s[KEY + ["supported"]].rename(columns={"supported": col}), on=KEY, how="left", validate="1:1")
    new["cond"] = new.cond.replace({"long": "multi"})
    meta += [dict(seed=r["seed"], sample_id=r["sample_id"], mode=r["mode"], cond={"long": "multi"}.get(r["cond"], r["cond"]),
                  attempts=r["attempts"], memory=r["memory"]) for r in raw if not r["failed"]]
    d = pd.concat([d42[d42.sample_id.isin(new.sample_id.unique())], new], ignore_index=True)
    d[["elr", "wp"]] = d[["elr", "wp"]].astype(float)
    return d, pd.DataFrame(meta)


def series(p):
    """Per-article series of the three estimands and of G per source, from a (mode, cond) pivot in percent."""
    G = {c: p[("blind", c)] - p[("aware", c)] for c in CONDS}
    out = {k: G[a] - G[b] for k, (a, b) in EST.items()}
    out.update({f"G {c}": G[c] for c in CONDS})
    return out


def twoway(X, n=N_BOOT, seed=SEED):
    """X: seeds x articles matrix of per-article contrasts; resample seeds and articles."""
    rng = np.random.default_rng(seed)
    k, a = X.shape
    ms = [X[rng.integers(0, k, k)][:, rng.integers(0, a, a)].mean() for _ in range(n)]
    return X.mean(), np.percentile(ms, 2.5), np.percentile(ms, 97.5)


def main():
    Path("results/e23").mkdir(parents=True, exist_ok=True)
    d, meta = load()
    from run_phase4 import tokenizers
    enc, _ = tokenizers()
    meta["memory_tokens"] = meta.memory.map(lambda t: len(enc(M, t)))
    meta["first_attempts"] = meta.attempts.map(lambda a: a[0]); meta["mean_attempts"] = meta.attempts.map(np.mean)
    n_art = d.sample_id.nunique()
    md = ["# E23 Multi-seed replication of E14 — analysis", "",
          f"Qwen3-14B, B = {B}, truncation-free, original prompts, {n_art} articles, Aware / Blind x Single / Filler / Multi.",
          "Seed 42 = the committed E13 / E14 chains; 143 / 244 / 345 / 446 = new runs (write attempt a: seed s + 100a; reader: s).",
          "G = Blind − Aware. `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples).", "",
          "Failed regenerations by seed: " + ", ".join(f"{s}: {int(d[d.seed == s].failed.astype(bool).sum())}" for s in SEEDS) + ".", ""]
    rows, cells = [], []
    bad_any = set(d[d.failed.astype(bool)].sample_id)
    for col, lbl in (("elr", "ELR"), ("wp", "WP")):
        per, mats = {}, {}
        md += [f"## {lbl}", "", "| Seed | n | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi | " + " | ".join(EST) + " |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for s in SEEDS:
            g = d[d.seed == s]
            g = g[~g.sample_id.isin(g[g.failed.astype(bool)].sample_id.unique())]
            p = g.pivot_table(index="sample_id", columns=["mode", "cond"], values=col, aggfunc="first").dropna() * 100
            C = series(p); per[s] = {k: boot_ci(v.to_numpy()) for k, v in C.items()}
            mats[s] = pd.DataFrame(C)
            cm = {(mo, c): p[(mo, c)].mean() for mo in ("aware", "blind") for c in CONDS}
            md.append(f"| {s} | {len(p)} | " + " | ".join(f"{cm[(mo, c)]:.1f}" for c in CONDS for mo in ("aware", "blind")) + " | "
                      + " | ".join(fmt(per[s][k]) for k in EST) + " |")
            cells.append(dict(outcome=lbl, seed=s, n=len(p), **{f"{mo}_{c}": v for (mo, c), v in cm.items()}))
            for k, t in per[s].items():
                rows.append(dict(outcome=lbl, level="seed", seed=s, n=len(p), estimand=k, est=t[0], lo=t[1], hi=t[2]))
        ids = sorted(set.intersection(*[set(mats[s].index) for s in SEEDS]) - bad_any)
        md += ["", f"Across seeds (pooled: each article averaged over the five seeds, n = {len(ids)} articles complete in every seed):", "",
               "| Estimand | Mean of 5 seeds | SD across seeds | Range | Negative in | CI excludes 0 in | Pooled, article bootstrap | Pooled, seeds x articles bootstrap |",
               "|---|---|---|---|---|---|---|---|"]
        for k in list(EST) + [f"G {c}" for c in CONDS]:
            v = np.array([per[s][k][0] for s in SEEDS])
            X = np.stack([mats[s].loc[ids, k].to_numpy() for s in SEEDS])
            pa, tw = boot_ci(X.mean(axis=0)), twoway(X)
            neg = int((v < 0).sum()); sig = sum(per[s][k][2] < 0 or per[s][k][1] > 0 for s in SEEDS)
            md.append(f"| {k} | {v.mean():+.1f} | {v.std(ddof=1):.1f} | {v.min():+.1f} to {v.max():+.1f} | {neg} / 5 | {sig} / 5 | {fmt(pa)} | {fmt(tw)} |")
            rows.append(dict(outcome=lbl, level="across", seed=-1, n=len(ids), estimand=k, est=pa[0], lo=pa[1], hi=pa[2],
                             seed_mean=v.mean(), seed_sd=v.std(ddof=1), n_negative=neg, n_sig=sig, twoway_lo=tw[1], twoway_hi=tw[2]))
        md.append("")
    S = pd.DataFrame(rows)
    S.round(3).to_csv("results/e23/e23_summary.csv", index=False)
    pd.DataFrame(cells).round(3).to_csv("results/e23/e23_cells.csv", index=False)
    md += ["## Regeneration and memory length by cell (mean over articles)", "",
           "| Seed | Cell | First-write attempts | Attempts per write | M4 model tokens |", "|---|---|---|---|---|"]
    A = meta.groupby(["seed", "mode", "cond"])[["first_attempts", "mean_attempts", "memory_tokens"]].mean()
    for s in SEEDS:
        for mo in ("aware", "blind"):
            for c in CONDS:
                r = A.loc[(s, mo, c)]
                md.append(f"| {s} | {mo} / {c} | {r.first_attempts:.2f} | {r.mean_attempts:.2f} | {r.memory_tokens:.0f} |")
    A.round(3).to_csv("results/e23/e23_attempts.csv")
    md += ["", "## Reading rule (pre-registered)", ""]
    for lbl in ("ELR", "WP"):
        s = S[(S.outcome == lbl) & (S.level == "across")].set_index("estimand")
        ps = S[(S.outcome == lbl) & (S.level == "seed")]
        L = s.loc["LENGTH (Filler − Single)"]; ls = ps[ps.estimand == "LENGTH (Filler − Single)"]
        rep = bool((ls.hi < 0).all() and L.hi < 0)
        sens = bool((np.sign(ls.est).nunique() > 1) or (L.seed_sd > abs(L.est) / 2))
        cs = ps[ps.estimand == "COMPETITION (Multi − Filler)"]
        md.append(f"- {lbl}{' (PRIMARY)' if lbl == 'ELR' else ''}: LENGTH {'replicates' if rep else 'does NOT replicate in every seed'} "
                  f"(pooled {fmt((L.est, L.lo, L.hi))}; negative with CI excluding 0 in {int((ls.hi < 0).sum())} / 5 seeds; seed SD {L.seed_sd:.1f}); "
                  f"{'seed-sensitive' if sens else 'not seed-sensitive'}. COMPETITION "
                  f"{'stays non-negative' if not (cs.hi < 0).any() else 'is negative with a CI excluding 0 in ' + str(int((cs.hi < 0).sum())) + ' seed(s)'} "
                  f"(per seed {', '.join(f'{x:+.1f}' for x in cs.est)}).")
    Path("results/e23/e23_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
