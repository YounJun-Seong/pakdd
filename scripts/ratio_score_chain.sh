#!/bin/bash
# Phase-6 E13 (compression ratio) scoring: up to two evaluator servers (one per GPU), each with its own cache shard, pulling
# result files from a shared queue; shards are merged into the canonical cache at the end.
# Re-runnable: files that already have a complete *_scored.csv are skipped.
#   env: REV_MODELS (default all three), REV_Q (queue dir name), EVAL_A / EVAL_B = "port:gpu"
set -u; cd "$(dirname "$0")/.."; . scripts/rev_env.sh; PY=.venv/bin/python
Q=logs_addexp/${REV_Q:-ratio_queue}; rm -rf "$Q"; mkdir -p "$Q/todo" "$Q/done" "$Q/failed"
i=0
for kind in answers enforced notrunc_ok enforced_mem notrunc_mem; do
  for m in ${REV_MODELS:-gpt-5.4-mini qwen3-8b qwen3-14b}; do
    case $kind in
      answers) stem=ratio_answers_$m ;; enforced) stem=ratio_$m ;; notrunc_ok) stem=ratio_notrunc_${m}_ok ;;
      enforced_mem) stem=ratio_${m}_mem ;; notrunc_mem) stem=ratio_notrunc_${m}_mem ;;
    esac
    [ -f "results/$stem.jsonl" ] || continue
    if [ -f "results/${stem}_scored.csv" ] && [ "$(( $(wc -l < results/${stem}_scored.csv) - 1 ))" -ge "$(wc -l < results/$stem.jsonl)" ]; then continue; fi
    i=$((i+1)); touch "$Q/todo/$(printf %02d $i)__$stem"
  done
done
echo "queued $i files"
worker () { port=$1; shard=cache/ratio_score_shard_$port.jsonl
  export SUPDRIFT_EVAL_URL=http://localhost:$port/v1 SUPDRIFT_SCORE_CACHE=$shard
  while true; do
    f=$(ls "$Q/todo" 2>/dev/null | sort | head -1); [ -z "$f" ] && break
    mv "$Q/todo/$f" "$Q/claimed_${port}_$f" 2>/dev/null || continue
    stem=${f#*__}; n=999
    for pass in 1 2 3; do
      $PY scripts/score_generic.py --chains "results/$stem.jsonl" --out "results/${stem}_scored.csv" --self-ico --concurrency 256 \
        >> "logs_addexp/ratio_score_$port.log" 2>&1 || { sleep 20; continue; }
      n=$($PY -c "import pandas as pd,sys; print(int(pd.read_csv(sys.argv[1])['claim_label'].isin(['EVAL_ERROR','PARSE_ERROR']).sum()))" "results/${stem}_scored.csv")
      echo "[ratio-score :$port] $stem pass $pass: $n dirty"; [ "$n" = "0" ] && break; sleep 10
    done
    [ "$n" -le 5 ] && mv "$Q/claimed_${port}_$f" "$Q/done/$f" || mv "$Q/claimed_${port}_$f" "$Q/failed/$f"
  done; }
pids=""
for spec in ${EVAL_A:-8305:1} ${EVAL_B:-}; do
  port=${spec%%:*}; gpu=${spec##*:}; ports="${ports:-} $port"
  bash scripts/rev_eval_up.sh "$port" "$gpu" && { worker "$port" & pids="$pids $!"; }
done
[ -z "$pids" ] && { echo RATIO_SCORE_FAILED no evaluator; exit 1; }
wait $pids
for port in $ports; do bash scripts/addexp_servers.sh down "$port"; done
sh=$(for port in $ports; do ls cache/ratio_score_shard_$port.jsonl 2>/dev/null; done)
[ -n "$sh" ] && $PY scripts/merge_score_cache.py $sh
echo "RATIO_SCORE_CHAIN_EXIT done=$(ls $Q/done | wc -l) failed=$(ls $Q/failed | wc -l)"
