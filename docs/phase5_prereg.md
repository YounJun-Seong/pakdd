# Phase 5 pre-registration — closing the two interpretive attacks (2026-09-18)

Written before any Phase-5 generation. Shared protocol as in Phase 4
(docs/phase4_prereg.md): cohort gate2_v1 (294), frozen evaluator v3, article
bootstrap B=2,000 seed 42, GEE clustered by article. Enforced-cap protocol
unless stated. New cache: cache/phase5_{model}.jsonl.

## P0-1 Oracle multi-warrant capacity control

Question: at budget B, could ALL candidate warrants have fit at all? If yes and
the blind model still fails, the failure is allocation, not capacity.

- Oracle representation, one line per ICO of the article's multi material,
  built from gold labels only (no model):
  `short`: `<outcome>: <increase|decrease|no difference>, <significant|n.s.>`
  `full` : `<outcome> [<intervention> vs <comparator>]: ..., ...`
  Header line `Findings from [PMC{pmcid}]:`. Same per-article span order as the
  chains. `short` is primary (most compact still-identifying form); `full` is
  reported as a sensitivity.
- Oracle-Target = the target line only; Oracle-All = all K lines.
- Fit(B) := oracle token length (that model's tokenizer) <= B, no truncation.
  Reported by K and B. When it does not fit, the memory given to the reader is
  the prefix-truncated oracle (same rule as the enforced chains) and the
  `fits` flag is carried into the analysis; the fit-only subset is the primary
  Oracle-All vs Model-Blind comparison, the all-article version secondary.
- Reader: each generator model answers (a) the target from Oracle-Target and
  Oracle-All; (b) EVERY ICO from Oracle-All (Oracle Expected Answerability,
  article-weighted, evaluator-eligible ICOs primary as in Phase 3).
- Model-Blind EA at the same budgets: the enforced blind/multi step-4 memories
  of ① (B = 25/40/50/150) queried with every ICO (new generation, same
  protocol as the paper's EA). Model-Aware SR from ①.
- Budgets {25, 40, 50, 150}, 294 articles, 3 models.
- Predictions: Fit(25) low for K>=4 in all tokenizers; Fit(50) > 90 % for K<=4;
  Oracle-All SR and EA >= Model-Aware SR at B >= 50; the Oracle-All − Model-Blind
  gap at B=50 exceeds 10 pp on the fit-only subset.

## P0-2 Truncation-free robustness

Question: does the Blindness x Competition interaction survive when NO memory
is ever cut?

- S100 (same 100 articles as the seed study), 3 models, aware/blind x
  single/multi, B = 25 and 50; plus the multi position arm (target first /
  middle / last, aware/blind) at B = 25.
- Each intermediate step: regenerate until the output is <= B tokens
  naturally, up to 20 attempts (attempt a>0 adds the stricter instruction and
  uses seed 42+100a, as in the Phase-3 regeneration control). The FIRST
  compliant output is used; nothing is ever truncated. If 20 attempts all
  fail the chain is marked failed and excluded; failure rate, mean attempts and
  natural-compliance rate per step are reported by cell.
- Analysis: 2x2 DiD and GEE as in ①; compared with the enforced-cap DiD on the
  same 100 articles; position penalties vs ③ on the same articles.
- Predictions: the SR DiD stays negative with CI excluding 0 in all models at
  B=25; the first-vs-last penalty gap shrinks by more than half relative to ③.

## P1-1 Memory trajectory M0 -> M4

Question: at which rewrite is the warrant lost?

- Replay every intermediate memory of the ① enforced-25 chains from cache (no
  generation): M1..M4 for the 4 cells x 294 x 3 models; M0 = the seed
  material itself (scored once per icoset, model-independent).
- Evaluator on each memory -> complete warrant (supported), target present
  (direction != NOT_MENTIONED), direction correct (direction == gold),
  asserted (certainty == ASSERTED).
- Report WP by step and cell; transition loss P(WP_t = 0 | WP_{t-1} = 1) and
  recovery P(WP_t = 1 | WP_{t-1} = 0); GEE `WP ~ blind * multi * stage`
  with stage categorical (M1 reference).
- Prediction: >= 70 % of the total M0 -> M4 warrant loss in blind/multi occurs
  at M0 -> M1; transition losses at M2..M4 are each < 8 pp.

## P1-2 Repeated candidate-subset randomization

- A5 (129 articles), K in {2,3,4,5}, subset seeds {143, 244, 345, 446} in
  addition to the existing 42 (⑤); the target is fixed, the K-1 distractors
  are the first K-1 of `random.Random(f"{sid}-K{seed}")`'s permutation of the
  pool; order shuffled per (article, K, seed). Aware and blind receive the
  same subset (paired). B = 50, 3 models.
- Analysis: per article x K, blind penalty averaged over the 5 subsets, then
  article bootstrap; GEE `supported ~ blind * K` on all subsets with article
  clustering; subset-seed variance reported.
- Prediction: the K-profile of ⑤ replicates (step at K=1->2, slope thereafter
  within the seed-42 CI).

## P2-1 Human audit of enforced-25 final answers (package only)

120 final answers from the ① enforced-25 grid (3 models x 4 cells x 10,
label-balanced, condition-blind): supported Y/N + failure type, same format
as the paper's nominal-25 audit; evaluator DiD vs human DiD. Built by
scripts/build_final_audit.py. (The memory-level enforced-25 audit — 144 items —
is already done: results/memory_audit_report.txt.)

## P2-2 Balanced compact memory baseline

Blind/multi, B = 50 and 150, 294 articles, 3 models, enforced cap. New mode
`blind_balanced`: "preserve one compact record for every finding, omit none:
<outcome>: <direction>, <statistical status>". Compared with free-form blind
from ① at the same B (SR, warrant, forced-truncation rate).

## Compute

GPU1 only (GPU0 is occupied by another user). Generation first (Qwen 8B+14B
on GPU1, GPT via API), then the evaluator on GPU1. Order: P1-1 replay (no GPU)
-> generation P0-2, P1-2, P0-1, P2-2 -> scoring P1-1, P0-1, P0-2, P1-2, P2-2.

### Protocol amendment before the full P0-2 run (2026-09-18, after a 3-article smoke test)
With a fixed instructed budget, GPT-5.4-mini failed 19/30 smoke chains at B=25
even after 20 attempts (its natural length under "25 tokens" is ~40-50
tokens, and seeds do not change it). To keep the no-truncation rule without
excluding most GPT chains, the INSTRUCTED budget shrinks 5 % per failed
attempt (floor 8 tokens; the stricter sentence from attempt 2 on), while
acceptance is always against the true cap B. Attempts and the instructed
budget at acceptance are recorded per step and reported; the same rule is
applied to all three models.

### Scope decision (2026-09-18 16:10)
Only P0-1 (oracle feasibility / oracle reader / model-blind EA) and P0-2
(forced-truncation diagnostics + the truncation-free S100 arm) are run.
P1-2 resample and P2-2 balanced were stopped before completion (partial GPT
resample rows are cached but not analysed). P1-1 trajectory scoring was already
running from cache and is kept as a supplementary result at no extra cost.
P0-2 diagnostics come from the ① enforced chains (results/phase5_truncdiag_summary.csv).

### 2026-09-18 18:05 — P0-1 / P0-2 outcomes (all three models scored)
P0-1. Oracle-All(short) fits at B=25 in 0 % of articles for every K and
tokenizer (51–80 tokens needed); at B=50 in 22 % (GPT) / 13 % (Qwen); at 150
in 98–99 %. At B=25 the truncated oracle is WORSE than the blind model
(EA oracle 64/49/53 vs blind 68/66/63 for GPT/8B/14B) → the 25-token regime is
capacity-bound. On fit-only articles the oracle reader reaches 96–97 % while
the same articles' blind chains give 78.5 (GPT, n=65) / 81.1 (8B, n=37) /
78.4 (14B, n=37) at B=50 and 88.3 / 92.7 / 88.9 at B=150 (n≈290); EA gaps at
150: +6.2 / +7.8 / +5.6. Prediction "gap > 10 pp at B=50 fit-only" holds for
all three (−18.4 / −16.2 / −18.9). The allocation-failure claim is supported at
B ≥ 50 and NOT at 25.
P0-2. Truncation-free (adaptive regeneration, never cut) SR DiD at B=25:
8B −20.2 [−32.1, −8.3], GPT −19.0 [−30, −8] (both survive; enforced −13/−16 on
the same articles); 14B −4.0 [−14, +6] but with 14–34 % chain failures
(selection; blind/single 34 %). At B=50: 8B −5.0 (n.s.), 14B −15.2 [−24.2,
−7.1], GPT −3.0 (n.s.) versus enforced −6 / −17 / −21 → for GPT the enforced
B=50 interaction was largely a truncation artefact; for 14B it is real.
Position without truncation: first−last SR +7.1 / +6.0 / +5.1 (all n.s.)
versus +21 / +25 / +26 enforced → the SR position effect is a prefix-truncation
artefact; a memory-level later-position vulnerability remains for 14B
(warrant first−last +26 [+8, +44]). Diagnostics: results/phase5_truncdiag_summary.csv.

### 2026-09-19 — P2-3 Structured blind memory at the higher budgets (written before generation)
Reviewer framing: the 25-token structured-slot baseline (Phase-4 ⑧) was force-
truncated in 98–99 % of chains, so it cannot speak to whether allocation failure
at B >= 50 (the regime where Oracle-All fits) is mitigable by representation.
- Mode `blind_slots` (unchanged prompt, unchanged cache key scheme of ⑧),
  blind/multi, B = 150 added to the existing 25/50; 294 articles, 3 models,
  enforced cap, depth 5. 25/50 are replayed from cache; only 150 is new.
- Comparison at B in {50, 150}, same articles, paired: Free-form Blind (①),
  Structured Blind (this), Aware (①), Oracle-All short (P0-1; fit-only subset
  and all-article). Outcomes SR (final) and complete-warrant (memory);
  structured − free-form paired article bootstrap CI; forced-truncation rate
  beside every number.
- Reading rule fixed now: structured > free-form with CI excluding 0 ->
  "allocation failure is partly mitigable by representation"; CI covering 0 ->
  "simple structure alone does not resolve future-query uncertainty";
  structured < free-form -> "uniform slot allocation adds overhead / fails to
  allocate adaptively". Any of the three is reported as-is.

### 2026-09-19 — P2-3 outcome (all three models scored; results/structured_baseline_summary.csv,
scripts/analyze_structured_baseline.py; raw results/phase4_slots_{model}.jsonl now hold B=25/50/150)
Structured − Free-form, blind/multi, paired article bootstrap (SR / warrant):
  B=50   8B −9.9 [−15.6, −4.1] / −13.9;  14B −4.1 [−9.9, +1.7] / −7.1 [−13.3, −1.0];  GPT −0.7 (n.s.) / −5.4 (n.s.)
  B=150  8B −5.4 [−9.9, −1.4] / −8.8 [−13.9, −3.4];  14B +1.0 [−3.4, +5.8] / −1.7 (n.s.);  GPT +2.0 [−2.4, +6.5] / −5.1 [−10.9, +0.7]
Structured forced truncation at 150 is 9/14/17 % (free-form 24/45/49 %), so the
structured arm is the cleaner one at 150 and still does not beat free-form.
Oracle-All − Structured on the fit-only subset at B=150 (n≈289): +8.7 [+4.5, +12.8]
(8B), +6.2 [+2.4, +10.4] (14B), +5.9 [+2.1, +10.0] (GPT) — all exclude 0, same
size as Oracle-All − Free-form (+3.5 n.s. / +7.3 / +7.9). At B=50 fit-only
(n=37/37/65) Oracle − Structured = +8.1 / +21.6 / +13.8.
Reading per the fixed rule: 14B and GPT -> "simple structure alone does not
resolve future-query uncertainty" (CI covers 0); 8B -> "uniform slot allocation
adds overhead" (structured worse, CI excludes 0). No model benefits at any
budget. The oracle gap at B >= 50 therefore survives a representation-level
mitigation: the failure is not the free-form format.
Infra: generator servers on GPU0 (14B) / GPU1 (8B); evaluator on GPU0 after
generation; 0 dirty rows; 25/50 replayed from cache and reproduce the ⑧ report exactly.

### 2026-09-19 — P0-1 addendum: Oracle-fit subset PAIRED gap with 95 % CI
(scripts/analyze_oracle_gap.py -> results/oracle_gap_summary.csv; no new generation)
Oracle-All(short) − Free-form Blind, same articles, paired article bootstrap B=2,000 seed 42.
Fit-only subset (primary):
  B=50   ELR  8B +16.2 [+2.7, +29.7] (n=37)  14B +18.9 [+5.4, +35.1] (n=37)  GPT +18.5 [+9.2, +27.7] (n=65)
         EA   8B +20.7 [+11.9, +29.3]        14B +20.7 [+9.9, +30.9]         GPT +14.8 [+8.7, +21.4]
  B=150  ELR  8B  +3.5 [+0.0, +7.3] (n=289)  14B  +7.3 [+2.8, +11.4] (n=289) GPT  +7.9 [+3.4, +12.4] (n=290)
         EA   8B  +7.9 [+5.0, +10.8]         14B  +5.5 [+2.8, +8.0]          GPT  +6.4 [+4.0, +8.7]
  B=40   only GPT has a usable fit subset (n=19): ELR +21.1 [+5.3, +42.1], EA +20.2 [+7.0, +35.1].
  B=25   no article fits (n=0) — capacity-bound; all-article gap is NEGATIVE (truncated oracle
         worse than blind: ELR −23.5 / −13.3 / −9.5).
Oracle − Aware on the same fit subsets: B=50 +10.8 / +16.2 / +9.2 (all exclude 0); B=150 +3.1 /
+0.3 / +2.8 (all n.s.) — at 150 the aware model is at the oracle ceiling, the blind model is not
(Blind − Aware at 150: −0.3 n.s. / −6.9 [−10.7, −3.1] / −5.2 [−9.3, −1.0]).
Sensitivity, `full` oracle format on its own fit subset at 150 (n=195/195/209): +6.7 [+3.1, +10.8] /
+7.7 [+3.6, +12.3] / +10.5 [+6.2, +15.3]. All-article (secondary) at 150 is within 0.2 pp of fit-only.
Reading: the allocation-failure gap is significant in every model at B=50 (ELR and EA) and in
every model at B=150 on EA; on ELR at 150 it is significant for 14B and GPT and borderline for 8B
(lower bound exactly 0.0), consistent with 8B's blind−aware ELR difference being ~0 at 150.

### 2026-09-19 — P2-4 Blind + Candidate Metadata (written before generation)
Question: how much of the residual Blind−Aware / Oracle−Blind gap at B >= 50 is
candidate-identity / semantic-disambiguation ambiguity rather than write-time
allocation under an unknown query?
- New arm `blind_meta` (exp `meta`, scripts/run_phase4.py): the Blind prompts
  are byte-identical to ①; only M0 changes. Each span of the multi material is
  prefixed with the identity of the comparison it was annotated for,
  `[Intervention: I | Comparator: C | Outcome: O]`, in the SAME per-article
  order as ① (verified 294/294). No direction, no significance, no indication
  of which candidate is the eventual target. Later steps receive only the
  previous memory, as in ①.
- Blind/multi, B = 150 primary (Oracle-All fits 98–99 %), B = 50 secondary;
  294 articles, 3 models, enforced cap, depth 5, seed 42.
- Comparisons, same articles, paired article bootstrap B=2,000 seed 42, ELR
  primary and warrant secondary: Blind+Meta − Blind; Aware − Blind+Meta;
  Oracle-All(short) − Blind+Meta on the fit-only subset. Forced-truncation
  rate beside every number.
- Reading rule fixed now (on ELR at B=150): (a) Blind+Meta − Blind CI excludes 0
  AND Aware − Blind+Meta CI covers 0 -> the residual is mostly candidate
  identity / semantic ambiguity; (b) both CIs exclude 0 -> disambiguation and
  allocation both contribute; (c) Blind+Meta − Blind CI covers 0 AND
  Oracle − Blind+Meta CI excludes 0 -> allocation/compression interpretation
  strengthened. Any outcome is reported as-is.

### 2026-09-19 — GPT-5.4-mini repeated-run robustness (written before generation)
Asymmetry: Qwen has seed robustness (S100, seeds 143/244), GPT has one run.
GPT-5.4-mini is a reasoning model whose sampling is fixed by the API (seed is
not honoured); the `seeds` experiment is therefore run for GPT as two
additional INDEPENDENT runs (cache keys tagged 143/244, same S100 subset,
2x2 x B in {25, 50, 150}) and reported as run-to-run variability of the DiD,
never as seed control. Same analysis as results/phase4_seeds_report.txt.

### 2026-09-19 — P2-4 outcome (all three models scored; results/meta_summary.csv, scripts/analyze_meta.py)
Blind+Meta − Blind (ELR / WP), paired article bootstrap, n=294:
  B=150  8B −1.7 [−5.4, +2.0] / +2.0 [−2.0, +6.1];  14B +0.7 [−3.1, +4.4] / +5.1 [+0.7, +9.5];  GPT −0.7 [−4.4, +2.7] / −0.7 [−5.4, +4.1]
  B=50   8B +2.4 [−2.0, +6.8] / +1.7 (n.s.);  14B −0.7 (n.s.) / −0.3 (n.s.);  GPT −4.8 [−10.2, +0.3] / −5.1 [−10.5, +0.0]
Aware − Blind+Meta (ELR) at 150: +2.0 (n.s.) / +6.5 [+3.1, +10.2] / +5.4 [+1.0, +9.9] — indistinguishable from Aware − Blind
(+0.3 / +7.1 / +4.8). Oracle-All − Blind+Meta on the fit-only subset at 150 (n≈289): +4.8 [+1.0, +9.0] /
+6.9 [+2.8, +11.1] / +8.6 [+4.5, +13.1], all exclude 0, same size as Oracle − Blind (+3.5 / +7.3 / +7.9).
Forced truncation Blind/Meta/Aware at 150: 24/20/14 (8B), 45/47/29 (14B), 49/56/20 (GPT); both-untruncated
subsets give the same null (ELR −2.5 / +3.2 / +1.7, all n.s.).
Reading per the fixed rule: outcome (c) in every model on ELR — candidate identity does not close the gap and
the oracle gap survives -> the residual at B >= 50 is write-time allocation under an unknown query, not
candidate-identity / semantic ambiguity. The one memory-level gain (14B WP +5.1) does not reach the final answer.

### 2026-09-19 — GPT-5.4-mini 3-run robustness (results/phase4_seeds_report.txt, results/phase4_seeds_summary.csv)
S100 subset, enforced cap, DiD per run (42 = main run; the API does not honour seeds, so 143/244 are independent re-runs).
  B=25   SR −16/−16/−13 (mean −15.0 ± 1.7)   warrant −23/−30/−28 (mean −27.0 ± 3.6)
  B=50   SR −21/−23/−30 (mean −24.7 ± 4.7)   warrant −35/−36/−37 (mean −36.0 ± 1.0)
  B=150  SR −11/−6/−8   (mean −8.3 ± 2.5)    warrant −11/−16/−10 (mean −12.3 ± 3.2)
All 9 DiDs negative and the same sign as the main run; run-to-run SD (1–5 pt) is well below the effect at every budget.
GPT now matches the 8B/14B robustness table: the Blind-vs-Aware gap is not a single-run artefact.

### 2026-09-29 — P3 Truncation / compliance by factorial cell at B=25 (no generation)
Reviewer attack: "the Blindness effect is a budget-compliance / truncation artefact".
scripts/analyze_truncation_cells.py reads the step records of the ① enforced-25 chains
(n=294 per cell): chain-level forced-truncation rate, truncation of the memory actually read
(M4), natural compliance (share of writes <= B as generated), mean realized length before
enforcement; the Blindness x Competition interaction on each of them (paired article bootstrap);
and the ELR / WP interaction (a) adjusted for truncation in the GEE and (b) on the articles whose
M4 was untruncated in all four cells. Reported as-is whatever the direction.

### 2026-09-29 — P2-4b Blind + Candidate Metadata at B=25 (written before generation)
Gap: the metadata control exists at B in {50, 150} only, while the primary stress result is at 25.
- Arm `blind_meta`, exp `meta`, UNCHANGED code and prompts (scripts/run_phase4.py); only
  `--budgets 25,50,150` instead of `50,150`. 50/150 are replayed from cache and must reproduce
  the 2026-09-19 rows byte-for-byte (checked against results/backup_pre_meta25/); only 25 is new.
  294 articles, multi material, 3 models, enforced cap, depth 5, seed 42.
- Generator weights re-downloaded after the 2026-09-28 cache wipe at the revisions that were
  `main` during the original runs (Qwen3-8B-FP8 220b46e3, Qwen3-14B-FP8 9a283b4a; both repos last
  modified 2025-07-26).
- Comparisons at B=25, same articles, paired article bootstrap B=2,000 seed 42, ELR primary and
  WP secondary: Blind+Meta − Blind; Aware − Blind+Meta; forced-truncation rate beside every
  number (scripts/analyze_meta.py, unchanged). Blind / Aware rows are the paper's enforced-25
  chains. No Oracle comparison at 25 (Oracle-All fits in 0 % of articles).
- Reading rule fixed now (ELR at B=25): (a) Blind+Meta − Blind CI covers 0 AND Aware − Blind+Meta
  CI excludes 0 -> "candidate-identity ambiguity alone does not explain the severe-capacity
  effect"; (b) Blind+Meta − Blind CI excludes 0 above 0 -> identity ambiguity contributes at 25
  and the size of the remaining Aware − Blind+Meta gap is reported; (c) Blind+Meta < Blind with
  CI excluding 0 -> the identity labels cost budget / M0 length at 25. In no case is the result
  read as evidence FOR allocation failure at 25: that regime is capacity-bound (P0-1).

### 2026-09-29 — P2-5 Candidate-wise independent warrant extraction (written before generation)
Question: can each model recover the warrant of every evidence item when it reads that item
ALONE, with no future query and no competition for memory? Separates (A) evidence-interpretation
failure from (B) loss during joint memory construction.
- Units: every candidate of the multi material of the 294 articles = 294 targets + 927
  distractors = 1,221 (span, ICO) pairs. Each span is shown alone under the usual header
  `Excerpts from source article [PMC{pmcid}]:`. The ICO is NOT shown (query-blind).
- Prompt (scripts/run_extraction.py, `EXTRACT_SYSTEM`): extract the evidential warrant; one
  record per finding in the span — Comparison, Outcome, Effect direction (Increase / Decrease /
  No Difference / Uncertain), Statistical status (Significant / Not Significant / Unclear); do
  not infer beyond the evidence. One call per candidate, temperature 0.7, seed 42, max 256
  tokens, no budget instruction, nothing truncated. Cache cache/extraction_{model}.jsonl.
- Scoring, primary: the frozen evaluator v3 reads the extraction against that candidate's own
  ICO (same criterion as Warrant Preservation): outcome identified (direction != NOT_MENTIONED),
  direction correct (direction == gold), full warrant (direction == gold AND ASSERTED); statistical
  status = ASSERTED given direction correct. Secondary, evaluator-free: the parsed Effect-direction
  / Statistical-status fields of single-record extractions against the gold label.
- Populations: targets (n=294; every target is evaluator-eligible by construction) primary;
  all evaluator-eligible candidates (targets + the 811 grounded distractors), article-weighted,
  secondary; all 1,221 reported for completeness.
- Comparisons, paired by article, bootstrap B=2,000 seed 42 (targets): Independent full warrant −
  Blind/Multi WP at B = 25, 50, 150; − Blind/Single WP; − Aware/Multi WP. The M0 ceiling (evaluator
  on the raw span) is 100 % for targets by construction.
- Also reported: token length of the extraction, and whether the K extractions of an article
  would jointly fit in B (25 / 50 / 150) — i.e. whether the independently recoverable warrants
  are a feasible memory at that budget.
- Reading rule fixed now: independent full-warrant accuracy >= 85 % with Independent − Blind/Multi
  CI excluding 0 -> "evidence-interpretation failure is reduced as an alternative explanation;
  substantial degradation arises during joint memory construction". Accuracy < 75 % -> the
  interpretation-failure explanation is NOT reduced and is reported as a limitation. Between:
  reported with the per-stage breakdown and no mechanism claim. At B=25 the comparison is
  confounded by capacity (one write vs four capped rewrites) and is stated as such; B=150 is the
  capacity-unconstrained comparison. Never worded as proof of allocation failure.

### 2026-09-29 — P3 outcome (scripts/analyze_truncation_cells.py, results/truncation_cells_b25.csv, docs/table_truncation_cells.tex)
Enforced 25, n=294 per cell, order Aware-S / Blind-S / Aware-M / Blind-M.
  Forced truncation (chain)   8B 63.3 / 61.6 / 62.6 / 73.1   14B 90.1 / 90.1 / 94.2 / 99.3   GPT 88.4 / 88.1 / 90.8 / 99.0
  Natural compliance (write)  8B 59.6 / 67.6 / 61.6 / 68.4   14B 29.8 / 42.4 / 29.4 / 35.4   GPT 33.8 / 37.5 / 34.5 / 24.4
  Length before enforcement   8B 24.9 / 23.8 / 24.5 / 25.2   14B 31.1 / 30.2 / 31.7 / 35.4   GPT 28.9 / 28.5 / 29.2 / 31.3
  M4 (memory read) truncated  8B 32.7 / 21.8 / 28.9 / 16.0   14B 62.6 / 46.3 / 61.9 / 52.0   GPT 56.1 / 50.0 / 54.1 / 61.9
Interaction on the forced-truncation rate: +12.2 [+3.7, +20.4] (8B), +5.1 [+0.7, +9.5] (14B), +8.5 [+4.4, +12.9]
(GPT) — small next to the 60–99 % base rates but NOT zero: Blind/Multi is the most-truncated cell in every model.
On M4 truncation the interaction is −2.0 (n.s.) / +6.5 (n.s.) / +13.9 [+4.4, +24.1].
Adjusting the GEE for truncation leaves the blind:multi coefficient unchanged (ELR 8B −1.05 -> −1.05, 14B −0.71 ->
−0.69, GPT −0.56 -> −0.53; WP −1.30 -> −1.30, −1.11 -> −1.10, −1.22 -> −1.19); the truncation covariate itself is
n.s. except 14B ELR (p = 0.06). Articles whose M4 was untruncated in all four cells: 8B n=126, ELR DiD −14.3
[−23.8, −4.8], WP −17.5 [−27.8, −7.9]; 14B n=25 (ELR −12.0 [−32, +12], WP −16.0 [−44, +8]); GPT n=25 (ELR −12.0
[−40, +20], WP −32.0 [−56, −4]). Reading: budget compliance differs modestly across cells and does not account
for the interaction in 8B (clean subset + P0-2) and GPT (P0-2); for 14B the evidence is the covariate adjustment
only (clean subset n=25, P0-2 n.s. under selection) and is worded accordingly.

### 2026-09-29 — P2-4b outcome: Blind + Candidate Metadata at B=25 (results/meta_summary.csv, docs/table_meta25.tex)
Replay check: generation rows at 50/150 identical to 2026-09-19 (588/588 per model). The evaluator re-read of the
replayed rows changed 3 (8B mem), 10 (14B final) and 35 (GPT mem) verdicts, because cache/classifier_scoring.jsonl
holds duplicate keys with conflicting responses (24,178 duplicate writes, 987 with a different verdict); the
committed 50/150 verdict files were therefore restored unchanged and only the B=25 rows are new (today's re-read is
kept in results/backup_pre_meta25/rescored_20260929_*). Blind / Aware at 25 use the paper's verdicts
(scripts/addexp_common.py). Known inconsistency left as found: the committed meta_summary.csv of 2026-09-19 reported
GPT WP Blind+Meta − Blind −5.1 (B=50) / −0.7 (B=150); the committed verdict files give −2.7 / −0.3 (all CIs cover 0).
Blind+Meta − Blind at B=25, n=294 (ELR / WP):
  8B  +4.4 [−0.7, +9.5] / +3.7 [−1.7, +9.5];  14B −3.1 [−8.5, +2.4] / +0.0 [−5.8, +5.4];  GPT +1.7 [−3.4, +7.1] / +1.0 [−4.8, +6.8]
Aware − Blind+Meta at B=25 (ELR / WP):
  8B +13.3 [+8.2, +18.7] / +28.9 [+23.5, +34.0];  14B +23.5 [+18.0, +29.3] / +39.1 [+33.3, +45.2];  GPT +16.3 [+10.5, +22.1] / +38.1 [+32.0, +44.6]
(Aware − Blind: +17.7 / +20.4 / +18.0 ELR.) Forced truncation Blind/Meta/Aware: 73/67/63, 99/100/94, 99/100/91.
Reading per the fixed rule: outcome (a) in every model — candidate-identity ambiguity alone does not explain the
severe-capacity effect. Caveat kept: 8B is the closest to a benefit (lower bound −0.7; exploratory both-untruncated
subset n=52: ELR +11.5 [+1.9, +23.1]), so the wording is "does not close the gap", not "has no effect".

### 2026-09-29 — P2-5 outcome: candidate-wise independent extraction (results/extraction_summary.csv)
Full warrant of the independent structured extraction, frozen evaluator, targets n=294:
  8B 75.2 [70.1, 79.9]   14B 78.2 [73.1, 82.7]   GPT 76.5 [71.8, 81.3]
  (outcome identified 85.4 / 86.1 / 87.1; direction correct 75.9 / 78.6 / 78.2; status given direction 99.1 / 99.6 / 97.8;
   eligible candidates, article-weighted: 78.6 / 79.6 / 78.9)
Independent − Blind/Multi WP: B=25 +16.0 [+9.5, +22.8] / +31.3 [+24.8, +37.8] / +23.8 [+16.3, +31.0];
B=150 −12.9 [−18.4, −7.5] / −6.1 [−12.2, −0.3] / −7.1 [−13.3, −1.0].
Reading per the fixed rule: 75–85 % -> the "between" case: per-stage breakdown reported, NO mechanism claim. The
prediction behind the experiment (independent accuracy far above the joint memory) holds only at B=25, where the
comparison is capacity-confounded, and is REVERSED at B=150.
Post-hoc diagnosis (not pre-registered): the structured record format is a lossy measurement. 13–15 % of targets
are scored NOT_MENTIONED because the records rename the groups / outcome and the evaluator cannot link them to the
ICO; 12–14 % of extractions carry a directional record marked Not Significant (the gold scheme calls that
NO_DIFFERENCE). Evaluator-free, the parsed records contain the gold label for 85.7 / 85.4 / 85.7 % of targets
(92–94 % allowing a reversed comparison orientation). The existing free-form query-blind single-item cell is the
cleaner interpretation reference: Blind/Single at B=150 (forced 0–2 %) WP 92.9 / 93.2 / 92.9, ELR 97.6 / 95.6 / 96.3,
against Blind/Multi 88.1 / 84.4 / 83.7 WP at the same budget.
Extraction length: 57–65 tokens per candidate, 236–270 per article; the K extractions fit jointly within 150 tokens
in 18–29 % of articles and never within 25 or 50.

### 2026-09-29 — P2-5b Candidate-wise FREE-FORM independent memory (POST-HOC; written before generation)
Status: post-hoc. Designed after the P2-5 outcome was seen (structured records scored 75–78 % and the record format
turned out to be a lossy input for the evaluator). Must be labelled post-hoc wherever it is reported. The target
values of the depth-matched arm are already known (they are the paper's Blind/Single cells at B=150: WP 92.9 /
93.2 / 92.9); what is new is every distractor candidate, the one-write memory, and the candidate-level joint memory.
- Independent arm: every candidate (294 targets + 927 distractors) is written ALONE with the UNCHANGED Blind prompts
  (BLIND_SYSTEM / BLIND_USER, no query), B = 150, enforced cap, depth 5 (four rewrites), temperature 0.7, seed 42 —
  i.e. the paper's Blind/Single chain applied to every candidate. Target chains are replayed from the paper's cache
  (cache/extra_hard_{model}.jsonl) and must reproduce the Blind/Single/150 memories; distractor chains are new
  (cache/extraction_{model}.jsonl). Both M1 (after one write) and M4 (after four rewrites, depth-matched to the
  joint memory) are scored.
- Joint arm: the Blind/Multi M4 memory at B=150 of the same article (paper's enforced chains, no generation) is
  scored against EVERY candidate's own ICO, not only the target's.
- Scoring: frozen evaluator v3, each text against the candidate's own ICO; outcome identified / direction correct /
  full warrant as in tab:warrant_stages. Target verdicts that already exist in the committed files
  (results/phase4_budget_{model}_mem_scored.csv) are used as committed, not re-read.
- Populations: evaluator-eligible candidates (294 targets + 811 grounded distractors), article-weighted, primary;
  targets and eligible distractors separately; all 1,221 for completeness.
- Comparison: Independent (M4, depth-matched; M1 secondary) − Joint full warrant, candidate differences averaged
  within article, article bootstrap B=2,000 seed 42. Forced-truncation rates beside every number.
- Reading rule fixed now (eligible candidates, M4): Independent >= 85 % AND Independent − Joint CI excluding 0 ->
  "evidence-interpretation failure is reduced as an alternative explanation; part of the warrant loss arises when
  the items must share one memory". Independent < 75 % -> not reduced. Otherwise per-stage numbers only. B=150 only:
  at 25 / 50 the K independent memories are not a feasible joint memory, so no claim is made there. Never worded as
  proof of allocation failure.

### 2026-09-29 — P2-5b outcome (POST-HOC; results/freeform_summary.csv, docs/table_freeform.tex, scripts/analyze_freeform.py)
Replay check: target chains 294/294 identical to the paper's Blind/Single/150 memories in every model; committed
target verdicts used (re-read differed in 0 rows). Independent chains forced 1.4 / 2.2 / 1.1 %; joint Blind/Multi
memories forced 24.5 / 44.9 / 49.3 %. Independent memory length 63–72 tokens.
Complete warrant, evaluator-eligible candidates (n=1,105, article-weighted), B=150, 8B / 14B / GPT:
  Independent, one write (M1)      94.6 [92.8, 96.3]   93.8 [92.1, 95.3]   94.2 [92.6, 95.8]
  Independent, four rewrites (M4)  92.2 [90.1, 94.3]   93.6 [91.8, 95.3]   93.6 [91.7, 95.4]
  Joint Blind/Multi (M4)           85.1 [82.6, 87.5]   84.1 [81.7, 86.6]   82.3 [79.5, 85.0]
  Independent M4 − Joint           +7.2 [+4.5, +9.9]   +9.5 [+6.9, +12.2]  +11.3 [+8.5, +14.3]
Targets (n=294): Independent M4 92.9 / 93.2 / 92.9, Joint 88.1 / 84.4 / 83.7, difference +4.8 [+0.3, +9.2] /
+8.8 [+4.1, +13.6] / +9.2 [+4.4, +13.9]. Eligible distractors (n=811): +8.0 / +9.7 / +12.7, all CIs exclude 0.
By K (eligible, independent vs joint): 8B K=3 91.6 vs 88.9, K=4 92.1 vs 83.8, K=5 93.9 vs 84.4; 14B 94.7 vs 87.2,
95.2 vs 87.6, 93.9 vs 81.0; GPT 91.6 vs 87.6, 96.6 vs 84.8, 94.6 vs 77.9.
Reading per the fixed rule: Independent >= 85 % and the CI of Independent − Joint excludes 0 in every model ->
evidence-interpretation failure is reduced as an alternative explanation; part of the warrant loss arises when the
items must share one memory.
Caveat that must travel with the claim: on the articles where neither the joint memory nor any independent chain was
ever truncated the difference shrinks to +3.9 [+1.0, +6.8] (8B, n=214), +3.9 [+0.4, +7.2] (14B, n=160) and
+2.3 [−0.9, +5.5] (GPT, n=149, n.s.). Most of the joint loss at 150 tokens therefore coincides with joint memories
that overflowed the budget and were cut (a selected, easier subset remains when they are removed). The result
separates "cannot interpret the item" from "loses it when writing jointly"; it does not separate allocation from
overflow/truncation, and the 25-token regime is untouched by it.

### 2026-09-29 — Canonical evaluator record (no generation, no scoring)
The committed results/*_scored.csv files are the canonical record, collected unchanged in
results/canonical_results.csv (288,061 rows; manifest results/canonical_manifest.json). Evaluator test-retest from the
24,178 items judged twice: 95.9 % agreement. cache/classifier_scoring.jsonl is now duplicate-free
(scripts/build_canonical.py); committed rows are never re-scored. All 14 committed summary files regenerate
cell-for-cell from the committed verdicts; the only exception is meta_summary.csv (GPT-5.4-mini WP at B=50 / 150:
Blind+Meta − Blind is −2.7 [−8.2, +2.0] / −0.3 [−4.4, +4.1], not −5.1 / −0.7 as written on 2026-09-19; ELR unchanged).

### 2026-09-29 — P4 Held-out replication (written before generation and before target verification)
Question: does the main qualitative pattern replicate on articles that were never used?
- Cohort: Evidence Inference 2.0 VALIDATION + TEST articles (892; disjoint from train and from every article used so
  far, asserted in scripts/build_heldout.py). Selection = scripts/build_gate2.py unchanged (span filters, unanimity,
  >= 3 usable prompts, target stratification rule, seed 42): 429 candidate articles. Targets kept iff the frozen
  evaluator recovers the gold label from the gold span, first 100 per label in candidate order (the gate2_v1 rule).
  Output data/heldout/heldout_v1.jsonl. No article is dropped after generation.
- Arms, all three models, enforced cap, depth 5, seed 42, unchanged prompts and chain code (run_phase4.chain):
  B=25 Aware/Blind x Single/Multi (primary); B=150 Aware/Multi, Blind/Multi and Oracle-All (short format, target
  read; fit-only subset primary, as in P0-1). Cache cache/heldout_{model}.jsonl.
- Outcomes and statistics exactly as the main grid: ELR (final) primary, WP (memory M4) secondary; probability-scale
  Blindness x Competition DiD with paired article bootstrap B=2,000 seed 42; GEE blind*multi clustered by article;
  forced-truncation rate per cell. At 150: Blind − Aware (Multi) and Oracle-All − Blind (fit-only), paired.
- Replication rule fixed now: the pattern "replicates in model X" iff the held-out ELR DiD at B=25 is negative with a
  95 % CI excluding 0. The sentence "the main qualitative pattern replicates on held-out articles" is used only if
  this holds in all three models; otherwise the models are named. Size is compared with the main cohort
  (−16.3 / −15.0 / −11.6) descriptively; no equivalence claim. B=150 results are secondary and reported as-is.

### 2026-09-29 — P4 outcome: held-out replication (results/heldout_summary.csv, docs/table_heldout.tex, scripts/analyze_heldout.py)
Cohort: 429 candidate articles from validation + test, 369 grounded targets (86.0 %), 295 kept under the 100-per-label
cap (100 / 100 / 95; validation 148, test 147). No article dropped after generation; 0 dirty evaluator rows.
Enforced 25 tokens, n=295 per cell, order Aware-S / Blind-S / Aware-M / Blind-M, DiD with 95 % article bootstrap:
  ELR  8B   92.9 / 89.8 / 90.8 / 72.5   DiD −15.3 [−21.0, −9.8]    (main −16.3 [−22.4, −9.9])
       14B  87.8 / 84.4 / 90.2 / 66.1   DiD −20.7 [−27.1, −13.9]   (main −15.0 [−21.8, −8.5])
       GPT  88.1 / 81.0 / 88.1 / 66.8   DiD −14.2 [−21.7, −6.8]    (main −11.6 [−18.4, −4.4])
  WP   8B   91.2 / 79.0 / 91.5 / 59.0   DiD −20.3 [−27.5, −12.9]   (main −21.8)
       14B  85.8 / 72.9 / 88.8 / 46.4   DiD −29.5 [−36.9, −22.4]   (main −26.5)
       GPT  92.2 / 76.3 / 91.9 / 52.9   DiD −23.1 [−30.2, −15.6]   (main −24.8)
GEE blind:multi (ELR): −0.93 (p = 2e-4), −1.26 (p = 3e-6), −0.75 (p = 0.005). Per split the ELR DiD is negative with
a CI excluding 0 in all six model x split cells (test −17.0 / −16.3 / −17.0; validation −13.5 / −25.0 / −11.5).
Forced truncation: 8B 62.0 / 58.0 / 58.3 / 71.5 (interaction +17.3 [+8.1, +26.4]); 14B 90.5 / 89.5 / 94.2 / 99.7
(+6.4); GPT 90.2 / 89.2 / 92.9 / 99.0 (+7.1) — the same profile as the main cohort.
Replication rule: met in all three models -> "the main qualitative pattern replicates on held-out articles".
B=150 (secondary), Multi: Blind − Aware ELR −1.4 [−4.4, +2.0] (8B), −5.1 [−8.5, −1.7] (14B), −5.1 [−8.5, −2.0] (GPT);
WP −3.7 [−7.8, +0.0], −7.5 [−11.9, −3.1], −12.5 [−16.9, −8.8]. Oracle-All (short) fits in 295/295; Oracle − Blind ELR
+4.4 [+1.0, +7.8], +5.4 [+1.7, +9.2], +3.7 [+0.0, +7.5]; Oracle − Aware +3.1 [−0.3, +6.4], +0.3, −1.4 (all cover 0).
Same ordering as the main cohort (8B: no Blind − Aware ELR gap at 150; 14B and GPT: gap), oracle gaps somewhat
smaller than on the main cohort (+3.5 / +7.3 / +7.9).
