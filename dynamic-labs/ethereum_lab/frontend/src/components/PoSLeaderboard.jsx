/**
 * PoSLeaderboard - Ranks validators by total ETH (balance + stake + rewards).
 * Highlights the current user's row. Win condition: earn the most ETH.
 */

import { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';

const POLL_INTERVAL_MS = 8000;

export function PoSLeaderboard({ provider, posAddress, PoSABI, wallet }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLeaderboard = useCallback(async () => {
    if (!provider || !posAddress || !PoSABI) return;
    try {
      setError(null);
      const contract = new ethers.Contract(posAddress, PoSABI, provider);
      const count = await contract.getValidatorCount();
      const countNum = Number(count);
      if (countNum === 0) {
        setRows([]);
        setLoading(false);
        return;
      }
      const addresses = [];
      for (let i = 0; i < countNum; i++) {
        const addr = await contract.validatorList(i);
        addresses.push(addr);
      }
      const statsPromises = addresses.map((addr) => contract.getValidatorStats(addr));
      const balancePromises = addresses.map((addr) => provider.getBalance(addr));
      const [statsList, balanceList] = await Promise.all([
        Promise.all(statsPromises),
        Promise.all(balancePromises),
      ]);
      const myAddr = wallet?.address?.toLowerCase();
      const data = addresses.map((addr, i) => {
        const stats = statsList[i];
        const stakeAmount = stats?.stakeAmount ?? stats?.[0] ?? 0n;
        const rewardAmount = stats?.rewardAmount ?? stats?.[1] ?? 0n;
        const balance = balanceList[i];
        const balanceEth = parseFloat(ethers.formatEther(balance));
        const stakeEth = parseFloat(ethers.formatEther(stakeAmount));
        const rewardEth = parseFloat(ethers.formatEther(rewardAmount));
        const totalEth = balanceEth + stakeEth + rewardEth;
        return {
          address: addr,
          balance: balanceEth,
          stake: stakeEth,
          reward: rewardEth,
          total: totalEth,
          isYou: myAddr && addr.toLowerCase() === myAddr,
        };
      });
      data.sort((a, b) => b.total - a.total);
      const ranked = data.map((r, i) => ({ ...r, rank: i + 1 }));
      setRows(ranked);
    } catch (e) {
      setError(e.message || 'Failed to load leaderboard');
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [provider, posAddress, PoSABI, wallet?.address]);

  useEffect(() => {
    fetchLeaderboard();
    const id = setInterval(fetchLeaderboard, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchLeaderboard]);

  if (loading && rows.length === 0) {
    return (
      <div style={{ padding: '1rem', color: '#94a3b8', fontSize: '0.9rem' }}>
        Loading leaderboard...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '1rem', color: '#f87171', fontSize: '0.9rem' }}>
        {error}
      </div>
    );
  }

  const myRow = rows.find((r) => r.isYou);
  const myRank = myRow ? myRow.rank : null;

  return (
    <div style={{
      background: 'rgba(15, 23, 42, 0.8)',
      borderRadius: '0.75rem',
      border: '1px solid rgba(59, 130, 246, 0.3)',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '0.75rem 1rem',
        background: 'rgba(59, 130, 246, 0.15)',
        borderBottom: '1px solid rgba(59, 130, 246, 0.3)',
        fontWeight: 'bold',
        fontSize: '0.95rem',
        color: '#93c5fd',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span>PoS Leaderboard</span>
        {myRank != null && (
          <span style={{ fontSize: '0.85rem', color: '#86efac' }}>
            You&apos;re #{myRank} of {rows.length}
          </span>
        )}
      </div>
      <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ background: 'rgba(0,0,0,0.2)' }}>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', color: '#94a3b8' }}>#</th>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'left', color: '#94a3b8' }}>Address</th>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#94a3b8' }}>Balance</th>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#94a3b8' }}>Staked</th>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#94a3b8' }}>Rewards</th>
              <th style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#86efac' }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr
                key={r.address}
                style={{
                  background: r.isYou ? 'rgba(34, 197, 94, 0.15)' : 'transparent',
                  borderBottom: '1px solid rgba(71, 85, 105, 0.3)',
                }}
              >
                <td style={{ padding: '0.5rem 0.75rem', color: r.isYou ? '#86efac' : '#e2e8f0' }}>
                  {r.rank}
                </td>
                <td style={{ padding: '0.5rem 0.75rem', fontFamily: 'monospace', fontSize: '0.8rem', color: r.isYou ? '#86efac' : '#cbd5e1' }}>
                  {r.address.slice(0, 6)}...{r.address.slice(-4)}
                  {r.isYou && ' (you)'}
                </td>
                <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#94a3b8' }}>
                  {r.balance.toFixed(4)}
                </td>
                <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#94a3b8' }}>
                  {r.stake.toFixed(4)}
                </td>
                <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', color: '#94a3b8' }}>
                  {r.reward.toFixed(4)}
                </td>
                <td style={{ padding: '0.5rem 0.75rem', textAlign: 'right', fontWeight: 'bold', color: '#86efac' }}>
                  {r.total.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && (
        <div style={{ padding: '1rem', color: '#64748b', fontSize: '0.9rem', textAlign: 'center' }}>
          No validators yet. Stake to join the leaderboard.
        </div>
      )}
    </div>
  );
}
