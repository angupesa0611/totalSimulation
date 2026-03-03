import React, { useMemo, useState, useCallback, useRef, useEffect } from 'react';
import Plot from 'react-plotly.js';
import PlaybackControls from './shared/PlaybackControls';
import { frameToPDB } from './molstar/trajectory';
import theme from '../theme.json';

/**
 * Full molecular dynamics viewer with 3D structure, trajectory playback,
 * energy plots, and simulation info.
 *
 * Used by: openmm, gromacs, namd, qmmm
 */
export default function MolStarViewer({ data }) {
  const [activeTab, setActiveTab] = useState('3d');
  const [currentFrame, setCurrentFrame] = useState(0);
  const canvasRef = useRef(null);
  const viewerRef = useRef(null);
  const [viewerReady, setViewerReady] = useState(false);

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No molecular dynamics data to display</div>;
  }

  const hasFrames = data.frames && data.frames.length > 0;
  const totalFrames = data.frames?.length || 0;

  // Initialize simple 3D viewer using Three.js (available from @react-three/fiber)
  // Mol* full integration deferred to avoid SCSS build issues — using canvas-based atom rendering
  useEffect(() => {
    if (activeTab !== '3d' || !hasFrames || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const renderFrame = (frameIdx) => {
      const frame = data.frames[frameIdx];
      if (!frame) return;

      const width = canvas.width;
      const height = canvas.height;
      ctx.fillStyle = '#0a0a0f';
      ctx.fillRect(0, 0, width, height);

      // Find bounds for auto-scaling
      let minX = Infinity, maxX = -Infinity;
      let minY = Infinity, maxY = -Infinity;
      for (const pos of frame) {
        minX = Math.min(minX, pos[0]);
        maxX = Math.max(maxX, pos[0]);
        minY = Math.min(minY, pos[1]);
        maxY = Math.max(maxY, pos[1]);
      }

      const rangeX = maxX - minX || 1;
      const rangeY = maxY - minY || 1;
      const scale = Math.min(width * 0.8, height * 0.8) / Math.max(rangeX, rangeY);
      const cx = width / 2;
      const cy = height / 2;
      const midX = (minX + maxX) / 2;
      const midY = (minY + maxY) / 2;

      // Element colors
      const elementColors = {
        'C': '#909090', 'N': '#3050F8', 'O': '#FF0D0D', 'H': '#FFFFFF',
        'S': '#FFFF30', 'P': '#FF8000', 'F': '#90E050', 'Cl': '#1FF01F',
        'CA': '#909090', 'CB': '#909090',
      };

      // Draw bonds (lines between close atoms)
      ctx.strokeStyle = '#333344';
      ctx.lineWidth = 1;
      for (let i = 0; i < frame.length; i++) {
        for (let j = i + 1; j < Math.min(frame.length, i + 8); j++) {
          const dx = frame[i][0] - frame[j][0];
          const dy = frame[i][1] - frame[j][1];
          const dz = frame[i][2] - frame[j][2];
          const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
          if (dist < 2.0) {  // Bond distance threshold in Angstroms
            const x1 = cx + (frame[i][0] - midX) * scale;
            const y1 = cy + (frame[i][1] - midY) * scale;
            const x2 = cx + (frame[j][0] - midX) * scale;
            const y2 = cy + (frame[j][1] - midY) * scale;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
          }
        }
      }

      // Draw atoms
      for (let i = 0; i < frame.length; i++) {
        const x = cx + (frame[i][0] - midX) * scale;
        const y = cy + (frame[i][1] - midY) * scale;
        const z = frame[i][2];

        // Get atom name for coloring
        const atomName = data.atom_names?.[i] || '';
        const element = atomName.replace(/[0-9]/g, '').trim();
        const color = elementColors[element] || elementColors[atomName] || '#6366f1';

        // Size varies with z-depth for pseudo-3D effect
        const depthScale = 1 + (z - (frame[0]?.[2] || 0)) * 0.02;
        const radius = Math.max(2, Math.min(6, 4 * depthScale));

        ctx.beginPath();
        ctx.arc(x, y, radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#00000044';
        ctx.lineWidth = 0.5;
        ctx.stroke();
      }

      // Frame info
      ctx.fillStyle = theme.colors.textSecondary;
      ctx.font = '11px monospace';
      ctx.fillText(`Frame ${frameIdx + 1}/${totalFrames}  |  ${data.n_atoms} atoms`, 10, height - 10);
    };

    // Set canvas size
    const parent = canvas.parentElement;
    canvas.width = parent.clientWidth;
    canvas.height = parent.clientHeight;

    renderFrame(currentFrame);
    viewerRef.current = { renderFrame };
    setViewerReady(true);

    return () => {
      viewerRef.current = null;
    };
  }, [activeTab, hasFrames, currentFrame, data]);

  // Update frame rendering when frame changes
  useEffect(() => {
    if (viewerRef.current && activeTab === '3d') {
      viewerRef.current.renderFrame(currentFrame);
    }
  }, [currentFrame, activeTab]);

  const handleFrameChange = useCallback((frameOrFn) => {
    if (typeof frameOrFn === 'function') {
      setCurrentFrame(prev => frameOrFn(prev));
    } else {
      setCurrentFrame(frameOrFn);
    }
  }, []);

  const energyTraces = useMemo(() => {
    if (!data.energies) return [];
    const steps = data.energies.map(e => e.step);
    return [
      { x: steps, y: data.energies.map(e => e.potential), name: 'Potential', line: { color: '#6366f1', width: 2 } },
      { x: steps, y: data.energies.map(e => e.kinetic), name: 'Kinetic', line: { color: '#22c55e', width: 2 } },
      { x: steps, y: data.energies.map(e => e.total), name: 'Total', line: { color: '#f59e0b', width: 2 } },
    ];
  }, [data]);

  const tabs = hasFrames ? ['3d', 'energy', 'info'] : ['energy', 'info'];

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Tab bar */}
      <div style={{ display: 'flex', gap: 4, padding: '8px 16px', borderBottom: `1px solid ${theme.colors.border}` }}>
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '6px 16px',
              background: activeTab === tab ? theme.colors.bgTertiary : 'transparent',
              border: activeTab === tab ? `1px solid ${theme.colors.accent}` : '1px solid transparent',
              borderRadius: 6,
              color: activeTab === tab ? theme.colors.text : theme.colors.textSecondary,
              fontSize: 13,
              cursor: 'pointer',
              textTransform: tab === '3d' ? 'uppercase' : 'capitalize',
            }}
          >
            {tab === '3d' ? '3D View' : tab}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {activeTab === '3d' && hasFrames && (
          <>
            <div style={{ flex: 1, position: 'relative' }}>
              <canvas
                ref={canvasRef}
                style={{ width: '100%', height: '100%', display: 'block' }}
              />
            </div>
            {totalFrames > 1 && (
              <PlaybackControls
                totalFrames={totalFrames}
                currentFrame={currentFrame}
                onFrameChange={handleFrameChange}
                fps={20}
              />
            )}
          </>
        )}

        {activeTab === 'energy' && energyTraces.length > 0 && (
          <div style={{ flex: 1 }}>
            <Plot
              data={energyTraces}
              layout={{
                title: { text: 'Energy vs Time', font: { color: theme.colors.text, size: 16 } },
                xaxis: { title: 'Step', color: theme.colors.textSecondary, gridcolor: theme.colors.border },
                yaxis: { title: 'Energy (kJ/mol)', color: theme.colors.textSecondary, gridcolor: theme.colors.border },
                paper_bgcolor: 'transparent',
                plot_bgcolor: 'transparent',
                font: { color: theme.colors.text },
                legend: { font: { color: theme.colors.text } },
                margin: { t: 50, r: 30, b: 50, l: 70 },
                autosize: true,
              }}
              config={{ responsive: true, displaylogo: false }}
              style={{ width: '100%', height: '100%' }}
              useResizeHandler
            />
          </div>
        )}

        {activeTab === 'info' && (
          <div style={{ padding: 24, overflow: 'auto' }}>
            <h3 style={{ fontSize: 16, marginBottom: 16, color: theme.colors.text }}>Simulation Info</h3>
            <InfoRow label="Tool" value={data.tool?.toUpperCase()} />
            <InfoRow label="Platform" value={data.platform} />
            <InfoRow label="Atoms" value={data.n_atoms} />
            <InfoRow label="Frames" value={data.n_frames} />
            <InfoRow label="Integrator" value={data.params?.integrator} />
            <InfoRow label="Temperature" value={data.params?.temperature ? `${data.params.temperature} K` : undefined} />
            <InfoRow label="Steps" value={data.params?.steps} />
            <InfoRow label="Timestep" value={data.params?.dt ? `${data.params.dt} ps` : undefined} />
            {data.n_qm_atoms != null && (
              <>
                <InfoRow label="QM Atoms" value={data.n_qm_atoms} />
                <InfoRow label="Total Atoms" value={data.n_total_atoms} />
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function InfoRow({ label, value }) {
  if (value == null) return null;
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: `1px solid ${theme.colors.border}` }}>
      <span style={{ color: theme.colors.textSecondary, fontSize: 13 }}>{label}</span>
      <span style={{ color: theme.colors.text, fontSize: 13, fontFamily: 'monospace' }}>{value ?? '—'}</span>
    </div>
  );
}
