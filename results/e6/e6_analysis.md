# E6 Contextual Evidence Robustness — analysis

Model qwen3-14b; truncation-free protocol; budgets 100 / 200 / 400; n = 294 articles per cell; frozen evaluator.
Design, exclusion rules and reading rule: `docs/phase6_prereg.md` (E6, frozen before generation).
This is a local-context experiment (span + up to two neighbouring sentences per side + ICO provenance); it is not a whole-document validation.
`*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples, seed 42).

## Input audit

| Condition | Candidates | Unique spans | Input tokens (14B) | Span-only tokens (14B) | Context tokens (ref) |
|---|---|---|---|---|---|
| single | 1.00 | 1.00 | 210 (p10–p90 124–291) | 83 | 79 |
| multi | 4.15 | 3.60 | 822 (p10–p90 504–1179) | 294 | 330 |

- Spans located in the full text: 92.7% of candidates (93.9% of targets); 54.1% in a body section, the rest in the abstract. Unlocated candidates keep span + ICO provenance only.
- Single contamination (recorded, not removed): another annotated finding inside the target context 41.8%; a sentence with statistical language 66.3%; either 69.7%.
- Multi overlap: identical evidence across candidates in 37.8% of articles; a context overlapping another candidate in 65.0%; the target finding repeated inside a distractor context in 38.8%; an unlocated candidate in 14.3%.

## Budget compliance, failures, realized memory length

| Arm | B | Cell | Failed % | First-attempt compliance % | Attempts / write | Source tokens | Memory tokens (p90) | Realized ratio % |
|---|---|---|---|---|---|---|---|---|
| context | 100 | aware/multi | 0.0 | 88.9 | 1.36 | 822 | 74 (93) | 9 |
| context | 100 | aware/single | 0.0 | 92.4 | 1.21 | 210 | 72 (93) | 34 |
| context | 100 | blind/multi | 0.0 | 77.8 | 2.13 | 822 | 83 (97) | 10 |
| context | 100 | blind/single | 0.0 | 83.6 | 1.67 | 210 | 80 (97) | 38 |
| context | 200 | aware/multi | 0.0 | 92.5 | 1.12 | 822 | 143 (181) | 17 |
| context | 200 | aware/single | 0.0 | 98.2 | 1.02 | 210 | 121 (159) | 57 |
| context | 200 | blind/multi | 0.0 | 86.0 | 1.33 | 822 | 162 (192) | 20 |
| context | 200 | blind/single | 0.0 | 97.2 | 1.05 | 210 | 134 (179) | 64 |
| context | 400 | aware/multi | 0.0 | 98.0 | 1.02 | 822 | 280 (352) | 34 |
| context | 400 | aware/single | 0.0 | 99.8 | 1.00 | 210 | 226 (286) | 107 |
| context | 400 | blind/multi | 0.0 | 95.7 | 1.05 | 822 | 285 (360) | 35 |
| context | 400 | blind/single | 0.0 | 100.0 | 1.00 | 210 | 206 (269) | 98 |
| span | 100 | aware/multi | 0.0 | 88.6 | 1.34 | 294 | 76 (94) | 26 |
| span | 100 | aware/single | 0.0 | 97.9 | 1.06 | 83 | 60 (82) | 72 |
| span | 100 | blind/multi | 0.0 | 83.2 | 2.05 | 294 | 82 (98) | 28 |
| span | 100 | blind/single | 0.0 | 97.8 | 1.14 | 83 | 59 (90) | 71 |
| span | 200 | aware/multi | 0.0 | 96.5 | 1.06 | 294 | 134 (175) | 45 |
| span | 200 | aware/single | 0.0 | 100.0 | 1.00 | 83 | 96 (136) | 115 |
| span | 200 | blind/multi | 0.0 | 92.9 | 1.18 | 294 | 145 (191) | 49 |
| span | 200 | blind/single | 0.0 | 99.7 | 1.00 | 83 | 79 (118) | 95 |
| span | 400 | aware/multi | 0.0 | 98.9 | 1.01 | 294 | 253 (328) | 86 |
| span | 400 | aware/single | 0.0 | 100.0 | 1.00 | 83 | 218 (288) | 263 |
| span | 400 | blind/multi | 0.0 | 98.8 | 1.01 | 294 | 229 (321) | 78 |
| span | 400 | blind/single | 0.0 | 100.0 | 1.00 | 83 | 146 (218) | 176 |

## ELR — four cells and DiD (complete cases)

| Arm | B | A-S | B-S | A-M | B-M | Blind − Aware, Single | Blind − Aware, Multi | DiD | n | Conservative bound |
|---|---|---|---|---|---|---|---|---|---|---|
| context | 100 | 94.6 | 94.2 | 95.2 | 86.7 | -0.3 [-3.1, +2.4] | -8.5 [-12.6, -4.4]* | **-8.2 [-12.6, -3.4]*** | 294 | -8.2 [-12.6, -3.4]* |
| context | 200 | 94.9 | 93.5 | 95.6 | 92.2 | -1.4 [-4.8, +1.7] | -3.4 [-6.8, +0.0] | **-2.0 [-6.8, +2.7]** | 294 | -2.0 [-6.8, +2.7] |
| context | 400 | 95.2 | 92.2 | 94.2 | 92.2 | -3.1 [-6.1, +0.0] | -2.0 [-5.4, +1.4] | **+1.0 [-3.1, +5.4]** | 294 | +1.0 [-3.1, +5.4] |
| span | 100 | 97.3 | 95.9 | 96.9 | 93.5 | -1.4 [-4.4, +1.7] | -3.4 [-6.5, -0.3]* | **-2.0 [-6.5, +2.4]** | 294 | -2.0 [-6.5, +2.4] |
| span | 200 | 93.5 | 96.3 | 93.2 | 94.6 | +2.7 [-0.3, +5.8] | +1.4 [-2.0, +4.4] | **-1.4 [-5.4, +2.7]** | 294 | -1.4 [-5.4, +2.7] |
| span | 400 | 95.2 | 93.9 | 94.6 | 92.9 | -1.4 [-4.4, +1.7] | -1.7 [-4.8, +1.0] | **-0.3 [-4.1, +3.1]** | 294 | -0.3 [-4.1, +3.1] |

### ELR — does context change the interaction? Delta = DiD(context) − DiD(span-only)

| B | DiD context | DiD span-only | Delta |
|---|---|---|---|
| 100 | -8.2 [-12.6, -3.4]* | -2.0 [-6.5, +2.4] | **-6.1 [-12.2, +0.0]** (n=294) |
| 200 | -2.0 [-6.8, +2.7] | -1.4 [-5.4, +2.7] | **-0.7 [-7.5, +5.8]** (n=294) |
| 400 | +1.0 [-3.1, +5.4] | -0.3 [-4.1, +3.1] | **+1.4 [-4.8, +7.5]** (n=294) |

### ELR — pre-registered secondary subsets (context arm)

| Subset | n articles | B=100 | B=200 | B=400 |
|---|---|---|---|---|
| all | 294 | -8.2 [-12.6, -3.4]* | -2.0 [-6.8, +2.7] | +1.0 [-3.1, +5.4] |
| single_no_annotated_contamination | 171 | -10.5 [-16.4, -4.7]* | -2.3 [-8.2, +3.5] | +2.3 [-2.9, +7.6] |
| single_no_contamination | 89 | -6.7 [-14.6, +0.0] | -1.1 [-10.1, +7.9] | +2.2 [-4.5, +10.1] |
| target_located | 276 | -8.3 [-12.7, -4.0]* | -3.3 [-8.3, +1.4] | +0.7 [-3.6, +5.4] |

## WP — four cells and DiD (complete cases)

| Arm | B | A-S | B-S | A-M | B-M | Blind − Aware, Single | Blind − Aware, Multi | DiD | n | Conservative bound |
|---|---|---|---|---|---|---|---|---|---|---|
| context | 100 | 96.9 | 93.9 | 93.5 | 87.1 | -3.1 [-6.1, -0.3]* | -6.5 [-10.5, -2.7]* | **-3.4 [-7.8, +1.4]** | 294 | -3.4 [-7.8, +1.4] |
| context | 200 | 94.2 | 93.5 | 94.6 | 91.5 | -0.7 [-3.4, +2.0] | -3.1 [-6.8, +0.7] | **-2.4 [-7.1, +2.7]** | 294 | -2.4 [-7.1, +2.7] |
| context | 400 | 94.9 | 92.9 | 94.2 | 91.8 | -2.0 [-5.1, +0.7] | -2.4 [-6.1, +1.4] | **-0.3 [-4.4, +3.7]** | 294 | -0.3 [-4.4, +3.7] |
| span | 100 | 96.3 | 93.5 | 95.6 | 87.8 | -2.7 [-5.8, +0.3] | -7.8 [-12.2, -4.1]* | **-5.1 [-9.9, -0.3]*** | 294 | -5.1 [-9.9, -0.3]* |
| span | 200 | 92.2 | 94.6 | 94.2 | 91.5 | +2.4 [-0.7, +5.4] | -2.7 [-5.8, +0.3] | **-5.1 [-9.5, -1.0]*** | 294 | -5.1 [-9.5, -1.0]* |
| span | 400 | 93.2 | 93.5 | 93.2 | 90.5 | +0.3 [-3.1, +3.7] | -2.7 [-6.1, +0.7] | **-3.1 [-7.8, +1.7]** | 294 | -3.1 [-7.8, +1.7] |

### WP — does context change the interaction? Delta = DiD(context) − DiD(span-only)

| B | DiD context | DiD span-only | Delta |
|---|---|---|---|
| 100 | -3.4 [-7.8, +1.4] | -5.1 [-9.9, -0.3]* | **+1.7 [-4.4, +7.8]** (n=294) |
| 200 | -2.4 [-7.1, +2.7] | -5.1 [-9.5, -1.0]* | **+2.7 [-3.7, +9.5]** (n=294) |
| 400 | -0.3 [-4.4, +3.7] | -3.1 [-7.8, +1.7] | **+2.7 [-3.4, +9.2]** (n=294) |

### WP — pre-registered secondary subsets (context arm)

| Subset | n articles | B=100 | B=200 | B=400 |
|---|---|---|---|---|
| all | 294 | -3.4 [-7.8, +1.4] | -2.4 [-7.1, +2.7] | -0.3 [-4.4, +3.7] |
| single_no_annotated_contamination | 171 | -3.5 [-9.4, +2.3] | -2.3 [-8.8, +4.1] | +2.3 [-3.5, +8.2] |
| single_no_contamination | 89 | -3.4 [-11.2, +5.6] | +4.5 [-3.4, +13.5] | +2.2 [-4.5, +9.0] |
| target_located | 276 | -2.5 [-7.2, +2.2] | -2.5 [-7.6, +2.2] | -1.1 [-5.4, +3.3] |

## References

Final answer straight from the uncompressed context input (no memory step), judged ELR: single +96.3 [+93.9, +98.3]; multi +95.9 [+93.5, +98.0].

Existing evidence-span results for the same model (not re-scored; DiD in pp):

| Experiment | Input | Protocol | Budget | ELR DiD | WP DiD |
|---|---|---|---|---|---|
| E3b | span-only (~294 tok) | truncation-free | 25 | -8.1 [-13.8, -2.5] (n=160) | -10.0 [-18.1, -1.9] |
| E3b | span-only (~294 tok) | truncation-free | 50 | -12.1 [-17.0, -7.3] (n=289) | -16.3 [-22.5, -10.0] |
| E1 | span-only (~294 tok) | enforced | 150 | -7.8 [-12.6, -3.1] | -13.3 [-19.4, -7.5] |
| E1 | span-only (~294 tok) | enforced | 256 | -2.0 [-6.5, +2.4] | -2.4 [-7.8, +2.7] |
| E1 | span-only (~294 tok) | enforced | 512 | +1.0 [-3.1, +5.1] | -2.0 [-6.5, +2.4] |
| E13 | multi-trial spans (~1,121 tok) | truncation-free | 100 | -29.9 [-36.1, -23.5] | -43.5 [-50.3, -36.7] |
| E13 | multi-trial spans (~1,121 tok) | truncation-free | 200 | -23.8 [-29.9, -18.0] | -33.3 [-39.5, -27.2] |
| E13 | multi-trial spans (~1,121 tok) | truncation-free | 400 | -3.7 [-8.8, +0.7] | -8.5 [-14.6, -2.7] |

## Reading rule (pre-registered)

- ELR, B=100: interaction persists with context (-8.2 [-12.6, -3.4]); no detectable change relative to span-only (Delta -6.1 [-12.2, +0.0]).
- ELR, B=200: interaction does not persist with context (-2.0 [-6.8, +2.7]); no detectable change relative to span-only (Delta -0.7 [-7.5, +5.8]).
- ELR, B=400: interaction does not persist with context (+1.0 [-3.1, +5.4]); no detectable change relative to span-only (Delta +1.4 [-4.8, +7.5]).
- WP, B=100: interaction does not persist with context (-3.4 [-7.8, +1.4]); no detectable change relative to span-only (Delta +1.7 [-4.4, +7.8]).
- WP, B=200: interaction does not persist with context (-2.4 [-7.1, +2.7]); no detectable change relative to span-only (Delta +2.7 [-3.7, +9.5]).
- WP, B=400: interaction does not persist with context (-0.3 [-4.4, +3.7]); no detectable change relative to span-only (Delta +2.7 [-3.4, +9.2]).

## Summary and interpretation (written after the outcomes; the rule above is the pre-registered part)

- Integrity: 5,292 chains, 0 failed regenerations, 0 dirty verdicts; no article excluded; design, context window,
  prompts and budgets unchanged after outcomes. E1–E5 and E13 results were not touched (span-only Single reuses the
  committed E13 verdicts).
- With local context and ICO provenance the judge-based ELR interaction persists only at B = 100
  (−8.2 [−12.6, −3.4]); it is absent at 200 and 400. The WP interaction does not reach significance at any budget
  in the context arm (−3.4 / −2.4 / −0.3).
- Context does not detectably change the interaction: no Delta CI excludes 0 (ELR at 100 is borderline,
  −6.1 [−12.2, +0.0]; WP Deltas are positive and non-significant). The data therefore support neither "context
  removes the effect" nor "context amplifies it".
- In the matched span-only arm (truncation-free, same budgets) the ELR interaction is absent at 100–400 and the WP
  interaction is small (−5.1 at 100 and 200). At these budgets the original Multi material (~294 tokens, ~4
  findings) is under little pressure, which agrees with E1.
- Absolute levels stay high: Blind/Multi ELR 86.7 / 92.2 / 92.2 with context (uncompressed input 95.9).
- Secondary subsets agree in sign and size with the full cohort at B = 100 (−10.5 without annotated contamination,
  n = 171; −6.7 [−14.6, +0.0] with no contamination, n = 89, underpowered).
- Post-hoc reading (not pre-registered): the context arm's Multi input is 822 tokens, so B = 100 is a 12 % nominal
  ratio, close to E13's 10 % — yet the DiD is −8.2 here against −29.9 in E13. The two inputs differ in the number
  of distinct findings (about 4 here, about 18 in E13), not in the ratio. This favours the CAPACITY reading of E13
  (loss appears when the budget cannot hold a compact record of every candidate finding) over a pure
  compression-ratio reading: sentences of context are cheap to drop, competing findings are not.
- Limits: one model (Qwen3-14B); local context only (two sentences per side), about half of the located spans are in
  the abstract; ICO provenance makes Blind/Single effectively question-aware; 41.8 % of Single inputs contain another
  annotated finding; context and provenance were tested as one package and cannot be separated.
