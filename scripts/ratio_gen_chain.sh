#!/bin/bash
# Phase-6 E13 generation, all three models: enforced -> notrunc -> labels per model.
# GPT through the API; Qwen 8B + 14B on one GPU (PID-tracked servers, shut down at the end).
set -u; cd "$(dirname "$0")/.."; . scripts/rev_env.sh; PY=.venv/bin/python; G=${ADDEXP_GPU:-1}
pipe () { m=$1; c=$2
  for cmd in enforced notrunc labels; do
    $PY scripts/run_ratio.py $cmd --model "$m" --concurrency "$c" >> "logs_addexp/ratio_gen_${m}.log" 2>&1 || { echo "RATIO_GEN_FAILED $m $cmd"; return 1; }
  done; echo "RATIO_GEN_OK $m"; }
for m in ${RATIO_MODELS:-gpt-5.4-mini qwen3-8b qwen3-14b}; do : > "logs_addexp/ratio_gen_${m}.log"; done
pg=""; p1=""; p2=""
case " ${RATIO_MODELS:-gpt-5.4-mini qwen3-8b qwen3-14b} " in *" gpt-5.4-mini "*) pipe gpt-5.4-mini 32 & pg=$! ;; esac
case " ${RATIO_MODELS:-gpt-5.4-mini qwen3-8b qwen3-14b} " in *" qwen3-8b "*)
  bash scripts/addexp_servers.sh up Qwen/Qwen3-8B-FP8 8304 "$G" 0.30 && { pipe qwen3-8b 48 & p1=$!; } || echo "RATIO_GEN_FAILED server 8b" ;; esac
case " ${RATIO_MODELS:-gpt-5.4-mini qwen3-8b qwen3-14b} " in *" qwen3-14b "*)
  bash scripts/addexp_servers.sh up Qwen/Qwen3-14B-FP8 8303 "$G" 0.40 && { pipe qwen3-14b 48 & p2=$!; } || echo "RATIO_GEN_FAILED server 14b" ;; esac
r1=0; r2=0; rg=0
[ -n "$p1" ] && { wait $p1; r1=$?; }; bash scripts/addexp_servers.sh down 8304
[ -n "$p2" ] && { wait $p2; r2=$?; }; bash scripts/addexp_servers.sh down 8303
[ -n "$pg" ] && { wait $pg; rg=$?; }
echo "RATIO_GEN_CHAIN_EXIT $r1 $r2 $rg"
