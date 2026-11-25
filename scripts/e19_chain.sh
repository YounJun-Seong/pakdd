#!/bin/bash
# Phase-6 E19 length-position control: Qwen3-14B generation (PID-tracked server), then scoring; servers down after each step.
set -u; cd "$(dirname "$0")/.."; . scripts/rev_env.sh; PY=.venv/bin/python; G=${ADDEXP_GPU:-1}
bash scripts/addexp_servers.sh up Qwen/Qwen3-14B-FP8 8303 "$G" 0.40 || { echo E19_FAILED server; bash scripts/addexp_servers.sh down 8303; exit 1; }
$PY scripts/run_e19.py --model qwen3-14b --concurrency 96 > logs_addexp/e19_gen_qwen3-14b.log 2>&1; r=$?
bash scripts/addexp_servers.sh down 8303
[ $r -ne 0 ] && { echo "E19_FAILED gen $r"; exit 1; }
echo E19_GEN_OK
bash scripts/rev_eval_up.sh 8305 "$G" || { echo E19_FAILED evaluator; exit 1; }
export SUPDRIFT_EVAL_URL=http://localhost:8305/v1 SUPDRIFT_SCORE_CACHE=cache/e19_score_shard_8305.jsonl
bad=0
for stem in e19_qwen3-14b_ok e19_qwen3-14b_mem; do
  n=999
  for pass in 1 2 3; do
    $PY scripts/score_generic.py --chains "results/$stem.jsonl" --out "results/${stem}_scored.csv" --self-ico --concurrency 256 >> logs_addexp/e19_score.log 2>&1 || { sleep 20; continue; }
    n=$($PY -c "import pandas as pd,sys; print(int(pd.read_csv(sys.argv[1])['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum()))" "results/${stem}_scored.csv")
    echo "[e19-score] $stem pass $pass: $n dirty"; [ "$n" = "0" ] && break; sleep 10
  done
  [ "$n" = "0" ] || bad=$((bad+1))
done
bash scripts/addexp_servers.sh down 8305
[ -f cache/e19_score_shard_8305.jsonl ] && $PY scripts/merge_score_cache.py cache/e19_score_shard_8305.jsonl
echo "E19_CHAIN_EXIT bad=$bad"
