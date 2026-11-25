"""Shared loader for the 2026-09-29 additional analyses.

The paper's enforced-25 numbers (Figure 2, tab:main_factorial, tab:warrant_stages) are the
evaluator verdicts stored in results/extra_hard_{model}_scored.csv (final answers) and
results/extra_hardmem_{model}_scored.csv (step-4 memory). The Phase-4 replay of the same
chains (results/phase4_budget_{model}.jsonl, identical texts 1176/1176) adds the per-step
token records but was re-scored and differs from the paper's verdicts in one row for
Qwen3-8B (memory) and one for Qwen3-14B (final). Every new B=25 analysis therefore takes the
design / token columns from the replay and the verdicts from the paper's source.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_phase4 import load_exp  # noqa: E402


def load_paper25(model):
    df = load_exp("budget", model)
    df = df[df["budget"] == 25].drop(columns=["sup_final", "sup_mem", "final_label", "mem_label"])
    fin = pd.read_csv(f"results/extra_hard_{model}_scored.csv").rename(columns={"icoset": "cond"})
    mem = pd.read_csv(f"results/extra_hardmem_{model}_scored.csv").rename(columns={"icoset": "cond"})
    mem = mem[mem["step"] == 4]
    k = ["sample_id", "mode", "cond"]
    df = df.merge(fin[k + ["supported", "claim_label"]].rename(
        columns={"supported": "sup_final", "claim_label": "final_label"}), on=k, validate="1:1")
    df = df.merge(mem[k + ["supported", "claim_label", "direction", "certainty"]].rename(
        columns={"supported": "sup_mem", "claim_label": "mem_label",
                 "direction": "mem_direction", "certainty": "mem_certainty"}), on=k, validate="1:1")
    df[["sup_final", "sup_mem"]] = df[["sup_final", "sup_mem"]].astype(int)
    assert len(df) == 4 * 294, len(df)
    return df
