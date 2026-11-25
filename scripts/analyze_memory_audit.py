"""④ Memory-warrant human audit — agreement with the frozen evaluator.

Input: one or two filled copies of data/annotation/memory_audit_task*.csv
(columns target_present / direction_correct / stat_status_preserved /
complete_warrant filled with Y, N or NA) plus the hidden key.

Reports, per annotator and (if two) for their consensus:
  raw agreement, Cohen's kappa, Gwet's AC1 between human complete_warrant and
  the evaluator's complete-warrant label (supported on the step-4 memory);
  precision / recall / F1 of the evaluator against the human label (human = truth);
  the same by model and by condition; inter-annotator kappa / AC1;
  sub-item agreement: human target_present vs evaluator direction != NOT_MENTIONED,
  human direction_correct vs evaluator direction == gold.

Usage: analyze_memory_audit.py filled_A.csv [filled_B.csv] [--key data/annotation/memory_audit_key.csv]
"""
import argparse

import numpy as np
import pandas as pd


def yn(v):
    s = str(v).strip().upper()
    return {"Y": 1, "YES": 1, "1": 1, "N": 0, "NO": 0, "0": 0}.get(s, np.nan)


def kappa(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = ~np.isnan(a) & ~np.isnan(b)
    a, b = a[ok], b[ok]
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return po, (po - pe) / (1 - pe) if pe < 1 else np.nan, len(a)


def gwet_ac1(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = ~np.isnan(a) & ~np.isnan(b)
    a, b = a[ok], b[ok]
    po = (a == b).mean()
    pi = (a.mean() + b.mean()) / 2
    pe = 2 * pi * (1 - pi)
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def prf(pred, truth):
    pred, truth = np.asarray(pred, float), np.asarray(truth, float)
    ok = ~np.isnan(pred) & ~np.isnan(truth)
    pred, truth = pred[ok], truth[ok]
    tp = ((pred == 1) & (truth == 1)).sum(); fp = ((pred == 1) & (truth == 0)).sum()
    fn = ((pred == 0) & (truth == 1)).sum()
    p = tp / (tp + fp) if tp + fp else np.nan
    r = tp / (tp + fn) if tp + fn else np.nan
    f = 2 * p * r / (p + r) if p and r else np.nan
    return p, r, f


def boot_kappa_ci(a, b, n_boot=2000, seed=42):
    rng = np.random.default_rng(seed)
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = ~np.isnan(a) & ~np.isnan(b); a, b = a[ok], b[ok]
    ks = []
    for _ in range(n_boot):
        i = rng.integers(0, len(a), len(a))
        ks.append(kappa(a[i], b[i])[1])
    return np.nanpercentile(ks, 2.5), np.nanpercentile(ks, 97.5)


def report(name, human, ev, df):
    po, k, n = kappa(human, ev)
    lo, hi = boot_kappa_ci(human, ev)
    ac1 = gwet_ac1(human, ev)
    p, r, f = prf(ev, human)
    print(f"\n[{name}] n={n}  human Y-rate {np.nanmean(human):.1%}  evaluator Y-rate {np.nanmean(ev):.1%}")
    print(f"  agreement {po:.1%}   Cohen kappa {k:.3f} [{lo:.3f}, {hi:.3f}]   Gwet AC1 {ac1:.3f}")
    print(f"  evaluator vs human (human = truth): precision {p:.3f}  recall {r:.3f}  F1 {f:.3f}")
    for col in ["model", "mode", "icoset"]:
        parts = []
        for v, g in df.groupby(col):
            po_, k_, n_ = kappa(human[g.index], ev[g.index])
            p_, r_, f_ = prf(ev[g.index], human[g.index])
            parts.append(f"{v}: agr {po_:.0%} k {k_:.2f} F1 {f_:.2f} (n={n_})")
        print(f"  by {col}: " + " | ".join(parts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("filled", nargs="+")
    ap.add_argument("--key", default="data/annotation/memory_audit_key.csv")
    args = ap.parse_args()
    key = pd.read_csv(args.key).set_index("item_id")
    ann = []
    for f in args.filled:
        d = pd.read_csv(f).set_index("item_id")
        d = d[d["complete_warrant"].notna() & (d["complete_warrant"].astype(str).str.strip() != "")]
        ann.append(d)
    common = set.intersection(*[set(d.index) for d in ann]) & set(key.index)
    print(f"annotated items with a key: {len(common)} (per file: {[len(d) for d in ann]})")
    df = key.loc[sorted(common)].copy()
    ev_cw = df["eval_complete_warrant"].astype(bool).astype(float).values
    ev_present = (df["eval_direction"] != "NOT_MENTIONED").astype(float).values
    ev_dir_ok = (df["eval_direction"] == df["gold_label"]).astype(float).values

    humans = []
    for i, d in enumerate(ann):
        d = d.loc[df.index]
        h = d["complete_warrant"].map(yn).values
        humans.append(h)
        report(f"annotator {i + 1}: complete warrant", h, ev_cw, df.reset_index(drop=True))
        for col, evx, label in [("target_present", ev_present, "target present"),
                                ("direction_correct", ev_dir_ok, "direction correct")]:
            if col in d:
                hx = d[col].map(yn).values
                po, k, n = kappa(hx, evx)
                print(f"  sub-item {label}: agreement {po:.1%}  kappa {k:.3f} (n={n})")
    if len(humans) == 2:
        po, k, n = kappa(humans[0], humans[1])
        print(f"\n[inter-annotator] agreement {po:.1%}  kappa {k:.3f}  AC1 {gwet_ac1(humans[0], humans[1]):.3f} (n={n})")
        cons = np.where(np.isnan(humans[0]) | np.isnan(humans[1]), np.nan,
                        ((humans[0] == 1) & (humans[1] == 1)).astype(float))
        report("consensus (both Y = preserved)", cons, ev_cw, df.reset_index(drop=True))


if __name__ == "__main__":
    main()
