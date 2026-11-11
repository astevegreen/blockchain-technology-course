/**
 * NodeGraph - Dynamic topology diagram showing instructor node and students.
 * Current user's node is highlighted. Updates as participants join.
 */

import { useMemo } from 'react';

function getRpcLabel(rpcUrl) {
  if (!rpcUrl?.trim()) return 'Instructor Node';
  try {
    const u = new URL(rpcUrl.trim());
    return u.hostname || 'Instructor Node';
  } catch {
    return 'Instructor Node';
  }
}

export default function NodeGraph({ validators = [], myAddress, rpcUrl }) {
  const width = 280;
  const height = 200;
  const cx = width / 2;
  const cy = height / 2;
  const centerRadius = 22;
  const orbitRadius = 70;
  const nodeRadius = 14;

  // Build node list: instructor at center, students on orbit. Always include current user.
  const nodes = useMemo(() => {
    const base = [...new Set(validators)].filter(Boolean);
    const students = myAddress && !base.some(a => a.toLowerCase() === myAddress.toLowerCase())
      ? [myAddress, ...base]
      : base;
    const angleStep = students.length > 0 ? (2 * Math.PI) / Math.max(students.length, 1) : 0;
    return students.map((addr, i) => {
      const angle = -Math.PI / 2 + i * angleStep; // Start from top
      return {
        id: addr,
        x: cx + orbitRadius * Math.cos(angle),
        y: cy + orbitRadius * Math.sin(angle),
        isMe: addr.toLowerCase() === myAddress?.toLowerCase(),
        label: addr.slice(0, 6) + '…',
      };
    });
  }, [validators, myAddress]);

  const rpcLabel = getRpcLabel(rpcUrl);

  return (
    <div style={{
      marginTop: '1rem',
      padding: '0.75rem',
      background: 'rgba(15, 23, 42, 0.6)',
      borderRadius: '0.5rem',
      border: '1px solid rgba(51, 65, 85, 0.5)',
    }}>
      <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', textAlign: 'center' }}>
        Network topology
      </div>
      <svg width={width} height={height} style={{ display: 'block', margin: '0 auto' }}>
        {/* Connection lines: students → instructor */}
        {nodes.map((n) => (
          <line
            key={n.id}
            x1={n.x}
            y1={n.y}
            x2={cx}
            y2={cy}
            stroke={n.isMe ? 'rgba(59, 130, 246, 0.6)' : 'rgba(71, 85, 105, 0.5)'}
            strokeWidth={n.isMe ? 2 : 1}
          />
        ))}

        {/* Center: Instructor node */}
        <circle
          cx={cx}
          cy={cy}
          r={centerRadius}
          fill="rgba(139, 92, 246, 0.3)"
          stroke="#8b5cf6"
          strokeWidth={2}
        />
        <text
          x={cx}
          y={cy - 4}
          textAnchor="middle"
          fill="#c4b5fd"
          fontSize="9"
          fontWeight="bold"
        >
          Instructor
        </text>
        <text
          x={cx}
          y={cy + 8}
          textAnchor="middle"
          fill="#94a3b8"
          fontSize="7"
        >
          {rpcLabel.length > 18 ? rpcLabel.slice(0, 16) + '…' : rpcLabel}
        </text>

        {/* Student nodes */}
        {nodes.map((n) => (
          <g key={n.id}>
            {n.isMe && (
              <circle
                cx={n.x}
                cy={n.y}
                r={nodeRadius + 6}
                fill="none"
                stroke="rgba(59, 130, 246, 0.6)"
                strokeWidth={2}
                strokeDasharray="4 2"
                style={{ animation: 'pulse 2s infinite' }}
              />
            )}
            <circle
              cx={n.x}
              cy={n.y}
              r={nodeRadius}
              fill={n.isMe ? 'rgba(59, 130, 246, 0.8)' : 'rgba(71, 85, 105, 0.6)'}
              stroke={n.isMe ? '#3b82f6' : '#475569'}
              strokeWidth={n.isMe ? 2 : 1}
            />
            <text
              x={n.x}
              y={n.y + nodeRadius + 12}
              textAnchor="middle"
              fill={n.isMe ? '#93c5fd' : '#94a3b8'}
              fontSize="8"
            >
              {n.isMe ? 'You' : n.label}
            </text>
          </g>
        ))}
      </svg>
      {nodes.length === 0 && (
        <div style={{ fontSize: '0.8rem', color: '#64748b', textAlign: 'center', marginTop: '0.5rem' }}>
          Stake or chat to appear on the graph
        </div>
      )}
    </div>
  );
}
