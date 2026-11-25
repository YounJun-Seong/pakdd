# Phase 4 pre-registration — causal-story experiments (2026-09-14)

Written BEFORE any Phase-4 generation. Analysis choices, subsets, budgets and
predictions below are fixed; anything changed later is logged in "Deviations".

## Shared protocol (unchanged from the paper)

- Cohort: `data/gate2/gate2_v1.jsonl`, 294 articles (94/100/100), paired in
  every cell. Same ICO span order RNG (`random.Random(f"{sample_id}-order")`)
  unless the experiment manipulates order.
- Chain: depth 5 (4 intermediate + final) unless stated; same model every step;
  final answer 80 instructed tokens; temperature 0.7, seed 42 (Qwen);
  GPT-5.4-mini reasoning_effort=low.
- **Enforced (hard-cap) protocol is primary** for ①②③⑤⑥: every intermediate
  memory is tokenizer-truncated to <= B tokens (same tokenizers as the paper:
  checkpoint tokenizer for Qwen, o200k_base for GPT). Instruction budget = B.
- Every step's RAW token count is recorded, so per-budget we report
  natural compliance (raw <= B at a step) and chain-level forced truncation
  (any step raw > B) without a separate audit.
- Outcomes, always all of them: final-answer Support Retention (SR); complete
  warrant preservation = frozen evaluator recovers gold label from the LAST
  intermediate memory; citation correctness; failure decomposition.
- Evaluator: classifier v3, frozen, unchanged. Cache: `cache/phase4_*.jsonl`.
- Statistics: paired bootstrap over articles (B=2,000, seed 42, one generator
  per statistic); logistic GEE clustered by article, exchangeable correlation,
  cluster-robust SE, `supported ~ blind * multi` per cell-set plus the
  experiment-specific three-way term. Primary metric of every experiment is the
  probability-scale DiD on final SR; warrant DiD is co-primary for ①.

## ① Budget sweep (S)

Question: is the Blindness x Competition interaction confined to the 25-token
extreme, i.e. is there a budget-dependent failure regime?

- Pilot (before the full run): Blind/Multi and Aware/Multi hard-cap chains at
  B in {40, 50, 75, 100, 150} on the pilot subset P60 = first 20 articles per
  gold label in `gate2_v1` order, all three models. Only forced-truncation and
  compliance are read from the pilot; no outcome is looked at.
- **B_high := the smallest B in the grid at which >= 90% of Blind/Multi chains
  complete with no forced truncation in ALL three models.** If none reaches
  90% at 150, B_high = 150 and the shortfall is reported.
- Full grid: B in {25 (existing `extra_hard`), 40, 50, B_high} x
  {aware, blind} x {single, multi} x 294 x 3 models.
- Analysis per budget: four cells, SR and warrant DiD with bootstrap CI, GEE
  interaction; across budgets: GEE `supported ~ blind*multi*budget_c` with
  budget centred and treated as numeric (log2 B), the three-way term is the
  budget-dependence test. Report forced-truncation rate next to every DiD.
- Predictions (fixed): |DiD| decreases monotonically with B in all models; at
  B_high the SR DiD is within [-5, +5] pp for at least two of three models.
  Either outcome is reportable; the claim becomes "regime-dependent" only if
  the monotone pattern holds.

## ② Length-matched competition control (S)

Question: is the Multi penalty caused by competing warrants or merely by longer
input / more chunks?

- Conditions (same 294 articles, blind AND aware, hard-cap B = 25 primary,
  B = 50 secondary):
  1. `single` — target span (existing)
  2. `single_filler` — target span + (K-1) chunks of same-article NON-results
     prose, total tokens matched to that article's multi material (+-10%)
  3. `single_dup` — target span + (K-1) paraphrases of the target span, same
     token matching; paraphrases written once by GPT-5.4-mini and accepted
     only if the frozen evaluator recovers the gold label from the paraphrase
     alone
  4. `multi` — existing
  K = number of ICOs in the article's multi material, so chunk count matches.
- Filler source: Evidence-Inference full text (`data/fulltext/PMC*.txt`,
  downloaded from the dataset's GitHub release). Sentences taken from text
  BEFORE the first Results heading; sentences containing digits, "%", "p <",
  "significant", "increase", "decrease", "reduc", "improv", "higher", "lower"
  are excluded, so no numerical finding is injected. Chunk order shuffled with
  the per-article RNG. Filler and paraphrase material are identical across
  generator models.
- Analysis: blind penalty per condition; contrasts multi - single_filler and
  multi - single_dup (paired bootstrap, GEE with condition dummies).
- Prediction: blind SR(single) ~ SR(single_filler) ~ SR(single_dup) >
  SR(multi); the two control-vs-multi contrasts exclude 0 in every model. If
  single_filler already reproduces the multi penalty, "competition" must be
  re-described as "input load" and the paper's term changes.

## ③ Target-position control (S)

Question: does prefix truncation explain the Blind/Multi failure?

- Same multi material, distractor relative order fixed as in the original
  shuffle; target moved to position first / middle (index floor(K/2)) / last.
  Blind and aware, hard-cap B = 25 and 50, 294 articles, 3 models.
- Analysis: blind penalty per position; position-balanced average is the
  headline; GEE `supported ~ blind * position`.
- Prediction: blind penalty at first vs last differs by < 5 pp. A last-only
  collapse is reported as a confound and the headline switches to the
  position-balanced estimate. The original-order data are additionally
  analysed observationally by the target's realised position.

## ④ Human memory-warrant audit (S)

- 360 last-intermediate memories: 3 models x 4 cells of the enforced-25 grid
  (the Fig. 2b data) x 30 articles, stratified 10/10/10 by gold label, drawn
  with seed 42; shuffled, condition-blind.
- Items per memory: target present? direction correct? statistical status
  preserved? complete warrant preserved? (yes/no each).
- Report: human vs evaluator agreement, Cohen's kappa and Gwet's AC1,
  precision/recall/F1 of the evaluator's complete-warrant label against the
  human label; two annotators if available, one with clinical background.
- Package built by `scripts/build_memory_audit.py`; nothing else changes.

## ⑤ Randomized competition dose-response (A)

- Subset A5: the 129 `gate2_v1` articles whose article has >= 4 additional
  filter-passing unanimous prompts (same filters as `build_gate2.py`).
- For each article a single per-article permutation of its distractor pool
  (`random.Random(f"{sample_id}-K")`); K in {1,2,3,4,5} uses the first K-1
  distractors of that permutation (nested sets), so K is manipulated within
  article with everything else held fixed. Order shuffled per (article, K).
- Blind and aware, hard-cap B = 25 primary, 50 secondary; 3 models.
- Analysis: GEE `supported ~ blind * K` (K numeric, centred), the blind:K slope
  is the dose-response test; plot aware and blind lines over K with bootstrap
  CIs. Also warrant.
- Prediction: blind slope < 0 and aware slope ~ 0 in every model; blind
  penalty at K=5 exceeds K=2 by > 10 pp.
- Note: distractors beyond the original 2-4 were not evaluator-verified; their
  readability is measured post hoc as in Phase 3 (`verify_distractor_spans.py`)
  and reported, not used for selection.

## ⑥ Full depth factorial (A)

- depth in {1, 3, 5} x {aware, blind} x {single, multi}, hard-cap B = 25, 294
  articles, 3 models. depth 1 = direct (no intermediate step, aware == blind)
  taken from the existing nominal grid (budget-independent); depth 5 =
  existing `extra_hard`; depth 3 generated now (2 intermediate steps).
- Written memory = last intermediate memory (step 2 at depth 3, step 4 at
  depth 5).
- Analysis: GEE `supported ~ blind * multi * depth_c`; DiD at each depth.
- Predictions are two-sided by design: DiD already present at depth 3 ->
  "emerges at the initial write and is amplified"; DiD ~ 0 at depth 3 and
  large at depth 5 -> "interacts with repeated consolidation".

## ⑦ Human-grounded cohort (A)

- All 360 candidate targets' gold spans + ICO, one question: is the annotated
  evidence sufficient to determine the effect label? (+ which label).
- Human-grounded cohort := candidates judged sufficient (independent of the
  evaluator). Re-analysis only: nominal 25, enforced 25, and the ① budget
  closest to 50 on that cohort.
- Package built by `scripts/build_grounding_audit.py`.

## ⑧ Query-blind structured allocation baseline (B, last)

- New blind mode `blind_slots`: the model itself writes one ultra-short slot per
  finding, `outcome | dir | sig`, under the same hard cap; compared with
  free-form blind at the same B (25, 50), multi, 294 articles, 3 models.
- Question is only "does explicit warrant-preserving allocation reduce the
  failure?", not SOTA.

## Compute plan

Generators on GPU0 (Qwen3-8B 0.25 + Qwen3-14B 0.30), evaluator on GPU1 via
`supervise_eval.sh`. GPT-5.4-mini via API; Phase-4 total ~60k short calls per
the estimates in `scripts/run_phase4.py --plan`.

Order: ① pilot -> ① full -> ② + ③ -> ⑤ -> ⑥ -> ④ + ⑦ packages -> ⑧.

## Deviations

(none yet)

### 2026-09-14 — ① pilot outcome (rule applied as written)
Blind/Multi chain-level forced truncation on P60: GPT-5.4-mini
100/98/90/77/52 % and Qwen3-14B 97/93/85/67/48 % at B = 40/50/75/100/150
(Qwen3-8B pilot pending; the rule is already decided by the other two).
No budget reaches the 90 % no-truncation criterion, so **B_high = 150** with the
shortfall reported. Mechanism: instructed length is followed only on average
(mean raw ≈ 0.85–0.9 B at every B), so one of four steps overshoots in about
half of the chains. Severity falls with B: tokens removed from a truncated step
22 % → 11 % (14B blind) from 40 to 150. The sweep therefore reports, next to
every DiD, (i) chain-level forced-truncation rate, (ii) step compliance and
(iii) truncation severity. Optional add-on if a truncation-free arm is wanted:
the regeneration protocol (≤ 4 attempts) at B = 150.

### Infrastructure (no design change)
Qwen3-8B-FP8 served on port 8304 instead of 8302 (8302 is used by another
project's bf16 Qwen3-8B server). Cache keys and prompts unchanged.

### 2026-09-14 — additions after the ① token audit (exploratory, not primary)
- At B = 150 the single-ICO cells are truncation-free (0–2 % of chains) while
  the multi-ICO cells still truncate 20–49 % (severity 8–14 %). A secondary
  sensitivity analysis will therefore repeat the B = 150 cell table on the
  subset of articles whose four chains all have forced == False. Labelled
  exploratory; the pre-registered primary remains the full-cohort DiD with the
  truncation rates reported beside it.
- GPT-5.4-mini generation stopped mid-③ (OpenAI credits exhausted); ① is
  complete for GPT. ③⑤⑥②⑧ for GPT resume from cache once credits are added.
- The Qwen generator servers were stopped after all Qwen generation finished
  so the evaluator could use GPU0; the single_dup arm (needs verified
  paraphrases) is generated afterwards with the servers restarted.

### 2026-09-14 — ① and ③ outcomes against the pre-registered predictions
- ① SR DiD at B=150: −1.4 (8B), −7.8 (14B), −5.1 (GPT). Prediction "within ±5 pp
  for ≥2 of 3 models" FAILS strictly (8B only); monotone shrinkage holds for 8B
  only (14B/GPT peak at B=40–50 because the single-ICO cells also fail at 25).
  Exploratory truncation-free subset at 150: DiD ≈ 0 in all models.
- ③ Prediction "first − last blind penalty < 5 pp" FAILS: enforced-25 first/last
  penalty 8B −7.5/−17.7, 14B −5.4/−32.3. Position-balanced enforced penalties
  (headline per the rule): 8B −14.9, 14B −22.2 (B=25); −11.9, −16.0 (B=50).
  Exploratory: within non-truncated chains the position effect disappears
  (8B B=50 blind SR first/middle/last 84.6/83.9/91.2; 14B 93.8/97.1/96.8), and
  in the paper's NOMINAL 25 grid the realised-position penalties are flat
  (8B −9.7/−12.1/−13.1; 14B −5.4/−8.6/−3.3; GPT −2.2/−9.3/+0.0). The enforced-cap
  position effect is therefore a prefix-truncation artefact; the nominal main
  result is position-invariant.

### 2026-09-14 — ③ (GPT), ⑤, ⑥, ②-filler, ⑧ outcomes (Qwen; GPT pending for ⑤⑥②⑧)
- ③ GPT-5.4-mini enforced-25 first/middle/last blind penalty −5.1/−25.5/−30.3
  (first − last +25.2 [+18.4, +32.3]); same at B=50. All three models show the
  prefix-truncation artefact; position-balanced enforced penalties: 8B −14.9,
  14B −22.2, GPT −20.3 (B=25).
- ⑤ Blind penalty is step-shaped: most of it appears at K=1→2 and final SR
  plateaus for K≥3 (8B −3.1/−11.6/−12.4/−14.7/−14.7; 14B −5.4/−17.8/−23.3/−24.8/
  −20.9). Prediction "K5 − K2 > 10 pp" FAILS on SR; holds for 14B warrant only
  (blind×K GEE p=0.006). Aware slope ≈ 0 as predicted.
- ⑥ DiD at depth 3 ≈ depth 5 (8B −16.3/−16.3; 14B −18.0/−15.3; three-way p=0.56/
  0.08): failure is complete at the initial write; no consolidation amplification.
- ② single_filler reproduces the multi warrant penalty entirely (8B −32.4 vs
  −32.0; 14B −41.4 vs −39.2) and most/all of the SR penalty for 8B; 14B keeps a
  significant residual multi − filler SR contrast (−12.2, −10.8). Prediction
  "single ≈ filler ≈ dup > multi" FAILS: per the pre-registered clause the
  mechanism is re-described as query-blind budget competition from ANY
  co-present content (input load), with competing findings adding a
  reader-level cost in the stronger model. Filler effect persists in
  non-truncated chains (not a truncation artefact).
- ⑧ Model-written slots are not better than free-form (8B worse: SR −11.9,
  warrant −20.7; 14B SR n.s., warrant −10.2); slot outputs are truncated in
  87–99 % of chains.

### 2026-09-14 23:05 — all scoring complete; GPT-5.4-mini outcomes
- ⑤ GPT: blind penalty K1..K5 = −10.1/−18.6/−21.7/−24.8/−24.8 (SR, B=25;
  blind×K p=0.031), warrant −14.0/−31.8/−36.4/−34.9/−36.4 (p=0.038); at B=50 the
  slope is steeper (SR −2.3 → −30.2, p=0.005; warrant p=5e-5). Same step-then-
  plateau shape; GPT alone keeps declining to K=5 at B=50.
- ⑥ GPT: DiD depth 3 vs 5 = −9.9 vs −11.6 (SR), −25.9 vs −24.8 (warrant);
  three-way p=0.90/0.85. Consistent with 8B/14B: no consolidation amplification.
- ② (n=211 articles with all four conditions): single_dup ≈ single in every
  model (SR penalty −2.4/−8.1/−1.9; warrant −10.0/−12.8/−11.4), so chunk count
  and token volume per se do NOT produce the penalty. single_filler reproduces
  the multi penalty at the warrant level for Qwen (8B −31.8 vs −33.2; 14B −41.2
  vs −40.3) and EXCEEDS it for GPT (SR −24.6 vs −15.6; warrant −49.8 vs −38.4;
  multi − filler = +9.0 [+0.9, +17.1] SR, +15.6 warrant). Mechanism: competition
  among DISTINCT co-present content for the query-blind budget; distinct
  findings add a reader-level cost only in 14B (multi − filler SR −11.8).
- ⑧ GPT: slots vs free-form B=25 SR −9.2 [−15.0, −3.1], warrant −14.3; B=50 n.s.
  No model benefits from model-written slot allocation.
- Scoring infrastructure note: one GPT depth-3 memory contained a NUL byte;
  score_generic.py now strips NUL/CR and sets an escapechar (no score changed).

### 2026-09-15 — ④ memory-warrant human audit (144 items, 1 annotator; file
graphharness/memory_audit_task_144_annotated.csv; report results/memory_audit_report.txt)
- complete_warrant: agreement 88.2 %, Cohen κ 0.708 [0.564, 0.836], Gwet AC1
  0.802; evaluator vs human (human = truth) precision 0.922, recall 0.913,
  F1 0.918. Confusion: ev-lenient 8, ev-strict 9 → errors balanced, and
  balanced across conditions (aware 5 lenient/3 strict; blind 3/6).
- By model κ: 8B 0.76, GPT 0.72, 14B 0.64. By mode: blind κ 0.74, aware 0.54
  (aware agreement 89 % with a ~85 % base rate). Sub-items: target present
  agreement 88.9 % κ 0.62; direction 87.3 % κ 0.41 (n=126).
- The 2×2 reproduces on human labels: blind/multi warrant rate human 38.9 %
  vs evaluator 38.9 %; DiD human −33.3 pp vs evaluator −30.6 pp on the same
  144 items. Human-labelled disagreements are mostly stricter completeness
  judgements (composite outcomes, comparator swaps, scope extensions).

### 2026-09-15 — seed robustness (S100, enforced cap, seeds 42/143/244; report
results/phase4_seeds_report.txt, summary results/phase4_seeds_summary.csv)
SR DiD mean ± SD across seeds: 8B −12.0±1.0 (B=25), −9.7±3.2 (50), −2.3±3.1 (150);
14B −20.7±6.8 (25), −15.7±5.1 (50), −9.7±5.9 (150). Warrant: 8B −16.3±1.5 /
−12.0±4.0 / −8.3±3.5; 14B −27.3±3.5 / −23.0±4.4 / −13.7±5.5. Sign and ordering
across budgets replicate in every seed; seed SD (1–7 pp) is below the
bootstrap CI half-width (~10 pp at n=100). Blind/multi truncation rates are
seed-invariant (8B 67–68/57–64/31–32 %; 14B 99/85–90/48 %). Servers stopped.
