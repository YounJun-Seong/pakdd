#!/bin/bash
# Score Phase-4 outputs with the frozen evaluator: finals (text) and last
# intermediate memories (memory) of results/phase4_{exp}_{model}.jsonl.
#   usage: phase4_score.sh <exp> <model> [<exp> <model> ...]
# Run under supervise_eval.sh so the 32B server is kept alive:
#   bash scripts/supervise_eval.sh "bash scripts/phase4_score.sh budget qwen3-8b"
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
while [ $# -ge 2 ]; do
  exp=$1; m=$2; shift 2
  src=results/phase4_${exp}_${m}.jsonl
  [ -f "$src" ] || { echo "missing $src"; exit 1; }
  mem=results/phase4_${exp}_${m}_mem.jsonl
  # memory rows: same design columns, text := last intermediate memory
  $PY - "$src" "$mem" <<'EOF'
import json, sys
src, dst = sys.argv[1], sys.argv[2]
with open(dst, "w") as f:
    for l in open(src):
        r = json.loads(l)
        r = {k: v for k, v in r.items() if k not in ("text", "steps")}
        r["text"] = r.pop("memory")
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
EOF
  for pass in 1 2 3 4; do
    $PY scripts/score_generic.py --chains "$src" --out "results/phase4_${exp}_${m}_final_scored.csv" --concurrency 256 || exit 1
    $PY scripts/score_generic.py --chains "$mem" --out "results/phase4_${exp}_${m}_mem_scored.csv" --concurrency 256 || exit 1
    n=$($PY -c "
import pandas as pd
print(sum(int(pd.read_csv(f)['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum())
      for f in ['results/phase4_${exp}_${m}_final_scored.csv','results/phase4_${exp}_${m}_mem_scored.csv']))")
    echo "[phase4-score] $exp $m pass $pass: $n dirty"
    [ "$n" = "0" ] && break
    sleep 10
  done
  [ "$n" = "0" ] || { echo "[phase4-score] $exp $m still dirty"; exit 1; }
done
echo PHASE4_SCORE_DONE
