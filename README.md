# What Will Matter Later? Source-Length Effects on Evidence Retention in Query-Blind Medical LLM Memory

Code, prompts, constructed sources, audit material and experiment records for the paper, together with its
supplementary material (`supplementary/supplementary_material.pdf`).

## Where to find what the paper refers to

| Item | File |
|---|---|
| Aware writer prompt (system / user) and final-answer prompt | `supdrift/chain.py` (`INTERMEDIATE_SYSTEM`, `INTERMEDIATE_USER`, `FINAL_SYSTEM`, `FINAL_USER`) |
| Blind writer prompt | `supdrift/chain2.py` (`BLIND_SYSTEM`, `BLIND_USER`) |
| Matched writer prompt, retry instruction, truncation-free protocol | `scripts/run_phase5.py` (`MATCHED_SYSTEM`, `MATCHED_USER`, `STRICTER`, `notrunc_chain`) |
| Evaluator rubric (frozen Qwen3-32B-FP8 classifier, prompt v3) | `supdrift/classifier.py` (`SYSTEM_PROMPT`, `USER_TEMPLATE`) |
| Sampling settings (temperature 0.7, seed 42, retry seed 42 + 100a) | `supdrift/chain.py`, `scripts/run_phase5.py` |
| Reference-token counting (`o200k_base`, tiktoken 0.14.0) | `scripts/build_longsource.py` (`ntok`, `render`) |
| Multi sources (about 1,000 reference tokens) | `scripts/build_longsource.py`, `data/longsource/longsource_v1.jsonl` |
| Length-matched Filler sources | `scripts/build_longfiller.py`, `data/longsource/longfiller_v1.jsonl` |
| Length-by-position sources (three placements x three lengths) | `scripts/build_e19_sources.py`, `data/longsource/e19_sources_v1.jsonl` |
| Cohort (294 articles, one target per article) | `data/gate2/gate2_v1.jsonl` |
| Audit codebook, blinded sheets, keys and ratings of the two LLM audit sessions | `data/audit/` |
| Pre-specified designs and reading rules | `docs/phase4_prereg.md`, `docs/phase5_prereg.md`, `docs/phase6_prereg.md` |
| Paired article bootstrap (2,000 resamples, seed 42, percentile intervals) | `scripts/analyze_phase4.py` (`boot_ci`) |

## Layout

```
supplementary/  supplementary material of the paper (PDF)
supdrift/       library: chat client with a JSONL call cache, memory chains, evaluator
scripts/        source construction, generation, scoring and analysis
data/           cohort, constructed sources, audit material (derived from Evidence Inference 2.0)
results/        generated chains (*.jsonl), evaluator verdicts (*_scored.csv), summaries and reports
docs/           pre-specification documents and reproducibility notes
figures/        figure files and captions
```

`results/` holds the chains and verdicts of the experiments reported in the paper: the extended-source experiment
under both protocols (`ratio_*`, `ratio_notrunc_*`), the length-matched control (`lenctrl_*`), the matched prompt
(`e15b200_*`), the first-write comparison (`e18_*`), the length-by-position experiment (`e19_*`), the contextualized
inputs (`e6_*`) and the verdicts of the original 25-token experiment (`gate2_scored_*`). For other auxiliary
experiments only the summary tables are included.

Experiment reports: `results/e15/` (matched prompt), `results/e16/` (filler audit), `results/e17/` (evaluator audit),
`results/e18/` (first write against fourth write), `results/e19/` (length by position), `results/e6/` (contextualized
inputs). Each directory holds a summary table (`*_summary.csv`) and a report (`*_report.md`) written by the
corresponding `scripts/analyze_*.py`.

## Data

The cohort and all sources are derived from the original Evidence Inference 2.0 release (`annotations_merged.csv`,
`prompts_merged.csv`, train split). The raw release and the article full texts are not redistributed here; obtain them
from the dataset authors and place them under `data/raw/` and `data/fulltext/`. Every record carries the PubMed Central
identifier (`pmcid`) and the dataset prompt identifier (`prompt_id`) of its target.

## Running

Python 3.10; `pip install -r requirements.txt`. Open-weight models are served with vLLM 0.11.0
(`Qwen/Qwen3-8B-FP8`, `Qwen/Qwen3-14B-FP8`, evaluator `Qwen/Qwen3-32B-FP8`); server helpers are
`scripts/addexp_servers.sh` and `scripts/rev_eval_up.sh`. Set `HF_HOME` and, for the API model, `OPENAI_API_KEY`,
then `source scripts/rev_env.sh`.

The analyses can be re-run from the stored chains and verdicts without any model, for example:

```
python scripts/analyze_e19.py     # results/e19/e19_summary.csv, e19_cells.csv, e19_report.md
python scripts/analyze_e17.py     # results/e17/e17_report.md
```

Stored evaluator verdicts are the record of the paper; the evaluator is stochastic, so re-scoring gives slightly
different verdicts.
