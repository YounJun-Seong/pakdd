"""P3 (2026-09-29): truncation / budget-compliance by factorial cell at the primary
enforced 25-token budget. No generation: every number is read from the step records
of the ① enforced chains (results/phase4_budget_{model}.jsonl, the same chains as
Figure 2 / tab:main_factorial; verdicts from the paper's source, see addexp_common),
n = 294 articles per cell, paired.

Per model x cell (Aware/Blind x Single/Multi):
  forced        chain-level forced-truncation rate (any of the 4 intermediate writes > B)
  final_forced  the memory actually read by the final step (M4) was truncated
  compliance    natural compliance = share of intermediate writes already <= B
  raw_len       mean realized length of a write before enforcement (tokens)
and the Blindness x Competition interaction ON THE TRUNCATION RATE itself (paired
article bootstrap, B=2000, seed 42), followed by three sensitivity versions of the
ELR / WP interaction: adjusted for truncation (GEE with forced as covariate),
restricted to articles whose M4 was untruncated in all four cells, and the
truncation-free regeneration arm (Phase-5 P0-2, S100) for reference.

Output: printed tables + results/truncation_cells_b25.csv + docs/table_truncation_cells.tex
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from addexp_common import load_paper25  # noqa: E402
from analyze_phase4 import boot_ci, did_boot  # noqa: E402

MODELS = ["qwen3-8b", "qwen3-14b", "gpt-5.4-mini"]
NAMES = {"qwen3-8b": "Qwen3-8B", "qwen3-14b": "Qwen3-14B", "gpt-5.4-mini": "GPT-5.4-mini"}
CELLS = [("aware", "single"), ("blind", "single"), ("aware", "multi"), ("blind", "multi")]
B = 25


def fmt(t):
    return f"{t[0]:+5.1f} [{t[1]:+5.1f}, {t[2]:+5.1f}]"


def main():
    rows, tex = [], []
    for m in MODELS:
        df = load_paper25(m)
        df["final_forced"] = df["step_raw"].map(lambda s: s[-1] > B)
        df["forced"] = df["forced"].astype(bool)
        df["compliance"] = df["step_raw"].map(lambda s: np.mean([x <= B for x in s]))
        df["raw_len"] = df["step_raw"].map(np.mean)
        print(f"\n{m}  (enforced B={B}, n={df['sample_id'].nunique()} articles per cell)")
        print(f"  {'cell':<14} {'forced%':>8} {'M4 cut%':>8} {'compl%':>8} {'raw len':>8} | {'ELR':>6} {'WP':>6}")
        cellvals = {}
        for mode, ico in CELLS:
            g = df[(df["mode"] == mode) & (df["cond"] == ico)]
            v = dict(forced=g["forced"].mean() * 100, final_forced=g["final_forced"].mean() * 100,
                     compliance=g["compliance"].mean() * 100, raw_len=g["raw_len"].mean(),
                     ELR=g["sup_final"].mean() * 100, WP=g["sup_mem"].mean() * 100)
            cellvals[(mode, ico)] = v
            print(f"  {mode + '/' + ico:<14} {v['forced']:8.1f} {v['final_forced']:8.1f} {v['compliance']:8.1f} "
                  f"{v['raw_len']:8.1f} | {v['ELR']:6.1f} {v['WP']:6.1f}")
            rows.append(dict(model=m, mode=mode, cond=ico, n=len(g), **v))
        rec = dict(model=m, mode="DiD", cond="blind x multi", n=df["sample_id"].nunique())
        for col in ("forced", "final_forced", "compliance", "raw_len"):
            t = did_boot(df.assign(**{col: df[col].astype(float)}), col)
            scale = 0.01 if col == "raw_len" else 1.0   # did_boot multiplies by 100
            t = (t[0] * scale, t[1] * scale, t[2] * scale)
            rec[col] = t[0]; rec[f"{col}_lo"] = t[1]; rec[f"{col}_hi"] = t[2]
            print(f"  interaction on {col:<13} {fmt(t)} {'tokens' if col == 'raw_len' else 'pp'}")
        # (a) unadjusted DiD, (b) adjusted for truncation, (c) M4 untruncated in all four cells
        for oc, name in [("sup_final", "ELR"), ("sup_mem", "WP")]:
            t = did_boot(df, oc)
            d = df.assign(y=df[oc].astype(int), blind=(df["mode"] == "blind").astype(int),
                          multi=(df["cond"] == "multi").astype(int), cut=df["final_forced"].astype(int),
                          anycut=df["forced"].astype(int))
            g0 = smf.gee("y ~ blind * multi", groups="sample_id", data=d, family=sm.families.Binomial(),
                         cov_struct=sm.cov_struct.Exchangeable()).fit()
            g1 = smf.gee("y ~ blind * multi + cut", groups="sample_id", data=d, family=sm.families.Binomial(),
                         cov_struct=sm.cov_struct.Exchangeable()).fit()
            g2 = smf.gee("y ~ blind * multi + anycut", groups="sample_id", data=d, family=sm.families.Binomial(),
                         cov_struct=sm.cov_struct.Exchangeable()).fit()
            print(f"  {name}: DiD {fmt(t[:3])} | GEE blind:multi {g0.params['blind:multi']:+.2f} (p={g0.pvalues['blind:multi']:.2g})"
                  f" | + M4-cut covariate {g1.params['blind:multi']:+.2f} (p={g1.pvalues['blind:multi']:.2g}; cut {g1.params['cut']:+.2f}, p={g1.pvalues['cut']:.2g})"
                  f" | + any-step-cut covariate {g2.params['blind:multi']:+.2f} (p={g2.pvalues['blind:multi']:.2g})")
            rec.update({f"{name}": t[0], f"{name}_lo": t[1], f"{name}_hi": t[2],
                        f"{name}_gee": g0.params["blind:multi"], f"{name}_gee_p": g0.pvalues["blind:multi"],
                        f"{name}_gee_adjM4": g1.params["blind:multi"], f"{name}_gee_adjM4_p": g1.pvalues["blind:multi"],
                        f"{name}_gee_adjAny": g2.params["blind:multi"], f"{name}_gee_adjAny_p": g2.pvalues["blind:multi"]})
            ok = df.groupby("sample_id")["final_forced"].sum()
            keep = ok[ok == 0].index
            sub = df[df["sample_id"].isin(keep)]
            if len(keep) >= 20:
                ts = did_boot(sub, oc)
                print(f"       M4 untruncated in all 4 cells (n={len(keep)}): {name} DiD {fmt(ts[:3])}")
                rec.update({f"{name}_clean_n": len(keep), f"{name}_clean": ts[0],
                            f"{name}_clean_lo": ts[1], f"{name}_clean_hi": ts[2]})
            else:
                print(f"       M4 untruncated in all 4 cells: n={len(keep)} (too few)")
                rec.update({f"{name}_clean_n": len(keep)})
        rows.append(rec)
        c = cellvals
        tex.append(f"{NAMES[m]} & Forced truncation & " + " & ".join(f"{c[k]['forced']:.1f}" for k in CELLS)
                   + f" & ${rec['forced']:+.1f}$ [{rec['forced_lo']:+.1f}, {rec['forced_hi']:+.1f}] \\\\")
        tex.append(" & Natural compliance & " + " & ".join(f"{c[k]['compliance']:.1f}" for k in CELLS)
                   + f" & ${rec['compliance']:+.1f}$ [{rec['compliance_lo']:+.1f}, {rec['compliance_hi']:+.1f}] \\\\")
        tex.append(" & Mean length before enforcement & " + " & ".join(f"{c[k]['raw_len']:.1f}" for k in CELLS)
                   + f" & ${rec['raw_len']:+.1f}$ [{rec['raw_len_lo']:+.1f}, {rec['raw_len_hi']:+.1f}] \\\\")
        tex.append("\\hline")
    pd.DataFrame(rows).to_csv("results/truncation_cells_b25.csv", index=False)
    head = ("\\begin{table*}[h]\n\\centering\n"
            "\\caption{Budget compliance by factorial cell at the enforced 25-token budget ($n{=}294$ articles per cell, "
            "paired; same chains as Table~\\ref{tab:main_factorial}). Forced truncation: share of chains (\\%) in which at "
            "least one of the four intermediate writes exceeded the budget and was prefix-truncated. Natural compliance: "
            "share of intermediate writes (\\%) that were within budget as generated. Length is in tokens of the writing "
            "model's tokenizer. The last column is the Blindness $\\times$ Competition interaction on that quantity with a "
            "95\\% article-level bootstrap interval.}\n\\label{tab:truncation_cells}\n\\resizebox{\\textwidth}{!}{\n"
            "\\begin{tabular}{llrrrrr}\n\\hline\n\\textbf{Model} & \\textbf{Quantity} & \\textbf{Aware-Single} & "
            "\\textbf{Blind-Single} & \\textbf{Aware-Multi} & \\textbf{Blind-Multi} & \\textbf{Interaction [95\\% CI]} \\\\\n\\hline\n")
    Path("docs/table_truncation_cells.tex").write_text(head + "\n".join(tex) + "\n\\end{tabular}\n}\n\\end{table*}\n")
    print("\nwrote results/truncation_cells_b25.csv, docs/table_truncation_cells.tex")


if __name__ == "__main__":
    main()
