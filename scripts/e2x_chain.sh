#!/bin/bash
# Phase-6 E20 / E21 / E23: generation (PID-tracked servers), then scoring; every server goes down right after its step.
set -u; cd "$(dirname "$0")/.."; . scripts/rev_env.sh; PY=.venv/bin/python; G=${ADDEXP_GPU:-1}
bash scripts/addexp_servers.sh up Qwen/Qwen3-14B-FP8 8303 "$G" 0.40 || { echo E2X_FAILED server14; bash scripts/addexp_servers.sh down 8303; exit 1; }
r=0
for cmd in e20 e21 e23; do
  $PY scripts/run_e2x.py $cmd --model qwen3-14b --concurrency 96 > "logs_addexp/${cmd}_gen_qwen3-14b.log" 2>&1 || { r=1; echo "E2X_FAILED gen $cmd"; break; }
  echo "E2X_GEN_OK $cmd qwen3-14b"
done
bash scripts/addexp_servers.sh down 8303
[ $r -ne 0 ] && exit 1
bash scripts/addexp_servers.sh up Qwen/Qwen3-8B-FP8 8304 "$G" 0.25 || { echo E2X_FAILED server8; bash scripts/addexp_servers.sh down 8304; exit 1; }
$PY scripts/run_e2x.py e20 --model qwen3-8b --concurrency 96 > logs_addexp/e20_gen_qwen3-8b.log 2>&1; r=$?
bash scripts/addexp_servers.sh down 8304
[ $r -ne 0 ] && { echo "E2X_FAILED gen e20 8b"; exit 1; }
echo "E2X_GEN_OK e20 qwen3-8b"
bash scripts/rev_eval_up.sh 8305 "$G" || { echo E2X_FAILED evaluator; exit 1; }
export SUPDRIFT_EVAL_URL=http://localhost:8305/v1 SUPDRIFT_SCORE_CACHE=cache/e2x_score_shard_8305.jsonl
bad=0
for stem in e20_answers_qwen3-14b e20_answers_qwen3-8b e21_qwen3-14b_ok e21_qwen3-14b_mem e23_qwen3-14b_ok e23_qwen3-14b_mem; do
  n=999
  for pass in 1 2 3; do
    $PY scripts/score_generic.py --chains "results/$stem.jsonl" --out "results/${stem}_scored.csv" --self-ico --concurrency 256 >> logs_addexp/e2x_score.log 2>&1 || { sleep 20; continue; }
    n=$($PY -c "import pandas as pd,sys; print(int(pd.read_csv(sys.argv[1])['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum()))" "results/${stem}_scored.csv")
    echo "[e2x-score] $stem pass $pass: $n dirty"; [ "$n" = "0" ] && break; sleep 10
  done
  [ "$n" = "0" ] || bad=$((bad+1))
done
bash scripts/addexp_servers.sh down 8305
[ -f cache/e2x_score_shard_8305.jsonl ] && $PY scripts/merge_score_cache.py cache/e2x_score_shard_8305.jsonl
echo "E2X_CHAIN_EXIT bad=$bad"
