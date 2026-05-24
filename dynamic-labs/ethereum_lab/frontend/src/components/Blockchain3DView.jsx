/**
 * Blockchain3DView - Gibson-style 3D blockchain visualization
 * Full chain, live growth, helix layout, edges, variable cube size, uncles, L1/L2.
 * Hover and proximity metadata tooltips.
 */
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Line, Html } from '@react-three/drei';
import * as THREE from 'three';
import { ethers } from 'ethers';

const RENDER_CAP = 2000;
const CUBE_SIZE = 0.8;
const HELIX_RADIUS = 3;
const ATTESTING_BLOCKS = 12;
const HELIX_ANGLE_STEP = 0.4;
const HELIX_VERTICAL_STEP = 0.5;
const FILTER_TRANSITION_DURATION = 1.4;
const FILTER_LERP_SPEED = 0.065;
const FILTER_DRIFT_AMOUNT = 8;

function getLayoutPosition(index, layout, yOffset = 0) {
  if (layout === 'helix') {
    const t = index * HELIX_ANGLE_STEP;
    return [
      HELIX_RADIUS * Math.cos(t),
      yOffset + index * HELIX_VERTICAL_STEP,
      HELIX_RADIUS * Math.sin(t),
    ];
  }
  if (layout === 'zigzag') {
    const offset = 1.5;
    return [
      (index % 2 === 0 ? 1 : -1) * offset,
      yOffset + index * 0.5,
      0,
    ];
  }
  return [index * 1.2, yOffset, 0];
}

function BlockCube({ block, position, scale, isSelected, isLatest, isNewBlock, isHovered, onSelect, onHover, onHoverEnd, color, animatedPosition, animatedScale, animatedOpacity }) {
  const handlePointerOver = (e) => {
    e.stopPropagation();
    document.body.style.cursor = 'pointer';
    onHover?.(block, animatedPosition ?? position);
  };
  const handlePointerOut = () => {
    document.body.style.cursor = 'default';
    onHoverEnd?.();
  };
  const baseOpacity = isNewBlock ? 1 : isLatest ? 0.95 : 0.85;
  const opacity = (animatedOpacity != null ? animatedOpacity : (isHovered ? 1 : baseOpacity));
  const displayPos = animatedPosition ?? position;
  const displayScale = animatedScale != null ? animatedScale : scale;
  return (
    <group position={displayPos} scale={displayScale}>
      {isHovered && opacity > 0.01 && (
        <mesh>
          <boxGeometry args={[CUBE_SIZE * 1.15, CUBE_SIZE * 1.15, CUBE_SIZE * 1.15]} />
          <meshBasicMaterial wireframe={true} color="#22ff88" transparent opacity={0.25} />
        </mesh>
      )}
      <mesh
        onClick={(e) => {
          e.stopPropagation();
          if (opacity > 0.01) onSelect(block);
        }}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        visible={opacity > 0.01}
      >
        <boxGeometry args={[CUBE_SIZE, CUBE_SIZE, CUBE_SIZE]} />
        <meshBasicMaterial
          wireframe={true}
          color={color || (isSelected ? '#00ffcc' : isLatest || isNewBlock ? '#22ff88' : '#22ff88')}
          transparent
          opacity={opacity}
        />
      </mesh>
    </group>
  );
}

function BlockEdge({ fromPos, toPos, color = '#22ff88', dashed = false }) {
  const points = useMemo(() => [fromPos, toPos], [fromPos, toPos]);
  return (
    <Line
      points={points}
      color={color}
      lineWidth={dashed ? 0.5 : 1}
      dashed={dashed}
    />
  );
}

function UncleCube({ uncle, position, onSelect, onHover, onHoverEnd }) {
  return (
    <group position={position} scale={0.5}>
      <mesh
        onClick={(e) => { e.stopPropagation(); onSelect(uncle); }}
        onPointerOver={(e) => { e.stopPropagation(); document.body.style.cursor = 'pointer'; onHover?.(uncle, position); }}
        onPointerOut={() => { document.body.style.cursor = 'default'; onHoverEnd?.(); }}
      >
        <boxGeometry args={[CUBE_SIZE, CUBE_SIZE, CUBE_SIZE]} />
        <meshBasicMaterial wireframe={true} color="#f9a8d4" transparent opacity={0.7} />
      </mesh>
    </group>
  );
}

function BlockTooltip({ block, position, isProximity, isAttesting }) {
  const hashStr = block?.hash ? String(block.hash) : '';
  const truncatedHash = hashStr.length > 12 ? `0x...${hashStr.slice(-8)}` : hashStr;
  const timestamp = block?.timestamp
    ? new Date(Number(block.timestamp) * 1000).toLocaleString()
    : '—';
  const statusLabel = isAttesting ? 'Attesting (not finalized)' : 'Finalized';
  return (
    <Html
      position={[position[0], position[1] + 1.2, position[2]]}
      distanceFactor={8}
      pointerEvents="none"
      style={{ opacity: isProximity ? 0.85 : 1, transition: 'opacity 0.15s' }}
    >
      <div
        style={{
          background: 'rgba(10,10,15,0.92)',
          border: '1px solid rgba(34,255,136,0.5)',
          color: '#22ff88',
          fontFamily: 'monospace',
          padding: '0.5rem 0.75rem',
          borderRadius: '0.25rem',
          fontSize: '0.8rem',
          minWidth: 140,
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 0,
            height: 2,
            background: 'rgba(34,255,136,0.6)',
            animation: 'scanLine 0.5s ease-out forwards',
          }}
        />
        <div style={{ marginBottom: '0.25rem', color: '#00ffcc', fontWeight: 600 }}>
          Block #{block?.number} {block?.layer === 'L2' && '(L2)'}
        </div>
        <div style={{ color: isAttesting ? '#fbbf24' : '#22ff88', fontSize: '0.7rem', marginBottom: '0.2rem' }}>{statusLabel}</div>
        <div style={{ color: '#93c5fd', fontSize: '0.75rem', marginBottom: '0.2rem' }}>{truncatedHash}</div>
        <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>
          {block?.txCount ?? 0} tx · {timestamp}
        </div>
      </div>
    </Html>
  );
}

const PROXIMITY_THRESHOLD = 15;

const DRAG_PLANE_SIZE = 150;
const DRAG_PLANE_Y = 0;

function DraggablePlane({ chainOffset, onOffsetChange }) {
  const { camera, gl, raycaster } = useThree();
  const planeRef = useRef();
  const isDraggingRef = useRef(false);
  const lastIntersectRef = useRef(null);

  const handlePointerDown = useCallback(
    (e) => {
      e.stopPropagation();
      isDraggingRef.current = true;
      lastIntersectRef.current = e.point.clone();
    },
    []
  );

  const getPointerFromEvent = useCallback((e) => {
    const rect = gl.domElement.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    const y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    return new THREE.Vector2(x, y);
  }, [gl.domElement]);

  useEffect(() => {
    const dom = gl.domElement;
    const onMove = (e) => {
      if (!isDraggingRef.current || !planeRef.current) return;
      const pointer = getPointerFromEvent(e);
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObject(planeRef.current);
      if (hits.length > 0) {
        const delta = hits[0].point.clone().sub(lastIntersectRef.current);
        lastIntersectRef.current = hits[0].point.clone();
        onOffsetChange((prev) => [prev[0] + delta.x, prev[1], prev[2] + delta.z]);
      }
    };
    const onUp = () => {
      isDraggingRef.current = false;
      lastIntersectRef.current = null;
    };
    dom.addEventListener('pointermove', onMove);
    dom.addEventListener('pointerup', onUp);
    dom.addEventListener('pointerleave', onUp);
    return () => {
      dom.removeEventListener('pointermove', onMove);
      dom.removeEventListener('pointerup', onUp);
      dom.removeEventListener('pointerleave', onUp);
    };
  }, [camera, gl.domElement, getPointerFromEvent, raycaster, onOffsetChange]);

  return (
    <mesh
      ref={planeRef}
      position={[0, DRAG_PLANE_Y, 0]}
      rotation={[-Math.PI / 2, 0, 0]}
      onPointerDown={handlePointerDown}
      visible={false}
    >
      <planeGeometry args={[DRAG_PLANE_SIZE, DRAG_PLANE_SIZE]} />
      <meshBasicMaterial transparent opacity={0} />
    </mesh>
  );
}

function ProximityDetector({ l1Blocks, l2Blocks, unclesMap, layout, setNearBlock, chainOffset, chainCenterOffset = 0 }) {
  const { camera } = useThree();
  const frameCount = useRef(0);
  const lastClosestRef = useRef(null);
  const [ox, oy, oz] = chainOffset;
  useFrame(() => {
    frameCount.current += 1;
    if (frameCount.current % 3 !== 0) return;
    const items = [];
    l1Blocks.forEach((block, i) => {
      const p = getLayoutPosition(i, layout, chainCenterOffset);
      items.push({ block, localPos: p, worldPos: [p[0] + ox, p[1] + oy, p[2] + oz] });
      (unclesMap.get(block.number) || []).forEach((u, ui) => {
        const pos = getLayoutPosition(i, layout, chainCenterOffset);
        const localPos = [pos[0] + (ui === 0 ? 1.5 : -1.5), pos[1] + 0.5, pos[2]];
        items.push({ block: u, localPos, worldPos: [localPos[0] + ox, localPos[1] + oy, localPos[2] + oz] });
      });
    });
    l2Blocks.forEach((block, i) => {
      const p = getLayoutPosition(i, layout, 4);
      items.push({ block, localPos: p, worldPos: [p[0] + ox, p[1] + oy, p[2] + oz] });
    });
    let closest = null;
    let minDist = PROXIMITY_THRESHOLD;
    const camPos = new THREE.Vector3();
    camera.getWorldPosition(camPos);
    for (const { block, localPos, worldPos } of items) {
      const pos = new THREE.Vector3(worldPos[0], worldPos[1], worldPos[2]);
      const d = camPos.distanceTo(pos);
      if (d < minDist) {
        minDist = d;
        closest = { block, position: localPos };
      }
    }
    const key = closest ? `${closest.block?.number}-${closest.block?.hash}` : null;
    if (key !== lastClosestRef.current) {
      lastClosestRef.current = key;
      setNearBlock(closest);
    }
  });
  return null;
}

function lerp(a, b, t) {
  return a + (b - a) * Math.min(1, Math.max(0, t));
}

function FitToViewEffect({ fitToView, blockCount, controlsRef }) {
  const { camera } = useThree();
  const prevFitRef = useRef(0);
  useFrame(() => {
    if (fitToView !== prevFitRef.current && blockCount > 0) {
      prevFitRef.current = fitToView;
      const extent = Math.max(50, (blockCount - 1) * HELIX_VERTICAL_STEP * 0.6);
      const distance = Math.max(80, Math.min(400, extent * 1.1));
      const dir = new THREE.Vector3(1, 1, 1).normalize();
      camera.position.set(dir.x * distance, dir.y * distance, dir.z * distance);
      camera.lookAt(0, 0, 0);
      camera.updateProjectionMatrix();
      const controls = controlsRef?.current;
      if (controls?.target) {
        controls.target.set(0, 0, 0);
      }
    }
  });
  return null;
}

function ChainScene({ blocks, unclesMap, selectedBlock, onSelectBlock, layout, blockRange, demoL2, lastKnownBlock, hoveredBlock, nearBlock, onHover, onHoverEnd, setNearBlock, chainOffset, onChainOffsetChange, isContractFiltered, involvedBlockNumbers, fitToView = 0, blockCount = 0 }) {
  const l1Blocks = blocks.filter((b) => (b.layer || 'L1') === 'L1');
  const l2Blocks = blocks.filter((b) => b.layer === 'L2');
  const l2YOffset = 4;

  const chainCenterOffset = -((l1Blocks.length - 1) / 2) * HELIX_VERTICAL_STEP;

  const tooltipTarget = hoveredBlock || nearBlock;
  const isHovered = (block) => hoveredBlock?.block?.number === block?.number && hoveredBlock?.block?.hash === block?.hash;

  const [, setAnimTick] = useState(0);
  const animStateRef = useRef(new Map());
  const filterStartRef = useRef(null);
  const prevFilterRef = useRef(false);

  const involvedSet = involvedBlockNumbers || new Set();
  const filteredBlocksOrdered = useMemo(() => {
    return l1Blocks.filter((b) => involvedSet.has(b.number));
  }, [l1Blocks, involvedSet]);
  const filteredCenterOffset = filteredBlocksOrdered.length > 0
    ? -((filteredBlocksOrdered.length - 1) / 2) * HELIX_VERTICAL_STEP
    : 0;
  const filteredIndices = useMemo(() => {
    const map = new Map();
    filteredBlocksOrdered.forEach((b, fi) => {
      const origIdx = l1Blocks.findIndex((x) => x.number === b.number);
      map.set(b.number, { filteredIndex: fi, originalIndex: origIdx });
    });
    return map;
  }, [l1Blocks, filteredBlocksOrdered]);

  const isTransitioningRef = useRef(false);
  const controlsRef = useRef();

  useFrame((state) => {
    const now = state.clock.elapsedTime;
    const wasFiltered = prevFilterRef.current;

    if (isContractFiltered && involvedSet.size > 0) {
      if (!wasFiltered) {
        filterStartRef.current = now;
        prevFilterRef.current = true;
        isTransitioningRef.current = true;
      }

      l1Blocks.forEach((block, i) => {
        const baseScale = 1 + Math.min((block.txCount || 0) / 20, 1.5);
        const info = filteredIndices.get(block.number);
        const isInvolved = !!info;

        let targetPos, targetScale, targetOpacity;
        if (isInvolved) {
          targetPos = getLayoutPosition(info.filteredIndex, layout, filteredCenterOffset);
          targetScale = baseScale;
          targetOpacity = 1;
        } else {
          const fromPos = getLayoutPosition(i, layout, chainCenterOffset);
          const drift = FILTER_DRIFT_AMOUNT * (i % 2 === 0 ? 1 : -1);
          targetPos = [fromPos[0] + drift, fromPos[1] - 3, fromPos[2] + drift * 0.5];
          targetScale = 0.15;
          targetOpacity = 0;
        }

        const fromPos = getLayoutPosition(i, layout, chainCenterOffset);
        const fromScale = 1 + Math.min((block.txCount || 0) / 20, 1.5);

        let current = animStateRef.current.get(block.number);
        if (!current) {
          current = {
            position: [fromPos[0], fromPos[1], fromPos[2]],
            scale: fromScale,
            opacity: 1,
          };
          animStateRef.current.set(block.number, current);
        }

        current.position[0] = lerp(current.position[0], targetPos[0], FILTER_LERP_SPEED);
        current.position[1] = lerp(current.position[1], targetPos[1], FILTER_LERP_SPEED);
        current.position[2] = lerp(current.position[2], targetPos[2], FILTER_LERP_SPEED);
        current.scale = lerp(current.scale, targetScale, FILTER_LERP_SPEED);
        current.opacity = lerp(current.opacity, targetOpacity, FILTER_LERP_SPEED);
      });

      const elapsed = now - (filterStartRef.current || now);
      if (elapsed < FILTER_TRANSITION_DURATION + 0.5) {
        setAnimTick((t) => t + 1);
      }
    } else if (wasFiltered && animStateRef.current.size > 0) {
      prevFilterRef.current = false;
      isTransitioningRef.current = true;
      filterStartRef.current = now;
    } else if (isTransitioningRef.current && !isContractFiltered && animStateRef.current.size > 0) {
      l1Blocks.forEach((block, i) => {
        const fromPos = getLayoutPosition(i, layout, chainCenterOffset);
        const fromScale = 1 + Math.min((block.txCount || 0) / 20, 1.5);
        const targetPos = fromPos;
        const targetScale = fromScale;
        const targetOpacity = 1;

        let current = animStateRef.current.get(block.number);
        if (!current) return;

        current.position[0] = lerp(current.position[0], targetPos[0], FILTER_LERP_SPEED);
        current.position[1] = lerp(current.position[1], targetPos[1], FILTER_LERP_SPEED);
        current.position[2] = lerp(current.position[2], targetPos[2], FILTER_LERP_SPEED);
        current.scale = lerp(current.scale, targetScale, FILTER_LERP_SPEED);
        current.opacity = lerp(current.opacity, targetOpacity, FILTER_LERP_SPEED);
      });

      const elapsed = now - (filterStartRef.current || now);
      if (elapsed > FILTER_TRANSITION_DURATION) {
        animStateRef.current.clear();
        isTransitioningRef.current = false;
      }
      setAnimTick((t) => t + 1);
    } else if (!isContractFiltered) {
      prevFilterRef.current = false;
      filterStartRef.current = null;
      isTransitioningRef.current = false;
      animStateRef.current.clear();
    }
  });

  return (
    <>
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1} color="#22ff88" />
      <pointLight position={[-10, -10, 10]} intensity={0.5} color="#00ffcc" />
      <OrbitControls ref={controlsRef} enablePan enableZoom enableRotate zoomToCursor minDistance={3} maxDistance={400} target={[0, 0, 0]} />
      <FitToViewEffect fitToView={fitToView} blockCount={blockCount} controlsRef={controlsRef} />
      <DraggablePlane chainOffset={chainOffset} onOffsetChange={onChainOffsetChange} />
      <ProximityDetector l1Blocks={l1Blocks} l2Blocks={l2Blocks} unclesMap={unclesMap} layout={layout} setNearBlock={setNearBlock} chainOffset={chainOffset} chainCenterOffset={chainCenterOffset} />

      <group position={chainOffset}>
        {tooltipTarget && (
          <BlockTooltip
            block={tooltipTarget.block}
            position={tooltipTarget.position}
            isProximity={!hoveredBlock && !!nearBlock}
            isAttesting={
              tooltipTarget.block?.layer !== 'L2' &&
              lastKnownBlock != null &&
              (lastKnownBlock - (tooltipTarget.block?.number ?? 0)) < ATTESTING_BLOCKS
            }
          />
        )}

        {l1Blocks.map((block, i) => {
        const pos = getLayoutPosition(i, layout, chainCenterOffset);
        const scale = 1 + Math.min((block.txCount || 0) / 20, 1.5);
        const uncles = unclesMap.get(block.number) || [];
        const isAttesting =
          lastKnownBlock != null && (lastKnownBlock - block.number) < ATTESTING_BLOCKS;
        const blockColor = isContractFiltered ? '#00ffcc' : isAttesting ? '#fbbf24' : '#22ff88';
        const anim = animStateRef.current.size > 0 ? animStateRef.current.get(block.number) : null;
        const animPos = anim ? anim.position : null;
        const animScale = anim ? anim.scale : null;
        const animOpacity = anim ? anim.opacity : null;
        return (
          <group key={`l1-${block.number}`}>
            <BlockCube
              block={block}
              position={pos}
              scale={scale}
              isSelected={selectedBlock?.number === block.number && selectedBlock?.layer !== 'L2'}
              isLatest={block.number === lastKnownBlock}
              isNewBlock={block.isNewBlock}
              isHovered={isHovered(block)}
              onSelect={onSelectBlock}
              onHover={onHover}
              onHoverEnd={onHoverEnd}
              color={blockColor}
              animatedPosition={animPos}
              animatedScale={animScale}
              animatedOpacity={animOpacity}
            />
            {i > 0 && (!isContractFiltered || (involvedSet.has(block.number) && involvedSet.has(l1Blocks[i - 1]?.number))) && (
              <BlockEdge
                fromPos={
                  animStateRef.current.size > 0
                    ? (animStateRef.current.get(l1Blocks[i - 1]?.number)?.position ?? getLayoutPosition(i - 1, layout, chainCenterOffset))
                    : getLayoutPosition(i - 1, layout, chainCenterOffset)
                }
                toPos={animPos ?? pos}
                color={isContractFiltered ? '#00ffcc' : '#22ff88'}
              />
            )}
            {!isContractFiltered && uncles.map((u, ui) => (
              <group key={`u-${block.number}-${ui}`}>
                <UncleCube
                  uncle={u}
                  position={[pos[0] + (ui === 0 ? 1.5 : -1.5), pos[1] + 0.5, pos[2]]}
                  onSelect={onSelectBlock}
                  onHover={onHover}
                  onHoverEnd={onHoverEnd}
                />
                <BlockEdge
                  fromPos={pos}
                  toPos={[pos[0] + (ui === 0 ? 1.5 : -1.5), pos[1] + 0.5, pos[2]]}
                  color="#f9a8d4"
                />
              </group>
            ))}
          </group>
        );
      })}

      {l2Blocks.map((block, i) => {
        const pos = getLayoutPosition(i, layout, l2YOffset);
        const scale = 1 + Math.min((block.txCount || 0) / 20, 1.5);
        return (
          <group key={`l2-${block.number}`}>
            <BlockCube
              block={block}
              position={pos}
              scale={scale}
              isSelected={selectedBlock?.number === block.number && selectedBlock?.layer === 'L2'}
              isLatest={false}
              isNewBlock={false}
              isHovered={isHovered(block)}
              onSelect={onSelectBlock}
              onHover={onHover}
              onHoverEnd={onHoverEnd}
              color="#00ffcc"
            />
            {i > 0 && (
              <BlockEdge fromPos={getLayoutPosition(i - 1, layout, l2YOffset)} toPos={pos} color="#00ffcc" />
            )}
            {l1Blocks.length > 0 && (
              <BlockEdge
                fromPos={pos}
                toPos={getLayoutPosition(Math.min(i, l1Blocks.length - 1), layout, chainCenterOffset)}
                color="#64748b"
                dashed={true}
              />
            )}
          </group>
        );
      })}
      </group>
    </>
  );
}

function blockToRecord(block) {
  const txs = block.prefetchedTransactions ?? block.transactions ?? [];
  return {
    number: Number(block.number),
    hash: block.hash,
    parentHash: block.parentHash,
    timestamp: block.timestamp,
    txCount: Array.isArray(txs) ? txs.length : 0,
    uncles: [],
    layer: block.layer || 'L1',
    isNewBlock: false,
  };
}

export function Blockchain3DView({ provider, rpcUrl, l2Provider, demoL2: demoL2Prop = false, l2Mode = false, showL2Info = false }) {
  const [blocks, setBlocks] = useState([]);
  const [unclesMap, setUnclesMap] = useState(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedBlock, setSelectedBlock] = useState(null);
  const [hoveredBlock, setHoveredBlock] = useState(null);
  const [nearBlock, setNearBlock] = useState(null);
  const [blockRange, setBlockRange] = useState({ mode: 'all', count: 500, from: 0, to: 500 });
  const [layout, setLayout] = useState('helix');
  const [lastKnownBlock, setLastKnownBlock] = useState(null);
  const [demoL2, setDemoL2] = useState(demoL2Prop);
  const [chainOffset, setChainOffset] = useState([0, 0, 0]);
  const [fitToView, setFitToView] = useState(0);
  const [contractFilter, setContractFilter] = useState(null);
  const [contractSearchInput, setContractSearchInput] = useState('');
  const [contractData, setContractData] = useState(null);
  const [contractSearchLoading, setContractSearchLoading] = useState(false);
  const [contractSearchError, setContractSearchError] = useState(null);
  const lastKnownRef = useRef(null);
  const blockSubscriptionRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const scanAbortRef = useRef(false);

  const fetchBlockRange = useCallback(
    async (start, end, append = false) => {
      if (!provider) return [];
      const fetched = [];
      const cap = Math.min(end - start + 1, RENDER_CAP);
      for (let i = start; i <= end && fetched.length < cap; i++) {
        try {
          const block = await provider.getBlock(i, true);
          if (block) {
            const rec = blockToRecord(block);
            rec.layer = 'L1';
            fetched.push(rec);
          }
        } catch (_) {}
      }
      if (append) {
        setBlocks((prev) => {
          const next = [...prev, ...fetched];
          if (blockRange.mode === 'last' && blockRange.count && next.length > blockRange.count) {
            return next.slice(-blockRange.count);
          }
          return next.slice(-RENDER_CAP);
        });
      } else {
        setBlocks(fetched);
      }
      return fetched;
    },
    [provider, blockRange.mode, blockRange.count]
  );

  const initialFetch = useCallback(async () => {
    if (!provider) return;
    setLoading(true);
    setError(null);
    try {
      const latest = Number(await provider.getBlockNumber());
      lastKnownRef.current = latest;

      let start = 0;
      let end = latest;

      if (blockRange.mode === 'last') {
        start = Math.max(0, latest - (blockRange.count || 500) + 1);
        end = latest;
      } else if (blockRange.mode === 'custom') {
        start = Math.max(0, blockRange.from ?? 0);
        end = Math.min(latest, blockRange.to ?? latest);
      }

      const count = Math.min(end - start + 1, RENDER_CAP);
      const fetched = [];
      for (let i = start; i <= end && fetched.length < count; i++) {
        const block = await provider.getBlock(i, true);
        if (block) {
          const rec = blockToRecord(block);
          rec.layer = 'L1';
          fetched.push(rec);
        }
      }
      setBlocks(fetched);
      setLastKnownBlock(latest);

      const unclesMapNext = new Map();
      for (let i = 0; i < Math.min(fetched.length, 50); i++) {
        const b = fetched[i];
        try {
          const raw = await provider.send('eth_getBlockByNumber', ['0x' + b.number.toString(16), false]);
          const uncleHashes = raw?.uncles || [];
          if (uncleHashes.length > 0) {
            const uncles = [];
            for (const h of uncleHashes.slice(0, 2)) {
              try {
                const u = await provider.getBlock(h);
                if (u) uncles.push(blockToRecord({ ...u, layer: 'uncle' }));
              } catch (_) {}
            }
            if (uncles.length) unclesMapNext.set(b.number, uncles);
          }
        } catch (_) {}
      }
      setUnclesMap(unclesMapNext);

      if (l2Provider) {
        try {
          const l2Latest = Number(await l2Provider.getBlockNumber());
          const l2Start = Math.max(0, l2Latest - 30);
          const l2Blocks = [];
          for (let i = l2Start; i <= l2Latest && l2Blocks.length < 31; i++) {
            const block = await l2Provider.getBlock(i, true);
            if (block) {
              const rec = blockToRecord(block);
              rec.layer = 'L2';
              l2Blocks.push(rec);
            }
          }
          setBlocks((prev) => [...prev, ...l2Blocks]);
        } catch (_) {}
      } else if (demoL2) {
        const demo = [];
        for (let i = 0; i < 8; i++) {
          demo.push({
            number: 9000 + i,
            hash: '0x' + '0'.repeat(63) + i.toString(16),
            parentHash: '0x' + '0'.repeat(63) + (i ? (i - 1).toString(16) : '0'),
            timestamp: Math.floor(Date.now() / 1000) - (8 - i) * 12,
            txCount: 5 + i,
            uncles: [],
            layer: 'L2',
            isNewBlock: false,
          });
        }
        setBlocks((prev) => [...prev, ...demo]);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch blocks');
      setBlocks([]);
    } finally {
      setLoading(false);
    }
  }, [provider, l2Provider, demoL2, blockRange.mode, blockRange.count, blockRange.from, blockRange.to]);

  const appendNewBlocks = useCallback(
    async (fromBlock, toBlock) => {
      if (!provider || fromBlock > toBlock) return;
      const newBlocks = [];
      for (let i = fromBlock; i <= toBlock; i++) {
        try {
          const block = await provider.getBlock(i, true);
          if (block) {
            const rec = blockToRecord(block);
            rec.layer = 'L1';
            rec.isNewBlock = true;
            newBlocks.push(rec);
          }
        } catch (_) {}
      }
      if (newBlocks.length > 0) {
        setBlocks((prev) => {
          let next = [...prev, ...newBlocks];
          if (blockRange.mode === 'last' && blockRange.count && next.length > blockRange.count) {
            next = next.slice(-blockRange.count);
          }
          return next.slice(-RENDER_CAP);
        });
        setTimeout(() => {
          setBlocks((p) =>
            p.map((b) => (b.isNewBlock ? { ...b, isNewBlock: false } : b))
          );
        }, 2000);
      }
      setLastKnownBlock(toBlock);
      lastKnownRef.current = toBlock;
    },
    [provider, blockRange.mode, blockRange.count]
  );

  useEffect(() => {
    initialFetch();
  }, [initialFetch]);

  useEffect(() => {
    if (!provider) return;
    const poll = async () => {
      try {
        const latest = Number(await provider.getBlockNumber());
        const last = lastKnownRef.current ?? 0;
        if (latest > last) {
          await appendNewBlocks(last + 1, latest);
        }
      } catch (_) {}
    };
    if (typeof provider.on === 'function') {
      const handler = (blockNumber) => {
        const n = Number(blockNumber);
        const last = lastKnownRef.current ?? 0;
        if (n > last) appendNewBlocks(last + 1, n);
      };
      provider.on('block', handler);
      blockSubscriptionRef.current = () => provider.off?.('block', handler);
    }
    pollIntervalRef.current = setInterval(poll, 2500);
    return () => {
      if (blockSubscriptionRef.current) blockSubscriptionRef.current();
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [provider, appendNewBlocks]);

  const refetchForRange = useCallback(() => {
    initialFetch();
  }, [initialFetch]);

  const scanContract = useCallback(
    async (addressInput) => {
      const raw = (addressInput || contractSearchInput || contractFilter || '').trim();
      if (!raw || !provider) return;
      const normalized = raw.startsWith('0x') ? raw.toLowerCase() : '0x' + raw.toLowerCase();
      if (!/^0x[a-f0-9]{40}$/.test(normalized)) {
        setContractSearchError('Enter a valid address (0x + 40 hex chars)');
        return;
      }
      setContractSearchError(null);
      setContractSearchLoading(true);
      scanAbortRef.current = false;
      try {
        const code = await provider.getCode(normalized);
        if (!code || code === '0x' || code === '0x0') {
          setContractSearchError('Not a contract');
          setContractSearchLoading(false);
          return;
        }
        const latest = Number(await provider.getBlockNumber());
        const maxBlocks = 500;
        const startBlock = Math.max(0, latest - maxBlocks + 1);
        let deploymentBlock = null;
        let deploymentTxHash = null;
        const getBlockTxs = (block) => block?.prefetchedTransactions ?? block?.transactions ?? [];
        for (let b = latest; b >= startBlock && !scanAbortRef.current; b--) {
          const block = await provider.getBlock(b, true);
          const txs = getBlockTxs(block);
          for (const tx of txs) {
            if (!tx) continue;
            const txHash = typeof tx === 'string' ? tx : tx.hash;
            if (!txHash) continue;
            try {
              const receipt = await provider.getTransactionReceipt(txHash);
              const created = receipt?.contractAddress;
              if (created && String(created).toLowerCase() === normalized) {
                deploymentBlock = Number(block.number);
                deploymentTxHash = txHash;
                break;
              }
            } catch (_) {}
          }
          if (deploymentBlock != null) break;
        }
        const scanStart = deploymentBlock ?? 0;
        const scanEnd = Math.min(latest, scanStart + 300);
        const involvedBlockNumbers = new Set();
        const transactions = [];
        const addressesSet = new Set([normalized]);
        for (let b = scanStart; b <= scanEnd && !scanAbortRef.current; b++) {
          const block = await provider.getBlock(b, true);
          const txs = getBlockTxs(block);
          for (const tx of txs) {
            if (!tx) continue;
            const txObj = typeof tx === 'object' ? tx : null;
            const txHash = typeof tx === 'string' ? tx : tx.hash;
            const to = txObj?.to;
            const from = txObj?.from;
            let type = null;
            let isDeployment = false;
            try {
              const receipt = await provider.getTransactionReceipt(txHash);
              const created = receipt?.contractAddress;
              if (created && String(created).toLowerCase() === normalized) {
                type = 'deployment';
                isDeployment = true;
              } else if (to && String(to).toLowerCase() === normalized) {
                type = 'to';
              } else if (from && String(from).toLowerCase() === normalized) {
                type = 'from';
              }
            } catch (_) {}
            if (type) {
              involvedBlockNumbers.add(Number(block.number));
              const fromAddr = txObj?.from ?? null;
              const toAddr = txObj?.to ?? (isDeployment ? normalized : null);
              if (fromAddr) addressesSet.add(fromAddr);
              if (toAddr) addressesSet.add(toAddr);
              transactions.push({
                blockNumber: Number(block.number),
                txHash,
                from: fromAddr,
                to: toAddr,
                value: txObj?.value ?? 0n,
                isDeployment,
                type: type || (isDeployment ? 'deployment' : 'to'),
              });
            }
          }
        }
        if (!scanAbortRef.current) {
          setContractFilter(normalized);
          setContractSearchInput(normalized);
          setContractData({
            address: normalized,
            deploymentBlock,
            deploymentTxHash,
            involvedBlockNumbers,
            transactions,
            addresses: Array.from(addressesSet),
          });
        }
      } catch (err) {
        if (!scanAbortRef.current) setContractSearchError(err?.message || 'Scan failed');
      } finally {
        setContractSearchLoading(false);
      }
    },
    [provider, contractSearchInput, contractFilter]
  );

  const copyToClipboard = (text) => navigator.clipboard.writeText(text);

  const blockRangeLabel =
    blocks.length > 0
      ? blockRange.mode === 'custom'
        ? `Blocks ${blockRange.from}–${blockRange.to}`
        : blockRange.mode === 'last'
          ? `Last ${blockRange.count}`
          : `Blocks 0–${blocks[blocks.length - 1]?.number ?? 0}`
      : '';

  if (!provider) {
    return (
      <div style={{ padding: '2rem', background: '#0a0a0f', color: '#64748b', borderRadius: '0.5rem', textAlign: 'center' }}>
        No provider. Connect to a chain first.
      </div>
    );
  }

  if (loading && blocks.length === 0) {
    return (
      <div style={{ padding: '2rem', background: '#0a0a0f', color: '#22ff88', borderRadius: '0.5rem', textAlign: 'center', fontFamily: 'monospace' }}>
        Loading blocks...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem', background: '#0a0a0f', color: '#f87171', borderRadius: '0.5rem', textAlign: 'center' }}>
        {error}
        <br />
        <button onClick={initialFetch} style={{ marginTop: '1rem', padding: '0.5rem 1rem', background: '#22ff88', color: '#0a0a0f', border: 'none', borderRadius: '0.25rem', cursor: 'pointer', fontWeight: 600 }}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: '1rem', height: '100%', minHeight: 400 }}>
      <div style={{ flex: 1, background: '#0a0a0f', borderRadius: '0.5rem', overflow: 'hidden' }}>
        <Canvas camera={{ position: [45, 45, 45], fov: 60 }} gl={{ antialias: true, alpha: false }} style={{ background: '#0a0a0f' }}>
          <ChainScene
            blocks={blocks}
            unclesMap={unclesMap}
            selectedBlock={selectedBlock}
            onSelectBlock={setSelectedBlock}
            layout={layout}
            blockRange={blockRange}
            demoL2={demoL2}
            lastKnownBlock={lastKnownBlock}
            hoveredBlock={hoveredBlock}
            nearBlock={nearBlock}
            onHover={(block, position) => setHoveredBlock(block ? { block, position } : null)}
            onHoverEnd={() => setHoveredBlock(null)}
            setNearBlock={setNearBlock}
            chainOffset={chainOffset}
            onChainOffsetChange={setChainOffset}
            isContractFiltered={!!(contractFilter && contractData)}
            involvedBlockNumbers={contractData?.involvedBlockNumbers}
            fitToView={fitToView}
            blockCount={blocks.filter((b) => (b.layer || 'L1') === 'L1').length}
          />
        </Canvas>
      </div>
      <div
        style={{
          width: 340,
          background: 'rgba(10, 10, 15, 0.95)',
          border: '1px solid rgba(34, 255, 136, 0.3)',
          borderRadius: '0.5rem',
          padding: '1rem',
          color: '#e2e8f0',
          fontFamily: 'monospace',
          fontSize: '0.85rem',
          overflowY: 'auto',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <span style={{ color: '#22ff88', fontWeight: 600 }}>Chain 3D Explorer</span>
          <span style={{ color: '#22c55e', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#22c55e', animation: 'pulse 1.5s infinite' }} />
            Live
          </span>
        </div>
        <div style={{ color: '#64748b', fontSize: '0.8rem', marginBottom: '0.5rem' }}>{rpcUrl || 'localhost:8545'}</div>
        <div style={{ color: '#94a3b8', fontSize: '0.8rem', marginBottom: '1rem' }}>{blockRangeLabel} · {blocks.length} blocks</div>

        <div style={{ marginBottom: '1rem' }}>
          <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '0.35rem' }}>View</div>
          <select
            value={blockRange.mode}
            onChange={(e) => {
              const m = e.target.value;
              setBlockRange((p) => ({ ...p, mode: m, count: m === 'last' ? 500 : p.count }));
            }}
            style={{ width: '100%', padding: '0.4rem', background: 'rgba(0,0,0,0.4)', border: '1px solid #475569', borderRadius: '0.25rem', color: '#e2e8f0', fontSize: '0.85rem' }}
          >
            <option value="all">All blocks</option>
            <option value="last">Last 500</option>
            <option value="custom">Custom range</option>
          </select>
          {blockRange.mode === 'last' && (
            <select
              value={blockRange.count}
              onChange={(e) => {
                setBlockRange((p) => ({ ...p, count: Number(e.target.value) }));
              }}
              style={{ width: '100%', marginTop: '0.35rem', padding: '0.4rem', background: 'rgba(0,0,0,0.4)', border: '1px solid #475569', borderRadius: '0.25rem', color: '#e2e8f0', fontSize: '0.85rem' }}
            >
              <option value={50}>Last 50</option>
              <option value={100}>Last 100</option>
              <option value={200}>Last 200</option>
              <option value={500}>Last 500</option>
              <option value={1000}>Last 1000</option>
            </select>
          )}
          {blockRange.mode === 'custom' && (
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.35rem' }}>
              <input
                type="number"
                placeholder="From"
                value={blockRange.from ?? ''}
                onChange={(e) => setBlockRange((p) => ({ ...p, from: parseInt(e.target.value, 10) || 0 }))}
                style={{ flex: 1, padding: '0.4rem', background: 'rgba(0,0,0,0.4)', border: '1px solid #475569', borderRadius: '0.25rem', color: '#e2e8f0' }}
              />
              <input
                type="number"
                placeholder="To"
                value={blockRange.to ?? ''}
                onChange={(e) => setBlockRange((p) => ({ ...p, to: parseInt(e.target.value, 10) || 0 }))}
                style={{ flex: 1, padding: '0.4rem', background: 'rgba(0,0,0,0.4)', border: '1px solid #475569', borderRadius: '0.25rem', color: '#e2e8f0' }}
              />
              <button onClick={refetchForRange} style={{ padding: '0.4rem 0.75rem', background: '#22ff88', color: '#0a0a0f', border: 'none', borderRadius: '0.25rem', cursor: 'pointer', fontWeight: 600 }}>
                Load
              </button>
            </div>
          )}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '0.35rem' }}>Contract address (0x...)</div>
          <div style={{ display: 'flex', gap: '0.35rem', marginBottom: '0.35rem' }}>
            <input
              type="text"
              placeholder="0x..."
              value={contractFilter ?? contractSearchInput}
              onChange={(e) => {
                setContractSearchError(null);
                if (contractFilter) setContractFilter(null);
                setContractSearchInput(e.target.value);
              }}
              onKeyDown={(e) => e.key === 'Enter' && scanContract(contractFilter ?? contractSearchInput)}
              style={{ flex: 1, padding: '0.4rem', background: 'rgba(0,0,0,0.4)', border: '1px solid #475569', borderRadius: '0.25rem', color: '#e2e8f0', fontFamily: 'monospace', fontSize: '0.85rem' }}
            />
            <button
              onClick={() => scanContract(contractFilter ?? contractSearchInput)}
              disabled={contractSearchLoading || !provider}
              style={{ padding: '0.4rem 0.75rem', background: contractSearchLoading ? '#334155' : '#22ff88', color: '#0a0a0f', border: 'none', borderRadius: '0.25rem', cursor: contractSearchLoading || !provider ? 'not-allowed' : 'pointer', fontWeight: 600, fontSize: '0.85rem' }}
            >
              {contractSearchLoading ? 'Scanning...' : 'Search'}
            </button>
            <button
              onClick={() => {
                scanAbortRef.current = true;
                setContractFilter(null);
                setContractSearchInput('');
                setContractData(null);
                setContractSearchError(null);
              }}
              style={{ padding: '0.4rem 0.75rem', background: 'transparent', border: '1px solid #475569', color: '#94a3b8', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.85rem' }}
            >
              Clear
            </button>
          </div>
          {contractSearchError && <div style={{ color: '#f87171', fontSize: '0.75rem', marginTop: '0.25rem' }}>{contractSearchError}</div>}
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <div style={{ color: '#64748b', fontSize: '0.75rem', marginBottom: '0.35rem' }}>Layout</div>
          <select
            value={layout}
            onChange={(e) => setLayout(e.target.value)}
            style={{ width: '100%', padding: '0.4rem', background: 'rgba(0,0,0,0.4)', border: '1px solid #475569', borderRadius: '0.25rem', color: '#e2e8f0', fontSize: '0.85rem' }}
          >
            <option value="helix">Helix</option>
            <option value="straight">Straight</option>
            <option value="zigzag">Zigzag</option>
          </select>
        </div>

        <div style={{ marginBottom: '1rem', display: 'flex', gap: '0.35rem' }}>
          <button
            onClick={() => setChainOffset([0, 0, 0])}
            style={{ flex: 1, padding: '0.4rem', background: 'rgba(0,0,0,0.4)', border: '1px solid #475569', borderRadius: '0.25rem', color: '#94a3b8', fontSize: '0.85rem', cursor: 'pointer' }}
          >
            Reset position
          </button>
          <button
            onClick={() => setFitToView((f) => f + 1)}
            style={{ flex: 1, padding: '0.4rem', background: 'rgba(34,255,136,0.15)', border: '1px solid rgba(34,255,136,0.4)', borderRadius: '0.25rem', color: '#22ff88', fontSize: '0.85rem', cursor: 'pointer' }}
          >
            Fit chain
          </button>
        </div>

        <div style={{ marginBottom: '1rem', fontSize: '0.8rem' }}>
          <span style={{ color: '#22ff88' }}>L1</span> base · <span style={{ color: '#00ffcc' }}>L2</span> rollup
        </div>
        <div style={{ marginBottom: '1rem', fontSize: '0.75rem', color: '#64748b' }}>
          <span style={{ color: '#22ff88' }}>●</span> Finalized · <span style={{ color: '#fbbf24' }}>●</span> Attesting
          <div style={{ marginTop: '0.25rem', fontSize: '0.7rem' }}>Newest blocks are still being attested and are not yet finalized.</div>
        </div>
        {!l2Provider && !l2Mode && (
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem', cursor: 'pointer', fontSize: '0.85rem' }}>
            <input type="checkbox" checked={demoL2} onChange={(e) => setDemoL2(e.target.checked)} /> Demo L2
          </label>
        )}

        {showL2Info && (
          <details style={{ marginBottom: '1rem', fontSize: '0.85rem' }}>
            <summary style={{ cursor: 'pointer', color: '#00ffcc', fontWeight: 600 }}>What is Layer 2?</summary>
            <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: 'rgba(0,255,204,0.08)', borderRadius: '0.5rem', border: '1px solid rgba(0,255,204,0.25)', color: '#94a3b8', lineHeight: 1.6 }}>
              <p style={{ margin: '0 0 0.5rem 0' }}>
                Layer 2 executes transactions off the main chain (L1), then posts data or proofs to L1. This inherits L1 security while scaling throughput.
              </p>
              <p style={{ margin: '0 0 0.5rem 0' }}>
                <strong style={{ color: '#e2e8f0' }}>Rollups</strong> batch many L2 transactions and post compressed data to L1. <strong style={{ color: '#e2e8f0' }}>Optimistic</strong> rollups use fraud proofs; <strong style={{ color: '#e2e8f0' }}>ZK</strong> rollups use validity proofs.
              </p>
              <p style={{ margin: 0 }}>
                You&apos;re viewing L1 (green) and L2 (cyan) blocks side by side — two chains, one security base.
              </p>
            </div>
          </details>
        )}

        {contractData && (
          <div
            style={{
              marginBottom: '1rem',
              padding: '0.75rem',
              background: 'rgba(0,255,204,0.08)',
              border: '1px solid rgba(0,255,204,0.3)',
              borderRadius: '0.5rem',
              fontSize: '0.8rem',
            }}
          >
            <div style={{ color: '#00ffcc', fontWeight: 600, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {contractData.address.slice(0, 10)}...{contractData.address.slice(-8)}
              <button onClick={() => copyToClipboard(contractData.address)} style={{ padding: '0.2rem 0.4rem', background: 'transparent', border: '1px solid #475569', color: '#94a3b8', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.7rem' }}>
                Copy
              </button>
            </div>
            {contractData.transactions.length === 0 ? (
              <div style={{ color: '#64748b', fontSize: '0.8rem' }}>No transactions found involving this contract in the scanned range.</div>
            ) : (
              <>
            {contractData.deploymentBlock != null && (
              <div style={{ marginBottom: '0.5rem', color: '#64748b', fontSize: '0.75rem' }}>
                Deployment: Block #{contractData.deploymentBlock}
                {contractData.deploymentTxHash && (
                  <>
                    {' · '}
                    <span style={{ color: '#93c5fd', wordBreak: 'break-all' }}>{String(contractData.deploymentTxHash).slice(0, 18)}...</span>
                    <button onClick={() => copyToClipboard(contractData.deploymentTxHash)} style={{ marginLeft: '0.25rem', padding: '0.1rem 0.3rem', background: 'transparent', border: '1px solid #475569', color: '#94a3b8', borderRadius: '0.2rem', cursor: 'pointer', fontSize: '0.65rem' }}>
                      Copy
                    </button>
                  </>
                )}
              </div>
            )}
            <div style={{ marginBottom: '0.5rem', color: '#64748b', fontSize: '0.75rem' }}>
              {contractData.involvedBlockNumbers.size} blocks · {contractData.transactions.length} transactions · {contractData.addresses.length} addresses
            </div>
            <div style={{ maxHeight: 120, overflowY: 'auto', marginBottom: '0.5rem' }}>
              <table style={{ width: '100%', fontSize: '0.7rem', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ color: '#64748b', textAlign: 'left' }}>
                    <th style={{ padding: '0.2rem 0.35rem 0.2rem 0' }}>Block</th>
                    <th style={{ padding: '0.2rem 0.35rem 0.2rem 0' }}>Tx</th>
                    <th style={{ padding: '0.2rem 0.35rem 0.2rem 0' }}>Type</th>
                    <th style={{ padding: '0.2rem 0.35rem 0.2rem 0' }}>Value</th>
                  </tr>
                </thead>
                <tbody>
                  {contractData.transactions.map((tx, i) => (
                    <tr key={i} style={{ borderTop: '1px solid rgba(71,85,105,0.5)' }}>
                      <td style={{ padding: '0.2rem 0.35rem 0.2rem 0', color: '#e2e8f0' }}>#{tx.blockNumber}</td>
                      <td style={{ padding: '0.2rem 0.35rem 0.2rem 0', color: '#93c5fd', maxWidth: 80, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {String(tx.txHash).slice(0, 10)}...
                        <button onClick={() => copyToClipboard(tx.txHash)} style={{ marginLeft: '0.15rem', padding: '0.05rem 0.2rem', background: 'transparent', border: '1px solid #475569', color: '#94a3b8', borderRadius: '0.15rem', cursor: 'pointer', fontSize: '0.6rem' }}>
                          Copy
                        </button>
                      </td>
                      <td style={{ padding: '0.2rem 0.35rem 0.2rem 0', color: tx.isDeployment ? '#fbbf24' : '#94a3b8' }}>{tx.type}</td>
                      <td style={{ padding: '0.2rem 0.35rem 0.2rem 0', color: '#22ff88' }}>
                        {(() => {
                          try {
                            const v = typeof tx.value === 'bigint' ? tx.value : BigInt(tx.value);
                            return v > 0n ? `${ethers.formatEther(v)} ETH` : '—';
                          } catch { return '—'; }
                        })()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ color: '#64748b', fontSize: '0.7rem', marginBottom: '0.25rem' }}>Addresses involved:</div>
            <div style={{ maxHeight: 60, overflowY: 'auto', fontSize: '0.7rem' }}>
              {contractData.addresses.map((addr, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', marginBottom: '0.15rem' }}>
                  <span style={{ color: '#93c5fd', wordBreak: 'break-all' }}>{addr.slice(0, 10)}...{addr.slice(-8)}</span>
                  <button onClick={() => copyToClipboard(addr)} style={{ padding: '0.05rem 0.2rem', background: 'transparent', border: '1px solid #475569', color: '#94a3b8', borderRadius: '0.15rem', cursor: 'pointer', fontSize: '0.65rem' }}>
                    Copy
                  </button>
                </div>
              ))}
            </div>
              </>
            )}
          </div>
        )}

        {selectedBlock ? (
          <>
            <div style={{ color: '#00ffcc', marginBottom: '0.5rem' }}>
              Block #{selectedBlock.number} {selectedBlock.layer === 'L2' && '(L2)'}
            </div>
            {selectedBlock.layer !== 'L2' && lastKnownBlock != null && (
              <div style={{ marginBottom: '0.5rem', fontSize: '0.8rem' }}>
                <span style={{ color: '#64748b' }}>Status: </span>
                <span style={{ color: (lastKnownBlock - selectedBlock.number) < ATTESTING_BLOCKS ? '#fbbf24' : '#22ff88' }}>
                  {(lastKnownBlock - selectedBlock.number) < ATTESTING_BLOCKS ? 'Attesting — not yet irreversible' : 'Finalized'}
                </span>
              </div>
            )}
            <div style={{ marginBottom: '0.5rem' }}>
              <span style={{ color: '#64748b' }}>Hash:</span>
              <div style={{ color: '#93c5fd', wordBreak: 'break-all', marginTop: '0.25rem' }}>{String(selectedBlock.hash)}</div>
              <button onClick={() => copyToClipboard(selectedBlock.hash)} style={{ marginTop: '0.25rem', padding: '0.2rem 0.5rem', background: 'transparent', border: '1px solid #475569', color: '#94a3b8', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}>
                Copy
              </button>
            </div>
            <div style={{ marginBottom: '0.5rem' }}>
              <span style={{ color: '#64748b' }}>Parent:</span>
              <div style={{ color: '#f9a8d4', wordBreak: 'break-all', marginTop: '0.25rem' }}>{String(selectedBlock.parentHash)}</div>
              <button onClick={() => copyToClipboard(selectedBlock.parentHash)} style={{ marginTop: '0.25rem', padding: '0.2rem 0.5rem', background: 'transparent', border: '1px solid #475569', color: '#94a3b8', borderRadius: '0.25rem', cursor: 'pointer', fontSize: '0.75rem' }}>
                Copy
              </button>
            </div>
            <div style={{ marginBottom: '0.5rem' }}>
              <span style={{ color: '#64748b' }}>Transactions:</span> <span style={{ color: '#22ff88' }}>{selectedBlock.txCount}</span>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>Timestamp:</span>{' '}
              <span style={{ color: '#e2e8f0' }}>
                {selectedBlock.timestamp ? new Date(Number(selectedBlock.timestamp) * 1000).toLocaleString() : '—'}
              </span>
            </div>
          </>
        ) : (
          <div style={{ color: '#64748b', fontSize: '0.9rem' }}>Click a block to view details. Point at a block and scroll to zoom in on it. Drag chain to reposition. Right-click to orbit.</div>
        )}
      </div>
    </div>
  );
}

export default Blockchain3DView;
