# Phase 6 pre-registration — reviewer-requested experiments (2026-11-21)

Written before any Phase-6 generation. Shared protocol as before: cohort gate2_v1 (294 articles), same three
generators, frozen evaluator v3 (canonical record of 2026-09-29; committed rows are never re-scored), paired article
bootstrap B=2,000 seed 42, GEE clustered by article. Order follows the reviewers' three core questions:
(1) does the problem exist at realistic memory capacity, (2) is it future-query blindness rather than hard truncation
or generic extraction error, (3) does the conclusion hold without the LLM judge. Driver scripts/run_rev.py, cache
cache/rev_{model}.jsonl, outputs results/rev_*. Infra: FP8 weights re-downloaded into a private HF cache at the
pinned revisions (8B 220b46e3, 14B 9a283b4a, 32B aa55da1e); scripts/rev_env.sh.

## E4 Judge-free ELR (direct label prediction)
The generator that wrote a memory reads it with the target question and outputs exactly one label: Increase /
Decrease / No-Difference / Uncertain (prompt LABEL_SYSTEM in scripts/run_rev.py; temperature 0, seed 42, max 8
tokens; GPT-5.4-mini at its fixed sampling). Judge-free ELR := label == gold. No evaluator call anywhere.
Applied to every stored memory (M4) of the enforced grid (B = 25, 40, 50, 150), the new large budgets (E1), the
truncation-free chains (E3) and the reference memories of E5 / E2.
Reported: four cells and the Blindness x Competition DiD at every budget, side by side with the judge-based ELR; row
agreement and Cohen's kappa between judge-supported and label-correct on the enforced-25 grid.
Reading rule: "the conclusion holds without the judge" in a model iff the judge-free DiD at B=25 is negative with a
95 % CI excluding 0. Reported per model, whatever the outcome.

## E5 Question-only and reference baselines
Same reader, same question, memory replaced by: nothing (question-only); Blind memory; Aware memory; gold Oracle-All
(short, untruncated) and Oracle-Target; Full Evidence (raw single span; raw multi material). Outcomes: judge-free
label for all; judge-based ELR of a natural-language answer for question-only (new), the rest from existing arms.
Question-only is run twice: with the four-way label set (how often the model commits without evidence) and as a
forced three-way guess (upper bound on what prior knowledge / exposure can give; chance = 1/3, labels 100/100/94).
Reading rule: if forced-guess accuracy is within 10 pp of chance, memory-free answering is not a viable explanation
of the ELR levels (86–90 % aware). A high value would not prove contamination and is reported as a limitation.

## E3 Hard-truncation confound
(a) Forced-truncation rate, natural compliance and realized length for all four cells at every budget
(25, 40, 50, 150 from the committed chains; 256, 512, 1024 from E1). No generation.
(b) Truncation-free chains on the FULL cohort (294 instead of S100): the Phase-5 P0-2 protocol unchanged
(regenerate until <= B, adaptive instructed budget, <= 20 attempts, never cut; S100 rows replay from cache),
B = 25 and 50, three models. Failure rate per cell reported separately. Analyses: complete-case DiD (articles
whose four cells all succeeded), and a conservative bound in which every failed chain is imputed against the
hypothesis (failed Blind/Multi and Aware/Single = supported, failed Aware/Multi and Blind/Single = unsupported).
Judge-based ELR / WP and judge-free ELR.
Reading rule: truncation is rejected as the explanation in a model iff the complete-case ELR DiD at B=25 is negative
with CI excluding 0; the bound is reported beside it. (S100 result known: 8B −20.2, GPT −19.0 survive, 14B −4.0 n.s.
with 14–34 % failures; the full cohort is run to settle 14B either way.)
(c) The large budgets of E1 are a second truncation-free regime by construction (see E1).

## E1 Larger memory budgets
Unchanged enforced chain (run_phase4.chain, depth 5, seed 42), Aware/Blind x Single/Multi, B = 256, 512, 1024,
294 articles, three models. Outcomes ELR, WP (M4), DiD, GEE, forced-truncation rate, realized memory length, and the
Oracle-All fit rate (short and full format) at each B.
Predictions written now: Oracle-All fits 100 % at B >= 256; forced truncation < 5 % at B >= 512; realized memory
length saturates well below B (the multi material is ~229 tokens). The paper's claim is about constrained memory, so
the expected outcome is that the ELR interaction shrinks toward 0 as B grows; whether a residual Blind − Aware gap
remains on Multi at 256–1024 is the open question and is reported as-is. If the interaction is absent at B >= 256
the paper must state the effect as a constrained-capacity phenomenon with its measured range (25–150).

## E2 Oracle comparison: generic extraction error vs blindness
Four memories for the same target question, same reader, same budget B in {150, 256, 512, 1024}:
  Gold Oracle-All   gold-derived lines (P0-1, short), no model involved in writing
  Model Oracle-All  the same model's own query-blind memories of each candidate written ALONE (the P2-5b chains:
                    unchanged Blind prompts, four rewrites = depth-matched to the joint memory; one-write M1 as
                    sensitivity), concatenated in the article's span order. No competition for space, no future query.
  Aware memory      enforced chain, Multi
  Blind memory      enforced chain, Multi
Model Oracle-All "fits" iff its token length <= B; the fit-only subset is primary (as in P0-1), paired.
Decomposition on that subset (ELR, judge-based and judge-free):
  Gold Oracle − Model Oracle  = generic extraction / rewriting error without competition and without a query
  Model Oracle − Blind        = additional loss when the same items must be written jointly under an unknown query
  Aware − Blind               = value of knowing the query at write time
Reading rule: blindness-related loss is separated from generic extraction error at budget B iff Model Oracle − Blind
is positive with CI excluding 0 on the fit-only subset. Limits stated now: Model Oracle-All controls the writer and
the input but not the amount of text (it is longer than the joint memory), so at budgets where the joint memory was
truncated the contrast still includes overflow; B >= 512 (no truncation expected) is the clean regime.

## Not run in this round
E6 (local context / full document), E8 (external dataset), E9 (more models), E10 (reasoning effort), E11 (clinician
raters), E12 (mitigation). E7: the memory-level human audit already exists (144 items, agreement 88.2 %, kappa 0.71);
E4 supplies the judge-independent check.

# Outcomes (2026-11-21; all three models generated and scored, 0 dirty evaluator rows, 0 unparsed labels)
Text dumps: logs_addexp/rev_{labels,bigbudget,notrunc,modeloracle,trunc}.txt; tables results/rev_*_summary.csv.

## E4 outcome — judge-free ELR
Judge-free DiD at B=25: 8B −11.6 [−18.7, −4.1], 14B −21.8 [−28.2, −15.3], GPT −13.6 [−22.1, −4.4]
(judge-based −16.3 / −15.0 / −11.6). Rule: HOLDS in all three models. Also negative with CI excluding 0 at B=40 in all
three (−13.9 / −12.9 / −30.6) and at B=50 for 14B and GPT (−8.2 / −28.2; 8B −5.4 n.s.).
Caveat: the label reader is the generator itself and its labelling skill differs. From the raw evidence the direct
label is right in 73.1 / 91.8 / 89.8 % (single span) and from gold Oracle-Target in 99.7 / 100 / 99.7 %; Qwen3-8B
over-predicts Increase (42–45 %) and agrees poorly with the judge (kappa 0.13–0.32; 14B 0.33–0.61; GPT 0.44–0.51).
The 8B judge-free levels are therefore not comparable with its judge-based levels; only the contrasts are read.

## E5 outcome — question-only
Four-way label with no notes: Uncertain in 100 % of items, all models. Forced three-way guess: 40.1 / 52.4 / 62.2 %
(chance 33.3). Natural-language answer with no notes, judged by the evaluator: ELR 32.0 / 50.0 / 23.1 %.
Rule: only 8B is within 10 pp of chance; for 14B and GPT memory-free answering is NOT negligible and is reported as a
limitation (question wording carries a prior on the direction; 14B commits to a direction in 67 % of memory-free
answers). The question is identical in the four cells of the factorial, so this floor cannot create the interaction,
but it does inflate absolute ELR levels, most in the low-information cells.

## E3 outcome — truncation
(a) Forced truncation in Blind/Multi: 73–99 % at 25, 24–49 % at 150, 7–17 % at 256, <= 1 % at 512 and 1024.
(b) Truncation-free chains, full cohort. Failure rates at B=25 (A-S / B-S / A-M / B-M): 8B 2.7 / 7.5 / 2.0 / 4.1,
14B 14.6 / 27.9 / 13.3 / 20.1, GPT 0 / 0 / 0 / 0; at B=50 <= 1 % everywhere.
  B=25 complete-case ELR DiD: 8B −15.7 [−22.4, −9.8] (n=255), 14B −8.1 [−13.8, −2.5] (n=160), GPT −15.0 [−21.1, −9.2]
  (n=294). Rule: truncation is rejected as the explanation in all three models. Conservative bound: GPT −15.0 (no
  failures), 8B −6.5 [−13.3, +0.3] (borderline), 14B uninformative (+32.7; 13–28 % failures) — for 14B the B=25 claim
  rests on the complete cases only. WP: −14.5 [−22.4, −6.7] / −10.0 [−18.1, −1.9] / −17.0 [−23.5, −10.5].
  B=50 (failures <= 1 %, bound = complete case): ELR 8B −6.1 [−11.3, −1.0], 14B −12.1 [−17.0, −7.3], GPT −6.5 [−11.6, −1.4];
  enforced on the same articles −6.1 / −14.5 / −20.7 — two thirds of GPT's enforced B=50 interaction was truncation,
  the remainder is significant.
  Judge-free ELR, truncation-free, B=25: −12.9 [−20.0, −5.5] / −10.6 [−18.8, −2.5] / −19.7 [−27.6, −11.9].

## E1 outcome — larger budgets
Oracle-All (short) fits 99.7 % at 256 and 100 % at 512 / 1024. Realized Blind/Multi memory 152–175 tokens at 256 and
195–260 at 512–1024 (never near the cap).
ELR DiD (judge): 256: −2.7 / −2.0 / +2.7; 512: −1.7 / +1.0 / +3.1; 1024: −0.7 / +1.7 / −1.4 — every CI covers 0.
Blind − Aware on Multi (judge ELR) is within ±1.7 pp at every B >= 256 in every model. WP: Blind − Aware on Multi
−5.1 [−8.8, −1.4] (256) and −3.4 [−6.8, −0.3] (512) for GPT only; otherwise n.s.
Judge-free: DiD n.s. except 14B at 512 (−5.4 [−10.2, −0.7]); a small Blind − Aware gap on Multi remains for 14B and
GPT (−4 to −5 pp) but a gap of the same size exists on Single, i.e. it is not competition-specific.
Reading (as pre-registered): the interaction is absent at B >= 256. The effect must be stated as a
constrained-capacity phenomenon with its measured range (B = 25–150; at 150 it is present for 14B and GPT only).

## E2 outcome — Gold vs Model Oracle-All
Model Oracle-All (M4) is 266–289 tokens long: it fits 4–7 % of articles at 150, 41–51 % at 256, 98 % at 512, 100 % at 1024.
Judge ELR on the fit-only subset, Gold Oracle / Model Oracle / Aware / Blind:
  512:  8B 96.2 / 92.4 / 94.1 / 94.1;  14B 96.2 / 93.7 / 94.1 / 93.7;  GPT 96.2 / 94.8 / 94.8 / 96.5
  1024: 8B 96.3 / 92.5 / 93.2 / 94.2;  14B 96.3 / 93.9 / 94.9 / 94.9;  GPT 96.3 / 94.9 / 95.2 / 94.6
Gold − Model (generic extraction error): +3.8 [+0.7, +7.3] / +2.4 [−1.0, +5.9] / +1.4 [−1.4, +4.5] at 512.
Model − Blind: −1.7 / +0.0 / −1.7 at 512, −1.7 / −1.0 / +0.3 at 1024; every CI covers 0 (also at 256).
Rule: blindness-related loss is NOT separated from generic extraction error at any budget where the comparison is
feasible — because at those budgets there is no blindness loss left to separate (E1). At B <= 150, where the effect
lives, the model's own non-competitive memories do not fit, so this design cannot decompose the effect there. What E2
does establish: with sufficient capacity the joint query-blind memory is as good as the same model's independent
per-item memories, and generic extraction error is 1–4 pp. The decomposition at constrained budgets remains the
earlier P2-5b result (post-hoc, truncation-confounded) and is still an open point for the reviewers.

---

# E13 Compression ratio (pre-registered 2026-11-22, before any generation)

Requested by the author after the E1 outcome: E1 raised the budget to 256 / 512 / 1024 tokens but the source
(the Multi material) is only ~229 tokens, so every budget >= 256 removed the compression pressure itself. E1
therefore cannot tell whether the interaction is tied to a small ABSOLUTE budget or to RELATIVE compression
pressure. E13 fixes the source at ~1,000 tokens and varies the budget.

## Material (built before this entry was written; no model output involved)
`scripts/build_longsource.py` -> `data/longsource/longsource_v1.jsonl`, all 294 cohort articles.
Long source = the home article's Multi material, exactly as in the main experiment, plus real annotated
evidence spans of OTHER cohort trials (each under its own `Excerpts from source article [PMC…]` header),
added trial by trial in a seeded order until the rendered material is 950–1,050 tokens (o200k_base reference
tokenizer). Nothing is padded, duplicated or paraphrased; every added span is a distinct annotated finding
with its own gold label. A trial sharing the home target's intervention and outcome is never added. Block
order is a seeded shuffle, so the home trial's position is random.
Realized: mean 1,011 tokens (950–1,050), 16.1 spans, 17.8 annotated findings, 4.5 trials per source;
target evidence starts in the first / middle / last third in 100 / 110 / 84 sources.
The task therefore becomes working notes accumulated over several trials (multi-document agent memory).

## Design
| Condition | Source | Budget | Nominal ratio |
|---|---|---|---|
| A | ~1,000 | 100 | 10 % |
| B | ~1,000 | 200 | 20 % |
| C | ~1,000 | 400 | 40 % |
| D | ~1,000 | 800 | 80 % |

Cells per budget: Aware / Blind x Single / Long, n = 294 each, depth 5 (4 rewrites + final answer), the three
generators, seed 42. Single is the unchanged target-only source (~70 tokens): at these budgets it is an
uncompressed pass-through control, kept so that the DiD has the same definition as in the paper.
Prompts are the frozen main-experiment prompts in every cell; only M0 differs.
Protocols: (1) enforced budget (primary; the protocol of the main grid and of E1); (2) truncation-free
(regenerate <= 20 attempts with the adaptive instructed budget, never cut; E3b protocol) on the same cells.
References (no hypothesis): final answer straight from the untruncated long source (ratio 100 % ceiling);
Gold Oracle-All length for the long source (fit rate per budget; no generation); realized ratio
(memory tokens / source tokens, model tokenizer); forced-truncation rate by cell.
Sensitivity (enforced, Long, B = 200 only): the blind prompt says "working notes about a clinical study";
a variant with "about one or more clinical studies" (mode blind_plural) checks that the singular wording
does not create the Blind loss. Reported as Blind_plural − Blind; not part of the rule.

## Outcomes and estimands
ELR (primary; final answer, frozen evaluator), WP (memory M4, frozen evaluator), judge-free ELR (direct label
by the generator, E4 protocol). Per budget: G_long = Blind − Aware | Long; DiD = G_long − (Blind − Aware | Single);
paired article bootstrap (B = 2000, seed 42). Dose–response contrast: DiD(100) − DiD(800), same bootstrap.
Truncation-free: complete-case DiD + the conservative imputation bound of E3b.

## Reading rule
"Present at B in a model" = ELR DiD < 0 with a 95 % CI excluding 0 under the enforced protocol.
"Robust at B" = also present in the truncation-free complete cases. A budget counts for the paper when it is
present in >= 2 of 3 models. Three accounts make different predictions (Gold Oracle-All for ~18 findings is
expected to need roughly 200–300 tokens):
- ABSOLUTE budget (effect only when the memory is small in absolute terms; E1 null at >= 256 read literally):
  present at most at 100; absent at 200, 400, 800.
- CAPACITY (effect while a lossless record of all candidates does not fit): present at 100 and 200, absent
  where Oracle-All fits (400, 800).
- RELATIVE pressure (effect whenever the source must be compressed, even if a lossless record would fit):
  present at 100, 200 and 400, attenuated at 800.
Decision: present at 200 or 400 in >= 2 of 3 models -> the E1 null is attributed to missing compression
pressure and the paper may state the effect as a function of compression pressure (capacity form if only up
to 200, relative form if also at 400). Present only at 100 or nowhere -> the absolute-budget scope (25–150
tokens) stands and E13 is reported as a negative result. If a budget is present under the enforced protocol
but not robust, the effect at that budget is attributed to hard truncation, not to blindness.
A significant DiD(100) − DiD(800) < 0 is required before the word "dose–response" is used.
Judge-free ELR and WP are reported next to ELR; disagreement in sign is reported, not resolved post hoc.

## Known limits (stated in advance)
The added competitors come from other trials, so they are topically farther from the target than the
same-article distractors of the main grid; Aware can discard them easily. Single vs Long differs in both
length and number of findings (no 1,000-token non-finding filler control in this round). Filler trials are
reused across sources, which the article-level bootstrap does not model.

## E13 outcome (2026-11-22) — Qwen3-8B and Qwen3-14B only
GPT-5.4-mini was NOT completed: the OpenAI account ran out of credits during the enforced arm
(`insufficient_quota`; 12.2k of ~20k intermediate rewrites are cached in `cache/ratio_gpt-5.4-mini.jsonl`, no
finals). All Qwen rows generated and scored: 0 dirty verdicts, 0 unparsed labels, 0 truncation-free failures.
Full dump: `logs_addexp/ratio_analysis.txt`; tables `results/ratio_summary.csv`, `results/ratio_design_summary.csv`.

Design check (8B / 14B): long source 1,121 model tokens; Gold Oracle-All 311 tokens, fits 0.3 % at 100, 4.8 % at
200, 88.1 % at 400, 100 % at 800. Forced truncation in Blind/Long: 54 / 95 % at 100, 55 / 87 % at 200, 52 / 74 %
at 400, 14 / 16 % at 800 (Aware/Long <= 17 %). Untruncated long source, judged answer: ELR 90.8 / 93.5.

ELR DiD, judge-based (8B / 14B):
| B (ratio) | enforced | truncation-free |
|---|---|---|
| 100 (10 %) | −33.7 [−40.1, −27.6] / −47.6 [−54.4, −40.8] | −30.3 [−36.4, −24.1] / −29.9 [−36.1, −23.5] |
| 200 (20 %) | −28.9 [−35.4, −23.1] / −36.7 [−43.5, −29.9] | −23.5 [−29.3, −18.0] / −23.8 [−29.9, −18.0] |
| 400 (40 %) | −15.6 [−22.1, −9.2] / −13.6 [−19.4, −7.8] | −7.8 [−13.6, −2.0] / −3.7 [−8.8, +0.7] |
| 800 (80 %) | −5.8 [−10.9, −1.0] / +3.1 [−1.7, +7.8] | −4.8 [−9.5, +0.0] / +3.4 [−1.4, +8.2] |
Dose–response contrast DiD(100) − DiD(800): enforced −27.9 [−36.1, −20.1] / −50.7 [−58.2, −42.5]; truncation-free
−25.5 [−33.0, −17.7] / −33.3 [−41.2, −25.8].
WP DiD, truncation-free: −45.2 / −43.5 at 100, −26.9 / −33.3 at 200, −7.5 [−12.9, −2.0] / −8.5 [−14.6, −2.7] at
400, +0.3 / +2.0 (n.s.) at 800. Judge-free ELR DiD, truncation-free: −36.1 / −33.0, −34.4 / −19.7, −23.8 / −9.9,
−19.4 [−26.9, −11.9] / −7.8 [−13.9, −2.0] (all CIs exclude 0).

Reading rule: present at 100, 200 and 400 in both Qwen models (2 of 3 -> counts for the paper), at 800 in 8B only.
Robust (truncation-free) at 100 and 200 in both, at 400 in 8B only, at 800 in neither.
-> The E1 null at >= 256 tokens is attributed to missing compression pressure, not to an absolute budget
threshold: with a 1,000-token source the interaction is large at 200 tokens and still present at 400 under the
enforced protocol. The robust range coincides with budgets where Gold Oracle-All does not fit (CAPACITY form);
at 400 (Oracle-All fits 88 %) a residual remains (ELR robust in 8B only; WP and judge-free robust in both), so the
RELATIVE form is only partly supported. At 800 the judge-based effect is gone.
-> Truncation share: for 14B the truncation-free DiD is 63 % / 65 % / 27 % of the enforced DiD at 100 / 200 / 400
(8B 90 % / 81 % / 50 %); the part of the 400-token effect in 14B that exceeds the truncation-free estimate is
attributed to hard truncation, per the rule.
-> "Dose–response" may be used (contrast significant in both models, both protocols).
Disagreement reported, not resolved: at 800 the judge-free DiD stays negative with CIs excluding 0 while the
judge-based DiD does not. The generator-as-reader is weak on long multi-trial notes (label from the untruncated
long source 52.0 % for 8B, 81.6 % for 14B, vs judged answers 90.8 / 93.5), so the judge-free gap at 800 mixes a
reading-difficulty component (long unfocused memory vs focused Aware memory) with information loss.
Sensitivity: plural blind wording at B=200, plural − frozen ELR +2.7 [−2.4, +7.8] / +0.3 [−4.1, +4.8] (n.s.; WP and
judge-free also n.s.).
EXPLORATORY (not pre-registered): under the enforced protocol the Blind − Aware gap is largest when the target
evidence sits in the last third of the source (14B: −67.9 at 100, −71.4 at 200, −34.5 at 400 vs −23.0 / −14.0 /
−6.0 in the first third), consistent with tail truncation inflating the enforced estimates.

Truncation-free arm, realized memory (added 2026-11-22; `results/ratio_notrunc_length_summary.csv`): failures 0 in
every cell. Mean M4 tokens, Long, Aware / Blind — 8B: 57 / 73 at 100, 114 / 153 at 200, 224 / 329 at 400, 384 / 586
at 800; 14B: 69 / 82, 128 / 170, 265 / 346, 520 / 637. Realized ratio of Blind/Long (memory / source): 8B 6.5 / 13.7 /
29.4 / 52.3 %, 14B 7.4 / 15.2 / 30.8 / 56.8 %. Attempts needed for the first Blind/Long write: 8B 3.9 / 2.7 / 2.4 / 1.1,
14B 6.9 / 5.0 / 2.7 / 1.1 (all other cells <= 1.6). Single memories are not compressed at these budgets (they grow
beyond the ~75-token source), as stated in the design.

---

# E6 Contextual Evidence Robustness (design frozen 2026-11-22, before any generation or evaluation)

Objective: does the Blindness x Competition interaction persist when the annotated evidence spans are supplemented
with local clinical context from the source article and with ICO provenance? This is a LOCAL-CONTEXT experiment;
it is not a whole-document validation and will not be described as one.

## Input (built before this entry; no model output involved)
`scripts/build_e6_context.py` -> `data/e6/e6_context_v1.jsonl`, `results/e6/e6_context_manifest.csv`,
`results/e6/e6_input_audit.csv`. Same 294 articles, target ICOs, gold labels and candidate order as the main grid.
Per candidate: the evidence span is located in the full text (first occurrence in a BODY section, else the
abstract); context = the rest of the span's own sentence + up to 2 whole sentences before and 2 after, same section,
<= 100 reference tokens of whole sentences per side; provenance = article id, section path, and the intervention /
comparator / outcome the span was annotated for (no direction, no significance, no target marker).
Single = the target passage only. Multi = the identical target passage + the original distractor passages.
Realized: spans located 92.7 % (targets 93.9 %; 54 % in a body section, the rest in the abstract); context 79
tokens per candidate; Single 210 and Multi 822 Qwen3-14B tokens (span-only 83 / 294).
Contamination, recorded and NOT removed: an annotated finding other than the target enters the Single input through
the target context in 41.8 % of articles; a sentence with statistical language in 66.3 %; either 69.7 %. In Multi,
37.8 % of articles have candidates with identical evidence, 65.0 % a context overlapping another candidate, 38.8 %
the target finding repeated inside a distractor context; 14.3 % have an unlocated candidate (kept span-only + ICO).
Consequence stated in advance: with ICO provenance the Single input names the target comparison, so Blind/Single is
effectively question-aware; and the Single cell is not competition-free in the contaminated articles.

## Design
Model Qwen3-14B. Budgets 100 / 200 / 400. Aware / Blind x Single / Multi, n = 294 per cell, depth 5, frozen
main-experiment prompts, truncation-free protocol (E3b: regenerate <= 20 attempts, adaptive instructed budget,
never cut). Arms: CONTEXT (above) and a matched SPAN-ONLY reference at the same budgets and protocol (Multi
generated now; Single = the E13 truncation-free Single chains, which are the identical span-only cells, committed
verdicts reused). Reference without hypothesis: final answer straight from the uncompressed context input.
Outcomes: judge-based ELR (primary) and memory-level WP, frozen evaluator. No exclusions; failed regenerations are
kept and reported (complete-case DiD + the E3b conservative bound). Context window, prompts and budgets are not
changed after outcomes are seen.

## Analysis and reading rule
Per budget and outcome: four cell means, DiD with paired article bootstrap (B = 2000, seed 42) for each arm, and
the contrast Delta = DiD_context − DiD_span (same bootstrap over articles).
- "Persists with context" at B: DiD_context < 0 with a 95 % CI excluding 0.
- "Context changes the effect" at B: the CI of Delta excludes 0 (sign reported). A DiD that is significant in one
  arm and not in the other is NOT by itself evidence of a change.
Secondary, reported whatever the result: DiD_context on (a) articles whose Single input has no annotated-finding
contamination, (b) articles with neither kind of contamination, (c) articles whose target span was located.
Also reported: natural budget compliance (first-attempt), failures, realized memory length, attempts per write.
Outputs: results/e6/e6_elr_summary.csv, e6_wp_summary.csv, e6_length_summary.csv, e6_analysis.md.
Limits stated in advance: one model; the package (context + ICO provenance) is tested as a whole, so its two parts
cannot be separated; the context arm's Multi input is ~2.8x longer than span-only, so a larger DiD in the context
arm at a given budget may reflect compression pressure (E13) rather than semantic context.

## E6 outcome (2026-11-22) — Qwen3-14B, truncation-free
All generated and scored: 5,292 chains, 0 failed regenerations, 0 dirty verdicts, no exclusions. Full report
`results/e6/e6_analysis.md` (+ `e6_elr_summary.csv`, `e6_wp_summary.csv`, `e6_length_summary.csv`,
`e6_context_manifest.csv`, `e6_input_audit.csv`).
ELR DiD, context arm: −8.2 [−12.6, −3.4] at 100, −2.0 [−6.8, +2.7] at 200, +1.0 [−3.1, +5.4] at 400.
WP DiD, context arm: −3.4 [−7.8, +1.4], −2.4 [−7.1, +2.7], −0.3 [−4.4, +3.7].
Span-only arm: ELR −2.0 / −1.4 / −0.3 (all n.s.); WP −5.1 [−9.9, −0.3], −5.1 [−9.5, −1.0], −3.1 [−7.8, +1.7].
Delta (context − span): ELR −6.1 [−12.2, +0.0], −0.7, +1.4; WP +1.7, +2.7, +2.7 — no CI excludes 0.
Rule: the interaction persists with context for ELR at B = 100 only; context does not detectably change the effect
at any budget. Subsets at B = 100 (ELR): no annotated contamination −10.5 [−16.4, −4.7] (n = 171), no contamination
−6.7 [−14.6, +0.0] (n = 89), target located −8.3 [−12.7, −4.0] (n = 276).
Post hoc (not part of the rule): 822-token context input at B = 100 (12 %) gives −8.2 whereas the 1,121-token
multi-trial input of E13 at B = 100 (10 %) gave −29.9; the inputs differ in the number of distinct findings (~4 vs
~18), which favours the capacity reading of E13 over a pure compression-ratio reading.

---

# E14 Length-matched control for E13 (design frozen 2026-11-22, before any generation)

Why: in E13 the Single cells keep the short target-only source (~80 tokens) while the Multi cells use the
~1,000-token multi-trial source, so the E13 DiD confounds the presence of competing findings with input length
(compression pressure). E14 adds the missing cell: a source of the same length and structure in which the target
is the only finding.

## Material (built before this entry; no model output involved)
`scripts/build_longfiller.py` -> `data/longsource/longfiller_v1.jsonl`. For every E13 long source, every evidence
span except the target is replaced by non-finding prose from the same trial's article (body sentences before the
Results section with every sentence that could carry a finding removed — the Phase-4 ② filler definition), token-
matched span by span with the cumulative length kept equal (o200k_base). Block order, headers and the position of
the target span are unchanged; sentences are never reused inside a source. When a trial has too little such prose
the remainder is borrowed from the other trials of the same source (17.6 % of filler spans; 192 sources have at
least one).
Exclusion rule (fixed now): a source is used only if every span could be filled and its length is within 5 % of
its E13 long source. 279 of 294 sources qualify (mean 1,009 vs 1,011 reference tokens; difference p5 −14, p95 +6).
The 15 excluded articles are dropped from ALL cells of the E14 analysis.

## Design
Qwen3-8B and Qwen3-14B; budgets 100 / 200 / 400 / 800; truncation-free protocol; frozen prompts; cells
Aware / Blind x Filler (new). Single and Multi (long) cells are the E13 truncation-free chains of the same 279
articles (committed verdicts reused). Outcomes: judge-based ELR (primary) and WP.

## Estimands and reading rule (per budget, paired article bootstrap, B = 2000, seed 42)
G_x = Blind − Aware in condition x.
- LENGTH component  = G_Filler − G_Single   (same single finding, short vs ~1,000-token input)
- COMPETITION component = G_Multi − G_Filler (same length, competing findings vs non-finding prose)
- their sum is the E13 DiD on these articles.
"Competition-specific at B": COMPETITION < 0 with a 95 % CI excluding 0. "Length-driven at B": LENGTH < 0 with a
CI excluding 0. Both can hold. If COMPETITION is not distinguishable from 0 where the E13 DiD is, the paper must
describe the E13 interaction as a query-blind loss under input load, not as a competition effect (Phase-4 ②
already found this pattern for WP at 25 / 50 tokens on the short source). Failed regenerations are kept and
reported; complete cases are analysed.
Limits stated in advance: filler is topical prose from the same trials, so it is "non-finding" by a lexical filter,
not by annotation; borrowed sentences sit under another trial's header; two models, no GPT.

## E14 outcome (2026-11-22) — Qwen3-8B and Qwen3-14B, truncation-free, n = 279
All generated and scored (2,232 chains per model, 0 failures, 0 dirty). Report `results/lenctrl_report.md`,
table `results/lenctrl_summary.csv`.
ELR, LENGTH (Filler − Single): 8B −44.1 [−50.5, −37.3], −24.7 [−30.8, −18.6], −8.2 [−14.0, −2.2], −5.4 [−10.8, +0.4];
14B −24.7 [−31.5, −17.9], −23.3 [−29.7, −17.2], −6.1 [−11.1, −0.4], +2.9 [−2.5, +8.6] (B = 100 / 200 / 400 / 800).
ELR, COMPETITION (Multi − Filler): 8B +14.3 [+7.2, +21.5], +0.0, +1.1, +0.4; 14B −5.0 [−12.9, +2.5], −0.7, +2.9, +1.1.
WP, COMPETITION: 8B +17.2 [+9.3, +24.7], +9.3 [+1.8, +16.8], +2.2, +11.8 [+5.4, +17.9]; 14B +11.8 [+3.2, +19.0],
+6.8, +5.4, +5.0 (others n.s.). Blind/Filler at B = 100: ELR 49.1 / 62.7, WP 28.7 / 29.4.
Rule: competition-specific at no budget in either model; length-driven at 100, 200 and 400 in both. The E13
interaction is therefore a query-blind loss under input load, not a competition effect; where the two inputs
differ, non-finding prose is the more harmful companion for the target.

---

# Phase 6 — E15 / E16 / E17 (written 2026-11-23, before any rating, generation or scoring)

Order fixed by the request of 2026-11-23: E16 and E17 first (existing data), then E15. E18–E21 are not started;
they are decided after these three.

## E16 Filler validation (existing data; no generation)
Question: is the E14 filler really free of findings and of target-relevant content?
- Deterministic, all 4,182 filler spans of the 279 constructible sources (`results/e16/e16_filler_spans_all.csv`,
  `e16_target_position.csv`): target slot and tokens before the target (filler vs E13 long source), number of
  occurrences of the target sentence in each source, lexical similarity of every filler span to the gold evidence
  (token Jaccard, ROUGE-L recall), statistical-marker regex.
- Rated sample: 100 spans, strata home_own 40 / other_own 30 / borrowed 30 (population 679 / 2,829 / 674), at most
  one span per source inside a stratum, seed "e16-sample". Two independent raters, blind to stratum and to all
  results, codebook `data/audit/CODEBOOK.md`. THE RATERS ARE LLM ANNOTATORS (two independent Claude sessions), not
  humans; the same blind sheets are kept for human annotation. Reported as such.
- Endpoints: contamination rate = share of spans rated `finding != NONE` (per rater, both-agree, either-rater),
  per stratum and population-weighted, Wilson 95 % CI; target leak = `finding == TARGET_RESULT` or
  `background_claim == TARGET` or `target_relevance == DIRECTION` or `duplicates_evidence == YES`; inter-rater
  agreement and kappa.
- Evaluator leak screen, all 279 sources (run with the E15 scoring; frozen evaluator): the filler source with every
  occurrence of the target sentence removed is classified for the target question. Leak = any label other than
  NOT_MENTIONED; "gold leak" = the gold label.
- Sensitivity (existing E14 verdicts, no new scoring): LENGTH and COMPETITION components recomputed after
  excluding (a) sources with a span flagged by either rater as a target leak or by the evaluator screen,
  (b) sources in which the target sentence occurs more than once in the filler or the long source.
- Reading: "filler valid" if the either-rater target-leak rate has an upper CI bound below 5 % and the E14
  conclusions (no negative COMPETITION component with CI excluding 0; LENGTH negative with CI excluding 0 at
  100 / 200 / 400) are unchanged in every sensitivity analysis. Otherwise the contaminated sources are named and
  the E14 statement is limited to the clean subset.

## E17 WP–ELR disagreement audit (existing outputs; no generation)
Question: when the evaluator says the memory lost the warrant (WP = 0) but the answer is right (ELR = 1), is the
answer grounded, guessed, or is one of the two automatic verdicts wrong?
- Sample: 150 E13 truncation-free chains, Multi cell, Blind writer, budgets 100 / 200, both models:
  WP0_ELR1 80 (20 per model x budget), WP0_ELR0 36, WP1_ELR1 34; seed "e17-sample"; `data/audit/e17_key.csv`.
- Two independent LLM raters (same as E16), blind to gold label, automatic verdicts, model, budget and class.
  Items: memory label, memory evidence (EXPLICIT / PARTIAL / ABSENT), answer label, answer grounding
  (STATED / INFERRED / MISATTRIBUTED / UNGROUNDED / NO_CLAIM).
- Endpoints (per rater and for items on which both raters agree):
  1. evaluator vs rater label agreement and kappa, memory and answer separately; evaluator WP false-negative rate
     = share of WP = 0 items whose memory the rater labels with the gold label; evaluator ELR false-positive rate
     = share of ELR = 1 items whose answer the rater does not label with the gold label.
  2. decomposition of the WP0_ELR1 class: (a) warrant actually in memory (evaluator miss), (b) answer inferred
     from partial evidence, (c) answer misattributed from another finding, (d) answer ungrounded (guess),
     (e) answer not actually correct (evaluator false positive).
  3. the same items in the two control classes as a check of the raters and the evaluator.
- Reading: the WP0_ELR1 class supports "answer without warrant" only to the extent of (b) + (c) + (d); (a) and (e)
  are evaluator error and are reported as a correction factor for the masking rates of
  `results/distortion_report.md`. No verdict is changed; the audit is reported separately from the automatic
  outcomes. Limits: LLM raters; sample restricted to Blind/Multi at 100 / 200; classes are sampled at fixed sizes,
  so class shares come from the full data, not from the sample.

## E15 Matched-prompt control (new generation)
Question: is the Blind − Aware loss caused by query availability, or by the different writing instructions of the
two original prompts (Aware: "about a clinical research question … Rewrite them as concise notes for the next
step"; Blind: "about a clinical study. The specific question … is not yet known. Condense the notes for future
use")?
Matched prompt (fixed now, not tuned): ONE system prompt and ONE instruction for both arms; the Aware arm differs
only by one extra first line of the user message, `Research question: What is the effect of "I" compared with "C"
on "O"?` followed by a blank line.
  system: "You are one step in a multi-step biomedical research assistant pipeline.\nYou receive working notes
  from the previous step about clinical research. A later step will answer a research question using only your
  notes.\nCondense the notes for the next step, within the length limit.\nPreserve the supporting evidence and
  source information as appropriate.\nOutput only the notes."
  user: "[Research question line, Aware only]Notes from the previous step:\n{material}\n\nCondense these notes so
  a later step can use them. Maximum length: {budget} tokens (about {words} words)."
The stricter-retry suffix, the final-answer prompt, sampling, seeds, tokenizer, budget acceptance and the
truncation-free regeneration rule are unchanged. Modes are stored as `aware_m` / `blind_m`.
Cells: Aware / Blind x Single / Filler / Multi, ALL regenerated under the matched prompt (the original chains are
used only as the comparison). Sources: original single-span source, `longfiller_v1`, `longsource_v1`; the E14
set of 279 articles, no further exclusion. Budget 200. Model Qwen3-14B (primary), Qwen3-8B (validation), run in
the same chain. Truncation-free; failures kept and reported; complete cases analysed.
Outcomes: judge-based ELR (primary) and WP, frozen evaluator.
Estimands (paired article bootstrap, B = 2000, seed 42): G_x = Blind − Aware in source x; LENGTH = G_Filler −
G_Single; COMPETITION = G_Multi − G_Filler; and, on the same articles, the change against the original prompts
D_LENGTH = LENGTH(matched) − LENGTH(original), likewise per cell.
Primary endpoint: LENGTH component of ELR, Qwen3-14B, B = 200 (original: −23.3 [−29.7, −17.2]).
Reading rule:
- "retained": LENGTH(matched) < 0 with a 95 % CI excluding 0 -> the query-visibility reading stands.
- "attenuated": D_LENGTH > 0 with a CI excluding 0; "largely reduced" if in addition |LENGTH(matched)| is below
  half of |LENGTH(original)| -> the original writing-policy framing contributed, and the paper must say how much.
- "not retained": LENGTH(matched) CI includes 0 -> the original Blind − Aware loss cannot be attributed to query
  visibility; the main claim has to be rewritten.
Both "retained" and "attenuated" can hold. The same rule is read for WP and for Qwen3-8B (secondary).
B = 100 is run only if the primary reading is not a clean "retained" (i.e. attenuated or not retained) in either
model; otherwise it is not run. Stop rule for E18: started only if the primary reading is "retained".
Limits stated in advance: one matched wording (the shared instruction is the "condense" wording, so the Aware arm
changes more than the Blind arm relative to the originals); one budget; two Qwen models; single seed.

## E15 outcome (2026-11-23) — B = 200, n = 279, truncation-free, 0 failed regenerations, 0 dirty verdicts
Report `results/e15/e15_report.md`, table `results/e15/e15_summary.csv`.
ELR LENGTH (matched vs original; change): 14B −18.3 [−24.4, −12.5] vs −23.3 [−29.7, −17.2]; +5.0 [−1.8, +11.5]
-> retained. 8B −30.8 [−36.6, −24.7] vs −24.7 [−30.8, −18.6]; −6.1 [−13.6, +1.1] -> retained.
WP LENGTH: 14B −30.1 [−37.3, −22.9] vs −40.1 [−47.0, −33.3]; +10.0 [+1.8, +18.3] -> retained, attenuated (not "largely
reduced": 75 % of the original remains). 8B −40.1 [−47.3, −32.6] vs −36.6; −3.6 [−11.1, +3.6] -> retained.
No cell rate changed by more than 4.3 points and none of the 24 cell changes has a CI excluding 0 (8B
Blind/Single ELR +1.4 [+0.0, +3.2] touches 0). COMPETITION under the matched prompt: ELR 14B −6.8 [−13.3, +0.0],
8B +6.8 [−0.7, +14.3]; WP 14B −0.7 (n.s.), 8B +11.5 [+3.2, +20.1] — opposite signs across models, as before.
Primary reading: RETAINED in both models. By the rule fixed above, B = 100 is not run and the E18 condition is met.

## E18 One-pass vs recursive memory (written 2026-11-23 before generation)
Question: is the loss specific to four successive rewrites, or already present after one write?
Design: Qwen3-14B, B = 200, the 279 E14 articles, Single / Filler / Multi x Aware / Blind, truncation-free.
One-pass = the chain stopped after the first write: M1 is written from the source under the same prompt, budget
and regeneration rule, and the reader answers from M1. The first write is taken from the SAME generation as the
four-pass chain (same cache key, verified by identical first-write attempt counts), so the comparison isolates
rewrites 2–4. Only the final answers from M1 are newly generated; M1 and those answers are scored by the frozen
evaluator. Run for both prompt families: original prompts (primary; four-pass = committed E13 / E14 verdicts) and
the E15 matched prompt (secondary; four-pass = E15 verdicts).
Estimands (paired article bootstrap, B = 2000, seed 42): cell rates, G_x, LENGTH and COMPETITION for one-pass;
RECURSION = four-pass − one-pass for each of them and for the Blind/Filler and Blind/Multi cell rates.
Reading rule (ELR primary, WP secondary, original prompts):
- "present after one write": LENGTH(one-pass) < 0 with a 95 % CI excluding 0 -> the loss is not specific to
  recursive rewriting.
- "aggravated by rewriting": RECURSION of LENGTH < 0 with a CI excluding 0 (the loss grows over rewrites 2–4).
- if LENGTH(one-pass) includes 0 and RECURSION is negative with a CI excluding 0 -> the loss is a property of
  recursive rewriting, and the paper's claims must be limited to that architecture.
Limits: one model, one budget; "one-pass" is the first step of the same chain, not a separately prompted
single-shot summariser; the one-pass memory may be shorter or longer than M4 (lengths reported).

## E16 / E17 outcome (2026-11-23) — reports `results/e16/e16_report.md`, `results/e17/e17_report.md`
E16: rated sample 1 / 100 target leak (1.0 % [0.2, 5.4]; criterion "upper bound below 5 %" missed by 0.4 points),
4 / 100 spans with an unrelated result (5.6 % weighted), 0 duplicates; rater agreement 96–100 %. Evaluator screen
6 / 279 sources with a direction label (2.2 % [1.0, 4.6]), 3 gold. Target sentence repeated in 19.0 % filler /
27.6 % Multi sources. E14 conclusions unchanged after excluding the 7 leak sources or the 77 repeated-target
sources at 100 / 200 tokens; ELR LENGTH at 400 loses significance in the n = 202 subset.
E17: ELR verdict vs raters 95–96 % (kappa 0.93–0.95); WP verdict 75 % (kappa 0.51); WP false negatives 21.6 % of
sampled WP = 0 items (both raters; about 15 % population-weighted), false positives 11.8 % of WP = 1; adjusted
Blind/Multi WP 47.8 / 51.0 % at 100 and 60.7 / 60.3 % at 200 (8B / 14B). WP0_ELR1: 65 % answer without stated
warrant, 30 % evaluator error (both raters). Raters are two LLM sessions, not humans.

## E18 outcome (2026-11-23) — Qwen3-14B, B = 200, n = 279, 0 failures, 0 dirty; `results/e18/e18_report.md`
Original prompts: ELR LENGTH one-pass −17.2 [−23.3, −11.1], four-pass −23.3, RECURSION −6.1 [−12.2, −0.4];
WP LENGTH one-pass −35.1 [−41.9, −28.3], four-pass −40.1, RECURSION −5.0 [−10.4, +0.4].
Matched prompt: ELR −17.2 [−24.0, −10.4] vs −18.3, RECURSION −1.1 (n.s.); WP −26.9 [−33.3, −20.4] vs −30.1, −3.2 (n.s.).
Rule: "present after one write" in all four readings; "aggravated by rewriting" only for ELR under the original
prompts. The loss is not specific to recursive rewriting.

## E19 Length–position control (written 2026-11-23 before generation)
Question (W3): E14's LENGTH component contrasts a target-only source (about 83 model tokens) with a 1,121-token
Filler source in which the target also sits at a different, article-specific position. Is the loss caused by the
amount of input, or by where the target sits in it?
Sources (`scripts/build_e19_sources.py`, built before this text was written; no generation involved): from every
E14 Filler source, 3 position arms x 3 length levels in which the target finding is the only finding and occurs
exactly once (repeated target sentences of E14 are dropped).
- first: home block first, target its first bullet (13 reference tokens = header before it at every level)
- last: home block last, target its last bullet (0 tokens after it at every level)
- middle: filler balanced around the target (target centre in the middle third of the source at every level)
- levels 200 / 500 / 1,000 reference tokens (o200k_base, the E13 / E14 tokenizer): 200 and 500 take the filler
  nearest to the target, extended outward sentence by sentence; 1,000 is all filler material of the E14 source.
  Within an arm the sources are nested (200 in 500 in 1,000). Filler text, headers and rendering are E14's.
Analysis set (fixed now): the 243 of 279 articles for which all nine sources are in tolerance (level +-15 %:
170–230, 425–575; 850–1,100 for the full level; at least one filler sentence; middle arm centre in [1/3, 2/3]).
All 279 are generated; the 36 others enter only a secondary all-article analysis. Realized lengths in the set:
200.5 / 499.2 / 1,000.5 (first), 203.1 / 503.9 / 1,000.5 (middle), 199.1 / 500.9 / 1,000.4 (last).
Design: Qwen3-14B, B = 200, Aware / Blind, truncation-free protocol unchanged (same retry rule, tokenizer,
seeds), four writes + reader, frozen evaluator, ELR and WP as defined. Two prompt families: original prompts
(primary; the manuscript's protocol) and the E15 matched prompt (secondary). 279 x 9 x 2 x 2 = 10,044 chains.
Estimands (paired article bootstrap, 2,000 resamples, seed 42, percentile CI), G(arm, L) = Blind − Aware:
- LEN(arm) = G(arm, 1000) − G(arm, 200); steps G(500) − G(200) and G(1000) − G(500)
- LEN_pooled = mean over the three arms of LEN(arm)                      <- PRIMARY (ELR, original prompts)
- POS(L) = G(last, L) − G(first, L) and G(middle, L) − G(first, L); POS_pooled = mean over the three levels
- the same contrasts on the Blind cell rates alone (Aware cells are near ceiling)
- reference rows, not tested: G_Single and G_Filler (natural position) of the same articles at B = 200 (E13 / E14
  committed verdicts for the original prompts, E15 for the matched prompt).
Reading rule:
- "length effect with position fixed": LEN_pooled < 0 with a 95 % CI excluding 0. "At every position" if each
  LEN(arm) has a CI excluding 0; otherwise the arms where it holds are named.
- "graded": G(200) >= G(500) >= G(1000) in the pooled point estimates and both pooled steps <= 0.
- "position effect": POS_pooled (last − first) with a CI excluding 0 (sign reported; an earlier 25-token arm
  found first > last for 14B at the memory level).
- LEN_pooled CI includes 0 -> with the position fixed, source length does not raise the Blind − Aware penalty;
  the E14 LENGTH component must then be described as a Filler-versus-target-only contrast that confounds
  position, and the paper's "length" wording has to go.
- both present -> both are reported with their sizes; neither is dropped.
WP is read by the same rule (secondary); the matched prompt is read by the same rule (secondary).
Sensitivity (fixed now): excluding the 7 E16 leak sources; all 279 articles regardless of tolerance.
Limits stated in advance: one model, one budget, one seed; the 200-level source is about 220 model tokens, i.e.
slightly above the budget, so it is a low-compression level, not a no-compression one (the target-only source is
the no-compression reference); the filler nearest the target is home-article prose and the filler added at
longer levels is mostly other trials' prose, so length grows together with the number of trial blocks
(1.3 / 2.6 / 4.6); in the first and last arms the absolute offset is fixed and the relative position is not
(target centre 0.21 / 0.08 / 0.04 and 0.86 / 0.95 / 0.97), in the middle arm the reverse.

## E19 outcome (2026-11-23) — Qwen3-14B, B = 200, 10,044 chains, 0 failures, 0 dirty; `results/e19/e19_report.md`
Primary (ELR, original prompts, n = 243): LEN_pooled −20.7 [−25.0, −16.7]; first −7.8 [−13.2, −2.5], middle −29.6
[−36.2, −23.0], last −24.7 [−31.7, −18.5]; pooled G −0.3 / −6.9 / −21.0 at 200 / 500 / 1,000 -> "length effect with
position fixed (at every position); graded". POS_pooled last − first −4.1 [−6.9, −1.2] -> "position effect", carried
by the 1,000-token level only (last − first −15.6, middle − first −20.2; n.s. at 200 and 500); interaction
LEN(middle) − LEN(first) −21.8 [−29.2, −14.4]. WP: LEN_pooled −29.2 [−33.9, −24.1] (first −12.3, middle −35.8,
last −39.5), POS_pooled −10.4 [−14.4, −6.6]. Matched prompt: ELR LEN_pooled −19.3 [−24.0, −15.2] (first −5.8*),
WP −28.3 [−33.1, −23.3] (first −5.8 [−12.8, +0.8], n.s.). Sensitivity sets: same readings, except matched-prompt
first-arm ELR with all 279 articles (−4.3 [−9.0, +0.4]). Both effects are reported; neither is dropped.

---

# Phase 6 — E20 / E21 / E23 (written 2026-11-27, before any generation or scoring of these experiments)

Origin: a pasted plan of eight experiments (E20–E27). Checked against the record first: E26 (same sentences,
position only) already exists as the 1,000-token level of E19 (the three arms hold the same sentence set in
279 / 279 articles); E22 rests on a comparison across different inputs (−23.8 is E13, 1,121 tokens and ~18
findings; −2.0 is the E6 context arm, 822 tokens and ~4 findings, whose own span-only reference gave −1.4) and is
not run; E24 / E25 / E27 need decisions outside this round. Run now, at the user's request: E20, E21, E23.
Common to all three: frozen prompts, truncation-free protocol (<= 20 attempts, instructed budget shrinking 5 % per
attempt, acceptance against the true budget), frozen evaluator (Qwen3-32B-FP8, prompt v3), judge-based ELR
(primary) and memory-level WP, paired article bootstrap (2,000 resamples, seed 42, percentile intervals),
complete cases, no exclusions after outcomes are seen. Committed verdicts of earlier experiments are reused and
never re-scored.

## E20 Full-source reading and loss stage (new: two reader calls per article and model; the rest is existing data)

Question: is the Blind loss on long sources a loss at the write stage, or does the reader already fail on the
uncompressed source?
- Articles: the 279 articles of E14. Models: Qwen3-8B and Qwen3-14B.
- New generation: the final answer straight from the uncompressed source, for Single (the target sentence under its
  article header = the gold evidence) and Filler. Same reader prompt and settings as every final answer
  (`answer_from`: temperature 0.7, seed 42, 80 instructed tokens). Multi: the E13 `full_long` answers, verdicts reused.
- Existing: Aware / Blind M4 chains of E13 / E14 (Single, Filler, Multi; B = 100 / 200 / 400 / 800) with ELR and WP
  verdicts; first-write memories of E18 (14B, B = 200) as a descriptive row.
- Estimands, per model, source and budget: FULL = ELR of the full-source answer; Blind M4 − FULL and
  Aware M4 − FULL (paired); FULL(Filler) − FULL(Single) and FULL(Multi) − FULL(Single).
- Loss-stage table, per model, mode, source and budget, over articles whose full-source answer is correct:
  WP = 1 & ELR = 1 retained and used; WP = 0 & ELR = 0 write-stage loss; WP = 1 & ELR = 0 read-stage failure;
  WP = 0 & ELR = 1 correct answer without a recoverable memory statement (E17: mostly answers without warrant,
  about 30 % evaluator error). "Evidence in memory" is the evaluator's WP verdict, i.e. label recoverability,
  not ICO completeness.
- Reading rule (primary: Qwen3-14B, B = 200, Filler; the same rule is read for the other cells):
  "write-stage loss" iff (i) Blind M4 − FULL < 0 with a CI excluding 0 and (ii) among articles with a correct
  full-source answer and a wrong Blind final answer, the share with WP = 0 has a Wilson 95 % lower bound above 50 %.
  "source-reading difficulty contributes" iff FULL(Filler) − FULL(Single) < 0 with a CI excluding 0; its size is
  then reported next to the Blind Filler − Single difference.
- Limits stated now: the full-source reader sees 1,000 tokens and the memory reader at most B, so Blind M4 − FULL
  is not a pure writer effect; the stage table rests on WP, whose agreement with the audit raters was 75 %.
  A four-condition stage diagnosis is not a new method; here it is only tied to the Aware / Blind contrast.

## E21 Source length x evidence composition (new generation)

Question: does the Blind − Aware gap grow with source length when the added material is competing findings, as it
does when it is non-finding prose (E19), and does the composition change the growth?
- Material (built before this entry; no model output involved): `scripts/build_e21_sources.py` ->
  `data/longsource/e21_sources_v1.jsonl`, `results/e21/e21_sources_summary.csv`.
  COMPETING: from the E13 long source; home block first, target finding as its first bullet; the other bullets are
  annotated findings (remaining home findings, then the other trial blocks in their E13 order), whole findings only,
  tried in reading order: a finding that keeps the source at or below the level is added, one that overshoots is
  added only if the source stays within the upper tolerance and lands closer, otherwise it is skipped at that level.
  Level 1,000 = all findings of the E13 source. Nested (200 within 500 within 1,000). Any bullet that is, contains
  or is contained in the target sentence is dropped (93 articles), so the target occurs exactly once.
  NON-COMPETING: the E19 `first` arm, unchanged (existing chains and verdicts).
  Levels 200 / 500 / 1,000 reference tokens (o200k_base), tolerances of E19 (170–230, 425–575, 850–1,100).
  Target position fixed: 13 reference tokens before the target in every source of both compositions.
- Cohort (fixed now): articles in the E19 primary set (243) whose three competing sources are in tolerance
  (257 of 279) = 235 articles. Realized (235): competing 205.3 ± 12.6 / 509.1 ± 17.3 / 992.0 ± 44.3 tokens,
  2.6 / 7.3 / 15.1 competing findings, 1.5 / 2.8 / 4.6 blocks; non-competing 200.5 ± 11.7 / 499.1 ± 13.6 /
  1,002.5 ± 37.3 tokens, 3.8 / 12.4 / 28.3 filler sentences, 1.3 / 2.6 / 4.6 blocks. At 200 and 500 tokens 72 % of
  the competing sources are a contiguous prefix of the queue (no skipped finding).
- Design: Qwen3-14B, B = 200, Aware / Blind, original prompts (primary) and the E15 matched prompt (secondary),
  four writes + reader. Competing sources of all 279 articles are generated (sensitivity); non-constructible ones
  are not in the primary analysis.
- Estimands (G = Blind − Aware; L in {200, 500, 1000}; C in {competing, non-competing}):
  COMPOSITION(L) = G(L, competing) − G(L, non-competing);
  LENGTH(C) = G(1000, C) − G(200, C);
  INTERACTION = LENGTH(competing) − LENGTH(non-competing).
- Reading rule (ELR, original prompts, n = 235):
  "length effect in both compositions" iff LENGTH(competing) and LENGTH(non-competing) are both < 0 with CIs
  excluding 0; "composition changes the length effect" iff the CI of INTERACTION excludes 0 (sign reported);
  "competition-specific loss at L" iff COMPOSITION(L) < 0 with a CI excluding 0. A LENGTH that is significant in one
  composition and not in the other is not by itself evidence of a difference.
- Secondary, reported whatever the result: WP; matched prompt; all articles with both sources available;
  excluding the 7 E16 leak sources; realized memory length and attempts per write in every cell.
- Limits stated now: one model, one budget, one seed, target first only (E19: the first position is where the
  length effect is smallest); "competing" and "non-competing" differ in more than the presence of findings
  (sentence type, number of bullets, statistical language); at 200 and 500 tokens the competing source prefers
  findings that fit, i.e. shorter ones; the non-competing material carries about 5.6 % unrelated result statements (E16).

## E23 Multi-seed replication of E14 (new generation)

Question: do the E14 contrasts hold across independent generation runs?
- Qwen3-14B, B = 200, the 279 articles of E14, Aware / Blind x Single / Filler / Multi, original prompts.
- Seeds: 42 (the existing E13 / E14 chains, verdicts reused) and four new base seeds 143, 244, 345, 446 (the seeds of
  the earlier seed studies). Within a run with base seed s: write attempt a uses seed s + 100a, the reader uses s
  (for s = 42 this is the protocol of record; the five seed sequences do not overlap). The base seed enters the
  generation cache key (`run_phase5.notrunc_chain(base_seed=...)`); nothing else differs between runs.
- Per seed: LENGTH = G_Filler − G_Single, COMPETITION = G_Multi − G_Filler, E13 DiD = G_Multi − G_Single, with the
  paired article bootstrap; cell means; failed regenerations; attempts per write and realized memory length by cell.
- Across seeds: mean and SD of the five per-seed estimates; number of seeds with a negative estimate and with a CI
  excluding 0. Pooled estimate: each article's outcome averaged over the five seeds, then the paired article
  bootstrap (articles are the resampling unit; the 5 x 279 observations are never treated as independent).
  Also reported: a two-way bootstrap resampling seeds and articles (2,000 resamples), which adds seed-to-seed
  variation to the interval; with five seeds this interval is itself imprecise.
- Reading rule (ELR): "replicates" iff LENGTH is negative with a CI excluding 0 in every seed and in the pooled
  estimate. "seed-sensitive" iff the sign of LENGTH differs between seeds or its seed SD exceeds half of the
  absolute pooled estimate. COMPETITION is read the same way against the E14 finding (not negative with a CI
  excluding 0): it "stays non-negative" iff no seed gives a negative estimate with a CI excluding 0.
- Limits stated now: one model, one budget (B = 100 is not run in this round); the evaluator is one frozen model
  and is not re-sampled; seeds change sampling only, not the sources or the prompts.

## E20 outcome (2026-11-27) — Qwen3-8B and Qwen3-14B, n = 279, 1,116 new answers, 0 dirty; `results/e20/e20_report.md`
Full-source ELR (8B / 14B): Single 95.3 / 98.6, Filler 92.8 / 93.2, Multi 90.7 / 93.9 (Multi = the E13 `full_long`
verdicts restricted to the 279 articles; 90.8 / 93.5 over the 294 of E13). FULL − FULL(Single): Filler −2.5
[−5.7, +0.7] / −5.4 [−8.2, −2.5]; Multi −4.7 [−8.2, −1.4] / −4.7 [−7.9, −1.8] -> "source-reading difficulty
contributes" for 14B (both long sources) and for 8B Multi; not shown for 8B Filler.
Primary (14B, B = 200, Filler): Blind M4 − FULL −20.8 [−26.2, −15.8]; among 260 full-correct articles the Blind final
answer is wrong in 63, with WP = 0 in 56 (88.9 % [78.8, 94.5]) -> "write-stage loss" (i and ii). Aware M4 − FULL −0.4
[−3.9, +2.9]. Same reading for 14B Multi at 200 (−22.2; 90.8 % [81.3, 95.7] of 65), both models and both long sources
at B = 100 (−30.1 to −43.7; write share 90.0–98.9 %), 8B at 200 (Filler −22.2, 94.0 %; Multi −21.9, 80.0 %) and
Filler at 400 (8B −10.0, 72.7 % [55.8, 84.9]; 14B −8.6, 69.7 % [52.7, 82.6]). NOT established (ii fails; the gap to
FULL is still negative except 14B Multi at 800): Multi at 400 and every long cell at 800 (14–36 wrong finals, write
share 48–65 %, Wilson lower bound <= 50).
Size of the read stage in the primary cell: read failure (WP 1 & ELR 0) 7 of 260 (2.7 %). First write (E18 M1, 14B,
B = 200, Blind): wrong finals 50 (Filler) / 60 (Multi) of the full-correct articles, write share 94.0 % / 90.0 % ->
the loss is already present after one write.
Not anticipated in the reading rule, reported as observed: "answer without memory" (WP 0 & ELR 1) is large in the
Blind long cells — 14B, B = 200: Filler 62 of 260 (23.8 %), Multi 37 of 262 (14.1 %); B = 100 Filler 91 of 260
(35.0 %) — against 2–4 % in the Aware cells. The final-answer ELR therefore understates how often the target
evidence is absent from a Blind memory (WP is the direct measure); E17 is the audit of these disagreement cells.
Single: Blind M4 − FULL −2.2 [−4.3, +0.0] (14B, 200); Aware/Single M4 is below FULL at 200–800 for 14B (−3.6 to −5.0).

## E21 outcome (2026-11-27) — Qwen3-14B, B = 200, 3,348 chains, 0 failures, 0 dirty; `results/e21/e21_report.md`
Primary (ELR, original prompts, common cohort n = 235). G at 200 / 500 / 1,000: competing +0.0 / −5.5 / −7.2;
non-competing −0.9 / −6.8 / −8.9. LENGTH(competing) −7.2 [−13.2, −1.7], LENGTH(non-competing) −8.1 [−13.2, −2.6],
INTERACTION +0.9 [−6.8, +8.1]; COMPOSITION(L) +0.9 [−4.3, +6.0] / +1.3 [−4.3, +6.8] / +1.7 [−4.3, +7.2]
-> "length effect in both compositions"; composition does not detectably change the length effect; no
competition-specific loss at any length. The 200 -> 500 step carries the effect in both (−5.5*, −6.0*); 500 -> 1,000
is −1.7 / −2.1, n.s. The INTERACTION interval is about ±7.5 points wide: an interaction of that size is not excluded.
WP: LENGTH −8.9 [−14.9, −3.4] / −11.9 [−18.3, −6.0], INTERACTION +3.0 [−5.5, +11.5]; COMPOSITION all positive, n.s.
Sensitivity (original): excluding the 7 leak sources (n = 228) and all 279 articles give the same reading
(ELR LENGTH −7.5 / −7.9 and −8.2 / −9.7).
Matched prompt (secondary): ELR LENGTH(competing) −3.4 [−8.9, +2.1] (n.s.), non-competing −6.0 [−11.1, −1.3],
INTERACTION +2.6 [−4.3, +9.8]; WP LENGTH(competing) −8.5 [−14.5, −2.6], non-competing −6.0 [−12.8, +0.9] (n.s.),
INTERACTION −2.6 [−11.5, +6.0]. Under the matched prompt "length effect in both compositions" is NOT met for either
outcome (one composition each); no interaction and no competition-specific loss there either.
Realized: competing sources 205 / 509 / 992 reference tokens (230 / 568 / 1,102 model tokens), 2.6 / 7.3 / 15.1
competing findings; Blind first-write attempts 1.1 / 3.6 / 4.9 (competing) vs 1.0 / 1.8 / 3.1 (non-competing).
Scope as pre-stated: target first only, where E19 found the length effect smallest (E19 first arm −7.8 on n = 243).

## E23 outcome (2026-11-27) — Qwen3-14B, B = 200, n = 279, 6,696 new chains, 0 failures, 0 dirty; `results/e23/e23_report.md`
ELR, per seed (42 / 143 / 244 / 345 / 446): LENGTH −23.3 / −22.2 / −19.7 / −16.8 / −19.4, every CI excluding 0;
COMPETITION −0.7 / +2.2 / +4.3 / +0.0 / +0.0, no CI excluding 0; E13 DiD −24.0 / −20.1 / −15.4 / −16.8 / −19.4,
every CI excluding 0. Across seeds: LENGTH mean −20.3, SD 2.5; pooled −20.3 [−24.9, −15.6] (article bootstrap),
[−25.7, −14.9] (seeds x articles). COMPETITION pooled +1.1 [−3.2, +5.4]. DiD pooled −19.1 [−23.3, −14.8], SD 3.3.
G pooled: Single +0.9 [−1.2, +3.1], Filler −19.4 [−23.4, −15.5], Multi −18.2 [−21.8, −14.7].
-> LENGTH "replicates"; not "seed-sensitive" (SD 2.5 < 10.2); COMPETITION "stays non-negative".
WP: LENGTH −40.1 / −40.5 / −34.1 / −31.9 / −43.4, pooled −38.0 [−42.9, −32.8], SD 4.8 -> replicates. COMPETITION
+6.8 / +12.2 / +6.1 / +8.2 / +10.8 (CI excluding 0 in 3 of 5 seeds), pooled +8.8 [+3.8, +14.0], two-way
[+2.6, +15.0]: at the memory level the Multi source retains the target MORE often than the Filler source.
Seed 42 is the largest LENGTH and DiD of the five on ELR (−23.3 vs mean −20.3; −24.0 vs mean −19.1): the single-seed
figures of record sit at the strong end of the seed range, inside it.
Regeneration: Blind first-write attempts 1.5–1.9 (Filler) and 4.8–5.0 (Multi) in every seed; M4 length stable
(Blind Filler 149–152, Multi 169–171 model tokens).

---
