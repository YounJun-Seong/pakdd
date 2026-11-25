# Mitigation table (multi-ICO, 25 tokens, depth 5)

| Model | Aware SR | Blind SR | +Instruction SR | +Structured (QAWP) SR | sig-inflation blind→instr→QAWP (%) |
|---|---|---|---|---|---|
| Qwen3-8B | 91.5 | 79.9 | 86.1 | 75.2 | 18 → 9 → 27 |
| Qwen3-14B | 95.9 | 89.5 | 89.8 | 82.0 | 5 → 8 → 16 |
| GPT-5.4-mini | 93.2 | 88.1 | 86.7 | 87.1 | 5 → 7 → 2 |

Paired QAWP−instruction @25tok: 8B −10.9pp [−17.0,−5.1]; 14B −7.8pp [−13.3,−3.1]; GPT +0.3pp [−4.8,+5.4].
