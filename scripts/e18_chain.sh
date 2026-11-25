#!/bin/bash
# Phase-6 E18 one-pass memory: Qwen3-14B answers from M1 (PID-tracked server), then scoring; servers down after each step.
set -u; cd "$(dirname "$0")/.."; . scripts/rev_env.sh; PY=.venv/bin/python; G=${ADDEXP_GPU:-1}
n0=$(wc -l < cache/ratio_qwen3-14b.jsonl); m0=$(wc -l < cache/e15_qwen3-14b.jsonl)
bash scripts/addexp_servers.sh up Qwen/Qwen3-14B-FP8 8303 "$G" 0.40 || { echo E18_FAILED server; bash scripts/addexp_servers.sh down 8303; exit 1; }
$PY scripts/run_e18.py --model qwen3-14b --concurrency 48 > logs_addexp/e18_gen_qwen3-14b.log 2>&1; r=$?
bash scripts/addexp_servers.sh down 8303
[ $r -ne 0 ] && { echo "E18_FAILED gen $r"; exit 1; }
echo "E18_GEN_OK new cache lines: ratio $(( $(wc -l < cache/ratio_qwen3-14b.jsonl) - n0 )), e15 $(( $(wc -l < cache/e15_qwen3-14b.jsonl) - m0 )) (expected 1674 each = final answers only)"
bash scripts/rev_eval_up.sh 8305 "$G" || { echo E18_FAILED evaluator; exit 1; }
export SUPDRIFT_EVAL_URL=http://localhost:8305/v1 SUPDRIFT_SCORE_CACHE=cache/e18_score_shard_8305.jsonl
bad=0
for stem in e18_qwen3-14b_ok e18_qwen3-14b_mem; do
  n=999
  for pass in 1 2 3; do
    $PY scripts/score_generic.py --chains "results/$stem.jsonl" --out "results/${stem}_scored.csv" --self-ico --concurrency 256 >> logs_addexp/e18_score.log 2>&1 || { sleep 20; continue; }
    n=$($PY -c "import pandas as pd,sys; print(int(pd.read_csv(sys.argv[1])['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum()))" "results/${stem}_scored.csv")
    echo "[e18-score] $stem pass $pass: $n dirty"; [ "$n" = "0" ] && break; sleep 10
  done
  [ "$n" = "0" ] || bad=$((bad+1))
done
bash scripts/addexp_servers.sh down 8305
[ -f cache/e18_score_shard_8305.jsonl ] && $PY scripts/merge_score_cache.py cache/e18_score_shard_8305.jsonl
echo "E18_CHAIN_EXIT bad=$bad"
