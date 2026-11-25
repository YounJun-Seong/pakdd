# Gate 2 human validation (간소화 기준, 2026-09-05)

240 items, 조건 blind + 셔플. annotation_key.csv는 채점 전에 열지 말 것.

각 item에서 ANSWER가 "INTERVENTION vs COMPARATOR가 OUTCOME에 미치는 효과"에 대해
주장하는 바를 EVIDENCE만 근거로 판정:

1. supported (Y/N) — answer의 주장(방향·단정성)이 evidence로 뒷받침되는가
2. supported=N인 경우 failure_type 하나:
   - qualifier: 방향은 맞지만 유의성/조건/범위 한정어가 사라져 더 강한 주장이 됨
     (no-difference를 효과로 단정, 유의한 효과를 no-difference로 단정 포함)
   - mutation: 방향 자체가 반대
   - omission: 해당 ICO를 다루지 않음
   - weakening: 방향은 맞지만 근거보다 약하게/애매하게만 말함
3. nodiff_to_effect (Y/N) — evidence가 "no significant difference"인데
   answer가 definitive effect를 주장하는가 (가장 위험한 유형, 별도 표기)

외부 의학 지식 사용 금지. evidence span만 근거로 판단.
