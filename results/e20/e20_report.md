# E20 Full-source reading and loss stage — analysis

FULL = the reader's answer straight from the uncompressed source (same reader prompt and settings as every final
answer). M4 cells are the committed truncation-free chains of E13 / E14. `*` = 95 % CI excludes 0 (paired article
bootstrap, 2,000 resamples). Stage table: over articles whose full-source answer is correct; memory evidence = the
evaluator's WP verdict (label recoverability).

## qwen3-8b  (n = 279)

### Full-source ELR (%)

| Source | FULL | vs Single |
|---|---|---|
| single | 95.3 [92.8, 97.5] | — |
| filler | 92.8 [90.0, 95.7] | -2.5 [-5.7, +0.7] |
| multi | 90.7 [87.1, 93.9] | -4.7 [-8.2, -1.4]* |

### M4 against the full source (ELR)

| B | Source | Aware M4 | Blind M4 | Aware M4 − FULL | Blind M4 − FULL |
|---|---|---|---|---|---|
| 100 | single | 96.8 | 94.6 | +1.4 [-1.1, +3.9] | -0.7 [-3.2, +1.8] |
| 100 | filler | 95.3 | 49.1 | +2.5 [-0.7, +5.7] | -43.7 [-49.5, -37.3]* |
| 100 | multi | 92.5 | 60.6 | +1.8 [-1.8, +5.7] | -30.1 [-36.2, -24.4]* |
| 200 | single | 95.3 | 97.1 | +0.0 [-2.9, +2.9] | +1.8 [-1.1, +4.7] |
| 200 | filler | 93.5 | 70.6 | +0.7 [-3.2, +4.7] | -22.2 [-27.6, -16.8]* |
| 200 | multi | 91.8 | 68.8 | +1.1 [-2.5, +5.0] | -21.9 [-27.6, -16.1]* |
| 400 | single | 94.6 | 97.1 | -0.7 [-3.9, +2.5] | +1.8 [-0.7, +4.3] |
| 400 | filler | 88.5 | 82.8 | -4.3 [-8.2, -0.4]* | -10.0 [-14.0, -5.7]* |
| 400 | multi | 86.0 | 81.4 | -4.7 [-9.0, -0.4]* | -9.3 [-14.0, -4.7]* |
| 800 | single | 95.0 | 95.7 | -0.4 [-3.2, +2.5] | +0.4 [-2.9, +3.2] |
| 800 | filler | 89.6 | 84.9 | -3.2 [-7.2, +0.7] | -7.9 [-11.8, -3.9]* |
| 800 | multi | 88.9 | 84.6 | -1.8 [-5.7, +2.5] | -6.1 [-10.4, -1.8]* |

## qwen3-14b  (n = 279)

### Full-source ELR (%)

| Source | FULL | vs Single |
|---|---|---|
| single | 98.6 [97.1, 99.6] | — |
| filler | 93.2 [90.0, 96.1] | -5.4 [-8.2, -2.5]* |
| multi | 93.9 [90.7, 96.4] | -4.7 [-7.9, -1.8]* |

### M4 against the full source (ELR)

| B | Source | Aware M4 | Blind M4 | Aware M4 − FULL | Blind M4 − FULL |
|---|---|---|---|---|---|
| 100 | single | 97.8 | 96.1 | -0.7 [-2.2, +0.7] | -2.5 [-5.0, +0.0] |
| 100 | filler | 89.2 | 62.7 | -3.9 [-7.9, -0.4]* | -30.5 [-36.6, -24.4]* |
| 100 | multi | 94.6 | 63.1 | +0.7 [-1.8, +3.6] | -30.8 [-37.3, -25.1]* |
| 200 | single | 93.5 | 96.4 | -5.0 [-7.9, -2.2]* | -2.2 [-4.3, +0.0] |
| 200 | filler | 92.8 | 72.4 | -0.4 [-3.9, +2.9] | -20.8 [-26.2, -15.8]* |
| 200 | multi | 92.8 | 71.7 | -1.1 [-4.3, +1.8] | -22.2 [-27.2, -17.2]* |
| 400 | single | 95.0 | 93.5 | -3.6 [-6.1, -1.4]* | -5.0 [-7.9, -2.2]* |
| 400 | filler | 92.1 | 84.6 | -1.1 [-4.3, +2.5] | -8.6 [-12.9, -3.9]* |
| 400 | multi | 92.5 | 87.8 | -1.4 [-5.0, +2.2] | -6.1 [-10.4, -2.1]* |
| 800 | single | 95.0 | 92.5 | -3.6 [-6.1, -1.4]* | -6.1 [-9.3, -2.9]* |
| 800 | filler | 88.2 | 88.5 | -5.0 [-9.0, -1.4]* | -4.7 [-8.2, -1.1]* |
| 800 | multi | 90.7 | 92.1 | -3.2 [-6.5, +0.0] | -1.8 [-5.0, +1.8] |

## Loss stage (articles with a correct full-source answer)

retained = WP 1 & ELR 1; write loss = WP 0 & ELR 0; read failure = WP 1 & ELR 0; answer without memory = WP 0 & ELR 1.
Write share = WP 0 among wrong final answers (Wilson 95 % CI).

| Model | Memory | B | Mode | Source | n full-correct | retained | write loss | read failure | answer w/o memory | wrong finals | write share of wrong finals |
|---|---|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b | M4 | 100 | aware | single | 266 | 259 (97.4%) | 3 (1.1%) | 1 (0.4%) | 3 (1.1%) | 4 | 75.0 [30.1, 95.4] |
| qwen3-8b | M4 | 100 | blind | single | 266 | 243 (91.4%) | 3 (1.1%) | 5 (1.9%) | 15 (5.6%) | 8 | 37.5 [13.7, 69.4] |
| qwen3-8b | M4 | 100 | aware | filler | 259 | 250 (96.5%) | 6 (2.3%) | 1 (0.4%) | 2 (0.8%) | 7 | 85.7 [48.7, 97.4] |
| qwen3-8b | M4 | 100 | blind | filler | 259 | 75 (29.0%) | 124 (47.9%) | 2 (0.8%) | 58 (22.4%) | 126 | 98.4 [94.4, 99.6] |
| qwen3-8b | M4 | 100 | aware | multi | 253 | 238 (94.1%) | 9 (3.6%) | 3 (1.2%) | 3 (1.2%) | 12 | 75.0 [46.8, 91.1] |
| qwen3-8b | M4 | 100 | blind | multi | 253 | 112 (44.3%) | 82 (32.4%) | 7 (2.8%) | 52 (20.6%) | 89 | 92.1 [84.6, 96.1] |
| qwen3-8b | M4 | 200 | aware | single | 266 | 251 (94.4%) | 6 (2.3%) | 3 (1.1%) | 6 (2.3%) | 9 | 66.7 [35.4, 87.9] |
| qwen3-8b | M4 | 200 | blind | single | 266 | 246 (92.5%) | 5 (1.9%) | 1 (0.4%) | 14 (5.3%) | 6 | 83.3 [43.6, 97.0] |
| qwen3-8b | M4 | 200 | aware | filler | 259 | 237 (91.5%) | 6 (2.3%) | 8 (3.1%) | 8 (3.1%) | 14 | 42.9 [21.4, 67.4] |
| qwen3-8b | M4 | 200 | blind | filler | 259 | 146 (56.4%) | 63 (24.3%) | 4 (1.5%) | 46 (17.8%) | 67 | 94.0 [85.6, 97.7] |
| qwen3-8b | M4 | 200 | aware | multi | 253 | 232 (91.7%) | 10 (4.0%) | 3 (1.2%) | 8 (3.2%) | 13 | 76.9 [49.7, 91.8] |
| qwen3-8b | M4 | 200 | blind | multi | 253 | 153 (60.5%) | 56 (22.1%) | 14 (5.5%) | 30 (11.9%) | 70 | 80.0 [69.2, 87.7] |
| qwen3-8b | M4 | 400 | aware | single | 266 | 250 (94.0%) | 6 (2.3%) | 5 (1.9%) | 5 (1.9%) | 11 | 54.5 [28.0, 78.7] |
| qwen3-8b | M4 | 400 | blind | single | 266 | 243 (91.4%) | 2 (0.8%) | 3 (1.1%) | 18 (6.8%) | 5 | 40.0 [11.8, 76.9] |
| qwen3-8b | M4 | 400 | aware | filler | 259 | 228 (88.0%) | 15 (5.8%) | 8 (3.1%) | 8 (3.1%) | 23 | 65.2 [44.9, 81.2] |
| qwen3-8b | M4 | 400 | blind | filler | 259 | 192 (74.1%) | 24 (9.3%) | 9 (3.5%) | 34 (13.1%) | 33 | 72.7 [55.8, 84.9] |
| qwen3-8b | M4 | 400 | aware | multi | 253 | 220 (87.0%) | 14 (5.5%) | 13 (5.1%) | 6 (2.4%) | 27 | 51.9 [34.0, 69.3] |
| qwen3-8b | M4 | 400 | blind | multi | 253 | 186 (73.5%) | 20 (7.9%) | 16 (6.3%) | 31 (12.3%) | 36 | 55.6 [39.6, 70.5] |
| qwen3-8b | M4 | 800 | aware | single | 266 | 253 (95.1%) | 6 (2.3%) | 2 (0.8%) | 5 (1.9%) | 8 | 75.0 [40.9, 92.9] |
| qwen3-8b | M4 | 800 | blind | single | 266 | 245 (92.1%) | 2 (0.8%) | 7 (2.6%) | 12 (4.5%) | 9 | 22.2 [6.3, 54.7] |
| qwen3-8b | M4 | 800 | aware | filler | 259 | 236 (91.1%) | 12 (4.6%) | 8 (3.1%) | 3 (1.2%) | 20 | 60.0 [38.7, 78.1] |
| qwen3-8b | M4 | 800 | blind | filler | 259 | 200 (77.2%) | 15 (5.8%) | 12 (4.6%) | 32 (12.4%) | 27 | 55.6 [37.3, 72.4] |
| qwen3-8b | M4 | 800 | aware | multi | 253 | 227 (89.7%) | 13 (5.1%) | 5 (2.0%) | 8 (3.2%) | 18 | 72.2 [49.1, 87.5] |
| qwen3-8b | M4 | 800 | blind | multi | 253 | 211 (83.4%) | 13 (5.1%) | 14 (5.5%) | 15 (5.9%) | 27 | 48.1 [30.7, 66.0] |
| qwen3-14b | M4 | 100 | aware | single | 275 | 267 (97.1%) | 3 (1.1%) | 0 (0.0%) | 5 (1.8%) | 3 | 100.0 [43.8, 100.0] |
| qwen3-14b | M4 | 100 | blind | single | 275 | 252 (91.6%) | 4 (1.5%) | 6 (2.2%) | 13 (4.7%) | 10 | 40.0 [16.8, 68.7] |
| qwen3-14b | M4 | 100 | aware | filler | 260 | 234 (90.0%) | 19 (7.3%) | 2 (0.8%) | 5 (1.9%) | 21 | 90.5 [71.1, 97.3] |
| qwen3-14b | M4 | 100 | blind | filler | 260 | 80 (30.8%) | 88 (33.8%) | 1 (0.4%) | 91 (35.0%) | 89 | 98.9 [93.9, 99.8] |
| qwen3-14b | M4 | 100 | aware | multi | 262 | 251 (95.8%) | 3 (1.1%) | 3 (1.1%) | 5 (1.9%) | 6 | 50.0 [18.8, 81.2] |
| qwen3-14b | M4 | 100 | blind | multi | 262 | 122 (46.6%) | 81 (30.9%) | 9 (3.4%) | 50 (19.1%) | 90 | 90.0 [82.1, 94.6] |
| qwen3-14b | M4 | 200 | aware | single | 275 | 252 (91.6%) | 12 (4.4%) | 4 (1.5%) | 7 (2.5%) | 16 | 75.0 [50.5, 89.8] |
| qwen3-14b | M4 | 200 | blind | single | 275 | 257 (93.5%) | 4 (1.5%) | 4 (1.5%) | 10 (3.6%) | 8 | 50.0 [21.5, 78.5] |
| qwen3-14b | M4 | 200 | aware | filler | 260 | 239 (91.9%) | 10 (3.8%) | 2 (0.8%) | 9 (3.5%) | 12 | 83.3 [55.2, 95.3] |
| qwen3-14b | M4 | 200 | blind | filler | 260 | 135 (51.9%) | 56 (21.5%) | 7 (2.7%) | 62 (23.8%) | 63 | 88.9 [78.8, 94.5] |
| qwen3-14b | M4 | 200 | aware | multi | 262 | 245 (93.5%) | 7 (2.7%) | 4 (1.5%) | 6 (2.3%) | 11 | 63.6 [35.4, 84.8] |
| qwen3-14b | M4 | 200 | blind | multi | 262 | 160 (61.1%) | 59 (22.5%) | 6 (2.3%) | 37 (14.1%) | 65 | 90.8 [81.3, 95.7] |
| qwen3-14b | M4 | 400 | aware | single | 275 | 254 (92.4%) | 6 (2.2%) | 5 (1.8%) | 10 (3.6%) | 11 | 54.5 [28.0, 78.7] |
| qwen3-14b | M4 | 400 | blind | single | 275 | 252 (91.6%) | 9 (3.3%) | 7 (2.5%) | 7 (2.5%) | 16 | 56.2 [33.2, 76.9] |
| qwen3-14b | M4 | 400 | aware | filler | 260 | 240 (92.3%) | 11 (4.2%) | 3 (1.2%) | 6 (2.3%) | 14 | 78.6 [52.4, 92.4] |
| qwen3-14b | M4 | 400 | blind | filler | 260 | 195 (75.0%) | 23 (8.8%) | 10 (3.8%) | 32 (12.3%) | 33 | 69.7 [52.7, 82.6] |
| qwen3-14b | M4 | 400 | aware | multi | 262 | 242 (92.4%) | 12 (4.6%) | 2 (0.8%) | 6 (2.3%) | 14 | 85.7 [60.1, 96.0] |
| qwen3-14b | M4 | 400 | blind | multi | 262 | 216 (82.4%) | 17 (6.5%) | 10 (3.8%) | 19 (7.3%) | 27 | 63.0 [44.2, 78.5] |
| qwen3-14b | M4 | 800 | aware | single | 275 | 256 (93.1%) | 9 (3.3%) | 2 (0.7%) | 8 (2.9%) | 11 | 81.8 [52.3, 94.9] |
| qwen3-14b | M4 | 800 | blind | single | 275 | 243 (88.4%) | 10 (3.6%) | 9 (3.3%) | 13 (4.7%) | 19 | 52.6 [31.7, 72.7] |
| qwen3-14b | M4 | 800 | aware | filler | 260 | 231 (88.8%) | 16 (6.2%) | 7 (2.7%) | 6 (2.3%) | 23 | 69.6 [49.1, 84.4] |
| qwen3-14b | M4 | 800 | blind | filler | 260 | 211 (81.2%) | 13 (5.0%) | 7 (2.7%) | 29 (11.2%) | 20 | 65.0 [43.3, 81.9] |
| qwen3-14b | M4 | 800 | aware | multi | 262 | 237 (90.5%) | 12 (4.6%) | 4 (1.5%) | 9 (3.4%) | 16 | 75.0 [50.5, 89.8] |
| qwen3-14b | M4 | 800 | blind | multi | 262 | 229 (87.4%) | 9 (3.4%) | 5 (1.9%) | 19 (7.3%) | 14 | 64.3 [38.8, 83.7] |
| qwen3-14b | M1 | 200 | aware | single | 275 | 256 (93.1%) | 9 (3.3%) | 3 (1.1%) | 7 (2.5%) | 12 | 75.0 [46.8, 91.1] |
| qwen3-14b | M1 | 200 | blind | single | 275 | 254 (92.4%) | 4 (1.5%) | 8 (2.9%) | 9 (3.3%) | 12 | 33.3 [13.8, 60.9] |
| qwen3-14b | M1 | 200 | aware | filler | 260 | 239 (91.9%) | 6 (2.3%) | 5 (1.9%) | 10 (3.8%) | 11 | 54.5 [28.0, 78.7] |
| qwen3-14b | M1 | 200 | blind | filler | 260 | 152 (58.5%) | 47 (18.1%) | 3 (1.2%) | 58 (22.3%) | 50 | 94.0 [83.8, 97.9] |
| qwen3-14b | M1 | 200 | aware | multi | 262 | 242 (92.4%) | 7 (2.7%) | 6 (2.3%) | 7 (2.7%) | 13 | 53.8 [29.1, 76.8] |
| qwen3-14b | M1 | 200 | blind | multi | 262 | 166 (63.4%) | 54 (20.6%) | 6 (2.3%) | 36 (13.7%) | 60 | 90.0 [79.9, 95.3] |

## Reading rule (pre-registered)

- qwen3-8b, B = 100, filler: Blind M4 − FULL -43.7 [-49.5, -37.3]*; write share 98.4 [94.4, 99.6] of 126 wrong finals -> write-stage loss (i True, ii True).
- qwen3-8b, B = 100, multi: Blind M4 − FULL -30.1 [-36.2, -24.4]*; write share 92.1 [84.6, 96.1] of 89 wrong finals -> write-stage loss (i True, ii True).
- qwen3-8b, B = 200, filler: Blind M4 − FULL -22.2 [-27.6, -16.8]*; write share 94.0 [85.6, 97.7] of 67 wrong finals -> write-stage loss (i True, ii True).
- qwen3-8b, B = 200, multi: Blind M4 − FULL -21.9 [-27.6, -16.1]*; write share 80.0 [69.2, 87.7] of 70 wrong finals -> write-stage loss (i True, ii True).
- qwen3-8b, B = 400, filler: Blind M4 − FULL -10.0 [-14.0, -5.7]*; write share 72.7 [55.8, 84.9] of 33 wrong finals -> write-stage loss (i True, ii True).
- qwen3-8b, B = 400, multi: Blind M4 − FULL -9.3 [-14.0, -4.7]*; write share 55.6 [39.6, 70.5] of 36 wrong finals -> NOT established as write-stage loss (i True, ii False).
- qwen3-8b, B = 800, filler: Blind M4 − FULL -7.9 [-11.8, -3.9]*; write share 55.6 [37.3, 72.4] of 27 wrong finals -> NOT established as write-stage loss (i True, ii False).
- qwen3-8b, B = 800, multi: Blind M4 − FULL -6.1 [-10.4, -1.8]*; write share 48.1 [30.7, 66.0] of 27 wrong finals -> NOT established as write-stage loss (i True, ii False).
- qwen3-14b, B = 100, filler: Blind M4 − FULL -30.5 [-36.6, -24.4]*; write share 98.9 [93.9, 99.8] of 89 wrong finals -> write-stage loss (i True, ii True).
- qwen3-14b, B = 100, multi: Blind M4 − FULL -30.8 [-37.3, -25.1]*; write share 90.0 [82.1, 94.6] of 90 wrong finals -> write-stage loss (i True, ii True).
- qwen3-14b, B = 200, filler (PRIMARY): Blind M4 − FULL -20.8 [-26.2, -15.8]*; write share 88.9 [78.8, 94.5] of 63 wrong finals -> write-stage loss (i True, ii True).
- qwen3-14b, B = 200, multi: Blind M4 − FULL -22.2 [-27.2, -17.2]*; write share 90.8 [81.3, 95.7] of 65 wrong finals -> write-stage loss (i True, ii True).
- qwen3-14b, B = 400, filler: Blind M4 − FULL -8.6 [-12.9, -3.9]*; write share 69.7 [52.7, 82.6] of 33 wrong finals -> write-stage loss (i True, ii True).
- qwen3-14b, B = 400, multi: Blind M4 − FULL -6.1 [-10.4, -2.1]*; write share 63.0 [44.2, 78.5] of 27 wrong finals -> NOT established as write-stage loss (i True, ii False).
- qwen3-14b, B = 800, filler: Blind M4 − FULL -4.7 [-8.2, -1.1]*; write share 65.0 [43.3, 81.9] of 20 wrong finals -> NOT established as write-stage loss (i True, ii False).
- qwen3-14b, B = 800, multi: Blind M4 − FULL -1.8 [-5.0, +1.8]; write share 64.3 [38.8, 83.7] of 14 wrong finals -> NOT established as write-stage loss (i False, ii False).

- qwen3-8b: FULL(filler) − FULL(single) -2.5 [-5.7, +0.7] -> source-reading difficulty not shown.
- qwen3-8b: FULL(multi) − FULL(single) -4.7 [-8.2, -1.4]* -> source-reading difficulty contributes.
- qwen3-14b: FULL(filler) − FULL(single) -5.4 [-8.2, -2.5]* -> source-reading difficulty contributes.
- qwen3-14b: FULL(multi) − FULL(single) -4.7 [-7.9, -1.8]* -> source-reading difficulty contributes.
