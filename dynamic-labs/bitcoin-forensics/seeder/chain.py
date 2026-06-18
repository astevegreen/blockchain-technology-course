"""L2 — Chain: the engine OWNS block production.

This is the fix for v33's #1 failure. v33 broadcast attack transactions and then *waited* for some
external miner (students/agents) to confirm them — so dependent hops never confirmed in order and the
peel chain never formed. Here the builder mines its own blocks on a private regtest it controls, so
every transaction confirms deterministically before the next step spends its output.

A dedicated throwaway *miner address* receives the coinbases so block rewards never pollute the
scenario wallets.
"""
from __future__ import annotations

import logging
import time
from typing import List, Optional

from .rpc import RpcClient


class Chain:
    """Block production / confirmation.

    Two modes:
      * ``self``     — the engine mines its own blocks (regtest test harness; fast, deterministic).
      * ``external`` — production: the seeder NEVER mines. The *student-station agents* produce blocks
                       and the background traffic. ``confirm()`` blocks until the agents have mined the
                       transaction (never proceeds unconfirmed — that was v33's fatal shortcut).

    Correctness is identical in both modes because every dependent step waits for its parent's
    confirmation before it is built (and inputs are named UTXOs, not wallet balances).
    """

    def __init__(
        self,
        rpc: RpcClient,
        miner_address: Optional[str] = None,
        coinbase_maturity: int = 100,   # ClassNet fork uses 10; mainnet/regtest default 100
        mining_mode: str = "self",      # "self" (test) | "external" (production / agents mine)
        maxtries: int = 100_000_000,    # ClassNet retargets difficulty every 4 blocks; default 1M can fail
        poll_interval: float = 3.0,
        confirm_timeout: float = 3600.0,
        logger: Optional[logging.Logger] = None,
    ):
        self.rpc = rpc
        self.miner_address = miner_address
        self.coinbase_maturity = coinbase_maturity
        self.mining_mode = mining_mode
        self.maxtries = maxtries
        self.poll_interval = poll_interval
        self.confirm_timeout = confirm_timeout
        self.log = logger or logging.getLogger("seeder.chain")

    def set_miner_address(self, address: str) -> None:
        self.miner_address = address

    # ---- state --------------------------------------------------------------
    def height(self) -> int:
        return int(self.rpc.call("getblockcount"))

    def best_hash(self) -> str:
        return self.rpc.call("getbestblockhash")

    def confirmations(self, txid: str) -> int:
        """Confirmations for a txid (0 if in mempool, -1 if unknown). Uses txindex via getrawtransaction."""
        try:
            tx = self.rpc.call("getrawtransaction", [txid, True])
        except Exception:
            return -1
        return int(tx.get("confirmations", 0)) if isinstance(tx, dict) else -1

    # ---- production ---------------------------------------------------------
    def mine(self, n: int = 1, to: Optional[str] = None) -> List[str]:
        if self.mining_mode != "self":
            raise RuntimeError("Chain.mine called in 'external' mode — the seeder must not mine")
        addr = to or self.miner_address
        if not addr:
            raise RuntimeError("Chain.mine: no miner address set")
        return self.rpc.call("generatetoaddress", [n, addr, self.maxtries])

    def confirm(self, txids, target: int = 1, max_blocks: int = 200) -> None:
        """Block until every txid has >= `target` confirmations.

        ``self`` mode mines blocks to make that happen; ``external`` mode polls and waits for the
        agents to mine. Either way we NEVER proceed with an unconfirmed parent.
        """
        want = [txids] if isinstance(txids, str) else list(txids)
        if self.mining_mode == "self":
            for _ in range(max_blocks):
                if all(self.confirmations(t) >= target for t in want):
                    return
                self.mine(1)
            missing = [t for t in want if self.confirmations(t) < target]
            raise RuntimeError(f"confirm: {missing} not confirmed after {max_blocks} blocks")
        # external: wait for the agents
        deadline = time.time() + self.confirm_timeout
        while time.time() < deadline:
            if all(self.confirmations(t) >= target for t in want):
                return
            self.log.info("waiting for agents to mine %d tx(s)...", sum(self.confirmations(t) < target for t in want))
            time.sleep(self.poll_interval)
        missing = [t for t in want if self.confirmations(t) < target]
        raise RuntimeError(f"confirm: timed out waiting for agents to mine {missing}")

    def wait_blocks(self, n: int) -> None:
        """Advance the tip by n blocks (v35 temporal hold). self: mine n; external: poll until height rises n."""
        target = self.height() + n
        if self.mining_mode == "self":
            while self.height() < target:
                self.mine(1)
            return
        deadline = time.time() + self.confirm_timeout
        while time.time() < deadline:
            if self.height() >= target:
                return
            self.log.info("temporal hold: tip %d, waiting for +%d (target %d)...", self.height(), n, target)
            time.sleep(self.poll_interval)
        raise RuntimeError(f"wait_blocks: tip stuck below {target}")

    def fund_via_coinbase(self, address: str, sats_needed: int, reward_sat: int = 50 * 100_000_000) -> None:
        """Mine enough *mature* coinbases to `address` to make `sats_needed` spendable.

        Mines `ceil(needed/reward)` blocks to the address, then `coinbase_maturity` more (to any miner
        address) so those coinbases mature and become spendable.
        """
        blocks = max(1, -(-sats_needed // reward_sat))  # ceil division
        self.mine(blocks, to=address)
        # mature them
        self.mine(self.coinbase_maturity, to=self.miner_address or address)
