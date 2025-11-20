#!/usr/bin/env python3
"""
Ethereum Load Generator and Metrics Exporter
Generates configurable transaction load and exposes metrics for Prometheus
"""

import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp
from eth_account import Account
from prometheus_client import Counter, Gauge, Histogram, start_http_server
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Prometheus metrics
transaction_counter = Counter(
    "eth_transactions_total", "Total transactions sent", ["status"]
)
rpc_requests_counter = Counter(
    "eth_rpc_requests_total", "Total RPC requests", ["method", "status"]
)
transaction_latency = Histogram(
    "eth_transaction_latency_seconds", "Transaction latency in seconds"
)
rpc_latency = Histogram(
    "eth_rpc_latency_seconds", "RPC request latency in seconds", ["method"]
)
current_tps = Gauge("eth_current_tps", "Current transactions per second")
current_rps = Gauge("eth_current_rps", "Current RPC requests per second")
current_mgas_per_second = Gauge(
    "eth_current_mgas_per_second", "Current million gas per second"
)
gas_used_total = Counter("eth_gas_used_total", "Total gas used")
block_number_gauge = Gauge("eth_block_number", "Current block number")
block_time_gauge = Gauge("eth_block_time_seconds", "Time between blocks")
failure_rate = Gauge("eth_failure_rate", "Transaction failure rate")


@dataclass
class LoadGeneratorConfig:
    """Configuration for the load generator"""

    geth_url: str = "http://localhost:8545"
    target_tps: float = 10.0
    metrics_port: int = 8080
    test_duration: int = 3600  # 1 hour
    private_key: str = os.getenv(
        "PRIVATE_KEY",
        "0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d",
    )
    signed_tx_hex: Optional[str] = os.getenv("SIGNED_TX_HEX")
    gas_limit: int = 21000
    gas_price: int = 20 * 10**9  # 20 Gwei


class EthereumLoadGenerator:
    def __init__(self, config: LoadGeneratorConfig):
        self.config = config
        self.web3 = Web3(Web3.HTTPProvider(config.geth_url))
        self.account = Account.from_key(config.private_key)
        self.session: Optional[aiohttp.ClientSession] = None
        self.chain_id: Optional[int] = None

        # Metrics tracking
        self.tx_count = 0
        self.tx_success_count = 0
        self.tx_failure_count = 0
        self.rpc_count = 0
        self.gas_used = 0
        self.last_metrics_time = time.time()
        self.last_tx_count = 0
        self.last_tx_success_count = 0
        self.last_tx_failure_count = 0
        self.last_rpc_count = 0
        self.last_gas_used = 0

        # Block tracking
        self.last_block_number = 0
        self.last_block_time = time.time()

        logger.info(f"Initialized load generator for {config.geth_url}")
        logger.info(f"Using account: {self.account.address}")

    async def start(self):
        """Start the load generator"""
        # Start Prometheus metrics server
        start_http_server(self.config.metrics_port)
        logger.info(
            f"Prometheus metrics server started on port {self.config.metrics_port}"
        )

        # Create aiohttp session
        self.session = aiohttp.ClientSession()

        # Check connection
        await self.check_connection()

        # Start background tasks
        tasks = [
            asyncio.create_task(self.transaction_worker()),
            asyncio.create_task(self.metrics_updater()),
            asyncio.create_task(self.block_monitor()),
        ]

        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            await self.cleanup()

    async def check_connection(self):
        """Check connection to Geth node"""
        try:
            result = await self.rpc_call("eth_blockNumber")
            block_num = int(result, 16)
            logger.info(f"Connected to Geth node, current block: {block_num}")

            # Get chain ID
            chain_id_result = await self.rpc_call("eth_chainId")
            self.chain_id = int(chain_id_result, 16)
            logger.info(f"Chain ID: {self.chain_id}")

            # Check if account is funded
            balance_result = await self.rpc_call(
                "eth_getBalance", [self.account.address, "latest"]
            )
            balance = int(balance_result, 16) / 10**18
            logger.info(f"Account balance: {balance} ETH")

            if balance < 1:
                logger.warning("Account balance is low, consider funding the account")

        except Exception as e:
            logger.error(f"Failed to connect to Geth node: {e}")
            raise

    async def rpc_call(self, method: str, params: list = None) -> Any:
        """Make an RPC call to the Geth node"""
        if params is None:
            params = []

        start_time = time.time()

        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}

        try:
            async with self.session.post(
                self.config.geth_url, json=payload
            ) as response:
                result = await response.json()

                latency = time.time() - start_time
                rpc_latency.labels(method=method).observe(latency)

                if "error" in result:
                    rpc_requests_counter.labels(method=method, status="error").inc()
                    raise Exception(f"RPC error: {result['error']}")

                rpc_requests_counter.labels(method=method, status="success").inc()
                self.rpc_count += 1

                return result["result"]

        except Exception as e:
            rpc_requests_counter.labels(method=method, status="error").inc()
            logger.error(f"RPC call failed for {method}: {e}")
            raise

    async def send_transaction(self) -> Dict[str, Any]:
        """Send a transaction to a random address"""
        start_time = time.time()

        try:
            # Generate random recipient
            recipient = f"0x{random.randbytes(20).hex()}"

            # Get nonce
            nonce_result = await self.rpc_call(
                "eth_getTransactionCount", [self.account.address, "pending"]
            )
            nonce = int(nonce_result, 16)

            # Build transaction
            tx = {
                "nonce": nonce,
                "to": Web3.to_checksum_address(recipient),
                "value": 1000000000000000,  # 0.001 ETH
                "gas": self.config.gas_limit,
                "gasPrice": self.config.gas_price,
                "chainId": self.chain_id,
            }

            # Sign transaction
            signed_tx = self.account.sign_transaction(tx)

            # Send transaction
            tx_hash = await self.rpc_call(
                "eth_sendRawTransaction", [signed_tx.rawTransaction.hex()]
            )

            latency = time.time() - start_time
            transaction_latency.observe(latency)
            transaction_counter.labels(status="success").inc()
            self.tx_count += 1
            self.tx_success_count += 1
            self.gas_used += self.config.gas_limit
            gas_used_total.inc(self.config.gas_limit)

            return {"hash": tx_hash, "status": "success", "latency": latency}

        except Exception as e:
            latency = time.time() - start_time
            transaction_latency.observe(latency)
            transaction_counter.labels(status="error").inc()
            self.tx_count += 1
            self.tx_failure_count += 1
            logger.error(f"Transaction failed: {e}")
            return {"status": "error", "latency": latency, "error": str(e)}

    async def transaction_worker(self):
        """Worker that generates transactions at the target TPS"""
        interval = 1.0 / self.config.target_tps

        logger.info(
            f"Starting transaction worker with target TPS: {self.config.target_tps}"
        )

        start_time = time.time()
        while time.time() - start_time < self.config.test_duration:
            await self.send_transaction()
            await asyncio.sleep(interval)

    async def metrics_updater(self):
        """Update rate metrics every second"""
        while True:
            await asyncio.sleep(1)

            current_time = time.time()
            time_diff = current_time - self.last_metrics_time

            if time_diff > 0:
                # Calculate rates
                tx_diff = self.tx_count - self.last_tx_count
                rpc_diff = self.rpc_count - self.last_rpc_count
                gas_diff = self.gas_used - self.last_gas_used

                tps = tx_diff / time_diff
                rps = rpc_diff / time_diff
                mgas_per_sec = (gas_diff / 1000000) / time_diff

                # Update Prometheus gauges

                current_tps.set(tps)
                current_rps.set(rps)
                current_mgas_per_second.set(mgas_per_sec)

                # Calculate failure rate using simple counters
                if self.tx_count > 0:
                    current_failure_rate = self.tx_failure_count / self.tx_count
                    failure_rate.set(current_failure_rate)
                else:
                    failure_rate.set(0.0)

                # Update last values
                self.last_metrics_time = current_time
                self.last_tx_count = self.tx_count
                self.last_tx_success_count = self.tx_success_count
                self.last_tx_failure_count = self.tx_failure_count
                self.last_rpc_count = self.rpc_count
                self.last_gas_used = self.gas_used

    async def block_monitor(self):
        """Monitor block production"""
        while True:
            try:
                result = await self.rpc_call("eth_blockNumber")
                block_number = int(result, 16)

                if block_number != self.last_block_number:
                    current_time = time.time()
                    if self.last_block_number > 0:
                        block_time = current_time - self.last_block_time
                        block_time_gauge.set(block_time)

                    block_number_gauge.set(block_number)
                    self.current_block_number = (
                        block_number  # Update current block for labels
                    )
                    self.last_block_number = block_number
                    self.last_block_time = current_time

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Block monitoring failed: {e}")
                await asyncio.sleep(5)

    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()


def main():
    """Main entry point"""
    config = LoadGeneratorConfig(
        geth_url=os.getenv("GETH_URL", "http://localhost:8545"),
        target_tps=float(os.getenv("TARGET_TPS", "10")),
        metrics_port=int(os.getenv("METRICS_PORT", "8080")),
        test_duration=int(os.getenv("TEST_DURATION", "3600")),
    )

    generator = EthereumLoadGenerator(config)
    asyncio.run(generator.start())


if __name__ == "__main__":
    main()
