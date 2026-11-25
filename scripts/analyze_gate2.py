"""Gate 2 analysis: question-blind vs question-aware compression.

PRE-REGISTERED PRIMARY CONTRAST (2026-09-04):
    blind + multi-ICO + 25tok   vs   aware + multi-ICO + 25tok
(same material, same budget; the only difference is whether the compressing
steps knew the future question). Everything else is secondary.

Failure decomposition on the final answer, vs the target's gold label
(never collapsed into one accuracy number):
  target_omission   claim_label == NOT_MENTIONED — the target ICO vanished
  weakening         claim_label == UNCERTAIN — target present but only hedged
  qualifier_loss    definitive claim that loses a significance qualifier:
                    gold NO_DIFFERENCE -> asserted direction (sig_inflation),
                    or gold direction -> asserted NO_DIFFERENCE (sig_deflation)
  mutation          asserted direction opposite to gold (reversal)
  supported         claim_label == gold

Also reported per condition: citation correctness (provenance retention) and
per-gold-label breakdown (negative-result loss = failures among gold
NO_DIFFERENCE targets).

Usage: analyze_gate2.py qwen3-8b gpt-5.4-mini
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

RNG = np.random.default_rng(42)
N_BOOT = 2000
DIRECTIONS = {"INCREASE", "DECREASE"}


def failure_class(gold: str, claim: str) -> str:
    if claim == gold:
        return "supported"
    if claim == "NOT_MENTIONED":
        return "target_omission"
    if claim == "UNCERTAIN":
        return "weakening"
    if gold == "NO_DIFFERENCE" and claim in DIRECTIONS:
        return "qualifier_loss"          # sig_inflation
    if gold in DIRECTIONS and claim == "NO_DIFFERENCE":
        return "qualifier_loss"          # sig_deflation
    if gold in DIRECTIONS and claim in DIRECTIONS:
        return "mutation"                # reversal
    return "other"


def paired_boot(diff: np.ndarray) -> tuple[float, float, float]:
    means = [diff[RNG.integers(0, len(diff), len(diff))].mean() for _ in range(N_BOOT)]
    return float(diff.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def analyze(model: str):
    df = pd.read_csv(f"results/gate2_scored_{model}.csv")
    fin = df[df["role"] == "final"].copy()
    fin["fail"] = [failure_class(g, c) for g, c in zip(fin["gold_label"], fin["claim_label"])]
    fin["cond"] = fin["mode"] + "/" + fin["icoset"] + "/" + fin["budget"].astype(str)

    print(f"\n{'='*92}\nMODEL: {model}   (n articles = {fin['sample_id'].nunique()})\n{'='*92}")

    tab = (fin.groupby(["mode", "icoset", "budget"])
           .agg(n=("fail", "size"),
                SR=("fail", lambda s: (s == "supported").mean()),
                omission=("fail", lambda s: (s == "target_omission").mean()),
                weakening=("fail", lambda s: (s == "weakening").mean()),
                qualifier_loss=("fail", lambda s: (s == "qualifier_loss").mean()),
                mutation=("fail", lambda s: (s == "mutation").mean()),
                cite=("citation_correct", "mean")))
    print("\nfinal-answer outcomes by condition:")
    print(tab.round(3).to_string())

    # PRIMARY CONTRAST
    a = fin[(fin["mode"] == "aware") & (fin["icoset"] == "multi") & (fin["budget"] == 25)]
    b = fin[(fin["mode"] == "blind") & (fin["icoset"] == "multi") & (fin["budget"] == 25)]
    piv = pd.merge(a[["sample_id", "fail"]], b[["sample_id", "fail"]],
                   on="sample_id", suffixes=("_aware", "_blind"))
    d_sr = (piv["fail_blind"] == "supported").astype(float) - \
           (piv["fail_aware"] == "supported").astype(float)
    m, lo, hi = paired_boot(d_sr.values)
    print(f"\nPRIMARY CONTRAST (blind - aware | multi-ICO, 25tok): "
          f"dSR={m*100:+.1f}pp [{lo*100:+.1f},{hi*100:+.1f}]  n={len(piv)}")
    verdict = "SIGNIFICANT" if hi < 0 else ("null" if lo <= 0 <= hi else "positive?")
    print(f"  -> {verdict}")

    # negative-result vulnerability: failures among gold NO_DIFFERENCE targets
    print("\nper-gold-label SR (blind/multi/25 vs aware/multi/25):")
    for gl in ["NO_DIFFERENCE", "INCREASE", "DECREASE"]:
        aa = a[a["gold_label"] == gl]; bb = b[b["gold_label"] == gl]
        print(f"  {gl:<14} aware={((aa['fail']=='supported').mean()):.3f} "
              f"blind={((bb['fail']=='supported').mean()):.3f}  (n={len(aa)})")

    # what does blind lose first? decomposition of the blind failures
    bf = b[b["fail"] != "supported"]["fail"].value_counts(normalize=True)
    if len(bf):
        print("\nblind/multi/25 failure decomposition:", dict(bf.round(3)))

    # depth-1 direct ceilings
    d1 = fin[fin["depth"] == 1]
    print("\ndepth-1 (direct) SR ceilings:")
    print(d1.groupby("icoset")["fail"].apply(lambda s: (s == "supported").mean()).round(3).to_string())


if __name__ == "__main__":
    for mdl in sys.argv[1:]:
        analyze(mdl)
