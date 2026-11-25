# E15 Matched-prompt control — analysis

Matched prompt: one system prompt and one instruction for both arms; the Aware arm only adds the question line.
Original prompt: the committed E13 (Single, Multi) and E14 (Filler) truncation-free chains of the same articles.
Judge-based outcomes; `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples). G = Blind − Aware.
LENGTH = G_Filler − G_Single; COMPETITION = G_Multi − G_Filler; change = matched − original on the same articles.

## qwen3-14b, B = 200

Failed regenerations (%): aware/single 0.0, aware/filler 0.0, aware/multi 0.0, blind/single 0.0, blind/filler 0.0, blind/multi 0.0.
M4 length (model tokens): aware/single 97, aware/filler 136, aware/multi 141, blind/single 81, blind/filler 153, blind/multi 169; mean attempts per write: aware/single 1.00, aware/filler 1.07, aware/multi 1.09, blind/single 1.00, blind/filler 1.21, blind/multi 2.15.

### ELR  (n = 279)

| Prompt | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |
|---|---|---|---|---|---|---|
| matched | 96.1 | 96.8 | 90.3 | 72.8 | 94.6 | 70.3 |
| original | 93.5 | 96.4 | 92.8 | 72.4 | 92.8 | 71.7 |
| matched − original | +2.5 [-0.4, +5.4] | +0.4 [-1.1, +2.2] | -2.5 [-6.1, +1.4] | +0.4 [-4.7, +5.4] | +1.8 [-1.1, +4.7] | -1.4 [-6.5, +3.2] |

| Estimand | Matched | Original | Matched − original |
|---|---|---|---|
| G_single | +0.7 [-1.8, +3.6] | +2.9 [+0.0, +6.1] | -2.2 [-5.7, +1.4] |
| G_filler | -17.6 [-23.3, -12.2]* | -20.4 [-25.8, -15.4]* | +2.9 [-3.2, +8.6] |
| G_multi | -24.4 [-30.1, -18.6]* | -21.1 [-26.5, -15.8]* | -3.2 [-9.0, +2.2] |
| LENGTH | **-18.3 [-24.4, -12.5]*** | -23.3 [-29.7, -17.2]* | +5.0 [-1.8, +11.5] |
| COMPETITION | -6.8 [-13.3, +0.0] | -0.7 [-7.2, +6.1] | -6.1 [-13.6, +1.8] |
| TOTAL | -25.1 [-31.2, -18.6]* | -24.0 [-30.1, -18.3]* | -1.1 [-7.9, +5.7] |

### WP  (n = 279)

| Prompt | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |
|---|---|---|---|---|---|---|
| matched | 95.0 | 92.8 | 87.1 | 54.8 | 93.5 | 60.6 |
| original | 92.5 | 94.6 | 90.7 | 52.7 | 91.8 | 60.6 |
| matched − original | +2.5 [-0.4, +5.7] | -1.8 [-4.7, +1.1] | -3.6 [-7.9, +0.7] | +2.2 [-3.9, +7.9] | +1.8 [-1.8, +5.4] | +0.0 [-5.0, +5.0] |

| Estimand | Matched | Original | Matched − original |
|---|---|---|---|
| G_single | -2.2 [-5.7, +1.4] | +2.2 [-1.1, +5.7] | -4.3 [-8.2, -0.4]* |
| G_filler | -32.3 [-38.4, -26.5]* | -38.0 [-44.1, -31.5]* | +5.7 [-1.1, +12.5] |
| G_multi | -33.0 [-39.1, -27.2]* | -31.2 [-37.3, -25.4]* | -1.8 [-8.6, +5.0] |
| LENGTH | **-30.1 [-37.3, -22.9]*** | -40.1 [-47.0, -33.3]* | +10.0 [+1.8, +18.3]* |
| COMPETITION | -0.7 [-8.6, +7.2] | +6.8 [-0.7, +14.3] | -7.5 [-17.2, +2.2] |
| TOTAL | -30.8 [-37.6, -24.0]* | -33.3 [-40.1, -26.9]* | +2.5 [-5.0, +10.0] |

## qwen3-8b, B = 200

Failed regenerations (%): aware/single 0.0, aware/filler 0.0, aware/multi 0.0, blind/single 0.0, blind/filler 0.0, blind/multi 0.0.
M4 length (model tokens): aware/single 81, aware/filler 115, aware/multi 120, blind/single 70, blind/filler 142, blind/multi 152; mean attempts per write: aware/single 1.01, aware/filler 1.00, aware/multi 1.01, blind/single 1.00, blind/filler 1.13, blind/multi 1.39.

### ELR  (n = 279)

| Prompt | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |
|---|---|---|---|---|---|---|
| matched | 95.3 | 98.6 | 94.3 | 66.7 | 92.8 | 72.0 |
| original | 95.3 | 97.1 | 93.5 | 70.6 | 91.8 | 68.8 |
| matched − original | +0.0 [-2.2, +2.2] | +1.4 [+0.0, +3.2] | +0.7 [-2.5, +4.3] | -3.9 [-9.3, +1.4] | +1.1 [-2.5, +4.7] | +3.2 [-2.5, +8.6] |

| Estimand | Matched | Original | Matched − original |
|---|---|---|---|
| G_single | +3.2 [+0.7, +5.7]* | +1.8 [-0.7, +4.7] | +1.4 [-1.1, +3.9] |
| G_filler | -27.6 [-33.3, -21.5]* | -22.9 [-28.7, -17.6]* | -4.7 [-11.5, +1.8] |
| G_multi | -20.8 [-26.2, -15.4]* | -22.9 [-28.3, -17.6]* | +2.2 [-3.6, +7.9] |
| LENGTH | **-30.8 [-36.6, -24.7]*** | -24.7 [-30.8, -18.6]* | -6.1 [-13.6, +1.1] |
| COMPETITION | +6.8 [-0.7, +14.3] | +0.0 [-7.2, +6.8] | +6.8 [-2.2, +15.4] |
| TOTAL | -24.0 [-29.7, -17.9]* | -24.7 [-30.5, -18.6]* | +0.7 [-5.7, +7.5] |

### WP  (n = 279)

| Prompt | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |
|---|---|---|---|---|---|---|
| matched | 94.3 | 92.8 | 92.1 | 50.5 | 92.1 | 62.0 |
| original | 93.5 | 91.8 | 93.2 | 54.8 | 90.7 | 61.6 |
| matched − original | +0.7 [-1.4, +3.2] | +1.1 [-2.2, +4.3] | -1.1 [-4.7, +2.5] | -4.3 [-9.7, +1.1] | +1.4 [-2.2, +5.0] | +0.4 [-4.7, +5.4] |

| Estimand | Matched | Original | Matched − original |
|---|---|---|---|
| G_single | -1.4 [-5.4, +2.2] | -1.8 [-5.7, +2.2] | +0.4 [-3.2, +3.9] |
| G_filler | -41.6 [-47.3, -35.1]* | -38.4 [-44.1, -31.9]* | -3.2 [-9.7, +2.9] |
| G_multi | -30.1 [-36.2, -23.7]* | -29.0 [-35.1, -22.6]* | -1.1 [-7.9, +5.4] |
| LENGTH | **-40.1 [-47.3, -32.6]*** | -36.6 [-43.7, -28.7]* | -3.6 [-11.1, +3.6] |
| COMPETITION | +11.5 [+3.2, +20.1]* | +9.3 [+1.8, +16.8]* | +2.2 [-7.2, +11.8] |
| TOTAL | -28.7 [-35.8, -21.1]* | -27.2 [-33.7, -20.4]* | -1.4 [-8.6, +5.7] |

## Reading rule (pre-registered; primary = ELR, Qwen3-14B, B = 200)

- qwen3-14b, B = 200, ELR: LENGTH matched -18.3 [-24.4, -12.5]* vs original -23.3 [-29.7, -17.2]*; change +5.0 [-1.8, +11.5] -> **retained**
- qwen3-14b, B = 200, WP: LENGTH matched -30.1 [-37.3, -22.9]* vs original -40.1 [-47.0, -33.3]*; change +10.0 [+1.8, +18.3]* -> **retained, attenuated**
- qwen3-8b, B = 200, ELR: LENGTH matched -30.8 [-36.6, -24.7]* vs original -24.7 [-30.8, -18.6]*; change -6.1 [-13.6, +1.1] -> **retained**
- qwen3-8b, B = 200, WP: LENGTH matched -40.1 [-47.3, -32.6]* vs original -36.6 [-43.7, -28.7]*; change -3.6 [-11.1, +3.6] -> **retained**

## Summary and reading (2026-11-23)

- Primary endpoint (ELR LENGTH, Qwen3-14B, B = 200): −18.3 [−24.4, −12.5] under the matched prompt against −23.3
  [−29.7, −17.2] under the original prompts; change +5.0 [−1.8, +11.5]. RETAINED. Qwen3-8B: −30.8 [−36.6, −24.7]
  against −24.7; change −6.1 [−13.6, +1.1]. RETAINED.
- WP LENGTH: 14B −30.1 against −40.1, change +10.0 [+1.8, +18.3] (attenuated by a quarter, 75 % remains); 8B −40.1
  against −36.6 (no change).
- The Blind − Aware loss on the long inputs is therefore not produced by the different writing instructions: with
  one shared system prompt and instruction, removing the question line alone costs 17.6–27.6 ELR points and
  32–42 WP points on the Filler source, and nothing on the short Single source.
- No cell rate moved by more than 4.3 points between prompts, and no cell change has a CI excluding 0.
- COMPETITION under the matched prompt: ELR 14B −6.8 [−13.3, +0.0], 8B +6.8 [−0.7, +14.3]; WP 14B −0.7, 8B +11.5
  [+3.2, +20.1]. Opposite signs in the two models; still no evidence for a competition-specific loss.
- Sensitivity (`e15_sensitivity.csv`): excluding the 7 E16 leak sources or the 77 repeated-target sources leaves
  LENGTH negative with a CI excluding 0 in both models and outcomes (14B ELR −18.8 and −22.3); the 14B ELR
  COMPETITION estimate shrinks to −5.9 [−12.5, +0.7] and −2.5 [−10.9, +5.9].
- By the pre-registered rule B = 100 was not run. Limits: one matched wording (the shared instruction is the
  "condense" wording), one budget, two Qwen models, single seed.
