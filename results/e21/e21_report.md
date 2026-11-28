# E21 Source length x evidence composition — analysis

Qwen3-14B, B = 200, truncation-free, four writes + reader, judge-based outcomes, target finding first in every source.
Competing = annotated findings added to the target (new chains); non-competing = filler prose (the E19 `first` arm).
G = Blind − Aware. LENGTH(C) = G(1000, C) − G(200, C); COMPOSITION(L) = G(L, competing) − G(L, non-competing);
INTERACTION = LENGTH(competing) − LENGTH(non-competing). `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples).

New chains: 3348; failed regenerations: 0.

## Competing sources (primary set)

| Level | Reference tokens | Model tokens | Competing findings | Blocks |
|---|---|---|---|---|
| 200 | 205 [180, 230] | 230 | 2.6 | 1.5 |
| 500 | 509 [472, 565] | 568 | 7.3 | 2.8 |
| 1000 | 992 [852, 1050] | 1102 | 15.1 | 4.6 |

## original prompts (primary)

M4 length in model tokens (first-write attempts), Aware / Blind:

| Composition | 200 | 500 | 1000 |
|---|---|---|---|
| competing | 133 (1.1) / 150 (1.1) | 138 (1.3) / 170 (3.6) | 131 (1.2) / 172 (4.9) |
| noncompeting | 120 (1.0) / 131 (1.0) | 129 (1.0) / 160 (1.8) | 130 (1.1) / 162 (3.1) |

### ELR  (n = 235)

Cell rates (%), Aware / Blind, and G = Blind − Aware:

| Composition | L = 200 | L = 500 | L = 1000 | LENGTH = G(1000) − G(200) | Blind(1000) − Blind(200) |
|---|---|---|---|---|---|
| competing | 93.6 / 93.6; G +0.0 [-3.8, +3.8] | 95.7 / 90.2; G -5.5 [-9.4, -2.1]* | 94.5 / 87.2; G -7.2 [-11.9, -3.0]* | **-7.2 [-13.2, -1.7]*** | -6.4 [-11.1, -1.7]* |
| noncompeting | 96.6 / 95.7; G -0.9 [-3.8, +2.1] | 95.7 / 88.9; G -6.8 [-10.6, -3.0]* | 94.9 / 86.0; G -8.9 [-13.2, -5.1]* | **-8.1 [-13.2, -2.6]*** | -9.8 [-14.5, -5.1]* |
| COMPOSITION (competing − non-competing) | +0.9 [-4.3, +6.0] | +1.3 [-4.3, +6.8] | +1.7 [-4.3, +7.2] | INTERACTION **+0.9 [-6.8, +8.1]** | +3.4 [-2.6, +9.4] |

| Step (G) | competing | non-competing |
|---|---|---|
| step 200->500 | -5.5 [-11.1, -0.4]* | -6.0 [-11.1, -0.4]* |
| step 500->1000 | -1.7 [-6.4, +3.0] | -2.1 [-7.2, +3.0] |

### WP  (n = 235)

Cell rates (%), Aware / Blind, and G = Blind − Aware:

| Composition | L = 200 | L = 500 | L = 1000 | LENGTH = G(1000) − G(200) | Blind(1000) − Blind(200) |
|---|---|---|---|---|---|
| competing | 93.6 / 90.2; G -3.4 [-7.2, +0.4] | 94.9 / 85.1; G -9.8 [-14.5, -5.5]* | 93.6 / 81.3; G -12.3 [-17.9, -7.2]* | **-8.9 [-14.9, -3.4]*** | -8.9 [-14.5, -3.8]* |
| noncompeting | 95.7 / 91.9; G -3.8 [-7.7, +0.0] | 96.6 / 83.0; G -13.6 [-18.3, -8.9]* | 91.9 / 76.2; G -15.7 [-21.3, -10.6]* | **-11.9 [-18.3, -6.0]*** | -15.7 [-21.7, -10.2]* |
| COMPOSITION (competing − non-competing) | +0.4 [-5.1, +5.5] | +3.8 [-2.6, +10.2] | +3.4 [-3.8, +10.2] | INTERACTION **+3.0 [-5.5, +11.5]** | +6.8 [-0.9, +14.5] |

| Step (G) | competing | non-competing |
|---|---|---|
| step 200->500 | -6.4 [-11.9, -0.4]* | -9.8 [-15.3, -4.3]* |
| step 500->1000 | -2.6 [-8.5, +3.4] | -2.1 [-8.1, +3.8] |

## matched prompt (secondary)

M4 length in model tokens (first-write attempts), Aware / Blind:

| Composition | 200 | 500 | 1000 |
|---|---|---|---|
| competing | 147 (1.2) / 153 (1.1) | 149 (1.6) / 170 (3.7) | 141 (1.5) / 175 (5.7) |
| noncompeting | 132 (1.0) / 133 (1.0) | 139 (1.1) / 159 (1.8) | 139 (1.2) / 160 (3.2) |

### ELR  (n = 235)

Cell rates (%), Aware / Blind, and G = Blind − Aware:

| Composition | L = 200 | L = 500 | L = 1000 | LENGTH = G(1000) − G(200) | Blind(1000) − Blind(200) |
|---|---|---|---|---|---|
| competing | 94.0 / 92.3; G -1.7 [-5.5, +2.1] | 94.5 / 91.9; G -2.6 [-6.4, +1.3] | 94.0 / 88.9; G -5.1 [-9.4, -0.9]* | **-3.4 [-8.9, +2.1]** | -3.4 [-8.1, +1.3] |
| noncompeting | 95.7 / 95.3; G -0.4 [-3.8, +3.0] | 96.2 / 89.4; G -6.8 [-11.1, -3.0]* | 94.0 / 87.7; G -6.4 [-11.5, -1.7]* | **-6.0 [-11.1, -1.3]*** | -7.7 [-11.9, -3.4]* |
| COMPOSITION (competing − non-competing) | -1.3 [-6.0, +3.4] | +4.3 [-1.3, +9.8] | +1.3 [-5.1, +7.7] | INTERACTION **+2.6 [-4.3, +9.8]** | +4.3 [-1.7, +10.2] |

| Step (G) | competing | non-competing |
|---|---|---|
| step 200->500 | -0.9 [-6.0, +4.3] | -6.4 [-11.1, -1.3]* |
| step 500->1000 | -2.6 [-7.7, +2.1] | +0.4 [-5.5, +6.4] |

### WP  (n = 235)

Cell rates (%), Aware / Blind, and G = Blind − Aware:

| Composition | L = 200 | L = 500 | L = 1000 | LENGTH = G(1000) − G(200) | Blind(1000) − Blind(200) |
|---|---|---|---|---|---|
| competing | 94.0 / 91.1; G -3.0 [-6.8, +0.9] | 94.5 / 87.7; G -6.8 [-11.5, -2.1]* | 93.2 / 81.7; G -11.5 [-16.6, -6.8]* | **-8.5 [-14.5, -2.6]*** | -9.4 [-14.5, -4.7]* |
| noncompeting | 96.6 / 88.1; G -8.5 [-13.2, -3.8]* | 94.5 / 84.7; G -9.8 [-15.3, -4.7]* | 93.6 / 79.1; G -14.5 [-20.0, -8.9]* | **-6.0 [-12.8, +0.9]** | -8.9 [-14.9, -3.0]* |
| COMPOSITION (competing − non-competing) | +5.5 [-0.4, +11.5] | +3.0 [-3.4, +9.4] | +3.0 [-3.8, +9.8] | INTERACTION **-2.6 [-11.5, +6.0]** | -0.4 [-8.1, +6.8] |

| Step (G) | competing | non-competing |
|---|---|---|
| step 200->500 | -3.8 [-9.4, +2.1] | -1.3 [-7.7, +5.1] |
| step 500->1000 | -4.7 [-10.6, +1.3] | -4.7 [-11.5, +2.1] |

## Reading rule (pre-registered)

- original, ELR, primary (common cohort) (n = 235) (PRIMARY): length effect in both compositions; composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -7.2 [-13.2, -1.7]*, non-competing -8.1 [-13.2, -2.6]*, INTERACTION +0.9 [-6.8, +8.1].
- original, ELR, excluding the 7 E16 leak sources (n = 228): length effect in both compositions; composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -7.5 [-13.6, -1.8]*, non-competing -7.9 [-13.6, -2.6]*, INTERACTION +0.4 [-7.0, +7.9].
- original, ELR, all articles with both sources (n = 279): length effect in both compositions; composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -8.2 [-13.6, -3.2]*, non-competing -9.7 [-14.7, -4.7]*, INTERACTION +1.4 [-5.0, +7.5].
- original, WP, primary (common cohort) (n = 235): length effect in both compositions; composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -8.9 [-14.9, -3.4]*, non-competing -11.9 [-18.3, -6.0]*, INTERACTION +3.0 [-5.5, +11.5].
- original, WP, excluding the 7 E16 leak sources (n = 228): length effect in both compositions; composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -9.6 [-15.8, -3.5]*, non-competing -11.8 [-18.4, -5.7]*, INTERACTION +2.2 [-6.6, +11.0].
- original, WP, all articles with both sources (n = 279): length effect in both compositions; composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -7.5 [-12.9, -1.8]*, non-competing -13.3 [-18.6, -7.5]*, INTERACTION +5.7 [-1.8, +13.6].
- matched, ELR, primary (common cohort) (n = 235): length effect NOT in both compositions (competing: no, non-competing: yes); composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -3.4 [-8.9, +2.1], non-competing -6.0 [-11.1, -1.3]*, INTERACTION +2.6 [-4.3, +9.8].
- matched, ELR, excluding the 7 E16 leak sources (n = 228): length effect NOT in both compositions (competing: no, non-competing: yes); composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -3.5 [-9.2, +2.2], non-competing -7.0 [-12.3, -2.2]*, INTERACTION +3.5 [-3.5, +10.1].
- matched, ELR, all articles with both sources (n = 279): length effect NOT in both compositions (competing: no, non-competing: no); composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -3.2 [-8.2, +1.8], non-competing -4.3 [-9.0, +0.4], INTERACTION +1.1 [-5.4, +7.2].
- matched, WP, primary (common cohort) (n = 235): length effect NOT in both compositions (competing: yes, non-competing: no); composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -8.5 [-14.5, -2.6]*, non-competing -6.0 [-12.8, +0.9], INTERACTION -2.6 [-11.5, +6.0].
- matched, WP, excluding the 7 E16 leak sources (n = 228): length effect NOT in both compositions (competing: yes, non-competing: no); composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -8.3 [-14.5, -2.6]*, non-competing -7.0 [-14.0, +0.0], INTERACTION -1.3 [-9.7, +7.5].
- matched, WP, all articles with both sources (n = 279): length effect NOT in both compositions (competing: yes, non-competing: no); composition does not detectably change the length effect; no competition-specific loss at any length. LENGTH competing -8.2 [-13.6, -2.5]*, non-competing -5.4 [-11.8, +0.7], INTERACTION -2.9 [-10.8, +4.7].
