#!/bin/bash
# Start a frozen-evaluator server on <port> <gpu>, sized to the memory free on that GPU now
# (own budget = min(free - 8 GB, 68 GB) / total; needs >= 44 GB free). Retries: a co-tenant
# allocating during model load makes the KV budget negative.   usage: rev_eval_up.sh <port> <gpu>
cd "$(dirname "$0")/.."; . scripts/rev_env.sh
port=$1; G=$2
curl -s -m 3 "localhost:$port/v1/models" | /usr/bin/grep -q "Qwen3-32B-FP8" && { echo "[eval-up] already serving on :$port"; exit 0; }
for try in 1 2 3 4; do
  read -r FREE TOTAL <<<"$(nvidia-smi -i "$G" --query-gpu=memory.free,memory.total --format=csv,noheader,nounits | tr -d ',')"
  if [ "$FREE" -ge 44000 ]; then
    WANT=$(( FREE - 8000 )); [ "$WANT" -gt 68000 ] && WANT=68000
    UTIL=$(awk -v t="$TOTAL" -v w="$WANT" 'BEGIN{printf "%.3f", w / t}')
    echo "[eval-up] :$port try $try: GPU$G free ${FREE}MiB -> util $UTIL"
    bash scripts/addexp_servers.sh up Qwen/Qwen3-32B-FP8 "$port" "$G" "$UTIL" --max-num-seqs 256 && exit 0
    bash scripts/addexp_servers.sh down "$port"
  else
    echo "[eval-up] :$port try $try: GPU$G has only ${FREE}MiB free"
  fi
  sleep 60
done
exit 1
