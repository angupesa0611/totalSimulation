import React, { useState, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Line } from '@react-three/drei';
import * as THREE from 'three';
import Plot from 'react-plotly.js';

function BlackHole({ radius }) {
  return (
    <mesh>
      <sphereGeometry args={[radius * 0.1, 32, 32]} />
      <meshStandardMaterial color="#000000" emissive="#facc15" emissiveIntensity={0.2} />
    </mesh>
  );
}

function EventHorizon({ radius }) {
  return (
    <mesh>
      <sphereGeometry args={[radius * 0.15, 32, 32]} />
      <meshStandardMaterial color="#facc15" transparent opacity={0.08} wireframe />
    </mesh>
  );
}

function GeodesicTrajectory({ trajectory }) {
  const points = useMemo(() => {
    return trajectory.map(t => {
      const r = t.r;
      const theta = t.theta;
      const phi = t.phi;
      return new THREE.Vector3(
        r * Math.sin(theta) * Math.cos(phi) * 0.1,
        r * Math.cos(theta) * 0.1,
        r * Math.sin(theta) * Math.sin(phi) * 0.1,
      );
    });
  }, [trajectory]);

  if (points.length < 2) return null;

  return (
    <>
      <Line points={points} color="#facc15" lineWidth={2} />
      {/* Current position marker */}
      <mesh position={points[points.length - 1]}>
        <sphereGeometry args={[0.05, 8, 8]} />
        <meshStandardMaterial color="#facc15" emissive="#facc15" emissiveIntensity={0.8} />
      </mesh>
    </>
  );
}

function GeodesicScene3D({ data }) {
  const trajectory = data.trajectory || [];
  const rs = data.schwarzschild_radius || 2.0;

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Canvas camera={{ position: [4, 3, 4], fov: 50 }}>
        <ambientLight intensity={0.3} />
        <pointLight position={[0, 0, 0]} intensity={1.5} color="#facc15" />
        <OrbitControls enableDamping />
        <gridHelper args={[10, 20, '#1a1a28', '#1a1a28']} />

        <BlackHole radius={rs} />
        <EventHorizon radius={rs} />
        {data.event_horizon && (
          <mesh>
            <sphereGeometry args={[data.event_horizon * 0.1, 32, 32]} />
            <meshStandardMaterial color="#ef4444" transparent opacity={0.05} wireframe />
          </mesh>
        )}

        <GeodesicTrajectory trajectory={trajectory} />
      </Canvas>

      {/* Info overlay */}
      <div style={{
        position: 'absolute', top: 16, right: 16,
        background: 'rgba(10,10,15,0.85)', padding: 12, borderRadius: 8,
        fontSize: 11, fontFamily: "'JetBrains Mono', monospace", color: '#e0e0e0',
        minWidth: 180,
      }}>
        <div style={{ fontWeight: 700, marginBottom: 6, color: '#facc15' }}>
          {data.metric_type === 'kerr' ? 'Kerr' : 'Schwarzschild'} Geodesic
        </div>
        <div>M = {data.M?.toExponential(2)}</div>
        <div>r_s = {rs?.toFixed(2)}</div>
        {data.a !== undefined && data.a !== 0 && <div>a = {data.a?.toFixed(3)}</div>}
        {data.event_horizon && <div>r+ = {data.event_horizon?.toFixed(2)}</div>}
        {data.perihelion_advance !== undefined && data.perihelion_advance !== null && (
          <div style={{ color: '#22c55e', marginTop: 4 }}>
            Precession: {(data.perihelion_advance * 180 / Math.PI * 3600).toFixed(2)} arcsec/orbit
          </div>
        )}
        <div style={{ marginTop: 4, fontSize: 10, color: '#8888a0' }}>
          {trajectory.length} trajectory points
        </div>
      </div>
    </div>
  );
}

function GWStrainPlot({ data }) {
  const plotLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 40, b: 50, l: 60 },
    xaxis: { title: 'Time (s)', gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    yaxis: { title: 'Strain (h)', gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    title: { text: 'Gravitational Wave Strain', font: { size: 14 } },
    legend: { font: { color: '#8888a0' } },
  };

  const plotData = [
    {
      x: data.time,
      y: data.h_plus,
      type: 'scatter',
      mode: 'lines',
      name: 'h+',
      line: { color: '#facc15', width: 1.5 },
    },
    {
      x: data.time,
      y: data.h_cross,
      type: 'scatter',
      mode: 'lines',
      name: 'hx',
      line: { color: '#a855f7', width: 1.5 },
    },
  ];

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1 }}>
        <Plot
          data={plotData}
          layout={plotLayout}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
          config={{ responsive: true }}
        />
      </div>
      <div style={{
        padding: '8px 16px', background: '#12121a', borderTop: '1px solid #2a2a3a',
        fontSize: 11, fontFamily: "'JetBrains Mono', monospace", color: '#8888a0',
        display: 'flex', gap: 16,
      }}>
        <span>M_total = {data.total_mass_solar} M_sun</span>
        <span>q = {data.mass_ratio}</span>
        <span>M_chirp = {data.chirp_mass?.toFixed(2)} M_sun</span>
      </div>
    </div>
  );
}

function TOVPlot({ data }) {
  const plotLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 40, b: 50, l: 70 },
    xaxis: { title: 'Radius (km)', gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    yaxis: { title: 'Value', gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a', type: 'log' },
    title: { text: 'TOV Neutron Star Structure', font: { size: 14 } },
    legend: { font: { color: '#8888a0' } },
  };

  const plotData = [
    {
      x: data.radius,
      y: data.pressure,
      type: 'scatter',
      mode: 'lines',
      name: 'Pressure (Pa)',
      line: { color: '#ef4444', width: 1.5 },
    },
    {
      x: data.radius,
      y: data.density,
      type: 'scatter',
      mode: 'lines',
      name: 'Density (kg/m³)',
      line: { color: '#22c55e', width: 1.5 },
    },
  ];

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1 }}>
        <Plot
          data={plotData}
          layout={plotLayout}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
          config={{ responsive: true }}
        />
      </div>
      <div style={{
        padding: '8px 16px', background: '#12121a', borderTop: '1px solid #2a2a3a',
        fontSize: 11, fontFamily: "'JetBrains Mono', monospace", color: '#8888a0',
        display: 'flex', gap: 16,
      }}>
        <span>R = {data.star_radius_km?.toFixed(2)} km</span>
        <span>M = {data.star_mass_solar?.toFixed(3)} M_sun</span>
        <span>rho_c = {data.central_density?.toExponential(2)} kg/m³</span>
      </div>
    </div>
  );
}

function BrillLindquistPlot({ data }) {
  const plotLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 80, b: 50, l: 60 },
    xaxis: { title: 'x (M)', gridcolor: '#2a2a3a' },
    yaxis: { title: 'y (M)', gridcolor: '#2a2a3a', scaleanchor: 'x' },
    title: { text: 'Brill-Lindquist Conformal Factor', font: { size: 14 } },
  };

  const plotData = [{
    z: data.conformal_factor,
    x: data.grid_x,
    y: data.grid_y,
    type: 'heatmap',
    colorscale: 'Inferno',
    zmin: 1,
    zmax: Math.min(10, Math.max(...data.conformal_factor.flat())),
    colorbar: {
      title: { text: 'psi', font: { color: '#e0e0e0' } },
      tickfont: { color: '#8888a0' },
    },
  }];

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ flex: 1 }}>
        <Plot
          data={plotData}
          layout={plotLayout}
          style={{ width: '100%', height: '100%' }}
          useResizeHandler
          config={{ responsive: true }}
        />
      </div>
      <div style={{
        padding: '8px 16px', background: '#12121a', borderTop: '1px solid #2a2a3a',
        fontSize: 11, fontFamily: "'JetBrains Mono', monospace", color: '#8888a0',
        display: 'flex', gap: 16,
      }}>
        <span>ADM mass = {data.ADM_mass?.toFixed(4)}</span>
        <span>m1 = {data.mass1?.toFixed(4)}</span>
        <span>m2 = {data.mass2?.toFixed(4)}</span>
        <span>d = {data.separation}</span>
      </div>
    </div>
  );
}

export default function GeodesicPlot({ data }) {
  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  // Route to the appropriate sub-visualizer based on data type
  if (data.simulation_type === 'gw_strain' && data.h_plus) {
    return <GWStrainPlot data={data} />;
  }

  if (data.simulation_type === 'tov_star' && data.pressure) {
    return <TOVPlot data={data} />;
  }

  if (data.simulation_type === 'brill_lindquist' && data.conformal_factor) {
    return <BrillLindquistPlot data={data} />;
  }

  if (data.trajectory) {
    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        <GeodesicScene3D data={data} />
      </div>
    );
  }

  return <div style={{ color: '#8888a0', padding: 24 }}>Unknown data format</div>;
}
