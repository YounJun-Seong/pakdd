#!/bin/bash
# Phase-6 E15 matched-prompt control (+ E16 evaluator leak screen): generation (Qwen3-14B primary, Qwen3-8B validation,
# PID-tracked servers) then scoring (frozen evaluator); servers down after each step.  E15_BUDGET (default 200).
set -u; cd "$(dirname "$0")/.."; . scripts/rev_env.sh; PY=.venv/bin/python; G=${ADDEXP_GPU:-1}; B=${E15_BUDGET:-200}
$PY scripts/build_e16_leak_input.py || { echo E15_FAILED leakinput; exit 1; }
bash scripts/addexp_servers.sh up Qwen/Qwen3-8B-FP8 8304 "$G" 0.30 && bash scripts/addexp_servers.sh up Qwen/Qwen3-14B-FP8 8303 "$G" 0.40 || { echo E15_FAILED servers; bash scripts/addexp_servers.sh down 8304; bash scripts/addexp_servers.sh down 8303; exit 1; }
$PY scripts/run_e15.py --model qwen3-8b --budget "$B" --concurrency 48 > "logs_addexp/e15_gen_b${B}_qwen3-8b.log" 2>&1 & p1=$!
$PY scripts/run_e15.py --model qwen3-14b --budget "$B" --concurrency 48 > "logs_addexp/e15_gen_b${B}_qwen3-14b.log" 2>&1 & p2=$!
wait $p1; r1=$?; wait $p2; r2=$?
bash scripts/addexp_servers.sh down 8304; bash scripts/addexp_servers.sh down 8303
[ $r1 -ne 0 ] || [ $r2 -ne 0 ] && { echo "E15_FAILED gen $r1 $r2"; exit 1; }
echo E15_GEN_OK
bash scripts/rev_eval_up.sh 8305 "$G" || { echo E15_FAILED evaluator; exit 1; }
export SUPDRIFT_EVAL_URL=http://localhost:8305/v1 SUPDRIFT_SCORE_CACHE=cache/e15_score_shard_8305.jsonl
bad=0
for stem in "e15b${B}_qwen3-14b_ok" "e15b${B}_qwen3-14b_mem" "e15b${B}_qwen3-8b_ok" "e15b${B}_qwen3-8b_mem" e16/e16_leak_input; do
  out="results/${stem}_scored.csv"; [ "$stem" = e16/e16_leak_input ] && out=results/e16/e16_leak_scored.csv
  n=999
  for pass in 1 2 3; do
    $PY scripts/score_generic.py --chains "results/$stem.jsonl" --out "$out" --self-ico --concurrency 256 >> "logs_addexp/e15_score_b${B}.log" 2>&1 || { sleep 20; continue; }
    n=$($PY -c "import pandas as pd,sys; print(int(pd.read_csv(sys.argv[1])['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum()))" "$out")
    echo "[e15-score] $stem pass $pass: $n dirty"; [ "$n" = "0" ] && break; sleep 10
  done
  [ "$n" = "0" ] || bad=$((bad+1))
done
bash scripts/addexp_servers.sh down 8305
[ -f cache/e15_score_shard_8305.jsonl ] && $PY scripts/merge_score_cache.py cache/e15_score_shard_8305.jsonl
echo "E15_CHAIN_EXIT bad=$bad"
