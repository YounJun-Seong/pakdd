#!/bin/bash
# Phase-6 E14: generation (Qwen3-8B + 14B, PID-tracked servers) then scoring (frozen evaluator); servers down after each step.
set -u; cd "$(dirname "$0")/.."; . scripts/rev_env.sh; PY=.venv/bin/python; G=${ADDEXP_GPU:-1}
bash scripts/addexp_servers.sh up Qwen/Qwen3-8B-FP8 8304 "$G" 0.30 && bash scripts/addexp_servers.sh up Qwen/Qwen3-14B-FP8 8303 "$G" 0.40 || { echo LENCTRL_FAILED servers; bash scripts/addexp_servers.sh down 8304; bash scripts/addexp_servers.sh down 8303; exit 1; }
$PY scripts/run_lencontrol.py --model qwen3-8b --concurrency 48 > logs_addexp/lenctrl_gen_qwen3-8b.log 2>&1 & p1=$!
$PY scripts/run_lencontrol.py --model qwen3-14b --concurrency 48 > logs_addexp/lenctrl_gen_qwen3-14b.log 2>&1 & p2=$!
wait $p1; r1=$?; wait $p2; r2=$?
bash scripts/addexp_servers.sh down 8304; bash scripts/addexp_servers.sh down 8303
[ $r1 -ne 0 ] || [ $r2 -ne 0 ] && { echo "LENCTRL_FAILED gen $r1 $r2"; exit 1; }
echo LENCTRL_GEN_OK
bash scripts/rev_eval_up.sh 8305 "$G" || { echo LENCTRL_FAILED evaluator; exit 1; }
export SUPDRIFT_EVAL_URL=http://localhost:8305/v1 SUPDRIFT_SCORE_CACHE=cache/lenctrl_score_shard_8305.jsonl
bad=0
for m in qwen3-8b qwen3-14b; do for stem in lenctrl_${m}_ok lenctrl_${m}_mem; do
  n=999
  for pass in 1 2 3; do
    $PY scripts/score_generic.py --chains "results/$stem.jsonl" --out "results/${stem}_scored.csv" --self-ico --concurrency 256 >> logs_addexp/lenctrl_score.log 2>&1 || { sleep 20; continue; }
    n=$($PY -c "import pandas as pd,sys; print(int(pd.read_csv(sys.argv[1])['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum()))" "results/${stem}_scored.csv")
    echo "[lenctrl-score] $stem pass $pass: $n dirty"; [ "$n" = "0" ] && break; sleep 10
  done
  [ "$n" = "0" ] || bad=$((bad+1))
done; done
bash scripts/addexp_servers.sh down 8305
[ -f cache/lenctrl_score_shard_8305.jsonl ] && $PY scripts/merge_score_cache.py cache/lenctrl_score_shard_8305.jsonl
echo "LENCTRL_CHAIN_EXIT bad=$bad"
