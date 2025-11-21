#!/bin/bash

# Ethereum Block Time Monitor
# Tracks block production times and transaction counts

RPC_URL="http://localhost:8545"
POLL_INTERVAL=1

previous_timestamp=$(date +%s)
previous_block_number=0
block_identifier="latest"

echo "Starting Ethereum block monitor..."
echo "Press Ctrl+C to stop"
echo

# Handle Ctrl+C gracefully
trap 'echo -e "\nMonitoring stopped by user"; exit 0' INT

while true; do
    # Fetch block data
    response=$(curl -s -X POST "$RPC_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"jsonrpc\": \"2.0\",
            \"method\": \"eth_getBlockByNumber\",
            \"params\": [\"$block_identifier\", false],
            \"id\": 1
        }")

    # Check if request was successful
    if [[ -z "$response" ]] || [[ "$response" == *'"error"'* ]]; then
        sleep $POLL_INTERVAL
        continue
    fi

    # Extract block data using jq
    block_number_hex=$(echo "$response" | jq -r '.result.number // empty')
    timestamp_hex=$(echo "$response" | jq -r '.result.timestamp // empty')
    transactions=$(echo "$response" | jq -r '.result.transactions | length')

    # Skip if no valid data
    if [[ -z "$block_number_hex" ]] || [[ -z "$timestamp_hex" ]]; then
        sleep $POLL_INTERVAL
        continue
    fi

    # Convert hex to decimal
    block_number=$((block_number_hex))
    current_timestamp=$((timestamp_hex))

    # Skip if same block
    if [[ $previous_block_number -eq $block_number ]]; then
        sleep $POLL_INTERVAL
        continue
    fi

    # Calculate time difference
    time_diff=$((current_timestamp - previous_timestamp))
    current_time=$(date +%H:%M:%S)

    # Display block information
    echo "Block $block_number: ${time_diff}s since last block, $transactions transactions, time: $current_time"

    # Update tracking variables
    previous_block_number=$block_number
    previous_timestamp=$current_timestamp

    # Prepare for next block
    next_block=$((block_number + 1))
    block_identifier=$(printf "0x%x" $next_block)

    sleep $POLL_INTERVAL
done