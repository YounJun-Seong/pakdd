"""Evidence-distortion analyses on EXISTING verdicts (2026-11-22; no generation, no scoring).

  1. absolute ELR / WP of the four cells (E13, both protocols; original 25-token grid; E6 context arm)
  2. masking: how often the final answer is right although the memory lost the warrant (WP = 0, ELR = 1)
  3. failure types of memories and answers: omitted (Not-Mentioned), hedged (Uncertain), and asserted wrong
     labels split into reversed direction / false effect (gold No-Difference) / lost effect (gold effect)

Outputs: results/distortion_cells.csv, distortion_masking.csv, distortion_failure_types.csv,
         results/distortion_report.md
Exploratory: none of this was pre-registered.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_phase4 import boot_ci  # noqa: E402

CELLS = [("aware", "single"), ("blind", "single"), ("aware", "multi"), ("blind", "multi")]
CELL_NAME = {("aware", "single"): "Aware-Single", ("blind", "single"): "Blind-Single",
             ("aware", "multi"): "Aware-Multi", ("blind", "multi"): "Blind-Multi"}
KEY = ["sample_id", "mode", "cond", "budget"]
TYPES = ["correct", "omitted", "hedged", "reversed", "false_effect", "lost_effect"]


def ftype(gold, claim):
    if claim == gold:
        return "correct"
    if claim == "NOT_MENTIONED":
        return "omitted"
    if claim == "UNCERTAIN":
        return "hedged"
    if gold == "NO_DIFFERENCE":
        return "false_effect"          # a significant effect is asserted where the trial found none
    if claim == "NO_DIFFERENCE":
        return "lost_effect"           # a significant effect is reported as no difference
    return "reversed"                  # Increase <-> Decrease


def pair(fin_path, mem_path, tidy=None):
    f, m = pd.read_csv(fin_path), pd.read_csv(mem_path)
    if tidy:
        f, m = tidy(f), tidy(m)
    for d in (f, m):
        assert not d.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any()
    f = f[KEY + ["gold_label", "claim_label", "supported"]].rename(columns={"claim_label": "ans_label", "supported": "elr"})
    m = m[KEY + ["claim_label", "supported"]].rename(columns={"claim_label": "mem_label", "supported": "wp"})
    d = f.merge(m, on=KEY, validate="1:1")
    d[["elr", "wp"]] = d[["elr", "wp"]].astype(int)
    d["ans_type"] = [ftype(g, c) for g, c in zip(d.gold_label, d.ans_label)]
    d["mem_type"] = [ftype(g, c) for g, c in zip(d.gold_label, d.mem_label)]
    return d


def sources():
    out = []
    ab = lambda d: d[d["mode"].isin(["aware", "blind"])].assign(cond=lambda x: x.cond.replace({"long": "multi"}))  # noqa: E731
    for m in ("qwen3-8b", "qwen3-14b"):
        out.append(("E13 1,000-token source", "truncation-free", m,
                    pair(f"results/ratio_notrunc_{m}_ok_scored.csv", f"results/ratio_notrunc_{m}_mem_scored.csv", ab)))
        out.append(("E13 1,000-token source", "enforced cap", m,
                    pair(f"results/ratio_{m}_scored.csv", f"results/ratio_{m}_mem_scored.csv", ab)))
    def old(d):
        d = d.rename(columns={"icoset": "cond"})
        if "step" in d:
            d = d[d.step == 4]
        return d.assign(budget=25)
    for m in ("qwen3-8b", "qwen3-14b", "gpt-5.4-mini"):
        out.append(("Original span source", "enforced cap", m,
                    pair(f"results/extra_hard_{m}_scored.csv", f"results/extra_hardmem_{m}_scored.csv", old)))
    ctx = lambda d: d[d.arm == "context"]  # noqa: E731
    out.append(("E6 contextual source", "truncation-free", "qwen3-14b",
                pair("results/e6_qwen3-14b_ok_scored.csv", "results/e6_qwen3-14b_mem_scored.csv", ctx)))
    return out


def pct(x):
    return float(np.mean(x) * 100) if len(x) else np.nan


def main():
    cells, mask, types = [], [], []
    for exp, proto, model, d in sources():
        for b in sorted(d.budget.unique()):
            for mo, c in CELLS:
                g = d[(d.budget == b) & (d["mode"] == mo) & (d.cond == c)]
                base = dict(experiment=exp, protocol=proto, model=model, budget=b, cell=CELL_NAME[(mo, c)], n=len(g))
                e, w = boot_ci(g.elr.to_numpy() * 100.0), boot_ci(g.wp.to_numpy() * 100.0)
                cells.append({**base, "ELR": e[0], "ELR_lo": e[1], "ELR_hi": e[2], "WP": w[0], "WP_lo": w[1], "WP_hi": w[2]})
                lost, kept = g[g.wp == 0], g[g.wp == 1]
                ci = boot_ci(lost.elr.to_numpy() * 100.0) if len(lost) >= 20 else (pct(lost.elr), np.nan, np.nan)
                mask.append({**base, "WP1_ELR1": pct((g.wp == 1) & (g.elr == 1)), "WP1_ELR0": pct((g.wp == 1) & (g.elr == 0)),
                             "WP0_ELR1": pct((g.wp == 0) & (g.elr == 1)), "WP0_ELR0": pct((g.wp == 0) & (g.elr == 0)),
                             "n_WP0": len(lost), "ELR_given_WP0": ci[0], "ELR_given_WP0_lo": ci[1], "ELR_given_WP0_hi": ci[2],
                             "ELR_given_WP1": pct(kept.elr),
                             # what the answer does when the memory no longer mentions the target at all
                             "n_mem_omitted": int((g.mem_type == "omitted").sum()),
                             "ans_correct_given_mem_omitted": pct(g[g.mem_type == "omitted"].elr),
                             "ans_asserted_wrong_given_mem_omitted": pct(g[g.mem_type == "omitted"].ans_type.isin(["reversed", "false_effect", "lost_effect"])),
                             "ans_abstains_given_mem_omitted": pct(g[g.mem_type == "omitted"].ans_type.isin(["omitted", "hedged"]))})
                for level, col in (("memory", "mem_type"), ("answer", "ans_type")):
                    vc = g[col].value_counts(normalize=True) * 100
                    fail = g[g[col] != "correct"]
                    fv = fail[col].value_counts(normalize=True) * 100 if len(fail) else {}
                    types.append({**base, "level": level, **{t: float(vc.get(t, 0.0)) for t in TYPES}, "n_failures": len(fail),
                                  "asserted_wrong": float(sum(vc.get(t, 0.0) for t in ("reversed", "false_effect", "lost_effect"))),
                                  "share_of_failures_omitted": float(fv.get("omitted", np.nan)) if len(fail) else np.nan,
                                  "share_of_failures_asserted_wrong": float(sum(fv.get(t, 0.0) for t in ("reversed", "false_effect", "lost_effect"))) if len(fail) else np.nan})
    C, K, T = pd.DataFrame(cells), pd.DataFrame(mask), pd.DataFrame(types)
    C.round(2).to_csv("results/distortion_cells.csv", index=False)
    K.round(2).to_csv("results/distortion_masking.csv", index=False)
    T.round(2).to_csv("results/distortion_failure_types.csv", index=False)

    md = ["# Evidence-distortion analyses on existing verdicts (2026-11-22)", "",
          "No new generation or scoring. Exploratory (not pre-registered). Failure types: **omitted** = evaluator finds the target",
          "comparison Not-Mentioned; **hedged** = stated but tentative (Uncertain); **reversed** = Increase <-> Decrease;",
          "**false effect** = gold No-Difference stated as a significant effect; **lost effect** = gold effect stated as no difference.",
          "The last three are asserted wrong labels (distortion in the narrow sense).", ""]
    for exp, proto in (("E13 1,000-token source", "truncation-free"), ("E13 1,000-token source", "enforced cap"),
                       ("Original span source", "enforced cap"), ("E6 contextual source", "truncation-free")):
        md += [f"## {exp} — {proto}", ""]
        c = C[(C.experiment == exp) & (C.protocol == proto)]
        md += ["### 1. Absolute ELR / WP by cell (%, 95 % CI)", "", "| Model | B | Cell | ELR | WP |", "|---|---|---|---|---|"]
        for r in c.itertuples():
            md.append(f"| {r.model} | {r.budget} | {r.cell} | {r.ELR:.1f} [{r.ELR_lo:.1f}, {r.ELR_hi:.1f}] | {r.WP:.1f} [{r.WP_lo:.1f}, {r.WP_hi:.1f}] |")
        k = K[(K.experiment == exp) & (K.protocol == proto) & K.cell.isin(["Aware-Multi", "Blind-Multi"])]
        md += ["", "### 2. Masking in the Multi cells: answer correct although the memory lost the warrant", "",
               "| Model | B | Cell | WP=0 & ELR=1 (% of chains) | WP=1 & ELR=0 | n with WP=0 | ELR given WP=0 [95 % CI] | ELR given WP=1 |", "|---|---|---|---|---|---|---|---|"]
        for r in k.itertuples():
            ci = f"{r.ELR_given_WP0:.1f} [{r.ELR_given_WP0_lo:.1f}, {r.ELR_given_WP0_hi:.1f}]" if r.n_WP0 >= 20 else (f"{r.ELR_given_WP0:.1f} (n<20)" if r.n_WP0 else "–")
            md.append(f"| {r.model} | {r.budget} | {r.cell} | {r.WP0_ELR1:.1f} | {r.WP1_ELR0:.1f} | {r.n_WP0} | {ci} | {r.ELR_given_WP1:.1f} |")
        t = T[(T.experiment == exp) & (T.protocol == proto) & (T.cell == "Blind-Multi")]
        md += ["", "### 3. Failure types in Blind-Multi (% of all chains in the cell)", "",
               "| Model | B | Level | Correct | Omitted | Hedged | Reversed | False effect | Lost effect | Asserted wrong, share of failures |", "|---|---|---|---|---|---|---|---|---|---|"]
        for r in t.itertuples():
            md.append(f"| {r.model} | {r.budget} | {r.level} | {r.correct:.1f} | {r.omitted:.1f} | {r.hedged:.1f} | {r.reversed:.1f} | {r.false_effect:.1f} | {r.lost_effect:.1f} | "
                      f"{r.share_of_failures_asserted_wrong:.0f}% of {r.n_failures} |")
        k2 = K[(K.experiment == exp) & (K.protocol == proto) & (K.cell == "Blind-Multi")]
        md += ["", "What the final answer does when the Blind-Multi memory no longer mentions the target:", "",
               "| Model | B | n | Answer correct | Answer asserts a wrong label | Answer abstains (not mentioned / hedged) |", "|---|---|---|---|---|---|"]
        for r in k2.itertuples():
            if r.n_mem_omitted:
                md.append(f"| {r.model} | {r.budget} | {r.n_mem_omitted} | {r.ans_correct_given_mem_omitted:.1f} | {r.ans_asserted_wrong_given_mem_omitted:.1f} | {r.ans_abstains_given_mem_omitted:.1f} |")
        md.append("")
    Path("results/distortion_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
