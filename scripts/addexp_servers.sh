#!/bin/bash
# PID-tracked vLLM servers for the 2026-09-29 additional experiments. Unlike
# stop_all_servers.sh / supervise_eval*.sh this never pattern-kills: another project
# (graphharness judge, same model, port 8301) runs under the same user on this host.
#   up   <hf-model> <port> <gpu> <util> [extra vllm args]   -> waits until the port serves
#   down <port>                                             -> kills only that server's process group
#   status
cd "$(dirname "$0")/.."
mkdir -p logs_addexp
cmd=$1; shift
case $cmd in
  up)
    model=$1; port=$2; gpu=$3; util=$4; shift 4
    if curl -s -m 3 "localhost:$port/v1/models" | /usr/bin/grep -q "$model"; then echo "already up: $port"; exit 0; fi
    CUDA_VISIBLE_DEVICES=$gpu setsid nohup .venv_vllm/bin/python -m vllm.entrypoints.openai.api_server \
      --model "$model" --served-model-name "$model" --port "$port" \
      --gpu-memory-utilization "$util" --max-model-len 8192 "$@" > "logs_addexp/vllm_$port.log" 2>&1 &
    echo $! > "logs_addexp/server_$port.pid"
    for i in $(seq 1 90); do
      sleep 10
      curl -s -m 3 "localhost:$port/v1/models" | /usr/bin/grep -q "$model" && { echo "UP $model :$port gpu$gpu pid $(cat logs_addexp/server_$port.pid)"; exit 0; }
      kill -0 "$(cat logs_addexp/server_$port.pid)" 2>/dev/null || { echo "server $model died"; tail -5 "logs_addexp/vllm_$port.log"; exit 1; }
    done
    echo "server $model did not come up"; exit 1 ;;
  down)
    port=$1; f="logs_addexp/server_$port.pid"
    [ -f "$f" ] || { echo "no pid file for $port"; exit 0; }
    pid=$(cat "$f")
    kill -TERM -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null
    for i in $(seq 1 15); do sleep 2; pgrep -g "$pid" >/dev/null 2>&1 || break; done
    pgrep -g "$pid" >/dev/null 2>&1 && kill -KILL -- "-$pid" 2>/dev/null
    rm -f "$f"; echo "DOWN :$port (pgid $pid)" ;;
  status)
    for f in logs_addexp/server_*.pid; do [ -f "$f" ] && echo "$f $(cat $f) $(kill -0 $(cat $f) 2>/dev/null && echo alive || echo dead)"; done
    nvidia-smi --query-gpu=index,memory.used,memory.free --format=csv,noheader ;;
esac
