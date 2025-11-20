# 🚀 Ethereum Load Generator Guide

*A simple Python tool that tests Ethereum blockchain performance and tracks metrics*

## 🎯 What Does This Tool Do?

Think of this like a **stress test for your car** - but for an Ethereum blockchain:

1. **Sends fake transactions** → Like pressing the gas pedal repeatedly
2. **Measures performance** → Like checking speedometer, fuel usage, engine temperature
3. **Reports results** → Like a dashboard showing all the stats

## 📊 Simple Overview Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Gen      │───▶│   Ethereum      │───▶│   Prometheus    │
│   (This Tool)   │    │   Blockchain    │    │   (Metrics)     │
│                 │    │                 │    │                 │
│ • Send TX       │    │ • Process TX    │    │ • Store Stats   │
│ • Measure Time  │    │ • Mine Blocks   │    │ • Make Graphs   │
│ • Count Success │    │ • Return Data   │    │ • Show Trends   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🏗️ Code Structure (The Big Picture)

### 1. **Configuration** 📝
```python
@dataclass
class LoadGeneratorConfig:
    geth_url: str = "http://localhost:8545"     # Where to find blockchain
    target_tps: float = 10.0                   # How many transactions per second
    concurrency: int = 10                      # How many workers
    metrics_port: int = 8080                   # Where to show stats
```

**What this does:** Sets up the "rules" for testing - like setting cruise control speed.

### 2. **Metrics Setup** 📈
```python
# These are like dashboard gauges in your car
transaction_counter = Counter(...)      # "How many transactions sent?"
current_tps = Gauge(...)               # "Current speed (transactions/sec)?"
transaction_latency = Histogram(...)   # "How long do transactions take?"
```

**What this does:** Creates "gauges" that Prometheus can read - like speedometer, fuel gauge, etc.

## 🔄 How The Tool Works (Step by Step)

### Step 1: Startup & Connection
```
🔌 Connect to Ethereum node
✅ Check if connection works
💰 Check account has money
🏃 Start background workers
```

### Step 2: Three Workers Running Simultaneously

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  TX Worker      │    │  Metrics Worker │    │  Block Monitor  │
│                 │    │                 │    │                 │
│ Every 0.1 sec:  │    │ Every 1 sec:    │    │ Every 1 sec:    │
│ • Send 1 TX     │    │ • Count TX/sec  │    │ • Check new     │
│ • Measure time  │    │ • Update gauges │    │   blocks        │
│ • Record result │    │ • Calculate %   │    │ • Time blocks   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📤 Transaction Worker (The Main Engine)

**What it does:** Sends transactions like an assembly line

### Process Flow:
```
1. 🎲 Generate random recipient address
   ↓
2. 🔢 Get account nonce (transaction number)
   ↓
3. ✍️ Sign transaction with private key
   ↓
4. 📡 Send to blockchain
   ↓
5. ⏱️ Measure how long it took
   ↓
6. 📊 Update metrics (success/fail, timing)
```

### Simple Code Example:
```python
async def send_transaction(self):
    start_time = time.time()                    # Start stopwatch

    # Build transaction (like filling out a form)
    tx = {
        'to': '0x1234...',                      # Who to send to
        'value': 1000000000000000,              # How much (0.001 ETH)
        'gas': 21000,                           # Fee limit
    }

    # Send it
    result = await self.rpc_call("eth_sendRawTransaction", [signed_tx])

    latency = time.time() - start_time          # Stop stopwatch
    transaction_latency.observe(latency)        # Record the time
```

## 📊 Metrics Worker (The Accountant)

**What it does:** Counts everything and calculates rates

### Every Second It Calculates:
- **TPS** (Transactions Per Second): `new_transactions / time_passed`
- **RPS** (RPC calls Per Second): `new_rpc_calls / time_passed`
- **MGas/s** (Million Gas Per Second): `gas_used / 1,000,000 / time_passed`
- **Failure Rate**: `failed_transactions / total_transactions`

```python
# Like checking your car's fuel efficiency every mile
tps = (current_tx_count - last_tx_count) / time_diff
current_tps.set(tps)  # Update the gauge
```

## 🧱 Block Monitor (The Timekeeper)

**What it does:** Watches for new blocks (like counting laps on a race track)

```python
async def block_monitor(self):
    while True:
        new_block = await get_latest_block_number()

        if new_block != last_block:
            # New block! Measure time since last one
            block_time = current_time - last_block_time
            block_time_gauge.set(block_time)  # Should be ~6 seconds
```

## 🏷️ Block Number Labels

**Why we add block numbers to metrics:**

Think of it like **tagging photos with the date** - helps you find specific moments later.

```python
# Instead of just: "sent 10 transactions"
transaction_counter.inc()

# We do: "sent 10 transactions during block 123"
transaction_counter.labels(block_number="123").inc()
```

**Benefits:**
- 🔍 **Find problems**: "Transactions were slow during blocks 100-110"
- 📈 **Track trends**: "Performance improved after block 200"
- 🧪 **Compare**: "Block 50 vs Block 150 performance"

## 🚀 How To Use

### 1. Environment Variables (Settings)
```bash
GETH_URL=http://localhost:8545        # Blockchain address
TARGET_TPS=10                         # Speed setting
PRIVATE_KEY=0x123...                  # Account key (from Kubernetes secret)
```

### 2. Run The Tool
```bash
python load_generator.py
```

### 3. View Metrics
Open browser: `http://localhost:8080/metrics`

You'll see output like:
```
eth_current_tps{block_number="42"} 9.8
eth_transaction_latency_seconds_bucket{block_number="42"} 156
eth_failure_rate{block_number="42"} 0.02
```

## 📊 Understanding the Metrics

| Metric Name | What It Measures | Good Value |
|-------------|------------------|------------|
| `eth_current_tps` | Transactions/second | Close to your target |
| `eth_current_rps` | API calls/second | Higher than TPS |
| `eth_transaction_latency_seconds` | How long transactions take | Under 1 second |
| `eth_failure_rate` | % of failed transactions | Under 5% (0.05) |
| `eth_block_time_seconds` | Time between blocks | ~6 seconds |

## 🔧 Common Issues & Solutions

### ❌ Problem: No transactions being sent
**Check:** Is `GETH_URL` correct? Is blockchain running?

### ❌ Problem: All transactions failing
**Check:** Does account have enough ETH? Is private key correct?

### ❌ Problem: Metrics show 0
**Check:** Is Prometheus scraping the right port (8080)?

### ❌ Problem: Very slow performance
**Check:** Is blockchain overloaded? Try lower `TARGET_TPS`

## 🎭 Real World Analogy

Imagine you're **testing a new pizza delivery service**:

- **Load Generator** = You (the tester)
- **Transactions** = Pizza orders you place
- **Blockchain** = The pizza restaurant
- **Metrics** = Your notebook tracking delivery times, success rate, etc.
- **Block Numbers** = Hour of the day (helps track "lunch rush" vs "quiet time")

You place orders every few seconds, time how long each takes, count successes/failures, and create charts showing when the service is fast vs slow.

## 🎯 Summary

This tool is a **performance tester** that:
1. **Bombards** the blockchain with transactions
2. **Measures** response times and success rates
3. **Reports** everything to Prometheus with detailed labels
4. **Helps you understand** if your blockchain can handle real-world load

The code uses **async programming** (doing multiple things at once) and **Prometheus metrics** (standardized way to track performance) to give you detailed insights into blockchain performance.