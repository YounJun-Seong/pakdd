# E17 WP–ELR disagreement audit — analysis

150 E13 truncation-free Blind/Multi chains (budgets 100 / 200, Qwen3-8B and 14B): WP0_ELR1 80, WP0_ELR0 36, WP1_ELR1 34.
Raters A and B are two independent LLM annotators (Claude sessions), blind to gold label, automatic verdicts, model, budget and class;
they are not human annotators. Codebook: `data/audit/CODEBOOK.md`. No automatic verdict is changed by this audit.

## 1. Evaluator against the raters

| Rater | Text | Label agreement with evaluator (5-way) | kappa | Supported (label = gold) agreement |
|---|---|---|---|---|
| A | memory M4 | 74.7% | 0.51 | 78.7% |
| A | final answer | 94.7% | 0.93 | 96.7% |
| B | memory M4 | 74.7% | 0.52 | 79.3% |
| B | final answer | 96.0% | 0.95 | 97.3% |

Rater A vs rater B: mem_label 96.7% (kappa 0.94); mem_evidence 92.0% (kappa 0.85); ans_label 98.0% (kappa 0.97); ans_grounding 90.0% (kappa 0.86).

## 2. Evaluator error rates implied by the raters

| Rater | WP false negative (WP=0, rater: memory states gold) | WP false positive (WP=1, rater: memory does not) | ELR false positive (ELR=1, rater: answer ≠ gold) | ELR false negative (ELR=0, rater: answer = gold) |
|---|---|---|---|---|
| A | 27/116 = 23.3 % [16.5, 31.7] | 5/34 = 14.7 % [6.4, 30.1] | 4/114 = 3.5 % [1.4, 8.7] | 1/36 = 2.8 % [0.5, 14.2] |
| B | 27/116 = 23.3 % [16.5, 31.7] | 4/34 = 11.8 % [4.7, 26.6] | 2/114 = 1.8 % [0.5, 6.2] | 2/36 = 5.6 % [1.5, 18.1] |
| both raters | 25/116 = 21.6 % [15.0, 29.9] | 4/34 = 11.8 % [4.7, 26.6] | 2/114 = 1.8 % [0.5, 6.2] | 1/36 = 2.8 % [0.5, 14.2] |

("both raters": an evaluator error is counted only when both raters contradict the evaluator.)

## 3. What the WP = 0 & ELR = 1 class consists of (n = 80)

| Category | Rater A | Rater B | Both agree |
|---|---|---|---|
| (a) warrant actually in memory (evaluator miss on M4) | 24/80 = 30.0 % [21.1, 40.8] | 23/80 = 28.7 % [20.0, 39.5] | 22 |
| (b) answer inferred from partial evidence | 28/80 = 35.0 % [25.5, 45.9] | 39/80 = 48.8 % [38.1, 59.5] | 28 |
| (c) answer misattributed from another finding | 12/80 = 15.0 % [8.8, 24.4] | 5/80 = 6.2 % [2.7, 13.8] | 5 |
| (d) answer ungrounded (guess / prior) | 13/80 = 16.2 % [9.7, 25.8] | 11/80 = 13.8 % [7.9, 23.0] | 11 |
| (e) answer not actually correct (evaluator false positive) | 3/80 = 3.8 % [1.3, 10.5] | 2/80 = 2.5 % [0.7, 8.7] | 2 |
| (f) other (stated-but-not-labelled / no claim) | 0/80 = 0.0 % [0.0, 4.6] | 0/80 = 0.0 % [0.0, 4.6] | 0 |

Category agreement between raters on this class: 85.0% (kappa 0.79).

Memory evidence in the WP = 0 & ELR = 1 class: rater A {'PARTIAL': 47, 'EXPLICIT': 26, 'ABSENT': 7}; rater B {'PARTIAL': 53, 'EXPLICIT': 25, 'ABSENT': 2}.

By model and budget (answer without warrant = b + c + d; evaluator error = a + e):

| Model | B | n | A: without warrant / evaluator error | B: without warrant / evaluator error |
|---|---|---|---|---|
| qwen3-14b | 100 | 20 | 65% / 35% | 75% / 25% |
| qwen3-14b | 200 | 20 | 60% / 40% | 65% / 35% |
| qwen3-8b | 100 | 20 | 70% / 30% | 70% / 30% |
| qwen3-8b | 200 | 20 | 70% / 30% | 65% / 35% |

## 4. Control classes

- WP0_ELR0 (n = 36): rater A: memory states gold 8%, answer states gold 3%, grounding {'NO_CLAIM': 18, 'INFERRED': 7, 'UNGROUNDED': 5, 'MISATTRIBUTED': 5, 'STATED': 1}; rater B: memory states gold 11%, answer states gold 6%, grounding {'NO_CLAIM': 19, 'INFERRED': 9, 'UNGROUNDED': 5, 'MISATTRIBUTED': 2, 'STATED': 1}
- WP1_ELR1 (n = 34): rater A: memory states gold 85%, answer states gold 97%, grounding {'STATED': 29, 'INFERRED': 5}; rater B: memory states gold 88%, answer states gold 100%, grounding {'STATED': 29, 'INFERRED': 5}

## 5. Population-weighted reading (class shares from all Blind/Multi chains; pooled class rates, both raters agree)

Pooled rates: memory states the gold label in 27.5% of WP0_ELR1 and 8.3% of WP0_ELR0 items; memory does not state it in 11.8% of WP1_ELR1 items (WP1_ELR0, 3–5 % of chains, was not sampled and is left unchanged). In WP0_ELR1 both raters see an answer without a stated warrant in 65.0% and an evaluator error in 30.0%.

| Model | B | WP (evaluator) | WP false-negative rate among WP=0 | WP, rater-adjusted | WP=0 & ELR=1 (evaluator) | of which answer without stated warrant |
|---|---|---|---|---|---|---|
| qwen3-8b | 100 | 43.9% | 15.4% | 47.8% | 20.7% | 13.5% (both raters) |
| qwen3-8b | 200 | 61.6% | 14.9% | 60.7% | 13.3% | 8.6% (both raters) |
| qwen3-14b | 100 | 48.3% | 15.3% | 51.0% | 18.7% | 12.2% (both raters) |
| qwen3-14b | 200 | 61.2% | 15.2% | 60.3% | 13.9% | 9.1% (both raters) |

## 6. Summary and reading (2026-11-23)

- The answer verdict (ELR) is confirmed: 95–96 % label agreement with either rater (kappa 0.93–0.95); 2 of 114
  ELR = 1 answers are not correct according to both raters.
- The memory verdict (WP) is where the evaluator and the raters differ: 75 % label agreement (kappa 0.51). 25 of 116
  WP = 0 memories state the gold label according to both raters; the evaluator called 23 of them Not-Mentioned.
  These are compressed statements that keep the direction for the intervention but drop the comparator or name a
  broader outcome ("Sunflower cake had no significant effect on carcass traits"; "LCI699 inhibited aldosterone").
  The evaluator is strict about the comparator / outcome match, the codebook tells raters to match generously.
  In the other direction 4 of 34 WP = 1 memories do not state the gold label according to both raters.
- Net effect on the WP level of Blind/Multi is small because the two errors offset: 43.9 -> 47.8 % and 48.3 -> 51.0 %
  at 100 tokens, 61.6 -> 60.7 % and 61.2 -> 60.3 % at 200 tokens (8B, 14B).
- WP = 0 & ELR = 1: about 65 % (both raters) are answers without a stated warrant — mostly inferred from partial
  evidence (35–49 %), then ungrounded (14–16 %) and misattributed from another finding (6–15 %); about 30 % are
  evaluator error (memory actually carries the warrant 28–30 %, answer not correct 2.5–4 %). The masking rates of
  `results/distortion_report.md` (WP = 0 & ELR = 1 in 19–21 % of Blind/Multi chains at 100 tokens, 13–14 % at 200)
  therefore correspond to about 12–14 % and 9 % of chains with a correct answer that the memory does not warrant.
- Limits: LLM raters of one model family (their mutual agreement, kappa 0.86–0.97, is not independent human
  agreement); only Blind/Multi at 100 / 200 tokens was sampled, so evaluator error in the other cells — and its
  effect on any Blind − Aware contrast or DiD — is not measured here; WP1_ELR0 was not sampled. Human sheet:
  `data/audit/e17_sheet_human.csv`.
