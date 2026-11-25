# Reproducibility reference for the Methods section
(2026-09-06; every value verified against the implementation)

## Generation (agents)
- Sampling: Qwen agents temperature 0.7, top-p 1.0 (default), per-request seed 42
  (vLLM). GPT-5.4-mini is a reasoning model: temperature/seed not supported;
  default sampling with reasoning_effort="low".
- Determinism: Qwen quasi-deterministic under fixed seed/server; GPT
  non-deterministic (state explicitly). All evaluator calls cached; analyses
  fully reproducible from cached responses.
- Length control: intermediate steps receive an instructed budget of {25, 50}
  tokens with a hard cap of 2xbudget+64 (instruction-driven compression, no
  mid-sentence truncation); final answers instructed 80 tokens (cap 224).
  For GPT, caps become max_completion_tokens = cap + 4000 (reasoning tokens).
- Model snapshots: Qwen/Qwen3-8B-FP8, Qwen/Qwen3-14B-FP8 (official HF FP8
  checkpoints; served with vLLM 0.11.0, torch 2.8.0+cu128, transformers
  4.57.1); gpt-5.4-mini-2026-03-17 (date-pinned API snapshot).
- Prompts: verbatim in supdrift/chain2.py (aware / blind / blind_instr /
  blind_qawp / final) and supdrift/classifier.py; include in appendix.

## Design
- Depth: main condition depth 5 (4 intermediate + 1 final); reference depth 1
  (direct, budget-independent). Same model at every step of a chain.
- Multi-ICO material: 1 target + 2-4 distractor prompts from the SAME article
  (articles with <2 usable distractors excluded) => 3-5 ICOs competing for one
  budget; mean material length ~229 tokens.
- ICO order: spans shuffled with a per-article seeded RNG
  (random.Random(f"{sample_id}-order")) — random across articles but IDENTICAL
  across conditions and models.
- Distractor selection: unanimous-label, filter-passing prompts of the same
  article (evidence 100-1200 chars, prose ratio >=0.60), deterministic shuffle,
  first 4. Targets stratified 100/100/94 by effect label and kept only if the
  frozen evaluator recovers the gold label from the gold span (294/360, 83.3%).
- Pairing: the same 294 articles are used in every condition x model; all
  contrasts and bootstraps are paired at the article level.

## Statistics
- Paired bootstrap: B=2,000, percentile 95% CI, resampling unit = article,
  seed 42.
- Regression: logistic GEE (binomial, logit link), exchangeable working
  correlation, clustered by article, cluster-robust SEs.
  Model: supported ~ blind * multi (25-token cells); three-way adds x tight
  (25 vs 50 tokens).

## Evaluator (frozen)
- Model: Qwen/Qwen3-32B-FP8 — weight-disjoint from all generators.
- Protocol: classifier v3, frozen (system-prompt SHA-256 prefix
  8185602a5917e3ef; frozen 2026-09-03 in data/pilot/cohort_freeze.json).
  Three attempts: thinking mode (temperature 0.6, top-p 0.95, seeds 42/43,
  max 2500/3500 tokens, repetition_penalty 1.05), then a no-think fallback
  (max 600). Output = direction x certainty -> 4-way claim label;
  supported := claim label == gold effect label.
- Validation: gold-span macro-F1 0.924, coverage 94.8% (n=474; 26 exclusions
  via human span audit only); human audit of 240 outputs: agreement 94.6%,
  Cohen's kappa 0.77 (PABAK 0.89), qualifier-loss precision 0.867,
  significance-inflation confirmation 9/9. Evaluator errors balanced across
  conditions (aware 6 vs blind 6) and directionally conservative
  (misses > false alarms).

## Data
- Source: original Evidence Inference 2.0 release (annotations_merged.csv /
  prompts_merged.csv; train-split articles). NOTE: the BigBio HF export is
  unusable for evidence-grounded work (one span copied to all prompts of an
  article) — documented in the paper's data section.

## Canonical evaluator results (2026-09-29)
- The committed `results/*_scored.csv` files are the canonical evaluator record; they are collected, unchanged, in
  `results/canonical_results.csv` (288,061 verdict rows) with `results/canonical_manifest.json` (evaluator spec, file
  hashes). Every reported number must be derivable from these files. Committed rows are never re-scored.
- The evaluator is stochastic (thinking mode, temperature 0.6): 24,178 items were judged twice by concurrent scoring
  processes and 987 received a different verdict — test-retest agreement 95.9 %. Report this as evaluator reliability.
- `cache/classifier_scoring.jsonl` is now duplicate-free (one response per key, chosen to reproduce the committed
  verdict of the first row that refers to it; `scripts/build_canonical.py`). 993 committed rows (0.34 %) concern an
  item that also carries a different committed verdict elsewhere; they are listed in
  `results/canonical_cache_mismatch.csv` and would change if re-scored. The pre-fix cache is kept as
  `cache/classifier_scoring.pre_canonical_20260929.jsonl`. `scripts/score_generic.py` takes an exclusive lock so two
  scoring processes can no longer run at once.
- The enforced-25 main grid is reported from `extra_hard_*` / `extra_hardmem_*` (loader `scripts/addexp_common.py`);
  the Phase-4 replay of the same texts differs in 2 of 7,056 verdicts and is not used for the 25-token cells.
