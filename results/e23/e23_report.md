# E23 Multi-seed replication of E14 — analysis

Qwen3-14B, B = 200, truncation-free, original prompts, 279 articles, Aware / Blind x Single / Filler / Multi.
Seed 42 = the committed E13 / E14 chains; 143 / 244 / 345 / 446 = new runs (write attempt a: seed s + 100a; reader: s).
G = Blind − Aware. `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples).

Failed regenerations by seed: 42: 0, 143: 0, 244: 0, 345: 0, 446: 0.

## ELR

| Seed | n | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi | LENGTH (Filler − Single) | COMPETITION (Multi − Filler) | E13 DiD (Multi − Single) |
|---|---|---|---|---|---|---|---|---|---|---|
| 42 | 279 | 93.5 | 96.4 | 92.8 | 72.4 | 92.8 | 71.7 | -23.3 [-29.7, -17.2]* | -0.7 [-7.2, +6.1] | -24.0 [-30.1, -18.3]* |
| 143 | 279 | 94.3 | 96.1 | 93.2 | 72.8 | 93.5 | 75.3 | -22.2 [-29.0, -15.1]* | +2.2 [-5.0, +9.0] | -20.1 [-26.2, -14.0]* |
| 244 | 279 | 95.7 | 95.0 | 93.5 | 73.1 | 91.0 | 74.9 | -19.7 [-25.8, -13.6]* | +4.3 [-2.9, +11.1] | -15.4 [-21.5, -9.0]* |
| 345 | 279 | 94.6 | 95.7 | 93.9 | 78.1 | 92.8 | 77.1 | -16.8 [-22.9, -10.8]* | +0.0 [-6.1, +6.5] | -16.8 [-22.9, -10.8]* |
| 446 | 279 | 93.9 | 93.5 | 94.6 | 74.9 | 92.8 | 73.1 | -19.4 [-25.8, -12.5]* | +0.0 [-7.2, +7.2] | -19.4 [-25.1, -13.6]* |

Across seeds (pooled: each article averaged over the five seeds, n = 279 articles complete in every seed):

| Estimand | Mean of 5 seeds | SD across seeds | Range | Negative in | CI excludes 0 in | Pooled, article bootstrap | Pooled, seeds x articles bootstrap |
|---|---|---|---|---|---|---|---|
| LENGTH (Filler − Single) | -20.3 | 2.5 | -23.3 to -16.8 | 5 / 5 | 5 / 5 | -20.3 [-24.9, -15.6]* | -20.3 [-25.7, -14.9]* |
| COMPETITION (Multi − Filler) | +1.1 | 2.1 | -0.7 to +4.3 | 1 / 5 | 0 / 5 | +1.1 [-3.2, +5.4] | +1.1 [-4.2, +6.5] |
| E13 DiD (Multi − Single) | -19.1 | 3.3 | -24.0 to -15.4 | 5 / 5 | 5 / 5 | -19.1 [-23.3, -14.8]* | -19.1 [-24.6, -13.8]* |
| G single | +0.9 | 1.5 | -0.7 to +2.9 | 2 / 5 | 0 / 5 | +0.9 [-1.2, +3.1] | +0.9 [-1.6, +3.6] |
| G filler | -19.4 | 2.0 | -20.4 to -15.8 | 5 / 5 | 5 / 5 | -19.4 [-23.4, -15.5]* | -19.4 [-23.7, -14.8]* |
| G multi | -18.2 | 2.3 | -21.1 to -15.8 | 5 / 5 | 5 / 5 | -18.2 [-21.8, -14.7]* | -18.2 [-22.7, -14.0]* |

## WP

| Seed | n | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi | LENGTH (Filler − Single) | COMPETITION (Multi − Filler) | E13 DiD (Multi − Single) |
|---|---|---|---|---|---|---|---|---|---|---|
| 42 | 279 | 92.5 | 94.6 | 90.7 | 52.7 | 91.8 | 60.6 | -40.1 [-47.0, -33.3]* | +6.8 [-0.7, +14.3] | -33.3 [-40.1, -26.9]* |
| 143 | 279 | 93.5 | 92.8 | 92.5 | 51.3 | 93.2 | 64.2 | -40.5 [-47.7, -33.7]* | +12.2 [+5.0, +19.4]* | -28.3 [-34.4, -22.2]* |
| 244 | 279 | 95.0 | 91.4 | 91.0 | 53.4 | 90.0 | 58.4 | -34.1 [-40.9, -27.2]* | +6.1 [-1.4, +14.0] | -28.0 [-34.8, -21.1]* |
| 345 | 279 | 95.0 | 92.8 | 92.1 | 58.1 | 92.1 | 66.3 | -31.9 [-39.1, -25.1]* | +8.2 [+0.7, +16.1]* | -23.7 [-30.1, -16.8]* |
| 446 | 279 | 93.9 | 93.2 | 92.8 | 48.7 | 91.8 | 58.4 | -43.4 [-50.5, -36.2]* | +10.8 [+2.5, +18.6]* | -32.6 [-39.4, -25.8]* |

Across seeds (pooled: each article averaged over the five seeds, n = 279 articles complete in every seed):

| Estimand | Mean of 5 seeds | SD across seeds | Range | Negative in | CI excludes 0 in | Pooled, article bootstrap | Pooled, seeds x articles bootstrap |
|---|---|---|---|---|---|---|---|
| LENGTH (Filler − Single) | -38.0 | 4.8 | -43.4 to -31.9 | 5 / 5 | 5 / 5 | -38.0 [-42.9, -32.8]* | -38.0 [-44.6, -31.5]* |
| COMPETITION (Multi − Filler) | +8.8 | 2.6 | +6.1 to +12.2 | 0 / 5 | 3 / 5 | +8.8 [+3.8, +14.0]* | +8.8 [+2.6, +15.0]* |
| E13 DiD (Multi − Single) | -29.2 | 3.9 | -33.3 to -23.7 | 5 / 5 | 5 / 5 | -29.2 [-33.8, -24.1]* | -29.2 [-35.3, -23.3]* |
| G single | -1.0 | 2.1 | -3.6 to +2.2 | 4 / 5 | 1 / 5 | -1.0 [-3.4, +1.4] | -1.0 [-4.1, +2.0] |
| G filler | -39.0 | 3.8 | -44.1 to -34.1 | 5 / 5 | 5 / 5 | -39.0 [-43.6, -34.3]* | -39.0 [-44.6, -33.0]* |
| G multi | -30.2 | 2.9 | -33.3 to -25.8 | 5 / 5 | 5 / 5 | -30.2 [-34.8, -25.4]* | -30.2 [-35.7, -24.7]* |

## Regeneration and memory length by cell (mean over articles)

| Seed | Cell | First-write attempts | Attempts per write | M4 model tokens |
|---|---|---|---|---|
| 42 | aware / single | 1.00 | 1.00 | 96 |
| 42 | aware / filler | 1.08 | 1.02 | 127 |
| 42 | aware / multi | 1.09 | 1.02 | 128 |
| 42 | blind / single | 1.01 | 1.00 | 79 |
| 42 | blind / filler | 1.78 | 1.20 | 152 |
| 42 | blind / multi | 4.99 | 2.00 | 170 |
| 143 | aware / single | 1.01 | 1.00 | 96 |
| 143 | aware / filler | 1.06 | 1.02 | 125 |
| 143 | aware / multi | 1.08 | 1.02 | 128 |
| 143 | blind / single | 1.01 | 1.00 | 81 |
| 143 | blind / filler | 1.79 | 1.20 | 152 |
| 143 | blind / multi | 4.81 | 1.97 | 171 |
| 244 | aware / single | 1.01 | 1.00 | 93 |
| 244 | aware / filler | 1.10 | 1.03 | 126 |
| 244 | aware / multi | 1.12 | 1.03 | 128 |
| 244 | blind / single | 1.01 | 1.00 | 79 |
| 244 | blind / filler | 1.61 | 1.15 | 150 |
| 244 | blind / multi | 4.86 | 1.97 | 169 |
| 345 | aware / single | 1.00 | 1.00 | 96 |
| 345 | aware / filler | 1.09 | 1.02 | 127 |
| 345 | aware / multi | 1.12 | 1.03 | 125 |
| 345 | blind / single | 1.02 | 1.00 | 80 |
| 345 | blind / filler | 1.94 | 1.23 | 152 |
| 345 | blind / multi | 4.98 | 2.00 | 171 |
| 446 | aware / single | 1.01 | 1.00 | 96 |
| 446 | aware / filler | 1.06 | 1.01 | 127 |
| 446 | aware / multi | 1.10 | 1.03 | 128 |
| 446 | blind / single | 1.01 | 1.00 | 78 |
| 446 | blind / filler | 1.54 | 1.13 | 149 |
| 446 | blind / multi | 4.98 | 2.00 | 171 |

## Reading rule (pre-registered)

- ELR (PRIMARY): LENGTH replicates (pooled -20.3 [-24.9, -15.6]*; negative with CI excluding 0 in 5 / 5 seeds; seed SD 2.5); not seed-sensitive. COMPETITION stays non-negative (per seed -0.7, +2.2, +4.3, +0.0, +0.0).
- WP: LENGTH replicates (pooled -38.0 [-42.9, -32.8]*; negative with CI excluding 0 in 5 / 5 seeds; seed SD 4.8); not seed-sensitive. COMPETITION stays non-negative (per seed +6.8, +12.2, +6.1, +8.2, +10.8).
