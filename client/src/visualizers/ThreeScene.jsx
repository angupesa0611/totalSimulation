import React, { useRef, useMemo, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line } from '@react-three/drei';
import * as THREE from 'three';

const COLORS = ['#f59e0b', '#6366f1', '#22c55e', '#ef4444', '#06b6d4', '#ec4899', '#8b5cf6', '#14b8a6'];

function OrbitTrails({ positions, names, frameIndex }) {
  return (
    <>
      {names.map((name, pIdx) => {
        // Trail: all frames up to current
        const trail = [];
        for (let f = 0; f <= frameIndex; f++) {
          const pos = positions[f][pIdx];
          trail.push(new THREE.Vector3(pos[0], pos[2], pos[1])); // swap y/z for better view
        }

        const color = COLORS[pIdx % COLORS.length];
        const current = positions[frameIndex][pIdx];
        const size = pIdx === 0 ? 0.08 : 0.03; // Sun larger

        return (
          <group key={pIdx}>
            {/* Trail line */}
            {trail.length > 1 && (
              <Line points={trail} color={color} lineWidth={1} opacity={0.5} transparent />
            )}
            {/* Current position sphere */}
            <mesh position={[current[0], current[2], current[1]]}>
              <sphereGeometry args={[size, 16, 16]} />
              <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} />
            </mesh>
          </group>
        );
      })}
    </>
  );
}

function AnimationController({ totalFrames, frameIndex, setFrameIndex, playing }) {
  useFrame(() => {
    if (playing) {
      setFrameIndex((prev) => (prev + 1) % totalFrames);
    }
  });
  return null;
}

export default function ThreeScene({ data }) {
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(true);

  if (!data || !data.positions) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No orbital data to display</div>;
  }

  const totalFrames = data.positions.length;

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas camera={{ position: [3, 3, 3], fov: 50 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[0, 0, 0]} intensity={2} color="#f59e0b" />
        <OrbitControls enableDamping />
        <gridHelper args={[6, 20, '#1a1a28', '#1a1a28']} />
        <AnimationController
          totalFrames={totalFrames}
          frameIndex={frameIndex}
          setFrameIndex={setFrameIndex}
          playing={playing}
        />
        <OrbitTrails
          positions={data.positions}
          names={data.names || []}
          frameIndex={frameIndex}
        />
      </Canvas>

      {/* Controls overlay */}
      <div style={{
        position: 'absolute', bottom: 16, left: 16, right: 16,
        display: 'flex', alignItems: 'center', gap: 12,
        background: 'rgba(10,10,15,0.8)', padding: '8px 16px', borderRadius: 8,
      }}>
        <button
          onClick={() => setPlaying(!playing)}
          style={{
            background: 'none', border: 'none', color: '#e0e0e0',
            fontSize: 18, cursor: 'pointer', padding: '4px 8px',
          }}
        >
          {playing ? '||' : '>'}
        </button>
        <input
          type="range"
          min={0}
          max={totalFrames - 1}
          value={frameIndex}
          onChange={(e) => { setPlaying(false); setFrameIndex(parseInt(e.target.value)); }}
          style={{ flex: 1, accentColor: '#6366f1' }}
        />
        <span style={{ fontSize: 12, color: '#8888a0', fontFamily: 'monospace', minWidth: 80 }}>
          {frameIndex + 1}/{totalFrames}
        </span>
      </div>
    </div>
  );
}
