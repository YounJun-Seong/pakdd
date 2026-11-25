#!/bin/bash
# Score Phase-5 outputs with the frozen evaluator.
#   trajectory : rows are memories (text) -> one scored csv
#   oracle, blindea : rows carry their own ICO -> --self-ico
#   notrunc, resample, balanced : final (text) + memory, like Phase 4
#   usage: phase5_score.sh <exp> <model> [<exp> <model> ...]   (under supervise_eval_cg.sh)
set -u
cd "$(dirname "$0")/.."
PY=.venv/bin/python
score () { $PY scripts/score_generic.py --chains "$1" --out "$2" --concurrency 256 $3 || exit 1; }
dirty () { $PY -c "
import pandas as pd,sys
print(sum(int(pd.read_csv(f)['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum()) for f in sys.argv[1:]))" "$@"; }
while [ $# -ge 2 ]; do
  exp=$1; m=$2; shift 2
  src=results/phase5_${exp}_${m}.jsonl
  [ -f "$src" ] || { echo "missing $src"; exit 1; }
  case $exp in
    trajectory)
      for pass in 1 2 3 4; do
        score "$src" "results/phase5_${exp}_${m}_scored.csv" ""
        n=$(dirty results/phase5_${exp}_${m}_scored.csv); echo "[phase5-score] $exp $m pass $pass: $n dirty"
        [ "$n" -le 5 ] && break; sleep 10; done ;;
    oracle|blindea)
      for pass in 1 2 3 4; do
        score "$src" "results/phase5_${exp}_${m}_scored.csv" "--self-ico"
        n=$(dirty results/phase5_${exp}_${m}_scored.csv); echo "[phase5-score] $exp $m pass $pass: $n dirty"
        [ "$n" -le 5 ] && break; sleep 10; done ;;
    *)
      # drop failed chains (no text) and build the memory file
      $PY - "$src" <<'EOF'
import json, sys
src = sys.argv[1]; base = src[:-6]
ok = [json.loads(l) for l in open(src)]
ok = [r for r in ok if r.get("text")]
with open(base + "_ok.jsonl", "w") as f:
    for r in ok: f.write(json.dumps(r, ensure_ascii=False) + "\n")
with open(base + "_mem.jsonl", "w") as f:
    for r in ok:
        r = {k: v for k, v in r.items() if k not in ("text", "steps")}; r["text"] = r.pop("memory")
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
EOF
      for pass in 1 2 3 4; do
        score "results/phase5_${exp}_${m}_ok.jsonl"  "results/phase5_${exp}_${m}_final_scored.csv" ""
        score "results/phase5_${exp}_${m}_mem.jsonl" "results/phase5_${exp}_${m}_mem_scored.csv" ""
        n=$(dirty results/phase5_${exp}_${m}_final_scored.csv results/phase5_${exp}_${m}_mem_scored.csv)
        echo "[phase5-score] $exp $m pass $pass: $n dirty"; [ "$n" -le 5 ] && break; sleep 10; done ;;
  esac
  [ "$n" -le 5 ] || { echo "[phase5-score] $exp $m still dirty"; exit 1; }
done
echo PHASE5_SCORE_DONE
