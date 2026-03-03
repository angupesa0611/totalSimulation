import React, { useState, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Line } from '@react-three/drei';
import * as THREE from 'three';

const COLORS = ['#a855f7', '#6366f1', '#22c55e', '#ef4444', '#06b6d4', '#ec4899', '#f59e0b', '#14b8a6'];

function RigidBody({ position, orientation, shape, color, size }) {
  const pos = position || [0, 0, 0];
  const quat = orientation
    ? new THREE.Quaternion(orientation[0], orientation[1], orientation[2], orientation[3])
    : new THREE.Quaternion();

  return (
    <mesh position={[pos[0], pos[2], pos[1]]} quaternion={quat}>
      {shape === 'box' ? (
        <boxGeometry args={[size, size, size]} />
      ) : shape === 'cylinder' ? (
        <cylinderGeometry args={[size * 0.5, size * 0.5, size, 16]} />
      ) : (
        <sphereGeometry args={[size * 0.5, 16, 16]} />
      )}
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.3} />
    </mesh>
  );
}

function TrailLines({ frames, objectNames, frameIndex }) {
  return (
    <>
      {objectNames.map((name, objIdx) => {
        const trail = [];
        for (let f = Math.max(0, frameIndex - 200); f <= frameIndex; f++) {
          if (frames[f] && frames[f][objIdx]) {
            const p = frames[f][objIdx].position;
            trail.push(new THREE.Vector3(p[0], p[2], p[1]));
          }
        }
        const color = COLORS[objIdx % COLORS.length];
        return trail.length > 1 ? (
          <Line key={objIdx} points={trail} color={color} lineWidth={1} opacity={0.4} transparent />
        ) : null;
      })}
    </>
  );
}

function AnimController({ totalFrames, setFrameIndex, playing }) {
  useFrame(() => {
    if (playing) {
      setFrameIndex(prev => (prev + 1) % totalFrames);
    }
  });
  return null;
}

function EnergyOverlay({ energies, frameIndex }) {
  if (!energies || energies.length === 0) return null;

  const current = energies[Math.min(frameIndex, energies.length - 1)];

  return (
    <div style={{
      position: 'absolute', top: 16, right: 16,
      background: 'rgba(10,10,15,0.85)', padding: 12, borderRadius: 8,
      fontSize: 11, fontFamily: "'JetBrains Mono', monospace", color: '#e0e0e0',
      minWidth: 160,
    }}>
      <div style={{ fontWeight: 700, marginBottom: 6, color: '#a855f7' }}>Energy</div>
      <div>KE: <span style={{ color: '#22c55e' }}>{current.kinetic?.toFixed(3)}</span></div>
      <div>PE: <span style={{ color: '#f59e0b' }}>{current.potential?.toFixed(3)}</span></div>
      <div>Total: <span style={{ color: '#6366f1' }}>{current.total?.toFixed(3)}</span></div>
      <div style={{ marginTop: 4, fontSize: 10, color: '#8888a0' }}>
        t = {current.time?.toFixed(3)}s
      </div>
    </div>
  );
}

export default function RigidBodyScene({ data }) {
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(true);

  if (!data || !data.frames || data.frames.length === 0) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No rigid body data to display</div>;
  }

  const totalFrames = data.frames.length;
  const currentFrame = data.frames[frameIndex] || [];
  const objectNames = data.object_names || [];

  // Determine shapes from simulation type
  const shapes = objectNames.map(() => 'sphere');

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Canvas camera={{ position: [5, 5, 5], fov: 50 }}>
        <ambientLight intensity={0.4} />
        <pointLight position={[5, 10, 5]} intensity={1} />
        <directionalLight position={[-5, 5, -5]} intensity={0.5} />
        <OrbitControls enableDamping />
        <gridHelper args={[10, 20, '#1a1a28', '#1a1a28']} />

        {/* Ground plane */}
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
          <planeGeometry args={[10, 10]} />
          <meshStandardMaterial color="#12121a" transparent opacity={0.5} />
        </mesh>

        <AnimController
          totalFrames={totalFrames}
          setFrameIndex={setFrameIndex}
          playing={playing}
        />
        <TrailLines
          frames={data.frames}
          objectNames={objectNames}
          frameIndex={frameIndex}
        />

        {currentFrame.map((obj, idx) => (
          <RigidBody
            key={idx}
            position={obj.position}
            orientation={obj.orientation}
            shape={shapes[idx]}
            color={COLORS[idx % COLORS.length]}
            size={0.6}
          />
        ))}
      </Canvas>

      <EnergyOverlay energies={data.energies} frameIndex={frameIndex} />

      {/* Playback controls */}
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
          type="range" min={0} max={totalFrames - 1} value={frameIndex}
          onChange={(e) => { setPlaying(false); setFrameIndex(parseInt(e.target.value)); }}
          style={{ flex: 1, accentColor: '#a855f7' }}
        />
        <span style={{ fontSize: 12, color: '#8888a0', fontFamily: 'monospace', minWidth: 80 }}>
          {frameIndex + 1}/{totalFrames}
        </span>
      </div>
    </div>
  );
}
