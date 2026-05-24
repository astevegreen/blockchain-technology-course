# Lab 4 — ReliefLedger Consensus: Proof of Work vs Proof of Stake

## Access

When this lab runs behind the shared outer router, use `/labs/consensus/student1/` and `/labs/consensus/instructor/`.

For standalone access without the outer router, the lab router publishes `http://localhost:8083/` by default.

## Overview
This lab demonstrates how consensus works and fails under different incentives.

## Proof of Work
### Tasks
1. **Honest Mining**
   ```bash
   python3 scripts/pow_local.py --id Student --miners 4 --difficulty 18
   ```
   Observe block creation and who wins.

2. **Selfish Mining**
   ```bash
   python3 scripts/pow_local.py --id Student --strategy selfish
   ```
   Student withholds blocks to gain advantage.

3. **Attacker Dominance**
   ```bash
   python3 scripts/pow_local.py --id Student --miners 4 --attacker_rate 0.005
   ```
   One miner has >30% rate. Observe network forks and reduced fairness.

### Record
Fill the table:
| Scenario | Role | Share % | Strategy | Reward % | Forks |
|-----------|------|----------|-----------|-----------|-------|

## Proof of Stake
### Tasks
1. **Stake Growth**
   ```bash
   python3 scripts/pos_sim.py --rounds 15
   ```

2. **Validator Strategy Game**
   ```bash
   python3 scripts/pos_strategy.py --rounds 10 --fee 0.01 --slash 0.1 --delay 0.3
   ```
   Decide which block(s) to sign when forks occur.
   Increase or decrease slashing to find the point where double-signing stops.

### Record
- Fork logs where double-signing occurred.
- Table of stake changes for each round.
- Paragraph explaining why double-signing is tempting and how slashing changes that.

## Reflection
Compare PoW and PoS on fairness, energy, security, and decentralization.
