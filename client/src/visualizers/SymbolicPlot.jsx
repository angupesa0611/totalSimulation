import React, { useMemo, useState } from 'react';
import Plot from 'react-plotly.js';

const ACCENT = '#a78bfa';

export default function SymbolicPlot({ data }) {
  const [tab, setTab] = useState('result');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const simType = data.simulation_type || 'symbolic_solve';

  const tabs = useMemo(() => {
    const t = ['result'];
    if (data.numeric_samples?.x?.length > 0) t.push('plot');
    if (simType === 'matrix_algebra') t.push('matrix');
    if (simType === 'code_generation') t.push('code');
    t.push('info');
    return t;
  }, [data, simType]);

  const darkLayout = {
    paper_bgcolor: '#0a0a0f',
    plot_bgcolor: '#12121a',
    font: { color: '#e0e0e0', family: "'Inter', sans-serif" },
    margin: { t: 40, r: 30, b: 50, l: 60 },
    xaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    yaxis: { gridcolor: '#2a2a3a', zerolinecolor: '#2a2a3a' },
    legend: { bgcolor: 'transparent', font: { color: '#8888a0' } },
  };

  const activeTab = tabs.includes(tab) ? tab : tabs[0];

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{
        display: 'flex', gap: 2, padding: '8px 16px',
        background: '#12121a', borderBottom: '1px solid #2a2a3a',
      }}>
        {tabs.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: '4px 12px', background: activeTab === t ? ACCENT : 'transparent',
              border: 'none', borderRadius: 4,
              color: activeTab === t ? '#fff' : '#8888a0',
              fontSize: 11, cursor: 'pointer', textTransform: 'capitalize',
            }}
          >{t}</button>
        ))}
      </div>

      {activeTab === 'result' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 16 }}>
            {simType === 'symbolic_solve' && 'Symbolic Solution'}
            {simType === 'calculus' && `Calculus — ${data.operation}`}
            {simType === 'matrix_algebra' && `Matrix — ${data.operation}`}
            {simType === 'ode_solve' && 'ODE Solution'}
            {simType === 'code_generation' && 'Code Generation'}
          </h4>

          {simType === 'symbolic_solve' && (
            <>
              <div style={{ marginBottom: 12, color: '#8888a0' }}>Equations: {JSON.stringify(data.equations)}</div>
              <div style={{ fontSize: 16, color: '#fff', marginBottom: 12 }}>
                Solutions: {JSON.stringify(data.solutions, null, 2)}
              </div>
              {data.latex && (
                <div style={{ color: ACCENT, fontSize: 12, marginTop: 8 }}>
                  LaTeX: {JSON.stringify(data.latex)}
                </div>
              )}
            </>
          )}

          {simType === 'calculus' && (
            <>
              <div style={{ marginBottom: 8, color: '#8888a0' }}>Expression: {data.expression}</div>
              <div style={{ marginBottom: 8, color: '#8888a0' }}>Operation: {data.operation}</div>
              <div style={{ fontSize: 16, color: '#fff', marginBottom: 12 }}>
                Result: {data.result}
              </div>
              {data.result_latex && (
                <div style={{ color: ACCENT, fontSize: 12 }}>LaTeX: {data.result_latex}</div>
              )}
            </>
          )}

          {simType === 'ode_solve' && (
            <>
              <div style={{ marginBottom: 8, color: '#8888a0' }}>ODE: {data.ode}</div>
              <div style={{ fontSize: 16, color: '#fff', marginBottom: 12 }}>
                Solution: {data.solution}
              </div>
              {data.solution_latex && (
                <div style={{ color: ACCENT, fontSize: 12 }}>LaTeX: {data.solution_latex}</div>
              )}
            </>
          )}

          {simType === 'matrix_algebra' && (
            <>
              <div style={{ marginBottom: 8, color: '#8888a0' }}>Matrix: {JSON.stringify(data.matrix)}</div>
              <div style={{ fontSize: 14, color: '#fff', marginBottom: 12 }}>
                Result: {data.result}
              </div>
              {data.eigenvalues && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ color: ACCENT, marginBottom: 4 }}>Eigenvalues:</div>
                  {data.eigenvalues.map((ev, i) => (
                    <div key={i} style={{ color: '#e0e0e0', marginLeft: 12 }}>
                      λ{i+1} = {ev.value} (mult: {ev.multiplicity})
                    </div>
                  ))}
                </div>
              )}
            </>
          )}

          {simType === 'code_generation' && (
            <>
              <div style={{ marginBottom: 8, color: '#8888a0' }}>Expression: {data.expression}</div>
              <div style={{ marginBottom: 8, color: '#8888a0' }}>Language: {data.language}</div>
            </>
          )}

          {/* SageMath results */}
          {data.tool === 'sagemath' && (
            <>
              <div style={{ marginBottom: 8, color: '#8888a0' }}>
                {data.operation && `Operation: ${data.operation}`}
                {data.compute && `Compute: ${data.compute}`}
              </div>
              <div style={{ fontSize: 14, color: '#fff', whiteSpace: 'pre-wrap' }}>
                {typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2)}
              </div>
              {data.result_latex && (
                <div style={{ color: ACCENT, fontSize: 12, marginTop: 8 }}>
                  LaTeX: {typeof data.result_latex === 'string' ? data.result_latex : JSON.stringify(data.result_latex)}
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'plot' && data.numeric_samples?.x?.length > 0 && (
        <div style={{ flex: 1 }}>
          <Plot
            data={[{
              x: data.numeric_samples.x,
              y: data.numeric_samples.y,
              type: 'scatter',
              mode: 'lines',
              line: { color: ACCENT, width: 2 },
              name: data.result || 'f(x)',
            }]}
            layout={{
              ...darkLayout,
              title: { text: `${data.operation || 'Result'} — ${data.expression || ''}`, font: { size: 14 } },
              xaxis: { ...darkLayout.xaxis, title: data.respect_to || 'x' },
              yaxis: { ...darkLayout.yaxis, title: 'y' },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler
            config={{ responsive: true }}
          />
        </div>
      )}

      {activeTab === 'matrix' && simType === 'matrix_algebra' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 16 }}>Matrix Details</h4>
          <table style={{ borderCollapse: 'collapse' }}>
            <tbody>
              {(data.matrix || []).map((row, i) => (
                <tr key={i}>
                  {row.map((val, j) => (
                    <td key={j} style={{
                      padding: '6px 12px', border: '1px solid #2a2a3a',
                      textAlign: 'center', color: '#e0e0e0',
                    }}>{val}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          {data.inverse_matrix && (
            <>
              <h4 style={{ color: ACCENT, marginTop: 16, marginBottom: 8 }}>Inverse</h4>
              <table style={{ borderCollapse: 'collapse' }}>
                <tbody>
                  {data.inverse_matrix.map((row, i) => (
                    <tr key={i}>
                      {row.map((val, j) => (
                        <td key={j} style={{
                          padding: '6px 12px', border: '1px solid #2a2a3a',
                          textAlign: 'center', color: '#e0e0e0',
                        }}>{val}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {activeTab === 'code' && simType === 'code_generation' && (
        <div style={{ padding: 24, overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Generated {data.language?.toUpperCase()} Code</h4>
          <pre style={{
            background: '#1a1a28', padding: 16, borderRadius: 4,
            color: '#e0e0e0', fontSize: 12, fontFamily: "'JetBrains Mono', monospace",
            overflowX: 'auto',
          }}>{data.generated_code}</pre>
          {data.ufl_code && (
            <>
              <h4 style={{ color: ACCENT, marginTop: 16, marginBottom: 12 }}>UFL Code (FEniCS)</h4>
              <pre style={{
                background: '#1a1a28', padding: 16, borderRadius: 4,
                color: '#e0e0e0', fontSize: 12, fontFamily: "'JetBrains Mono', monospace",
                overflowX: 'auto',
              }}>{data.ufl_code}</pre>
            </>
          )}
        </div>
      )}

      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          {data.expression && <div>Expression: {data.expression}</div>}
          {data.operation && <div>Operation: {data.operation}</div>}
          {data.ufl_code && <div style={{ marginTop: 8, color: ACCENT }}>UFL code available for FEniCS coupling</div>}
        </div>
      )}
    </div>
  );
}
