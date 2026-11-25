# E16 Filler validation — analysis

Raters A and B are two independent LLM annotators (Claude sessions), blind to stratum and to every result; they are
not human annotators. Codebook: `data/audit/CODEBOOK.md`. Sample: 100 filler spans (home_own 40 / other_own 30 / borrowed 30).

## 1. Deterministic checks (all 4,182 filler spans, 279 sources)

- Target slot identical in every source; reference tokens before the target, filler − long: mean +1.2, max |diff| 20.
- Target sentence occurs more than once: filler 19.0% of sources, E13 long source 27.6% (the original single-span source: once). Duplicates are exact copies carried by other candidates of the home article; in the long source the sentence can
  also sit inside a longer competitor span, which the filler replaces.
- Lexical similarity to the gold evidence: max token Jaccard 0.24, max ROUGE-L recall 0.44; statistical-marker regex hits 0 spans.
- Strata in the population: {'other_own': 2829, 'home_own': 679, 'borrowed': 674}.

## 2. Rated sample (% of spans, Wilson 95 % CI; weighted = population-weighted over the three strata)

| Rater | Measure | home_own (n=40) | other_own (n=30) | borrowed (n=30) | weighted |
|---|---|---|---|---|---|
| A | finding | 0.0 [0.0, 8.8] | 6.7 [1.8, 21.3] | 6.7 [1.8, 21.3] | 5.6 (unweighted 4.0 [1.6, 9.8]) |
| A | any_claim | 12.5 [5.5, 26.1] | 10.0 [3.5, 25.6] | 10.0 [3.5, 25.6] | 10.4 (unweighted 11.0 [6.3, 18.6]) |
| A | target_leak | 2.5 [0.4, 12.9] | 0.0 [0.0, 11.4] | 0.0 [0.0, 11.4] | 0.4 (unweighted 1.0 [0.2, 5.4]) |
| A | topic_related | 72.5 [57.2, 83.9] | 0.0 [0.0, 11.4] | 26.7 [14.2, 44.4] | 16.1 (unweighted 37.0 [28.2, 46.8]) |
| A | broken_text | 5.0 [1.4, 16.5] | 0.0 [0.0, 11.4] | 3.3 [0.6, 16.7] | 1.3 (unweighted 3.0 [1.0, 8.5]) |
| B | finding | 0.0 [0.0, 8.8] | 6.7 [1.8, 21.3] | 6.7 [1.8, 21.3] | 5.6 (unweighted 4.0 [1.6, 9.8]) |
| B | any_claim | 12.5 [5.5, 26.1] | 10.0 [3.5, 25.6] | 10.0 [3.5, 25.6] | 10.4 (unweighted 11.0 [6.3, 18.6]) |
| B | target_leak | 2.5 [0.4, 12.9] | 0.0 [0.0, 11.4] | 0.0 [0.0, 11.4] | 0.4 (unweighted 1.0 [0.2, 5.4]) |
| B | topic_related | 72.5 [57.2, 83.9] | 0.0 [0.0, 11.4] | 26.7 [14.2, 44.4] | 16.1 (unweighted 37.0 [28.2, 46.8]) |
| B | broken_text | 5.0 [1.4, 16.5] | 0.0 [0.0, 11.4] | 3.3 [0.6, 16.7] | 1.3 (unweighted 3.0 [1.0, 8.5]) |
| both | finding | 0.0 [0.0, 8.8] | 6.7 [1.8, 21.3] | 6.7 [1.8, 21.3] | 5.6 (unweighted 4.0 [1.6, 9.8]) |
| both | any_claim | 12.5 [5.5, 26.1] | 10.0 [3.5, 25.6] | 10.0 [3.5, 25.6] | 10.4 (unweighted 11.0 [6.3, 18.6]) |
| both | target_leak | 2.5 [0.4, 12.9] | 0.0 [0.0, 11.4] | 0.0 [0.0, 11.4] | 0.4 (unweighted 1.0 [0.2, 5.4]) |
| both | topic_related | 67.5 [52.0, 79.9] | 0.0 [0.0, 11.4] | 26.7 [14.2, 44.4] | 15.3 (unweighted 35.0 [26.4, 44.7]) |
| both | broken_text | 5.0 [1.4, 16.5] | 0.0 [0.0, 11.4] | 3.3 [0.6, 16.7] | 1.3 (unweighted 3.0 [1.0, 8.5]) |
| either | finding | 0.0 [0.0, 8.8] | 6.7 [1.8, 21.3] | 6.7 [1.8, 21.3] | 5.6 (unweighted 4.0 [1.6, 9.8]) |
| either | any_claim | 12.5 [5.5, 26.1] | 10.0 [3.5, 25.6] | 10.0 [3.5, 25.6] | 10.4 (unweighted 11.0 [6.3, 18.6]) |
| either | target_leak | 2.5 [0.4, 12.9] | 0.0 [0.0, 11.4] | 0.0 [0.0, 11.4] | 0.4 (unweighted 1.0 [0.2, 5.4]) |
| either | topic_related | 77.5 [62.5, 87.7] | 0.0 [0.0, 11.4] | 26.7 [14.2, 44.4] | 16.9 (unweighted 39.0 [30.0, 48.8]) |
| either | broken_text | 5.0 [1.4, 16.5] | 0.0 [0.0, 11.4] | 3.3 [0.6, 16.7] | 1.3 (unweighted 3.0 [1.0, 8.5]) |

Inter-rater agreement: finding 100.0% (kappa 1.00); background_claim 100.0% (kappa 1.00); target_relevance 96.0% (kappa 0.92); duplicates_evidence 100.0% (kappa nan); well_formed 100.0% (kappa 1.00).

Spans flagged by either rater as a finding or a target leak: 5 (listed in `e16_flagged_items.csv`); target leaks: 1.

## 3. Evaluator leak screen (all 279 filler sources, target sentence removed)

- Any label other than Not-Mentioned: 6 / 279 = 2.2 % [1.0, 4.6]; labels: {'NOT_MENTIONED': 273, 'DECREASE': 3, 'INCREASE': 3}.
- Gold label recovered without the target sentence: 3 / 279 = 1.1 % [0.4, 3.1].

## 4. Sensitivity of the E14 decomposition (existing verdicts; LENGTH = Filler − Single, COMPETITION = Multi − Filler)

| Model | Outcome | B | All 279: LENGTH | COMPETITION | excl. flagged/leak sources: n | LENGTH | COMPETITION | excl. repeated-target sources: n | LENGTH | COMPETITION |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b | ELR | 100 | -44.1 [-50.5, -37.3]* | +14.3 [+7.2, +21.5]* | 272 | -44.1 [-51.1, -37.5]* | +14.3 [+7.0, +21.7]* | 202 | -47.5 [-55.9, -39.6]* | +12.9 [+4.0, +21.8]* |
| qwen3-8b | ELR | 200 | -24.7 [-30.8, -18.6]* | +0.0 [-7.2, +6.8] | 272 | -24.6 [-30.9, -18.8]* | +0.4 [-6.6, +7.4] | 202 | -26.7 [-33.7, -19.3]* | +0.0 [-8.9, +8.9] |
| qwen3-8b | ELR | 400 | -8.2 [-14.0, -2.2]* | +1.1 [-6.8, +8.6] | 272 | -8.1 [-14.3, -1.8]* | +1.5 [-6.6, +9.6] | 202 | -6.4 [-13.4, +0.5] | +2.5 [-6.9, +11.9] |
| qwen3-8b | ELR | 800 | -5.4 [-10.8, +0.4] | +0.4 [-6.1, +6.5] | 272 | -5.5 [-11.4, +0.0] | +0.7 [-5.9, +7.0] | 202 | -7.4 [-14.4, -0.5]* | +1.0 [-6.4, +7.9] |
| qwen3-8b | WP | 100 | -60.9 [-67.7, -54.5]* | +17.2 [+9.3, +24.7]* | 272 | -61.0 [-67.6, -53.7]* | +17.6 [+9.6, +25.4]* | 202 | -64.9 [-72.3, -56.9]* | +19.3 [+9.9, +28.7]* |
| qwen3-8b | WP | 200 | -36.6 [-43.7, -28.7]* | +9.3 [+1.8, +16.8]* | 272 | -36.0 [-43.4, -27.9]* | +9.6 [+1.8, +17.3]* | 202 | -38.6 [-47.0, -29.2]* | +6.9 [-2.0, +15.8] |
| qwen3-8b | WP | 400 | -10.0 [-16.1, -3.6]* | +2.2 [-5.4, +9.3] | 272 | -9.6 [-15.8, -3.7]* | +1.8 [-5.5, +9.2] | 202 | -9.9 [-17.3, -2.5]* | +0.0 [-8.9, +8.4] |
| qwen3-8b | WP | 800 | -11.8 [-17.6, -6.1]* | +11.8 [+5.4, +17.9]* | 272 | -11.8 [-17.6, -6.2]* | +12.1 [+5.9, +18.8]* | 202 | -13.9 [-20.8, -6.9]* | +13.4 [+6.4, +20.3]* |
| qwen3-14b | ELR | 100 | -24.7 [-31.5, -17.9]* | -5.0 [-12.9, +2.5] | 272 | -25.0 [-31.6, -18.4]* | -4.8 [-12.5, +3.3] | 202 | -27.2 [-35.1, -18.8]* | -4.0 [-13.4, +5.0] |
| qwen3-14b | ELR | 200 | -23.3 [-29.7, -17.2]* | -0.7 [-7.2, +6.1] | 272 | -23.2 [-29.8, -16.5]* | +0.0 [-7.0, +7.4] | 202 | -27.2 [-35.1, -19.3]* | +0.0 [-8.9, +8.9] |
| qwen3-14b | ELR | 400 | -6.1 [-11.1, -0.4]* | +2.9 [-3.2, +8.6] | 272 | -6.2 [-11.8, -0.7]* | +2.6 [-3.3, +8.8] | 202 | -4.5 [-11.4, +3.0] | +3.0 [-4.5, +10.9] |
| qwen3-14b | ELR | 800 | +2.9 [-2.5, +8.6] | +1.1 [-4.3, +6.5] | 272 | +3.3 [-2.6, +8.8] | +1.1 [-4.0, +6.2] | 202 | +3.5 [-3.5, +10.4] | +1.0 [-5.4, +7.4] |
| qwen3-14b | WP | 100 | -55.2 [-62.0, -48.0]* | +11.8 [+3.2, +19.0]* | 272 | -55.5 [-62.1, -47.8]* | +12.5 [+4.4, +21.0]* | 202 | -58.4 [-66.8, -49.5]* | +13.9 [+4.0, +23.3]* |
| qwen3-14b | WP | 200 | -40.1 [-47.0, -33.3]* | +6.8 [-0.7, +14.3] | 272 | -40.4 [-47.1, -33.5]* | +7.7 [+0.0, +15.1] | 202 | -43.6 [-51.0, -36.1]* | +5.9 [-3.0, +15.3] |
| qwen3-14b | WP | 400 | -14.3 [-20.1, -8.2]* | +5.4 [-1.4, +11.8] | 272 | -14.7 [-20.6, -8.8]* | +5.9 [-0.7, +12.9] | 202 | -14.4 [-21.8, -6.9]* | +4.0 [-4.0, +12.4] |
| qwen3-14b | WP | 800 | -4.3 [-10.0, +1.1] | +5.0 [-0.7, +11.1] | 272 | -4.0 [-9.6, +1.5] | +5.1 [-1.1, +11.4] | 202 | -4.0 [-11.4, +3.0] | +5.9 [-1.0, +13.4] |

Excluded in the flagged/leak analysis: 7 sources (rater target leaks 1, evaluator screen 6); in the repeated-target analysis: 77 sources.

## 5. Summary and reading (2026-11-23)

- Rated sample: 1 of 100 spans leaks the target answer (F016, home article background sentence citing a prior null
  result for the target intervention): 1.0 % [0.2, 5.4] unweighted, 0.4 % population-weighted. The pre-registered
  criterion (upper CI bound below 5 %) is missed by 0.4 points; with n = 100 it could only be met with zero leaks.
- Evaluator screen, full coverage: with the target sentence removed, 6 of 279 filler sources (2.2 % [1.0, 4.6]) are
  still given a direction label, 3 of them the gold label (1.1 %). This criterion-equivalent bound is below 5 %.
- The filler is not finding-free: 4 of 100 spans (5.6 % weighted) contain a result unrelated to the target, 11 %
  contain a result or an effect claim of any kind. With about 15 filler spans per source this is roughly 0.8
  unrelated result statements per source, against about 17 competing findings in the Multi source. The filter is
  lexical; "non-finding prose" should be written as "predominantly non-finding prose".
- 72.5 % of home-article filler spans are topically related to the target trial (methods / background of the same
  study) without giving the direction; filler from other trials is not.
- Target position is matched (same slot, mean +1.2 reference tokens). New asymmetry: the target sentence occurs more
  than once in 19.0 % of filler and 27.6 % of Multi sources (never in Single).
- Sensitivity: excluding the 7 leak sources (n = 272) or the 77 repeated-target sources (n = 202) leaves every E14
  conclusion unchanged at 100 and 200 tokens (LENGTH negative with CI excluding 0 in both models and both outcomes;
  COMPETITION never negative with a CI excluding 0). At 400 tokens the ELR LENGTH component loses significance in
  the n = 202 subset (8B −6.4 [−13.4, +0.5], 14B −4.5 [−11.4, +3.0]).
- Verdict: the E14 conclusion stands on the clean subsets. The raters are LLM annotators of one model family; a
  human pass on `data/audit/e16_sheet_human.csv` is still open.
