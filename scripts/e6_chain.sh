#!/bin/bash
# Phase-6 E6: generation (Qwen3-14B, PID-tracked server) then scoring (frozen evaluator), one GPU, servers down after each step.
set -u; cd "$(dirname "$0")/.."; . scripts/rev_env.sh; PY=.venv/bin/python; G=${ADDEXP_GPU:-1}; M=qwen3-14b
bash scripts/addexp_servers.sh up Qwen/Qwen3-14B-FP8 8303 "$G" 0.45 || { echo E6_FAILED server; exit 1; }
$PY scripts/run_e6.py gen --model $M --concurrency 64 > logs_addexp/e6_gen_$M.log 2>&1; rc=$?
bash scripts/addexp_servers.sh down 8303
[ $rc -ne 0 ] && { echo "E6_FAILED gen"; exit 1; }
echo "E6_GEN_OK"
bash scripts/rev_eval_up.sh 8305 "$G" || { echo E6_FAILED evaluator; exit 1; }
export SUPDRIFT_EVAL_URL=http://localhost:8305/v1 SUPDRIFT_SCORE_CACHE=cache/e6_score_shard_8305.jsonl
bad=0
for stem in e6_answers_$M e6_${M}_ok e6_${M}_mem; do
  n=999
  for pass in 1 2 3; do
    $PY scripts/score_generic.py --chains "results/$stem.jsonl" --out "results/${stem}_scored.csv" --self-ico --concurrency 256 >> logs_addexp/e6_score.log 2>&1 || { sleep 20; continue; }
    n=$($PY -c "import pandas as pd,sys; print(int(pd.read_csv(sys.argv[1])['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum()))" "results/${stem}_scored.csv")
    echo "[e6-score] $stem pass $pass: $n dirty"; [ "$n" = "0" ] && break; sleep 10
  done
  [ "$n" = "0" ] || bad=$((bad+1))
done
bash scripts/addexp_servers.sh down 8305
[ -f cache/e6_score_shard_8305.jsonl ] && $PY scripts/merge_score_cache.py cache/e6_score_shard_8305.jsonl
echo "E6_CHAIN_EXIT bad=$bad"
