#!/usr/bin/env python3
import socket
import threading
import json
import time
import random
import subprocess
import logging
import sys
import argparse
import signal
import os
from logging.handlers import RotatingFileHandler

"""
AI Disclosure: this script was fully vibed by Gemini 3 Pro
Patched v4: Restores Janitor mode with high threshold (4000) + IBD Fix.
"""

# --- DEFAULT CONFIGURATION ---
DEFAULT_PORT = 31337
DEFAULT_LOG_PATH = "agent.log"
DEFAULT_WALLET_NAME = "student"
# UPDATED: Only clean the mempool if it exceeds 4000 transactions
DEFAULT_MEMPOOL_TRIGGER = 4000 
MAX_CONCURRENT_CONNECTIONS = 10 

class BitcoinAgent:
    def __init__(self, port, log_path, wallet_name, mempool_trigger, verbose=False):
        self.running = True
        self.port = port
        self.wallet_name = wallet_name
        self.mempool_trigger = mempool_trigger
        self.verbose = verbose
        self.rpc_cmd = ["bitcoin-cli", f"-rpcwallet={self.wallet_name}"]
        self.rpc_timeout = 30 # [FIX] Prevent hangs
        
        # --- CONCURRENCY LOCKS ---
        self.addr_lock = threading.Lock()
        self.peer_lock = threading.Lock()
        
        self.conn_limit = threading.Semaphore(MAX_CONCURRENT_CONNECTIONS)
        
        # Setup Rotating Logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S',
            handlers=[
                RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger("Agent")
        
        # State
        self.local_addresses = []
        self.peer_map = {} 
        self.last_rpc_error = None
        
        # Ensure wallet exists and load initial state
        self.check_wallet()
        self.refresh_local_addresses()

    # --- BITCOIN RPC HELPERS ---
    def rpc(self, method, params=None):
        """Executes a bitcoin-cli command with safe parsing and timeouts."""
        self.last_rpc_error = None 
        if params is None: params = []
        
        cmd = self.rpc_cmd + [method] + [str(p) for p in params]
        
        if self.verbose:
            self.logger.info(f"CMD EXEC: {' '.join(cmd)}")

        try:
            # [FIX] Added timeout=30 to prevent zombie processes if bitcoind hangs
            result_bytes = subprocess.check_output(cmd, stderr=subprocess.PIPE, timeout=self.rpc_timeout)
            result_str = result_bytes.decode('utf-8').strip()
            
            if self.verbose and result_str:
                log_out = result_str if len(result_str) < 100 else result_str[:100] + "..."
                self.logger.info(f"CMD RESP: {log_out}")

            try:
                return json.loads(result_str)
            except json.JSONDecodeError:
                return result_str

        except subprocess.TimeoutExpired:
            self.logger.error(f"RPC TIMEOUT: {method} took >{self.rpc_timeout}s")
            return None
        except subprocess.CalledProcessError as e:
            if e.stderr:
                try:
                    self.last_rpc_error = e.stderr.decode('utf-8').strip()
                except:
                    self.last_rpc_error = str(e.stderr)
            
            if self.verbose:
                log_msg = self.last_rpc_error if self.last_rpc_error else str(e)
                self.logger.error(f"CMD FAIL: {log_msg}")
            return None
            
        except Exception as e:
            self.last_rpc_error = str(e)
            self.logger.error(f"RPC Error ({method}): {e}")
            return None

    def check_wallet(self):
        """Ensures the target wallet exists."""
        wallets = self.rpc("listwallets")
        if wallets is None or (isinstance(wallets, list) and self.wallet_name not in wallets):
            self.logger.info(f"Creating wallet: {self.wallet_name}")
            try:
                subprocess.run(["bitcoin-cli", "createwallet", self.wallet_name], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=30)
            except Exception as e:
                self.logger.error(f"Failed to create wallet {self.wallet_name}: {e}")

    def refresh_local_addresses(self):
        """Fetches current addresses from the wallet to populate local list."""
        try:
            addr = self.rpc("getnewaddress")
            if addr and isinstance(addr, str):
                with self.addr_lock:
                    if addr not in self.local_addresses:
                        self.local_addresses.append(addr)
        except Exception as e:
            self.logger.error(f"Error refreshing addresses: {e}")

    def get_my_shareable_address(self):
        """Returns a random local address to share with peers."""
        try:
            with self.addr_lock:
                if not self.local_addresses:
                    return None
                return random.choice(self.local_addresses)
        except Exception as e:
            self.logger.error(f"Error getting local address: {e}")
            return None
            
    def wait_for_ibd(self):
        """Blocks execution until Initial Block Download is complete."""
        self.logger.info("Checking Initial Block Download (IBD) status...")
        while self.running:
            try:
                info = self.rpc("getblockchaininfo")
                if info and isinstance(info, dict):
                    # Check if IBD is active
                    if info.get("initialblockdownload", False):
                        self.logger.info("Node is in IBD (Downloading blocks). Waiting for sync...")
                        time.sleep(10)
                        continue
                    
                    # Optional: Also wait for verification progress if available
                    progress = float(info.get("verificationprogress", 0))
                    if progress > 0.99:
                        self.logger.info("Node is synced (IBD complete). Starting operations.")
                        return
                    else:
                        self.logger.info(f"Waiting for sync (Progress: {progress*100:.2f}%)...")
                        
            except Exception as e:
                self.logger.error(f"Error checking IBD status: {e}")
            
            time.sleep(5)

    # --- NETWORKING (P2P Address Exchange) ---
    def start_listener(self):
        """Starts the TCP server to listen for address exchanges."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.bind(('0.0.0.0', self.port))
                server.listen(10)
                server.settimeout(1.0) 
                self.logger.info(f"Listener started on port {self.port}")

                while self.running:
                    try:
                        # Acquire semaphore to limit active threads
                        if not self.conn_limit.acquire(blocking=False):
                            time.sleep(0.1)
                            continue

                        try:
                            client, addr = server.accept()
                        except socket.timeout:
                            self.conn_limit.release()
                            continue
                        except Exception:
                            self.conn_limit.release()
                            # [FIX] Essential sleep to prevent CPU death spiral on OS error (e.g. EMFILE)
                            time.sleep(1)
                            continue

                        # Spawn thread
                        t = threading.Thread(target=self.handle_client_connection, args=(client, addr))
                        t.daemon = True
                        t.start()
                        
                    except Exception as e:
                        self.logger.error(f"Listener critical loop error: {e}")
                        time.sleep(1)
        except Exception as e:
            self.logger.critical(f"Failed to bind port {self.port}: {e}")
            self.running = False

    def handle_client_connection(self, client_sock, client_addr):
        ip = client_addr[0]
        try:
            client_sock.settimeout(5)
            
            # RECV
            data = client_sock.recv(1024).decode('utf-8')
            if self.verbose:
                self.logger.info(f"NET RECV [from {ip}]: {data}")

            msg = json.loads(data)
            peer_wallet_addr = msg.get("address")
            
            if peer_wallet_addr:
                with self.peer_lock:
                    self.peer_map[ip] = peer_wallet_addr
                self.logger.info(f"Received address from {ip}: {peer_wallet_addr}")

            # SEND
            my_addr = self.get_my_shareable_address()
            response = json.dumps({"address": my_addr})
            
            if self.verbose:
                self.logger.info(f"NET SEND [to {ip}]: {response}")

            client_sock.sendall(response.encode('utf-8'))

        except Exception as e:
            if self.verbose:
                self.logger.warning(f"Connection error with {ip}: {e}")
        finally:
            try:
                client_sock.close()
            except:
                pass
            self.conn_limit.release()

    def exchange_with_peer(self, target_ip):
        if target_ip == "127.0.0.1": return 

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3)
                s.connect((target_ip, self.port))

                # SEND
                my_addr = self.get_my_shareable_address()
                msg = json.dumps({"address": my_addr})
                
                if self.verbose:
                    self.logger.info(f"NET SEND [to {target_ip}]: {msg}")

                s.sendall(msg.encode('utf-8'))

                # RECV
                data = s.recv(1024).decode('utf-8')
                
                if self.verbose:
                    self.logger.info(f"NET RECV [from {target_ip}]: {data}")

                response = json.loads(data)
                peer_wallet_addr = response.get("address")
                
                if peer_wallet_addr:
                    with self.peer_lock:
                        self.peer_map[target_ip] = peer_wallet_addr
                    self.logger.info(f"Exchanged with {target_ip}: Got {peer_wallet_addr}")

        except Exception as e:
            if self.verbose:
                self.logger.debug(f"Exchange failed with {target_ip}: {e}")

    # --- BACKGROUND LOOPS ---
    def loop_peer_discovery(self):
        while self.running:
            try:
                peers = self.rpc("getpeerinfo")
                if peers and isinstance(peers, list):
                    active_ips = []
                    for p in peers:
                        if isinstance(p, dict) and 'addr' in p:
                            ip = p['addr'].split(':')[0]
                            active_ips.append(ip)

                    if active_ips:
                        self.logger.info(f"Discovery: Found {len(active_ips)} peers.")
                        for ip in active_ips:
                            if not self.running: break
                            self.exchange_with_peer(ip)
            except Exception as e:
                self.logger.error(f"Discovery Loop Error: {e}")
            
            for _ in range(300):
                if not self.running: return
                time.sleep(1)

    def loop_address_gen(self):
        while self.running:
            try:
                wait_time = random.randint(10, 15)
                for _ in range(wait_time):
                    if not self.running: return
                    time.sleep(1)
                
                self.refresh_local_addresses()
                
            except Exception as e:
                self.logger.error(f"Address Gen Loop Error: {e}")

    def loop_transactions(self):
        while self.running:
            try:
                # Sleep first
                wait_time = random.randint(30, 90)
                for _ in range(wait_time):
                    if not self.running: return
                    time.sleep(1)

                # --- 1. MEMPOOL CHECK [RESTORED] ---
                try:
                    mempool_info = self.rpc("getmempoolinfo")
                    if mempool_info and isinstance(mempool_info, dict):
                        count = int(mempool_info.get("size", 0))
                        
                        if count > self.mempool_trigger:
                            self.logger.info(f"Mempool Congestion ({count} > {self.mempool_trigger}). Mining 1 block to clear...")
                            mine_addr = self.get_my_shareable_address()
                            if mine_addr:
                                self.rpc("generatetoaddress", [1, mine_addr])
                                time.sleep(2)
                except Exception as e:
                    self.logger.error(f"Mempool check failed: {e}")


                # --- 2. BALANCE CHECK ---
                bal = self.rpc("getbalance")
                current_bal = 0.0
                try:
                    if bal is not None:
                        current_bal = float(bal)
                except ValueError:
                    pass

                # Mine if explicitly broke (Survival Mode)
                if current_bal == 0.0:
                    self.logger.warning("Balance is 0.0. Mining 1 block to refill...")
                    mine_addr = self.get_my_shareable_address()
                    if mine_addr:
                        self.rpc("generatetoaddress", [1, mine_addr])
                    continue

                if current_bal < 0.001:
                    continue

                # --- 3. SEND TRANSACTIONS ---
                tx_targets = {}

                # A. Send to Peer
                target_addr = None
                target_ip = None
                
                with self.peer_lock:
                    peer_ips = list(self.peer_map.keys())
                    if peer_ips:
                        target_ip = random.choice(peer_ips)
                        target_addr = self.peer_map[target_ip]
                
                if target_addr:
                    amount = round(random.uniform(0.01, 0.5), 5)
                    tx_targets[target_addr] = amount
                    self.logger.info(f"Queueing TX to peer {target_ip} ({amount} BTC)")

                # B. Send to Self (Churn)
                my_target = self.get_my_shareable_address()
                if my_target:
                    amount = round(random.uniform(0.01, 0.5), 5)
                    tx_targets[my_target] = amount
                    self.logger.info(f"Queueing Churn TX to self ({amount} BTC)")

                if tx_targets:
                    txid = self.rpc("sendmany", ["", json.dumps(tx_targets)])
                    
                    if txid and isinstance(txid, str):
                        self.logger.info(f"Broadcasted TXID: {txid}")
                    else:
                        if self.last_rpc_error and "Unconfirmed UTXOs are available" in self.last_rpc_error:
                             self.logger.info("Mempool chain limit detected (Unconfirmed UTXOs). Mining 1 block to clear...")
                             # If we are stuck with unconfirmed UTXOs, we MUST mine to unstick ourselves.
                             mine_addr = self.get_my_shareable_address()
                             if mine_addr:
                                 self.rpc("generatetoaddress", [1, mine_addr])
                        else:
                             self.logger.warning("Transaction failed (Insufficient Funds?). Mining 1 block to recover...")
                             mine_addr = self.get_my_shareable_address()
                             if mine_addr:
                                 self.rpc("generatetoaddress", [1, mine_addr])

            except Exception as e:
                self.logger.error(f"Transaction Loop Error: {e}")

    # --- MAIN ENTRY POINT ---
    def start(self):
        self.logger.info(f"Starting Bitcoin Agent on port {self.port} (Wallet: {self.wallet_name})...")
        if self.verbose:
            self.logger.info("Verbose Logging: ENABLED")
        
        # [FIX] Wait for Initial Block Download to prevent race conditions
        self.wait_for_ibd()
        
        self.logger.info("Press Ctrl+C to stop.")

        threads = [
            threading.Thread(target=self.start_listener),
            threading.Thread(target=self.loop_peer_discovery),
            threading.Thread(target=self.loop_address_gen),
            threading.Thread(target=self.loop_transactions)
        ]

        for t in threads:
            t.daemon = True
            t.start()

        def signal_handler(sig, frame):
            self.logger.info("Shutdown signal received. Stopping threads...")
            self.running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while self.running:
            time.sleep(0.5)
        
        self.logger.info("Agent stopped cleanly.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bitcoin Lab Agent")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to listen for address exchange")
    parser.add_argument("--log-path", type=str, default=DEFAULT_LOG_PATH, help="Path to log file")
    parser.add_argument("--wallet", type=str, default=DEFAULT_WALLET_NAME, help="Name of the wallet to control")
    parser.add_argument("--mempool-trigger", type=int, default=DEFAULT_MEMPOOL_TRIGGER, help="Mine a block if pending txs exceed this amount")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging of commands and traffic")
    
    args = parser.parse_args()
    
    time.sleep(5) 
    
    agent = BitcoinAgent(
        port=args.port, 
        log_path=args.log_path, 
        wallet_name=args.wallet, 
        mempool_trigger=args.mempool_trigger,
        verbose=args.verbose
    )
    agent.start()