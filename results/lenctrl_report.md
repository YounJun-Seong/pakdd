# E14 Length-matched control for E13 — analysis

Truncation-free protocol; judge-based outcomes; Single and Multi cells are the E13 chains of the same articles.
Filler = same structure and length as the E13 long source, target finding kept, every other span replaced by
non-finding prose from the same trials. `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples).

## qwen3-8b  (n = 279 articles; filler source 1056 model tokens)

Failed regenerations (filler cells): B=100 aware 0.0% / blind 0.0%, B=200 aware 0.0% / blind 0.0%, B=400 aware 0.0% / blind 0.0%, B=800 aware 0.0% / blind 0.0%.
Blind/Filler memory tokens: B=100 66, B=200 145, B=400 306, B=800 549.

### ELR

| B | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi | Blind − Aware, Filler | LENGTH (Filler − Single) | COMPETITION (Multi − Filler) | E13 DiD (Multi − Single) |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | 96.8 | 94.6 | 95.3 | 49.1 | 92.5 | 60.6 | -46.2 [-52.3, -40.1]* | -44.1 [-50.5, -37.3]* | **+14.3 [+7.2, +21.5]*** | -29.7 [-36.2, -23.6]* |
| 200 | 95.3 | 97.1 | 93.5 | 70.6 | 91.8 | 68.8 | -22.9 [-28.7, -17.6]* | -24.7 [-30.8, -18.6]* | **+0.0 [-7.2, +6.8]** | -24.7 [-30.5, -18.6]* |
| 400 | 94.6 | 97.1 | 88.5 | 82.8 | 86.0 | 81.4 | -5.7 [-11.5, -0.4]* | -8.2 [-14.0, -2.2]* | **+1.1 [-6.8, +8.6]** | -7.2 [-12.9, -1.1]* |
| 800 | 95.0 | 95.7 | 89.6 | 84.9 | 88.9 | 84.6 | -4.7 [-9.3, +0.0] | -5.4 [-10.8, +0.4] | **+0.4 [-6.1, +6.5]** | -5.0 [-10.4, +0.0] |

### WP

| B | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi | Blind − Aware, Filler | LENGTH (Filler − Single) | COMPETITION (Multi − Filler) | E13 DiD (Multi − Single) |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | 96.4 | 91.8 | 94.3 | 28.7 | 92.5 | 44.1 | -65.6 [-71.0, -59.9]* | -60.9 [-67.7, -54.5]* | **+17.2 [+9.3, +24.7]*** | -43.7 [-50.2, -37.3]* |
| 200 | 93.5 | 91.8 | 93.2 | 54.8 | 90.7 | 61.6 | -38.4 [-44.1, -31.9]* | -36.6 [-43.7, -28.7]* | **+9.3 [+1.8, +16.8]*** | -27.2 [-33.7, -20.4]* |
| 400 | 94.6 | 91.4 | 88.2 | 74.9 | 90.0 | 78.9 | -13.3 [-19.0, -7.5]* | -10.0 [-16.1, -3.6]* | **+2.2 [-5.4, +9.3]** | -7.9 [-13.6, -2.2]* |
| 800 | 94.3 | 93.9 | 91.0 | 78.9 | 89.2 | 88.9 | -12.2 [-17.2, -7.2]* | -11.8 [-17.6, -6.1]* | **+11.8 [+5.4, +17.9]*** | +0.0 [-4.7, +4.7] |

## qwen3-14b  (n = 279 articles; filler source 1056 model tokens)

Failed regenerations (filler cells): B=100 aware 0.0% / blind 0.0%, B=200 aware 0.0% / blind 0.0%, B=400 aware 0.0% / blind 0.0%, B=800 aware 0.0% / blind 0.0%.
Blind/Filler memory tokens: B=100 75, B=200 152, B=400 312, B=800 579.

### ELR

| B | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi | Blind − Aware, Filler | LENGTH (Filler − Single) | COMPETITION (Multi − Filler) | E13 DiD (Multi − Single) |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | 97.8 | 96.1 | 89.2 | 62.7 | 94.6 | 63.1 | -26.5 [-32.3, -20.4]* | -24.7 [-31.5, -17.9]* | **-5.0 [-12.9, +2.5]** | -29.7 [-36.2, -23.3]* |
| 200 | 93.5 | 96.4 | 92.8 | 72.4 | 92.8 | 71.7 | -20.4 [-25.8, -15.4]* | -23.3 [-29.7, -17.2]* | **-0.7 [-7.2, +6.1]** | -24.0 [-30.1, -18.3]* |
| 400 | 95.0 | 93.5 | 92.1 | 84.6 | 92.5 | 87.8 | -7.5 [-11.8, -2.9]* | -6.1 [-11.1, -0.4]* | **+2.9 [-3.2, +8.6]** | -3.2 [-8.2, +1.8] |
| 800 | 95.0 | 92.5 | 88.2 | 88.5 | 90.7 | 92.1 | +0.4 [-3.2, +4.3] | +2.9 [-2.5, +8.6] | **+1.1 [-4.3, +6.5]** | +3.9 [-0.7, +9.0] |

### WP

| B | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi | Blind − Aware, Filler | LENGTH (Filler − Single) | COMPETITION (Multi − Filler) | E13 DiD (Multi − Single) |
|---|---|---|---|---|---|---|---|---|---|---|
| 100 | 96.4 | 93.2 | 87.8 | 29.4 | 94.6 | 48.0 | -58.4 [-64.5, -52.3]* | -55.2 [-62.0, -48.0]* | **+11.8 [+3.2, +19.0]*** | -43.4 [-50.2, -36.6]* |
| 200 | 92.5 | 94.6 | 90.7 | 52.7 | 91.8 | 60.6 | -38.0 [-44.1, -31.5]* | -40.1 [-47.0, -33.3]* | **+6.8 [-0.7, +14.3]** | -33.3 [-40.1, -26.9]* |
| 400 | 92.8 | 94.3 | 90.7 | 77.8 | 91.8 | 84.2 | -12.9 [-17.9, -8.2]* | -14.3 [-20.1, -8.2]* | **+5.4 [-1.4, +11.8]** | -9.0 [-15.4, -3.2]* |
| 800 | 93.5 | 91.0 | 88.2 | 81.4 | 89.2 | 87.5 | -6.8 [-11.5, -2.5]* | -4.3 [-10.0, +1.1] | **+5.0 [-0.7, +11.1]** | +0.7 [-4.7, +6.1] |

## Reading rule (pre-registered), ELR

- B=100: competition-specific in 0/2 models (-); length-driven in 2/2 (qwen3-8b, qwen3-14b).
- B=200: competition-specific in 0/2 models (-); length-driven in 2/2 (qwen3-8b, qwen3-14b).
- B=400: competition-specific in 0/2 models (-); length-driven in 2/2 (qwen3-8b, qwen3-14b).
- B=800: competition-specific in 0/2 models (-); length-driven in 0/2 (-).

## Summary and interpretation (written after the outcomes; the rule above is the pre-registered part)
- Integrity: 2,232 chains per model, 0 failed regenerations, 0 dirty verdicts; 279 articles in every cell; E13 Single and
  Multi verdicts reused unchanged.
- The COMPETITION component is never negative with a CI excluding 0. It is indistinguishable from 0 for ELR at every
  budget except 8B at 100, where it is POSITIVE (+14.3): replacing the competing findings by non-finding prose makes
  the query-blind loss as large or larger.
- The LENGTH component reproduces the whole E13 interaction: ELR −44.1 / −24.7 / −8.2 (8B) and −24.7 / −23.3 / −6.1
  (14B) at 100 / 200 / 400, against E13 DiDs of −29.7 / −24.7 / −7.2 and −29.7 / −24.0 / −3.2 on the same articles.
- WP shows the same and more: Blind/Filler memories keep the only finding in 28.7 % (8B) and 29.4 % (14B) of sources
  at B = 100, versus 44.1 % and 48.0 % when the rest of the source consists of findings (competition component
  +17.2 and +11.8, CIs exclude 0).
- Reading per the fixed rule: the E13 interaction is length-driven at 100, 200 and 400 in both models and
  competition-specific at no budget. It must be described as query-blind loss under input load (a long source that
  has to be compressed), not as an effect of competing findings. This repeats, at 100–400 tokens and without
  truncation, what Phase-4 ② found at 25 / 50 tokens on the short source.
- Post hoc: a finding surrounded by methods and background prose is dropped by a query-blind writer at least as
  often as a finding surrounded by other findings; the writer does not treat the single result sentence as the
  part worth keeping.
- Limits: filler is non-finding by a lexical filter; 17.6 % of filler spans are borrowed from another trial of the
  same source; two Qwen models; 15 articles excluded by the construction rule.
