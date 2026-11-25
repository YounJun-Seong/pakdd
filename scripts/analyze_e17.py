"""Phase-6 E17 WP-ELR disagreement audit, analysis (docs/phase6_prereg.md, 2026-11-23).
Inputs: data/audit/e17_key.csv, e17_ratings_{A,B}.jsonl (LLM raters). Outputs: results/e17/e17_items.csv,
e17_summary.csv, e17_report.md"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_e16 import kappa, wilson  # noqa: E402

CATS = ["a_warrant_in_memory", "b_inferred_from_partial", "c_misattributed", "d_ungrounded", "e_answer_not_correct", "f_other"]
CAT_TXT = {"a_warrant_in_memory": "(a) warrant actually in memory (evaluator miss on M4)", "b_inferred_from_partial": "(b) answer inferred from partial evidence",
           "c_misattributed": "(c) answer misattributed from another finding", "d_ungrounded": "(d) answer ungrounded (guess / prior)",
           "e_answer_not_correct": "(e) answer not actually correct (evaluator false positive)", "f_other": "(f) other (stated-but-not-labelled / no claim)"}


def category(gold, mem, ans, grounding):
    if ans != gold:
        return "e_answer_not_correct"
    if mem == gold:
        return "a_warrant_in_memory"
    return {"INFERRED": "b_inferred_from_partial", "MISATTRIBUTED": "c_misattributed", "UNGROUNDED": "d_ungrounded"}.get(grounding, "f_other")


def pc(k, n):
    w = wilson(k, n); return f"{k}/{n} = {w[0]:.1f} % [{w[1]:.1f}, {w[2]:.1f}]"


def main():
    K = pd.read_csv("data/audit/e17_key.csv")
    R = {}
    for r in "AB":
        p = Path(f"data/audit/e17_ratings_{r}.jsonl")
        if p.exists():
            d = pd.DataFrame([json.loads(l) for l in open(p) if l.strip()]).set_index("item_id")
            assert sorted(d.index) == sorted(K.item_id), r
            R[r] = d.loc[K.item_id].reset_index(drop=True)
    D = K.copy()
    for r, d in R.items():
        for f in ("mem_label", "mem_evidence", "ans_label", "ans_grounding", "note"):
            D[f"{f}_{r}"] = d[f].to_numpy() if f in d else ""
        D[f"cat_{r}"] = [category(g, m, a, gr) for g, m, a, gr in zip(D.gold_label, D[f"mem_label_{r}"], D[f"ans_label_{r}"], D[f"ans_grounding_{r}"])]
    D.to_csv("results/e17/e17_items.csv", index=False)
    wp0, wp1, e1, e0 = D.cls.str.startswith("WP0"), D.cls.str.startswith("WP1"), D.cls.str.endswith("ELR1"), D.cls.str.endswith("ELR0")
    md = ["# E17 WP–ELR disagreement audit — analysis", "",
          "150 E13 truncation-free Blind/Multi chains (budgets 100 / 200, Qwen3-8B and 14B): WP0_ELR1 80, WP0_ELR0 36, WP1_ELR1 34.",
          "Raters A and B are two independent LLM annotators (Claude sessions), blind to gold label, automatic verdicts, model, budget and class;",
          "they are not human annotators. Codebook: `data/audit/CODEBOOK.md`. No automatic verdict is changed by this audit.", ""]
    rows = []
    md += ["## 1. Evaluator against the raters", "", "| Rater | Text | Label agreement with evaluator (5-way) | kappa | Supported (label = gold) agreement |", "|---|---|---|---|---|"]
    for r in R:
        for txt, col, ev, sup in (("memory M4", f"mem_label_{r}", "mem_eval", wp1), ("final answer", f"ans_label_{r}", "ans_eval", e1)):
            po, ka = kappa(D[col], D[ev]); s = ((D[col] == D.gold_label) == sup).mean()
            md.append(f"| {r} | {txt} | {po:.1%} | {ka:.2f} | {s:.1%} |")
            rows.append(dict(rater=r, measure=f"label_agreement_{txt}", value=po * 100, kappa=ka, n=len(D)))
    if len(R) == 2:
        md += ["", "Rater A vs rater B: " + "; ".join(f"{f} {kappa(D[f + '_A'], D[f + '_B'])[0]:.1%} (kappa {kappa(D[f + '_A'], D[f + '_B'])[1]:.2f})"
                                                     for f in ("mem_label", "mem_evidence", "ans_label", "ans_grounding")) + "."]
    md += ["", "## 2. Evaluator error rates implied by the raters", "",
           "| Rater | WP false negative (WP=0, rater: memory states gold) | WP false positive (WP=1, rater: memory does not) | ELR false positive (ELR=1, rater: answer ≠ gold) | ELR false negative (ELR=0, rater: answer = gold) |", "|---|---|---|---|---|"]
    views = {r: (D[f"mem_label_{r}"] == D.gold_label, D[f"ans_label_{r}"] == D.gold_label) for r in R}
    if len(R) == 2:
        views["both raters"] = (views["A"][0] & views["B"][0], views["A"][1] & views["B"][1])
        views["both (negated)"] = (views["A"][0] | views["B"][0], views["A"][1] | views["B"][1])
    for v, (mg, ag) in views.items():
        if v == "both (negated)":
            continue
        neg_m = ~(views["both (negated)"][0]) if v == "both raters" else ~mg
        neg_a = ~(views["both (negated)"][1]) if v == "both raters" else ~ag
        md.append(f"| {v} | {pc(int((wp0 & mg).sum()), int(wp0.sum()))} | {pc(int((wp1 & neg_m).sum()), int(wp1.sum()))} | "
                  f"{pc(int((e1 & neg_a).sum()), int(e1.sum()))} | {pc(int((e0 & ag).sum()), int(e0.sum()))} |")
        rows += [dict(rater=v, measure="wp_false_negative", value=100 * (wp0 & mg).sum() / wp0.sum(), n=int(wp0.sum())),
                 dict(rater=v, measure="wp_false_positive", value=100 * (wp1 & neg_m).sum() / wp1.sum(), n=int(wp1.sum())),
                 dict(rater=v, measure="elr_false_positive", value=100 * (e1 & neg_a).sum() / e1.sum(), n=int(e1.sum())),
                 dict(rater=v, measure="elr_false_negative", value=100 * (e0 & ag).sum() / e0.sum(), n=int(e0.sum()))]
    md += ["", "(\"both raters\": an evaluator error is counted only when both raters contradict the evaluator.)", "",
           "## 3. What the WP = 0 & ELR = 1 class consists of (n = 80)", "", "| Category | " + " | ".join(f"Rater {r}" for r in R) + (" | Both agree |" if len(R) == 2 else " |"),
           "|---|" + "---|" * (len(R) + (1 if len(R) == 2 else 0))]
    M = D[D.cls == "WP0_ELR1"]
    for c in CATS:
        cells = [pc(int((M[f"cat_{r}"] == c).sum()), len(M)) for r in R]
        if len(R) == 2:
            cells.append(f"{int(((M.cat_A == c) & (M.cat_B == c)).sum())}")
        md.append(f"| {CAT_TXT[c]} | " + " | ".join(cells) + " |")
        for r in R:
            rows.append(dict(rater=r, measure=f"wp0elr1_{c}", value=100 * (M[f"cat_{r}"] == c).mean(), n=len(M)))
    if len(R) == 2:
        md += ["", f"Category agreement between raters on this class: {(M.cat_A == M.cat_B).mean():.1%} (kappa {kappa(M.cat_A, M.cat_B)[1]:.2f})."]
    md += ["", "Memory evidence in the WP = 0 & ELR = 1 class: " + "; ".join(f"rater {r} {M[f'mem_evidence_{r}'].value_counts().to_dict()}" for r in R) + ".", "",
           "By model and budget (answer without warrant = b + c + d; evaluator error = a + e):", "",
           "| Model | B | n | " + " | ".join(f"{r}: without warrant / evaluator error" for r in R) + " |", "|---|---|---|" + "---|" * len(R)]
    for (m, b), g in M.groupby(["model", "budget"]):
        md.append(f"| {m} | {b} | {len(g)} | " + " | ".join(
            f"{g[f'cat_{r}'].isin(CATS[1:4]).mean():.0%} / {g[f'cat_{r}'].isin([CATS[0], CATS[4]]).mean():.0%}" for r in R) + " |")
    md += ["", "## 4. Control classes", ""]
    for cls in ("WP0_ELR0", "WP1_ELR1"):
        g = D[D.cls == cls]
        md.append(f"- {cls} (n = {len(g)}): " + "; ".join(
            f"rater {r}: memory states gold {(g[f'mem_label_{r}'] == g.gold_label).mean():.0%}, answer states gold {(g[f'ans_label_{r}'] == g.gold_label).mean():.0%}, "
            f"grounding {g[f'ans_grounding_{r}'].value_counts().to_dict()}" for r in R))
    md.append("")
    if len(R) == 2:
        # population weighting: class shares of ALL Blind/Multi chains (truncation-free) x pooled class rates (both raters)
        both_mem = (D.mem_label_A == D.gold_label) & (D.mem_label_B == D.gold_label)
        fn = {c: both_mem[D.cls == c].mean() for c in ("WP0_ELR1", "WP0_ELR0")}
        fp = 1 - ((D.mem_label_A == D.gold_label) | (D.mem_label_B == D.gold_label))[D.cls == "WP1_ELR1"].mean()
        M = D[D.cls == "WP0_ELR1"]
        unwarranted = (M.cat_A.isin(CATS[1:4]) & M.cat_B.isin(CATS[1:4])).mean()
        err = (M.cat_A.isin([CATS[0], CATS[4]]) & M.cat_B.isin([CATS[0], CATS[4]])).mean()
        md += ["## 5. Population-weighted reading (class shares from all Blind/Multi chains; pooled class rates, both raters agree)", "",
               f"Pooled rates: memory states the gold label in {fn['WP0_ELR1']:.1%} of WP0_ELR1 and {fn['WP0_ELR0']:.1%} of WP0_ELR0 items; "
               f"memory does not state it in {fp:.1%} of WP1_ELR1 items (WP1_ELR0, 3–5 % of chains, was not sampled and is left unchanged). "
               f"In WP0_ELR1 both raters see an answer without a stated warrant in {unwarranted:.1%} and an evaluator error in {err:.1%}.", "",
               "| Model | B | WP (evaluator) | WP false-negative rate among WP=0 | WP, rater-adjusted | WP=0 & ELR=1 (evaluator) | of which answer without stated warrant |", "|---|---|---|---|---|---|---|"]
        KEY = ["sample_id", "mode", "cond", "budget"]
        for m in ("qwen3-8b", "qwen3-14b"):
            f = pd.read_csv(f"results/ratio_notrunc_{m}_ok_scored.csv")[KEY + ["supported"]].rename(columns={"supported": "elr"})
            w = pd.read_csv(f"results/ratio_notrunc_{m}_mem_scored.csv")[KEY + ["supported"]].rename(columns={"supported": "wp"})
            d = f.merge(w, on=KEY); d = d[(d.cond == "long") & (d["mode"] == "blind")]
            for b in (100, 200):
                g = d[d.budget == b]
                s01, s00, s11 = ((~g.wp) & g.elr).mean(), ((~g.wp) & (~g.elr)).mean(), (g.wp & g.elr).mean()
                fnr = (s01 * fn["WP0_ELR1"] + s00 * fn["WP0_ELR0"]) / (s01 + s00)
                adj = g.wp.mean() + s01 * fn["WP0_ELR1"] + s00 * fn["WP0_ELR0"] - s11 * fp
                md.append(f"| {m} | {b} | {g.wp.mean():.1%} | {fnr:.1%} | {adj:.1%} | {s01:.1%} | {s01 * unwarranted:.1%} (both raters) |")
                rows.append(dict(rater="both", measure=f"wp_adjusted_{m}_{b}", value=adj * 100, n=len(g)))
                rows.append(dict(rater="both", measure=f"masking_without_warrant_{m}_{b}", value=s01 * unwarranted * 100, n=len(g)))
        md.append("")
    pd.DataFrame(rows).round(2).to_csv("results/e17/e17_summary.csv", index=False)
    Path("results/e17/e17_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
