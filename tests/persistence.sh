#!/bin/bash
# Test Geth persistence across pod restarts
# Verifies that blockchain state is preserved when the pod restarts

echo "Testing Geth persistence..."

# Get block number before restart
echo "Getting current block number..."
block_before=$(curl -s -X POST http://localhost:8545/ \
  -H 'content-type: application/json' \
  -d '{"method":"eth_blockNumber","params":[],"id":1,"jsonrpc":"2.0"}' \
  | jq -r .result 2>/dev/null)

printf "\033[31mBlock number before restart: %d\033[0m\n" "$block_before"

# Restart the pod
echo "Restarting Geth pod..."
kubectl rollout restart sts/geth-devnet -n geth

# Wait for pod to be ready
echo "Waiting for pod to be healthy..."
sleep 3
kubectl wait --for=condition=ready pod \
  -l app=geth-devnet -n geth --timeout=300s

echo "Getting block number after restart..."

while true; do
  result=$(curl -s -X POST http://localhost:8545/ \
    -H 'content-type: application/json' \
    -d '{"method":"eth_blockNumber","params":[],"id":1,"jsonrpc":"2.0"}' \
    | jq -r .result 2>/dev/null)

  if [ "$result" != "null" ] && [ "$result" != "" ]; then
    break
  fi
  sleep 1
done

# Get block number after restart
block_after=$(curl -s -X POST http://localhost:8545/ \
  -H 'content-type: application/json' \
  -d '{"method":"eth_blockNumber","params":[],"id":1,"jsonrpc":"2.0"}' \
  | jq -r .result)

printf "\033[31mBlock number after restart: %d\033[0m\n" "$block_after"
