#!/usr/bin/env python3
import time
import subprocess
import json
import argparse
import logging
import sys
from datetime import datetime

"""
Bitcoin Lab Pacer (Heartbeat) - v2 Fixed
Ensures the blockchain never freezes by mining a block if no activity 
is detected for a set interval.
"""

# Defaults
DEFAULT_INTERVAL_MIN = 30
DEFAULT_WALLET_NAME = "pacer"
DEFAULT_LOG_PATH = "pacer.log"

class BitcoinPacer:
    def __init__(self, interval_minutes, wallet_name, log_path):
        self.interval_seconds = interval_minutes * 60
        self.wallet_name = wallet_name
        self.rpc_cmd = ["bitcoin-cli", f"-rpcwallet={self.wallet_name}"]
        
        # Setup Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("Pacer")
        
        self.ensure_wallet()
        self.last_block_time = time.time()
        self.last_height = 0

    def rpc(self, method, params=None):
        if params is None: params = []
        cmd = self.rpc_cmd + [method] + [str(p) for p in params]
        try:
            result = subprocess.check_output(cmd, stderr=subprocess.PIPE, timeout=60)
            result_str = result.decode('utf-8').strip()
            
            # [FIX] Try JSON first, fallback to raw string if that fails
            # (Necessary because 'getnewaddress' returns a plain string, not JSON)
            try:
                return json.loads(result_str)
            except json.JSONDecodeError:
                return result_str
                
        except Exception as e:
            self.logger.error(f"RPC Error ({method}): {e}")
            return None

    def ensure_wallet(self):
        """Creates the pacer wallet if it doesn't exist."""
        wallets = self.rpc("listwallets")
        if wallets is None: 
            wallets = []
            
        if self.wallet_name not in wallets:
            self.logger.info(f"Creating pacer wallet: {self.wallet_name}")
            try:
                # We use subprocess directly here to ignore the output
                subprocess.run(["bitcoin-cli", "createwallet", self.wallet_name], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except Exception as e:
                # If it fails, it might already exist but not be loaded, which is fine
                self.logger.warning(f"Wallet creation skipped (might already exist): {e}")

    def get_blockchain_info(self):
        return self.rpc("getblockchaininfo")

    def mine_block(self):
        """Mines exactly one block to the pacer wallet."""
        self.logger.info("❤️  HEARTBEAT TRIGGERED: Mining 1 block...")
        try:
            addr = self.rpc("getnewaddress")
            if not addr:
                self.logger.error("Could not get address for mining.")
                return

            # Mine 1 block
            self.rpc("generatetoaddress", [1, addr])
            self.logger.info("✅ Block mined successfully.")
        except Exception as e:
            self.logger.error(f"Mining failed: {e}")

    def run(self):
        self.logger.info(f"Starting Pacer. Interval: {self.interval_seconds/60} minutes.")
        
        while True:
            try:
                info = self.get_blockchain_info()
                if not info:
                    time.sleep(10)
                    continue

                current_height = info.get('blocks', 0)
                best_block_hash = info.get('bestblockhash', "")
                
                # Get the timestamp of the last block
                block_data = self.rpc("getblock", [best_block_hash])
                if block_data:
                    last_block_timestamp = block_data.get('time', time.time())
                    time_since_last = time.time() - last_block_timestamp
                    
                    self.logger.info(f"Height: {current_height} | Last Block: {int(time_since_last/60)} min ago")

                    # TRIGGER CONDITION:
                    if time_since_last > self.interval_seconds:
                        self.logger.warning(f"Staleness detected ({int(time_since_last)}s > {self.interval_seconds}s).")
                        self.mine_block()
                    else:
                        # Chain is healthy, do nothing
                        pass

            except KeyboardInterrupt:
                self.logger.info("Stopping Pacer.")
                break
            except Exception as e:
                self.logger.error(f"Loop error: {e}")

            # Check every 60 seconds
            time.sleep(60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bitcoin Lab Pacer")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_MIN, help="Minutes between blocks")
    parser.add_argument("--wallet", type=str, default=DEFAULT_WALLET_NAME, help="Wallet name")
    parser.add_argument("--log", type=str, default=DEFAULT_LOG_PATH, help="Log file path")
    
    args = parser.parse_args()
    
    pacer = BitcoinPacer(args.interval, args.wallet, args.log)
    pacer.run()