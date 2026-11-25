#!/bin/bash
# Keep the 32B evaluator alive and drive an evaluation command to completion.
# The LLM cache makes every retry resume where the last attempt died.
#   usage: supervise_eval.sh "<command run from project root>" <done-marker>
set -u
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ"
CMD="$1"
ATTEMPTS=0
EVAL_GPU=1
MAX_ATTEMPTS=500

free_mb () { nvidia-smi --query-gpu=memory.total,memory.used --format=csv,noheader,nounits -i "$1" | awk -F, '{print $1-$2}'; }

wait_for_gpu_memory () {
  # 32B FP8 needs ~37GB; wait until EITHER GPU has room, remember which
  while true; do
    for g in 0 1; do
      f=$(free_mb $g)
      if [ "$f" -ge 39000 ]; then EVAL_GPU=$g; return 0; fi
    done
    echo "[supervise] no GPU with 39GB free (gpu0=$(free_mb 0) gpu1=$(free_mb 1)); waiting..."
    sleep 180
  done
}

server_up () { curl -s -m 3 localhost:8301/v1/models 2>/dev/null | grep -q FP8; }

start_server () {
  pkill -9 -f "Qwen3-32B-FP8" 2>/dev/null
  # reap orphaned engine cores (children survive the API server and hold GPU
  # memory; ours are identifiable as user-owned VLLM::EngineCore with ppid 1)
  for pid in $(nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader | grep EngineCore | cut -d, -f1); do
    if [ "$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')" = "1" ] && \
       [ "$(ps -o user= -p "$pid" 2>/dev/null | tr -d ' ')" = "$(whoami)" ]; then
      echo "[supervise] reaping orphaned engine core $pid"
      kill -9 "$pid" 2>/dev/null
    fi
  done
  sleep 5
  wait_for_gpu_memory
  # size our allocation to what is actually free (leave 2GB slack), capped 0.85
  f=$(free_mb $EVAL_GPU)
  UTIL=$(awk -v f="$f" 'BEGIN{u=(f-2000)/81559; if(u>0.85)u=0.85; printf "%.2f", u}')
  echo "[supervise] starting server on GPU$EVAL_GPU with util=$UTIL (free ${f}MiB)"
  nohup bash -c "CUDA_VISIBLE_DEVICES=$EVAL_GPU exec $PROJ/.venv_vllm/bin/python -m vllm.entrypoints.openai.api_server \
    --model Qwen/Qwen3-32B-FP8 --served-model-name Qwen/Qwen3-32B-FP8 \
    --port 8301 --gpu-memory-utilization $UTIL --max-model-len 8192 --enforce-eager" \
    > "$PROJ/logs_vllm_32b.log" 2>&1 &
  for i in $(seq 1 60); do
    sleep 10
    server_up && return 0
  done
  return 1
}

while [ "$ATTEMPTS" -lt "$MAX_ATTEMPTS" ]; do
  ATTEMPTS=$((ATTEMPTS+1))
  echo "[supervise] attempt $ATTEMPTS"
  if ! server_up; then
    echo "[supervise] (re)starting evaluator server..."
    start_server || { echo "[supervise] server failed to start"; continue; }
  fi
  echo "[supervise] running: $CMD"
  eval "$CMD" &
  CMD_PID=$!
  # throughput watchdog: the vLLM 0.11 scheduler can wedge silently (requests
  # accepted, none complete, health check green). If no cache file grows for
  # 15 min while the command runs, kill server+command and start over.
  stall=0
  last_m=$(stat -c %Y "$PROJ"/cache/*.jsonl 2>/dev/null | sort -n | tail -1 || echo 0)
  while kill -0 "$CMD_PID" 2>/dev/null; do
    sleep 120
    m=$(stat -c %Y "$PROJ"/cache/*.jsonl 2>/dev/null | sort -n | tail -1 || echo 0)
    if [ "$m" != "$last_m" ]; then stall=0; last_m=$m; else stall=$((stall+120)); fi
    if [ "$stall" -ge 900 ]; then
      echo "[supervise] WATCHDOG: no evaluator progress for ${stall}s — restarting"
      kill -9 "$CMD_PID" 2>/dev/null
      # the command's python grandchildren survive the wrapper kill — reap them
      pkill -9 -f "scripts/score_chains.py" 2>/dev/null
      pkill -9 -f "scripts/score_gate2.py" 2>/dev/null
      pkill -9 -f "scripts/verify_gate2_targets.py" 2>/dev/null
      pkill -9 -f "Qwen3-32B-FP8" 2>/dev/null
      break
    fi
  done
  if wait "$CMD_PID"; then
    echo "[supervise] SUPERVISED_DONE"
    exit 0
  fi
  echo "[supervise] command failed or was watchdog-killed; retrying"
  sleep 5
done
echo "[supervise] GAVE_UP after $MAX_ATTEMPTS attempts"
exit 1
