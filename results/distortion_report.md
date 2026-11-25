# Evidence-distortion analyses on existing verdicts (2026-11-22)

No new generation or scoring. Exploratory (not pre-registered). Failure types: **omitted** = evaluator finds the target
comparison Not-Mentioned; **hedged** = stated but tentative (Uncertain); **reversed** = Increase <-> Decrease;
**false effect** = gold No-Difference stated as a significant effect; **lost effect** = gold effect stated as no difference.
The last three are asserted wrong labels (distortion in the narrow sense).

## E13 1,000-token source — truncation-free

### 1. Absolute ELR / WP by cell (%, 95 % CI)

| Model | B | Cell | ELR | WP |
|---|---|---|---|---|
| qwen3-8b | 100 | Aware-Single | 95.9 [93.5, 98.0] | 95.6 [93.2, 97.6] |
| qwen3-8b | 100 | Blind-Single | 94.6 [91.8, 96.9] | 92.2 [89.1, 94.9] |
| qwen3-8b | 100 | Aware-Multi | 92.5 [89.5, 95.2] | 92.5 [89.5, 95.6] |
| qwen3-8b | 100 | Blind-Multi | 60.9 [55.4, 66.3] | 43.9 [37.8, 50.0] |
| qwen3-8b | 200 | Aware-Single | 95.2 [92.9, 97.6] | 93.9 [91.2, 96.6] |
| qwen3-8b | 200 | Blind-Single | 96.9 [94.9, 98.6] | 91.5 [88.1, 94.6] |
| qwen3-8b | 200 | Aware-Multi | 91.2 [88.1, 94.2] | 90.8 [87.4, 93.9] |
| qwen3-8b | 200 | Blind-Multi | 69.4 [63.9, 74.5] | 61.6 [55.8, 67.3] |
| qwen3-8b | 400 | Aware-Single | 94.2 [91.5, 96.6] | 94.9 [92.5, 97.3] |
| qwen3-8b | 400 | Blind-Single | 96.9 [94.9, 98.6] | 91.5 [88.1, 94.6] |
| qwen3-8b | 400 | Aware-Multi | 86.4 [82.3, 90.1] | 89.8 [86.4, 93.2] |
| qwen3-8b | 400 | Blind-Multi | 81.3 [76.9, 85.7] | 78.9 [74.5, 83.3] |
| qwen3-8b | 800 | Aware-Single | 94.6 [91.8, 96.9] | 94.2 [91.5, 96.6] |
| qwen3-8b | 800 | Blind-Single | 95.6 [93.2, 97.6] | 93.2 [90.5, 95.9] |
| qwen3-8b | 800 | Aware-Multi | 88.8 [85.0, 92.2] | 89.1 [85.4, 92.5] |
| qwen3-8b | 800 | Blind-Multi | 85.0 [81.0, 88.8] | 88.4 [84.4, 91.8] |
| qwen3-14b | 100 | Aware-Single | 97.3 [95.2, 99.0] | 96.3 [93.9, 98.3] |
| qwen3-14b | 100 | Blind-Single | 95.9 [93.5, 98.0] | 93.5 [90.8, 95.9] |
| qwen3-14b | 100 | Aware-Multi | 94.2 [91.2, 96.6] | 94.6 [91.8, 96.9] |
| qwen3-14b | 100 | Blind-Multi | 62.9 [57.5, 68.7] | 48.3 [42.9, 54.1] |
| qwen3-14b | 200 | Aware-Single | 93.5 [90.5, 96.3] | 92.2 [89.1, 95.2] |
| qwen3-14b | 200 | Blind-Single | 96.3 [93.9, 98.3] | 94.6 [91.8, 96.9] |
| qwen3-14b | 200 | Aware-Multi | 93.2 [90.5, 95.9] | 92.2 [89.1, 94.9] |
| qwen3-14b | 200 | Blind-Multi | 72.1 [67.0, 77.2] | 61.2 [55.4, 66.7] |
| qwen3-14b | 400 | Aware-Single | 95.2 [92.8, 97.6] | 93.2 [90.1, 95.9] |
| qwen3-14b | 400 | Blind-Single | 93.9 [91.2, 96.3] | 93.5 [90.8, 96.3] |
| qwen3-14b | 400 | Aware-Multi | 92.5 [89.5, 95.2] | 92.2 [88.8, 94.9] |
| qwen3-14b | 400 | Blind-Multi | 87.4 [83.3, 91.2] | 84.0 [79.9, 87.8] |
| qwen3-14b | 800 | Aware-Single | 95.2 [92.5, 97.6] | 93.5 [90.8, 96.3] |
| qwen3-14b | 800 | Blind-Single | 92.9 [89.8, 95.6] | 90.1 [86.7, 93.2] |
| qwen3-14b | 800 | Aware-Multi | 90.8 [87.4, 93.9] | 89.5 [85.7, 92.9] |
| qwen3-14b | 800 | Blind-Multi | 91.8 [88.8, 94.9] | 88.1 [84.7, 91.8] |

### 2. Masking in the Multi cells: answer correct although the memory lost the warrant

| Model | B | Cell | WP=0 & ELR=1 (% of chains) | WP=1 & ELR=0 | n with WP=0 | ELR given WP=0 [95 % CI] | ELR given WP=1 |
|---|---|---|---|---|---|---|---|
| qwen3-8b | 100 | Aware-Multi | 1.7 | 1.7 | 22 | 22.7 [4.5, 40.9] | 98.2 |
| qwen3-8b | 100 | Blind-Multi | 20.7 | 3.7 | 165 | 37.0 [30.3, 44.2] | 91.5 |
| qwen3-8b | 200 | Aware-Multi | 3.1 | 2.7 | 27 | 33.3 [14.8, 51.9] | 97.0 |
| qwen3-8b | 200 | Blind-Multi | 13.3 | 5.4 | 113 | 34.5 [25.7, 43.4] | 91.2 |
| qwen3-8b | 400 | Aware-Multi | 2.4 | 5.8 | 30 | 23.3 [10.0, 40.0] | 93.6 |
| qwen3-8b | 400 | Blind-Multi | 11.9 | 9.5 | 62 | 56.5 [43.5, 69.4] | 87.9 |
| qwen3-8b | 800 | Aware-Multi | 3.4 | 3.7 | 32 | 31.2 [15.6, 46.9] | 95.8 |
| qwen3-8b | 800 | Blind-Multi | 6.1 | 9.5 | 34 | 52.9 [38.2, 70.6] | 89.2 |
| qwen3-14b | 100 | Aware-Multi | 1.7 | 2.0 | 16 | 31.2 (n<20) | 97.8 |
| qwen3-14b | 100 | Blind-Multi | 18.7 | 4.1 | 152 | 36.2 [28.9, 44.1] | 91.5 |
| qwen3-14b | 200 | Aware-Multi | 2.4 | 1.4 | 23 | 30.4 [13.0, 47.8] | 98.5 |
| qwen3-14b | 200 | Blind-Multi | 13.9 | 3.1 | 114 | 36.0 [27.2, 44.7] | 95.0 |
| qwen3-14b | 400 | Aware-Multi | 2.0 | 1.7 | 23 | 26.1 [8.7, 43.5] | 98.2 |
| qwen3-14b | 400 | Blind-Multi | 8.2 | 4.8 | 47 | 51.1 [36.2, 66.0] | 94.3 |
| qwen3-14b | 800 | Aware-Multi | 3.1 | 1.7 | 31 | 29.0 [12.9, 45.2] | 98.1 |
| qwen3-14b | 800 | Blind-Multi | 7.1 | 3.4 | 35 | 60.0 [42.9, 77.1] | 96.1 |

### 3. Failure types in Blind-Multi (% of all chains in the cell)

| Model | B | Level | Correct | Omitted | Hedged | Reversed | False effect | Lost effect | Asserted wrong, share of failures |
|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b | 100 | memory | 43.9 | 50.3 | 1.4 | 0.7 | 2.4 | 1.4 | 8% of 165 |
| qwen3-8b | 100 | answer | 60.9 | 19.4 | 2.4 | 4.1 | 4.8 | 8.5 | 44% of 115 |
| qwen3-8b | 200 | memory | 61.6 | 33.0 | 1.7 | 1.0 | 1.4 | 1.4 | 10% of 113 |
| qwen3-8b | 200 | answer | 69.4 | 14.3 | 2.7 | 1.7 | 5.1 | 6.8 | 44% of 90 |
| qwen3-8b | 400 | memory | 78.9 | 16.7 | 1.4 | 0.3 | 2.0 | 0.7 | 15% of 62 |
| qwen3-8b | 400 | answer | 81.3 | 8.8 | 2.7 | 2.0 | 3.7 | 1.4 | 38% of 55 |
| qwen3-8b | 800 | memory | 88.4 | 8.8 | 1.0 | 0.7 | 0.3 | 0.7 | 15% of 34 |
| qwen3-8b | 800 | answer | 85.0 | 5.8 | 2.4 | 2.0 | 3.4 | 1.4 | 45% of 44 |
| qwen3-14b | 100 | memory | 48.3 | 46.3 | 0.3 | 0.0 | 2.4 | 2.7 | 10% of 152 |
| qwen3-14b | 100 | answer | 62.9 | 20.1 | 2.0 | 1.0 | 4.4 | 9.5 | 40% of 109 |
| qwen3-14b | 200 | memory | 61.2 | 32.3 | 1.4 | 1.0 | 2.7 | 1.4 | 13% of 114 |
| qwen3-14b | 200 | answer | 72.1 | 16.7 | 2.4 | 1.0 | 3.4 | 4.4 | 32% of 82 |
| qwen3-14b | 400 | memory | 84.0 | 12.9 | 1.4 | 0.0 | 0.7 | 1.0 | 11% of 47 |
| qwen3-14b | 400 | answer | 87.4 | 6.8 | 2.0 | 0.7 | 1.7 | 1.4 | 30% of 37 |
| qwen3-14b | 800 | memory | 88.1 | 8.8 | 0.3 | 1.4 | 0.0 | 1.4 | 23% of 35 |
| qwen3-14b | 800 | answer | 91.8 | 4.4 | 0.7 | 1.0 | 1.0 | 1.0 | 38% of 24 |

What the final answer does when the Blind-Multi memory no longer mentions the target:

| Model | B | n | Answer correct | Answer asserts a wrong label | Answer abstains (not mentioned / hedged) |
|---|---|---|---|---|---|
| qwen3-8b | 100 | 148 | 40.5 | 22.3 | 37.2 |
| qwen3-8b | 200 | 97 | 37.1 | 23.7 | 39.2 |
| qwen3-8b | 400 | 49 | 61.2 | 12.2 | 26.5 |
| qwen3-8b | 800 | 26 | 53.8 | 15.4 | 30.8 |
| qwen3-14b | 100 | 136 | 39.0 | 20.6 | 40.4 |
| qwen3-14b | 200 | 95 | 37.9 | 13.7 | 48.4 |
| qwen3-14b | 400 | 38 | 55.3 | 2.6 | 42.1 |
| qwen3-14b | 800 | 26 | 61.5 | 3.8 | 34.6 |

## E13 1,000-token source — enforced cap

### 1. Absolute ELR / WP by cell (%, 95 % CI)

| Model | B | Cell | ELR | WP |
|---|---|---|---|---|
| qwen3-8b | 100 | Aware-Single | 95.6 [93.2, 98.0] | 95.2 [92.9, 97.6] |
| qwen3-8b | 100 | Blind-Single | 94.9 [92.2, 97.3] | 91.8 [88.8, 94.6] |
| qwen3-8b | 100 | Aware-Multi | 92.9 [89.8, 95.6] | 92.5 [89.5, 95.2] |
| qwen3-8b | 100 | Blind-Multi | 58.5 [53.1, 63.9] | 38.8 [33.0, 44.2] |
| qwen3-8b | 200 | Aware-Single | 95.2 [92.9, 97.6] | 93.9 [91.2, 96.6] |
| qwen3-8b | 200 | Blind-Single | 96.9 [94.9, 98.6] | 91.5 [88.1, 94.6] |
| qwen3-8b | 200 | Aware-Multi | 91.5 [88.1, 94.6] | 91.2 [87.8, 94.2] |
| qwen3-8b | 200 | Blind-Multi | 64.3 [58.8, 70.1] | 59.9 [54.4, 65.6] |
| qwen3-8b | 400 | Aware-Single | 94.2 [91.5, 96.6] | 94.9 [92.5, 97.3] |
| qwen3-8b | 400 | Blind-Single | 96.9 [94.9, 98.6] | 91.5 [88.1, 94.6] |
| qwen3-8b | 400 | Aware-Multi | 86.4 [82.3, 90.1] | 89.8 [86.4, 93.2] |
| qwen3-8b | 400 | Blind-Multi | 73.5 [68.7, 78.2] | 72.1 [66.7, 76.9] |
| qwen3-8b | 800 | Aware-Single | 94.6 [91.8, 96.9] | 93.9 [91.2, 96.3] |
| qwen3-8b | 800 | Blind-Single | 95.6 [93.2, 97.6] | 93.2 [90.5, 95.9] |
| qwen3-8b | 800 | Aware-Multi | 88.8 [85.0, 92.2] | 88.8 [85.0, 92.2] |
| qwen3-8b | 800 | Blind-Multi | 84.0 [79.9, 88.1] | 85.7 [81.6, 89.8] |
| qwen3-14b | 100 | Aware-Single | 96.9 [94.9, 98.6] | 95.6 [93.2, 98.0] |
| qwen3-14b | 100 | Blind-Single | 95.6 [93.2, 97.6] | 93.2 [90.5, 95.6] |
| qwen3-14b | 100 | Aware-Multi | 93.9 [91.2, 96.6] | 93.2 [90.1, 95.9] |
| qwen3-14b | 100 | Blind-Multi | 44.9 [39.8, 50.7] | 30.6 [25.5, 35.7] |
| qwen3-14b | 200 | Aware-Single | 93.5 [90.5, 96.3] | 92.2 [89.1, 95.2] |
| qwen3-14b | 200 | Blind-Single | 96.3 [93.9, 98.3] | 94.6 [91.8, 96.9] |
| qwen3-14b | 200 | Aware-Multi | 93.5 [90.8, 96.3] | 91.5 [88.1, 94.6] |
| qwen3-14b | 200 | Blind-Multi | 59.5 [54.1, 65.0] | 53.4 [48.0, 59.2] |
| qwen3-14b | 400 | Aware-Single | 95.2 [92.8, 97.6] | 93.2 [90.1, 95.9] |
| qwen3-14b | 400 | Blind-Single | 93.9 [91.2, 96.3] | 93.5 [90.8, 96.3] |
| qwen3-14b | 400 | Aware-Multi | 91.8 [88.8, 94.9] | 91.5 [88.1, 94.6] |
| qwen3-14b | 400 | Blind-Multi | 76.9 [72.1, 81.6] | 74.1 [69.4, 78.9] |
| qwen3-14b | 800 | Aware-Single | 95.2 [92.5, 97.6] | 93.9 [91.2, 96.3] |
| qwen3-14b | 800 | Blind-Single | 93.2 [90.1, 95.9] | 90.1 [86.7, 93.2] |
| qwen3-14b | 800 | Aware-Multi | 91.2 [87.8, 94.2] | 89.5 [85.7, 92.9] |
| qwen3-14b | 800 | Blind-Multi | 92.2 [89.1, 94.9] | 88.8 [85.0, 92.2] |

### 2. Masking in the Multi cells: answer correct although the memory lost the warrant

| Model | B | Cell | WP=0 & ELR=1 (% of chains) | WP=1 & ELR=0 | n with WP=0 | ELR given WP=0 [95 % CI] | ELR given WP=1 |
|---|---|---|---|---|---|---|---|
| qwen3-8b | 100 | Aware-Multi | 1.7 | 1.4 | 22 | 22.7 [4.5, 40.9] | 98.5 |
| qwen3-8b | 100 | Blind-Multi | 22.4 | 2.7 | 180 | 36.7 [30.0, 43.9] | 93.0 |
| qwen3-8b | 200 | Aware-Multi | 2.7 | 2.4 | 26 | 30.8 [15.4, 50.0] | 97.4 |
| qwen3-8b | 200 | Blind-Multi | 10.5 | 6.1 | 118 | 26.3 [18.6, 34.7] | 89.8 |
| qwen3-8b | 400 | Aware-Multi | 2.4 | 5.8 | 30 | 23.3 [10.0, 40.0] | 93.6 |
| qwen3-8b | 400 | Blind-Multi | 8.8 | 7.5 | 82 | 31.7 [22.0, 41.5] | 89.6 |
| qwen3-8b | 800 | Aware-Multi | 3.4 | 3.4 | 33 | 30.3 [15.2, 45.5] | 96.2 |
| qwen3-8b | 800 | Blind-Multi | 7.1 | 8.8 | 42 | 50.0 [35.7, 64.3] | 89.7 |
| qwen3-14b | 100 | Aware-Multi | 2.4 | 1.7 | 20 | 35.0 [15.0, 55.0] | 98.2 |
| qwen3-14b | 100 | Blind-Multi | 16.0 | 1.7 | 204 | 23.0 [17.6, 28.9] | 94.4 |
| qwen3-14b | 200 | Aware-Multi | 2.7 | 0.7 | 25 | 32.0 [12.0, 52.0] | 99.3 |
| qwen3-14b | 200 | Blind-Multi | 10.9 | 4.8 | 137 | 23.4 [16.1, 30.7] | 91.1 |
| qwen3-14b | 400 | Aware-Multi | 2.0 | 1.7 | 25 | 24.0 [8.0, 44.0] | 98.1 |
| qwen3-14b | 400 | Blind-Multi | 7.5 | 4.8 | 76 | 28.9 [19.7, 38.2] | 93.6 |
| qwen3-14b | 800 | Aware-Multi | 3.1 | 1.4 | 31 | 29.0 [16.1, 45.2] | 98.5 |
| qwen3-14b | 800 | Blind-Multi | 5.8 | 2.4 | 33 | 51.5 [36.4, 66.7] | 97.3 |

### 3. Failure types in Blind-Multi (% of all chains in the cell)

| Model | B | Level | Correct | Omitted | Hedged | Reversed | False effect | Lost effect | Asserted wrong, share of failures |
|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b | 100 | memory | 38.8 | 57.5 | 0.7 | 0.3 | 1.4 | 1.4 | 5% of 180 |
| qwen3-8b | 100 | answer | 58.5 | 23.5 | 1.4 | 2.4 | 6.1 | 8.2 | 40% of 122 |
| qwen3-8b | 200 | memory | 59.9 | 35.0 | 1.7 | 1.0 | 1.0 | 1.4 | 8% of 118 |
| qwen3-8b | 200 | answer | 64.3 | 20.1 | 3.1 | 1.0 | 4.8 | 6.8 | 35% of 105 |
| qwen3-8b | 400 | memory | 72.1 | 22.8 | 1.0 | 1.0 | 2.4 | 0.7 | 15% of 82 |
| qwen3-8b | 400 | answer | 73.5 | 14.3 | 3.1 | 1.7 | 4.1 | 3.4 | 35% of 78 |
| qwen3-8b | 800 | memory | 85.7 | 11.2 | 1.0 | 0.7 | 0.7 | 0.7 | 14% of 42 |
| qwen3-8b | 800 | answer | 84.0 | 7.1 | 2.4 | 1.4 | 3.4 | 1.7 | 40% of 47 |
| qwen3-14b | 100 | memory | 30.6 | 65.3 | 1.4 | 0.3 | 1.7 | 0.7 | 4% of 204 |
| qwen3-14b | 100 | answer | 44.9 | 40.5 | 2.0 | 0.3 | 4.4 | 7.8 | 23% of 162 |
| qwen3-14b | 200 | memory | 53.4 | 44.2 | 0.7 | 0.7 | 0.7 | 0.3 | 4% of 137 |
| qwen3-14b | 200 | answer | 59.5 | 32.7 | 1.0 | 0.3 | 2.4 | 4.1 | 17% of 119 |
| qwen3-14b | 400 | memory | 74.1 | 23.5 | 1.0 | 0.3 | 0.3 | 0.7 | 5% of 76 |
| qwen3-14b | 400 | answer | 76.9 | 16.3 | 1.0 | 0.3 | 2.4 | 3.1 | 25% of 68 |
| qwen3-14b | 800 | memory | 88.8 | 8.2 | 0.3 | 1.4 | 0.0 | 1.4 | 24% of 33 |
| qwen3-14b | 800 | answer | 92.2 | 4.8 | 0.7 | 0.7 | 1.0 | 0.7 | 30% of 23 |

What the final answer does when the Blind-Multi memory no longer mentions the target:

| Model | B | n | Answer correct | Answer asserts a wrong label | Answer abstains (not mentioned / hedged) |
|---|---|---|---|---|---|
| qwen3-8b | 100 | 169 | 38.5 | 21.3 | 40.2 |
| qwen3-8b | 200 | 103 | 28.2 | 18.4 | 53.4 |
| qwen3-8b | 400 | 67 | 31.3 | 17.9 | 50.7 |
| qwen3-8b | 800 | 33 | 51.5 | 15.2 | 33.3 |
| qwen3-14b | 100 | 192 | 23.4 | 14.6 | 62.0 |
| qwen3-14b | 200 | 130 | 23.1 | 10.0 | 66.9 |
| qwen3-14b | 400 | 69 | 27.5 | 10.1 | 62.3 |
| qwen3-14b | 800 | 24 | 50.0 | 4.2 | 45.8 |

## Original span source — enforced cap

### 1. Absolute ELR / WP by cell (%, 95 % CI)

| Model | B | Cell | ELR | WP |
|---|---|---|---|---|
| qwen3-8b | 25 | Aware-Single | 89.5 [86.1, 92.9] | 87.1 [83.3, 90.8] |
| qwen3-8b | 25 | Blind-Single | 88.1 [84.4, 91.8] | 76.2 [71.4, 81.0] |
| qwen3-8b | 25 | Aware-Multi | 89.1 [85.4, 92.5] | 91.8 [88.4, 94.6] |
| qwen3-8b | 25 | Blind-Multi | 71.4 [66.3, 76.5] | 59.2 [53.4, 64.6] |
| qwen3-14b | 25 | Aware-Single | 89.5 [85.7, 92.9] | 87.1 [83.0, 90.8] |
| qwen3-14b | 25 | Blind-Single | 84.0 [79.6, 88.1] | 74.5 [69.4, 79.3] |
| qwen3-14b | 25 | Aware-Multi | 86.4 [82.0, 90.1] | 86.1 [81.6, 90.1] |
| qwen3-14b | 25 | Blind-Multi | 66.0 [60.5, 71.4] | 46.9 [41.2, 52.7] |
| gpt-5.4-mini | 25 | Aware-Single | 88.8 [84.7, 92.5] | 90.5 [87.1, 93.5] |
| gpt-5.4-mini | 25 | Blind-Single | 82.3 [78.2, 86.4] | 76.2 [71.4, 81.0] |
| gpt-5.4-mini | 25 | Aware-Multi | 86.7 [82.7, 90.5] | 91.8 [88.8, 94.9] |
| gpt-5.4-mini | 25 | Blind-Multi | 68.7 [63.6, 74.1] | 52.7 [46.9, 58.5] |

### 2. Masking in the Multi cells: answer correct although the memory lost the warrant

| Model | B | Cell | WP=0 & ELR=1 (% of chains) | WP=1 & ELR=0 | n with WP=0 | ELR given WP=0 [95 % CI] | ELR given WP=1 |
|---|---|---|---|---|---|---|---|
| qwen3-8b | 25 | Aware-Multi | 0.0 | 2.7 | 24 | 0.0 [0.0, 0.0] | 97.0 |
| qwen3-8b | 25 | Blind-Multi | 15.0 | 2.7 | 120 | 36.7 [28.3, 45.8] | 95.4 |
| qwen3-14b | 25 | Aware-Multi | 2.7 | 2.4 | 41 | 19.5 [9.7, 31.7] | 97.2 |
| qwen3-14b | 25 | Blind-Multi | 20.7 | 1.7 | 156 | 39.1 [31.4, 46.2] | 96.4 |
| gpt-5.4-mini | 25 | Aware-Multi | 2.4 | 7.5 | 24 | 29.2 [12.5, 45.8] | 91.9 |
| gpt-5.4-mini | 25 | Blind-Multi | 20.4 | 4.4 | 139 | 43.2 [34.5, 51.1] | 91.6 |

### 3. Failure types in Blind-Multi (% of all chains in the cell)

| Model | B | Level | Correct | Omitted | Hedged | Reversed | False effect | Lost effect | Asserted wrong, share of failures |
|---|---|---|---|---|---|---|---|---|---|
| qwen3-8b | 25 | memory | 59.2 | 34.4 | 0.7 | 2.0 | 1.7 | 2.0 | 14% of 120 |
| qwen3-8b | 25 | answer | 71.4 | 8.2 | 4.1 | 3.7 | 6.8 | 5.8 | 57% of 84 |
| qwen3-14b | 25 | memory | 46.9 | 48.0 | 0.7 | 0.7 | 2.0 | 1.7 | 8% of 156 |
| qwen3-14b | 25 | answer | 66.0 | 10.9 | 3.7 | 1.4 | 6.1 | 11.9 | 57% of 100 |
| gpt-5.4-mini | 25 | memory | 52.7 | 42.9 | 0.0 | 0.7 | 2.7 | 1.0 | 9% of 139 |
| gpt-5.4-mini | 25 | answer | 68.7 | 7.1 | 7.1 | 1.4 | 2.7 | 12.9 | 54% of 92 |

What the final answer does when the Blind-Multi memory no longer mentions the target:

| Model | B | n | Answer correct | Answer asserts a wrong label | Answer abstains (not mentioned / hedged) |
|---|---|---|---|---|---|
| qwen3-8b | 25 | 101 | 40.6 | 31.7 | 27.7 |
| qwen3-14b | 25 | 141 | 40.4 | 30.5 | 29.1 |
| gpt-5.4-mini | 25 | 126 | 45.2 | 30.2 | 24.6 |

## E6 contextual source — truncation-free

### 1. Absolute ELR / WP by cell (%, 95 % CI)

| Model | B | Cell | ELR | WP |
|---|---|---|---|---|
| qwen3-14b | 100 | Aware-Single | 94.6 [91.8, 96.9] | 96.9 [94.9, 98.6] |
| qwen3-14b | 100 | Blind-Single | 94.2 [91.2, 96.6] | 93.9 [91.2, 96.3] |
| qwen3-14b | 100 | Aware-Multi | 95.2 [92.9, 97.6] | 93.5 [90.8, 96.3] |
| qwen3-14b | 100 | Blind-Multi | 86.7 [82.7, 90.5] | 87.1 [83.0, 90.8] |
| qwen3-14b | 200 | Aware-Single | 94.9 [92.2, 97.3] | 94.2 [91.5, 96.9] |
| qwen3-14b | 200 | Blind-Single | 93.5 [90.5, 96.3] | 93.5 [90.8, 96.3] |
| qwen3-14b | 200 | Aware-Multi | 95.6 [93.2, 97.6] | 94.6 [91.8, 96.9] |
| qwen3-14b | 200 | Blind-Multi | 92.2 [88.8, 95.2] | 91.5 [88.1, 94.6] |
| qwen3-14b | 400 | Aware-Single | 95.2 [92.9, 97.6] | 94.9 [92.2, 97.3] |
| qwen3-14b | 400 | Blind-Single | 92.2 [89.1, 95.2] | 92.9 [89.8, 95.6] |
| qwen3-14b | 400 | Aware-Multi | 94.2 [91.5, 96.9] | 94.2 [91.5, 96.6] |
| qwen3-14b | 400 | Blind-Multi | 92.2 [89.1, 95.2] | 91.8 [88.8, 94.6] |

### 2. Masking in the Multi cells: answer correct although the memory lost the warrant

| Model | B | Cell | WP=0 & ELR=1 (% of chains) | WP=1 & ELR=0 | n with WP=0 | ELR given WP=0 [95 % CI] | ELR given WP=1 |
|---|---|---|---|---|---|---|---|
| qwen3-14b | 100 | Aware-Multi | 3.4 | 1.7 | 19 | 52.6 (n<20) | 98.2 |
| qwen3-14b | 100 | Blind-Multi | 5.4 | 5.8 | 38 | 42.1 [26.3, 57.9] | 93.4 |
| qwen3-14b | 200 | Aware-Multi | 2.7 | 1.7 | 16 | 50.0 (n<20) | 98.2 |
| qwen3-14b | 200 | Blind-Multi | 4.8 | 4.1 | 25 | 56.0 [36.0, 76.0] | 95.5 |
| qwen3-14b | 400 | Aware-Multi | 2.4 | 2.4 | 17 | 41.2 (n<20) | 97.5 |
| qwen3-14b | 400 | Blind-Multi | 5.8 | 5.4 | 24 | 70.8 [54.2, 87.5] | 94.1 |

### 3. Failure types in Blind-Multi (% of all chains in the cell)

| Model | B | Level | Correct | Omitted | Hedged | Reversed | False effect | Lost effect | Asserted wrong, share of failures |
|---|---|---|---|---|---|---|---|---|---|
| qwen3-14b | 100 | memory | 87.1 | 9.2 | 0.7 | 0.3 | 2.0 | 0.7 | 24% of 38 |
| qwen3-14b | 100 | answer | 86.7 | 3.7 | 1.7 | 1.0 | 3.7 | 3.1 | 59% of 39 |
| qwen3-14b | 200 | memory | 91.5 | 4.8 | 0.7 | 0.3 | 1.4 | 1.4 | 36% of 25 |
| qwen3-14b | 200 | answer | 92.2 | 1.4 | 1.4 | 0.7 | 2.0 | 2.4 | 65% of 23 |
| qwen3-14b | 400 | memory | 91.8 | 4.1 | 1.4 | 1.4 | 0.7 | 0.7 | 33% of 24 |
| qwen3-14b | 400 | answer | 92.2 | 1.4 | 2.4 | 1.7 | 1.7 | 0.7 | 52% of 23 |

What the final answer does when the Blind-Multi memory no longer mentions the target:

| Model | B | n | Answer correct | Answer asserts a wrong label | Answer abstains (not mentioned / hedged) |
|---|---|---|---|---|---|
| qwen3-14b | 100 | 27 | 51.9 | 22.2 | 25.9 |
| qwen3-14b | 200 | 14 | 57.1 | 21.4 | 21.4 |
| qwen3-14b | 400 | 12 | 75.0 | 16.7 | 8.3 |

