# E19 Length–position control — analysis

Qwen3-14B, B = 200, truncation-free, four writes + reader, judge-based outcomes. Sources: the E14 filler material with the target
at a fixed position (first / middle / last) and three nested lengths (200 / 500 / 1,000 reference tokens).
G = Blind − Aware. LEN(arm) = G(1000) − G(200). POS = G(other arm) − G(first) at the same length. `*` = 95 % CI excludes 0
(paired article bootstrap, 2,000 resamples). Negative LEN = the Blind − Aware penalty grows with source length.

Chains: 10044; failed regenerations: 0.

## Sources (primary set)

| Arm | Level | Reference tokens | Model tokens | Tokens before target | Tokens after target | Target centre (relative) |
|---|---|---|---|---|---|---|
| first | 200 | 201 [172, 229] | 215 | 13 | 131 | 0.21 |
| first | 500 | 499 [461, 539] | 525 | 13 | 430 | 0.08 |
| first | 1000 | 1001 [866, 1055] | 1044 | 13 | 932 | 0.04 |
| middle | 200 | 203 [183, 229] | 219 | 79 | 68 | 0.53 |
| middle | 500 | 504 [477, 536] | 532 | 231 | 217 | 0.51 |
| middle | 1000 | 1001 [866, 1055] | 1044 | 483 | 461 | 0.51 |
| last | 200 | 199 [170, 228] | 213 | 144 | 0 | 0.86 |
| last | 500 | 501 [475, 528] | 526 | 446 | 0 | 0.95 |
| last | 1000 | 1000 [866, 1055] | 1044 | 945 | 0 | 0.97 |

## original prompts (primary)

M4 length in model tokens (first-write attempts), Aware / Blind:

| Arm | 200 | 500 | 1000 |
|---|---|---|---|
| first | 120 (1.0) / 131 (1.0) | 129 (1.0) / 160 (1.8) | 130 (1.1) / 161 (3.1) |
| middle | 120 (1.0) / 132 (1.0) | 130 (1.1) / 150 (1.4) | 130 (1.1) / 151 (1.5) |
| last | 123 (1.0) / 129 (1.0) | 129 (1.1) / 149 (1.3) | 126 (1.1) / 150 (1.6) |

### ELR  (n = 243)

Cell rates (%), Aware / Blind, and G = Blind − Aware:

| Arm | L = 200 | L = 500 | L = 1000 | LEN = G(1000) − G(200) | Blind(1000) − Blind(200) |
|---|---|---|---|---|---|
| first | 96.7 / 95.5; G -1.2 [-4.5, +1.6] | 95.9 / 89.3; G -6.6 [-10.7, -2.9]* | 95.1 / 86.0; G -9.1 [-13.6, -4.9]* | **-7.8 [-13.2, -2.5]*** | -9.5 [-14.0, -4.9]* |
| middle | 94.2 / 94.7; G +0.4 [-2.9, +3.3] | 92.2 / 82.7; G -9.5 [-14.0, -4.9]* | 93.4 / 64.2; G -29.2 [-35.4, -23.0]* | **-29.6 [-36.2, -23.0]*** | -30.5 [-36.6, -24.3]* |
| last | 95.9 / 95.9; G +0.0 [-2.9, +2.9] | 93.4 / 88.9; G -4.5 [-8.6, +0.0] | 95.9 / 71.2; G -24.7 [-30.9, -19.3]* | **-24.7 [-31.7, -18.5]*** | -24.7 [-30.5, -18.9]* |
| pooled | G -0.3 [-2.3, +1.6] | G -6.9 [-9.7, -4.1]* | G -21.0 [-25.0, -17.3]* | **-20.7 [-25.0, -16.7]*** | -21.5 [-25.8, -17.7]* |

| Contrast (G) | first | middle | last | pooled |
|---|---|---|---|---|
| step 200->500 | -5.3 [-10.3, -0.4]* | -9.9 [-14.8, -4.5]* | -4.5 [-9.9, +0.8] | -6.6 [-10.0, -3.0]* |
| step 500->1000 | -2.5 [-7.8, +2.9] | -19.8 [-26.3, -13.6]* | -20.2 [-27.6, -13.2]* | -14.1 [-18.5, -10.2]* |

| Position contrast (G) | L = 200 | L = 500 | L = 1000 | pooled |
|---|---|---|---|---|
| last − first | +1.2 [-2.5, +5.3] | +2.1 [-2.9, +7.4] | -15.6 [-22.2, -9.5]* | -4.1 [-6.9, -1.2]* |
| middle − first | +1.6 [-2.1, +5.8] | -2.9 [-9.1, +3.3] | -20.2 [-26.3, -14.0]* | -7.1 [-10.7, -3.7]* |
| LEN(last) − LEN(first) | | | | -16.9 [-25.5, -9.5]* |
| LEN(middle) − LEN(first) | | | | -21.8 [-29.2, -14.4]* |

Reference (same articles, existing verdicts; not part of the test): target-only source 94.7 / 96.7, G +2.1 [-1.2, +5.3]; E14 Filler (natural position) 92.2 / 72.0, G -20.2 [-25.9, -14.4]* (n = 243).

### WP  (n = 243)

Cell rates (%), Aware / Blind, and G = Blind − Aware:

| Arm | L = 200 | L = 500 | L = 1000 | LEN = G(1000) − G(200) | Blind(1000) − Blind(200) |
|---|---|---|---|---|---|
| first | 95.9 / 91.8; G -4.1 [-7.8, -0.4]* | 96.7 / 83.1; G -13.6 [-18.1, -9.1]* | 92.2 / 75.7; G -16.5 [-21.8, -11.1]* | **-12.3 [-18.5, -6.2]*** | -16.0 [-21.8, -10.7]* |
| middle | 91.8 / 83.5; G -8.2 [-13.2, -3.3]* | 93.0 / 65.4; G -27.6 [-33.7, -21.4]* | 89.7 / 45.7; G -44.0 [-50.6, -37.4]* | **-35.8 [-43.6, -28.0]*** | -37.9 [-44.4, -30.9]* |
| last | 93.8 / 89.7; G -4.1 [-8.6, +0.4] | 93.4 / 75.7; G -17.7 [-23.5, -12.3]* | 94.2 / 50.6; G -43.6 [-50.2, -37.4]* | **-39.5 [-47.3, -31.3]*** | -39.1 [-45.7, -32.1]* |
| pooled | G -5.5 [-8.4, -2.7]* | G -19.6 [-23.5, -15.9]* | G -34.7 [-39.0, -30.3]* | **-29.2 [-33.9, -24.1]*** | -31.0 [-35.4, -26.5]* |

| Contrast (G) | first | middle | last | pooled |
|---|---|---|---|---|
| step 200->500 | -9.5 [-14.8, -4.5]* | -19.3 [-26.3, -12.3]* | -13.6 [-20.6, -7.0]* | -14.1 [-18.1, -10.0]* |
| step 500->1000 | -2.9 [-9.1, +3.3] | -16.5 [-24.3, -8.6]* | -25.9 [-32.9, -18.5]* | -15.1 [-19.2, -11.0]* |

| Position contrast (G) | L = 200 | L = 500 | L = 1000 | pooled |
|---|---|---|---|---|
| last − first | +0.0 [-5.3, +5.3] | -4.1 [-10.7, +2.1] | -27.2 [-34.6, -19.3]* | -10.4 [-14.4, -6.6]* |
| middle − first | -4.1 [-9.9, +1.6] | -14.0 [-21.0, -6.6]* | -27.6 [-34.6, -20.2]* | -15.2 [-19.6, -11.0]* |
| LEN(last) − LEN(first) | | | | -27.2 [-36.6, -17.7]* |
| LEN(middle) − LEN(first) | | | | -23.5 [-32.5, -14.0]* |

Reference (same articles, existing verdicts; not part of the test): target-only source 93.4 / 95.5, G +2.1 [-1.2, +5.3]; E14 Filler (natural position) 90.1 / 52.3, G -37.9 [-44.4, -31.3]* (n = 243).

## matched prompt (secondary)

M4 length in model tokens (first-write attempts), Aware / Blind:

| Arm | 200 | 500 | 1000 |
|---|---|---|---|
| first | 132 (1.0) / 133 (1.0) | 139 (1.1) / 160 (1.9) | 139 (1.2) / 160 (3.2) |
| middle | 132 (1.0) / 137 (1.0) | 141 (1.1) / 154 (1.5) | 139 (1.2) / 149 (1.5) |
| last | 134 (1.0) / 134 (1.0) | 139 (1.1) / 151 (1.5) | 136 (1.2) / 151 (1.5) |

### ELR  (n = 243)

Cell rates (%), Aware / Blind, and G = Blind − Aware:

| Arm | L = 200 | L = 500 | L = 1000 | LEN = G(1000) − G(200) | Blind(1000) − Blind(200) |
|---|---|---|---|---|---|
| first | 95.9 / 95.5; G -0.4 [-3.7, +2.9] | 96.3 / 89.7; G -6.6 [-10.7, -2.9]* | 94.2 / 88.1; G -6.2 [-11.1, -1.6]* | **-5.8 [-10.7, -0.8]*** | -7.4 [-11.9, -3.3]* |
| middle | 91.8 / 93.8; G +2.1 [-2.1, +6.6] | 91.4 / 84.0; G -7.4 [-12.4, -2.1]* | 88.9 / 62.6; G -26.3 [-33.3, -20.2]* | **-28.4 [-35.8, -21.0]*** | -31.3 [-37.9, -25.5]* |
| last | 95.5 / 96.3; G +0.8 [-2.1, +3.7] | 92.2 / 89.3; G -2.9 [-6.6, +0.4] | 93.4 / 70.4; G -23.0 [-29.2, -16.9]* | **-23.9 [-30.5, -17.3]*** | -25.9 [-31.7, -20.6]* |
| pooled | G +0.8 [-1.0, +2.7] | G -5.6 [-8.6, -2.9]* | G -18.5 [-22.8, -14.7]* | **-19.3 [-24.0, -15.2]*** | -21.5 [-25.5, -17.8]* |

| Contrast (G) | first | middle | last | pooled |
|---|---|---|---|---|
| step 200->500 | -6.2 [-11.5, -1.2]* | -9.5 [-16.0, -2.5]* | -3.7 [-8.6, +1.2] | -6.4 [-10.2, -3.0]* |
| step 500->1000 | +0.4 [-5.8, +6.2] | -18.9 [-26.3, -11.9]* | -20.2 [-27.2, -13.2]* | -12.9 [-17.0, -9.2]* |

| Position contrast (G) | L = 200 | L = 500 | L = 1000 | pooled |
|---|---|---|---|---|
| last − first | +1.2 [-2.9, +5.3] | +3.7 [-1.2, +8.2] | -16.9 [-23.9, -9.9]* | -4.0 [-7.3, -0.7]* |
| middle − first | +2.5 [-3.3, +7.8] | -0.8 [-6.6, +4.9] | -20.2 [-27.2, -13.6]* | -6.2 [-9.9, -2.7]* |
| LEN(last) − LEN(first) | | | | -18.1 [-25.5, -10.7]* |
| LEN(middle) − LEN(first) | | | | -22.6 [-30.9, -14.4]* |

Reference (same articles, existing verdicts; not part of the test): target-only source 96.3 / 97.1, G +0.8 [-2.1, +3.7]; E14 Filler (natural position) 90.5 / 71.6, G -18.9 [-24.7, -13.2]* (n = 243).

### WP  (n = 243)

Cell rates (%), Aware / Blind, and G = Blind − Aware:

| Arm | L = 200 | L = 500 | L = 1000 | LEN = G(1000) − G(200) | Blind(1000) − Blind(200) |
|---|---|---|---|---|---|
| first | 96.7 / 88.1; G -8.6 [-13.2, -4.1]* | 94.2 / 84.8; G -9.5 [-14.8, -4.1]* | 93.4 / 79.0; G -14.4 [-19.8, -9.1]* | **-5.8 [-12.8, +0.8]** | -9.1 [-14.8, -3.7]* |
| middle | 92.2 / 87.2; G -4.9 [-9.9, -0.4]* | 89.3 / 74.1; G -15.2 [-21.0, -9.1]* | 88.9 / 44.4; G -44.4 [-51.0, -38.3]* | **-39.5 [-47.7, -31.7]*** | -42.8 [-49.4, -36.6]* |
| last | 93.0 / 90.5; G -2.5 [-6.2, +1.2] | 91.4 / 79.0; G -12.3 [-18.1, -7.4]* | 92.2 / 50.2; G -42.0 [-48.6, -35.0]* | **-39.5 [-46.9, -32.1]*** | -40.3 [-46.5, -33.7]* |
| pooled | G -5.3 [-8.2, -2.7]* | G -12.3 [-15.9, -8.8]* | G -33.6 [-38.3, -29.2]* | **-28.3 [-33.1, -23.3]*** | -30.7 [-34.7, -26.7]* |

| Contrast (G) | first | middle | last | pooled |
|---|---|---|---|---|
| step 200->500 | -0.8 [-7.0, +5.8] | -10.3 [-17.7, -2.9]* | -9.9 [-16.9, -3.7]* | -7.0 [-11.1, -2.9]* |
| step 500->1000 | -4.9 [-11.9, +1.7] | -29.2 [-37.9, -21.4]* | -29.6 [-37.4, -21.4]* | -21.3 [-25.4, -17.1]* |

| Position contrast (G) | L = 200 | L = 500 | L = 1000 | pooled |
|---|---|---|---|---|
| last − first | +6.2 [+0.8, +11.9]* | -2.9 [-9.9, +4.1] | -27.6 [-35.0, -20.2]* | -8.1 [-11.8, -4.2]* |
| middle − first | +3.7 [-2.9, +10.3] | -5.8 [-13.6, +2.1] | -30.0 [-37.9, -22.2]* | -10.7 [-14.7, -6.3]* |
| LEN(last) − LEN(first) | | | | -33.7 [-43.6, -23.9]* |
| LEN(middle) − LEN(first) | | | | -33.7 [-44.0, -23.9]* |

Reference (same articles, existing verdicts; not part of the test): target-only source 95.9 / 92.6, G -3.3 [-7.0, +0.4]; E14 Filler (natural position) 88.1 / 53.1, G -35.0 [-42.0, -28.4]* (n = 243).

## Reading rule (pre-registered; primary = ELR, original prompts, primary set)

**primary (all nine sources in tolerance)**

- original, ELR (n = 243): LEN_pooled -20.7 [-25.0, -16.7]; first -7.8 [-13.2, -2.5], middle -29.6 [-36.2, -23.0], last -24.7 [-31.7, -18.5]; POS_pooled last − first -4.1 [-6.9, -1.2] -> **length effect with position fixed (at every position); graded; position effect (last − first -4.1)**
- original, WP (n = 243): LEN_pooled -29.2 [-33.9, -24.1]; first -12.3 [-18.5, -6.2], middle -35.8 [-43.6, -28.0], last -39.5 [-47.3, -31.3]; POS_pooled last − first -10.4 [-14.4, -6.6] -> **length effect with position fixed (at every position); graded; position effect (last − first -10.4)**
- matched, ELR (n = 243): LEN_pooled -19.3 [-24.0, -15.2]; first -5.8 [-10.7, -0.8], middle -28.4 [-35.8, -21.0], last -23.9 [-30.5, -17.3]; POS_pooled last − first -4.0 [-7.3, -0.7] -> **length effect with position fixed (at every position); graded; position effect (last − first -4.0)**
- matched, WP (n = 243): LEN_pooled -28.3 [-33.1, -23.3]; first -5.8 [-12.8, +0.8], middle -39.5 [-47.7, -31.7], last -39.5 [-46.9, -32.1]; POS_pooled last − first -8.1 [-11.8, -4.2] -> **length effect with position fixed (CI excludes 0 in: middle, last); graded; position effect (last − first -8.1)**

**excluding the 7 E16 leak sources**

- original, ELR (n = 236): LEN_pooled -20.6 [-25.0, -16.7]; first -7.6 [-13.1, -2.5], middle -29.7 [-36.4, -22.9], last -24.6 [-31.4, -18.2]; POS_pooled last − first -3.8 [-6.6, -1.0] -> **length effect with position fixed (at every position); graded; position effect (last − first -3.8)**
- original, WP (n = 236): LEN_pooled -29.5 [-34.5, -25.0]; first -12.3 [-18.6, -6.4], middle -36.0 [-43.6, -28.0], last -40.3 [-48.3, -32.2]; POS_pooled last − first -10.5 [-14.5, -6.5] -> **length effect with position fixed (at every position); graded; position effect (last − first -10.5)**
- matched, ELR (n = 236): LEN_pooled -19.9 [-24.4, -15.8]; first -6.8 [-11.9, -1.7], middle -28.8 [-36.9, -21.6], last -24.2 [-30.9, -17.8]; POS_pooled last − first -4.0 [-7.2, -0.6] -> **length effect with position fixed (at every position); graded; position effect (last − first -4.0)**
- matched, WP (n = 236): LEN_pooled -29.0 [-33.6, -24.3]; first -6.8 [-14.0, +0.0], middle -39.8 [-47.9, -32.2], last -40.3 [-47.9, -32.6]; POS_pooled last − first -8.2 [-12.4, -4.1] -> **length effect with position fixed (CI excludes 0 in: middle, last); graded; position effect (last − first -8.2)**

**all articles**

- original, ELR (n = 279): LEN_pooled -21.3 [-25.2, -17.4]; first -9.7 [-14.7, -4.7], middle -31.5 [-38.0, -25.1], last -22.6 [-28.7, -16.8]; POS_pooled last − first -3.3 [-6.0, -0.7] -> **length effect with position fixed (at every position); graded; position effect (last − first -3.3)**
- original, WP (n = 279): LEN_pooled -29.7 [-34.1, -25.3]; first -13.3 [-18.6, -7.5], middle -36.9 [-44.1, -29.7], last -39.1 [-45.9, -31.9]; POS_pooled last − first -9.9 [-13.6, -6.3] -> **length effect with position fixed (at every position); graded; position effect (last − first -9.9)**
- matched, ELR (n = 279): LEN_pooled -17.7 [-22.0, -13.5]; first -4.3 [-9.0, +0.4], middle -26.5 [-33.3, -20.1], last -22.2 [-28.7, -16.1]; POS_pooled last − first -3.9 [-7.0, -1.0] -> **length effect with position fixed (CI excludes 0 in: middle, last); graded; position effect (last − first -3.9)**
- matched, WP (n = 279): LEN_pooled -27.7 [-32.4, -23.1]; first -5.4 [-11.8, +0.7], middle -38.0 [-45.2, -30.5], last -39.8 [-46.6, -33.0]; POS_pooled last − first -8.1 [-11.8, -4.7] -> **length effect with position fixed (CI excludes 0 in: middle, last); graded; position effect (last − first -8.1)**


## Summary and reading (written after the analysis, 2026-11-23)

1. **Length effect with the position fixed: yes, at every position, graded.** Primary endpoint (ELR, original
   prompts, n = 243): LEN_pooled −20.7 [−25.0, −16.7]; pooled G −0.3 / −6.9 / −21.0 at 200 / 500 / 1,000 tokens.
   By arm: first −7.8 [−13.2, −2.5], middle −29.6 [−36.2, −23.0], last −24.7 [−31.7, −18.5].
   WP: LEN_pooled −29.2 [−33.9, −24.1]; first −12.3, middle −35.8, last −39.5.
2. **Position alone does not produce the loss.** At 200 tokens there is no ELR gap at any position
   (−1.2 / +0.4 / +0.0) and no position contrast (last − first +1.2, middle − first +1.6, both n.s.).
   The same holds at 500 tokens for ELR.
3. **Position changes how much a long source costs (length × position interaction).** At 1,000 tokens the gap is
   −9.1 with the target first, −29.2 in the middle and −24.7 at the end (last − first −15.6 [−22.2, −9.5],
   middle − first −20.2 [−26.3, −14.0]); LEN(middle) − LEN(first) −21.8 [−29.2, −14.4], LEN(last) − LEN(first)
   −16.9 [−25.5, −9.5]. With the target first the gap stops growing after 500 tokens (step 500→1,000 −2.5, n.s.);
   in the other two arms most of the loss comes from that step (−19.8 and −20.2). The pre-registered pooled
   position contrast is −4.1 [−6.9, −1.2] (ELR) and −10.4 [−14.4, −6.6] (WP), but it is carried entirely by the
   1,000-token level.
4. **The loss is in the Blind cells.** Aware ELR stays between 92.2 and 96.7 % in all nine cells; Blind ELR goes from
   94.7–95.9 % at 200 tokens to 86.0 (first) / 64.2 (middle) / 71.2 % (last) at 1,000.
5. **E14 is consistent with this.** The E14 Filler source (target at its natural position) gives G −20.2 on the same
   articles, between the first (−9.1) and middle (−29.2) arms; the target-only source gives +2.1.
6. **Matched prompt (secondary): same reading.** ELR LEN_pooled −19.3 [−24.0, −15.2]; first −5.8 [−10.7, −0.8],
   middle −28.4, last −23.9. WP LEN_pooled −28.3 [−33.1, −23.3]; the first arm is not significant for WP
   (−5.8 [−12.8, +0.8]).
7. **Sensitivity.** Excluding the 7 E16 leak sources (n = 236) changes no reading. With all 279 articles the
   original-prompt readings are unchanged; under the matched prompt the first-arm ELR effect loses significance
   (−4.3 [−9.0, +0.4]).

What the paper can say: the Blind − Aware loss needs a source that has to be compressed (no loss at 200 tokens at any
position), it grows with source length when the position is held fixed, and it is about three times larger when the
target is not the first item of the source. E14's "LENGTH" component is therefore a real length effect whose size
depends on the target position; it should not be presented as position-free.

Limits: one model, one budget, one seed. Longer sources also contain more trial blocks (1.3 / 2.6 / 4.6), so
"length" here is tokens and blocks together. "First" fixes the absolute and (nearly) the relative start, so the
protection of the first arm cannot be assigned to absolute rather than relative position; middle (relative position
fixed) and last (distance to the end fixed) lose about the same. The 200-token level is a low-compression level
(about 215 model tokens for B = 200), not a no-compression one. Blind first-arm memories needed more regeneration
at 1,000 tokens (3.1 first-write attempts against 1.5–1.6 in the other arms) and are slightly longer (161 against
150 tokens): they were written under a tighter instructed budget and still lost less.
Figure: `figures/pakdd_fig_e19_length_position.(pdf|png)` (`scripts/e19_figure.py`).
