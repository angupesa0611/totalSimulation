import React, { useMemo, useState } from 'react';

const ACCENT = '#a78bfa';

export default function ProofView({ data }) {
  const [tab, setTab] = useState('result');

  if (!data) {
    return <div style={{ color: '#8888a0', padding: 24 }}>No data to display</div>;
  }

  const isLean = data.tool === 'lean4';
  const isGAP = data.tool === 'gap';

  const tabs = useMemo(() => {
    const t = ['result'];
    if (isLean && data.messages?.length > 0) t.push('messages');
    if (isGAP && data.character_table_text) t.push('char_table');
    if (isGAP && data.conjugacy_classes) t.push('classes');
    if (isGAP && data.irreducible_representations) t.push('irreps');
    t.push('info');
    return t;
  }, [data, isLean, isGAP]);

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
          >{t.replace('_', ' ')}</button>
        ))}
      </div>

      {activeTab === 'result' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          {isLean && (
            <>
              <div style={{
                display: 'inline-block', padding: '6px 16px', borderRadius: 4,
                background: data.verified ? '#22c55e22' : '#ef444422',
                border: `1px solid ${data.verified ? '#22c55e' : '#ef4444'}`,
                color: data.verified ? '#22c55e' : '#ef4444',
                fontSize: 16, fontWeight: 600, marginBottom: 16,
              }}>
                {data.verified ? 'VERIFIED' : 'FAILED'}
              </div>

              {data.errors?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <h4 style={{ color: '#ef4444', marginBottom: 8 }}>Errors</h4>
                  {data.errors.map((err, i) => (
                    <div key={i} style={{ color: '#ef4444', marginBottom: 4, fontSize: 12, padding: 8, background: '#ef444411', borderRadius: 4 }}>
                      {err}
                    </div>
                  ))}
                </div>
              )}

              {data.proof_term && (
                <div style={{ marginTop: 16 }}>
                  <h4 style={{ color: ACCENT, marginBottom: 8 }}>Proof Term</h4>
                  <pre style={{
                    background: '#1a1a28', padding: 12, borderRadius: 4,
                    color: '#e0e0e0', fontSize: 12, overflowX: 'auto',
                  }}>{data.proof_term}</pre>
                </div>
              )}
            </>
          )}

          {isGAP && (
            <>
              <h4 style={{ color: ACCENT, marginBottom: 16 }}>
                {data.group_type ? `${data.group_type.charAt(0).toUpperCase() + data.group_type.slice(1)} Group` : 'Group'} (n={data.n})
              </h4>

              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <tbody>
                  {data.group_order && (
                    <tr style={{ borderBottom: '1px solid #2a2a3a' }}>
                      <td style={{ padding: '8px 12px', color: '#8888a0' }}>Order</td>
                      <td style={{ padding: '8px 12px', color: '#e0e0e0', fontWeight: 600 }}>{data.group_order}</td>
                    </tr>
                  )}
                  {data.n_conjugacy_classes && (
                    <tr style={{ borderBottom: '1px solid #2a2a3a' }}>
                      <td style={{ padding: '8px 12px', color: '#8888a0' }}>Conjugacy Classes</td>
                      <td style={{ padding: '8px 12px', color: '#e0e0e0', fontWeight: 600 }}>{data.n_conjugacy_classes}</td>
                    </tr>
                  )}
                  {data.center_order !== undefined && (
                    <tr style={{ borderBottom: '1px solid #2a2a3a' }}>
                      <td style={{ padding: '8px 12px', color: '#8888a0' }}>Center Order</td>
                      <td style={{ padding: '8px 12px', color: '#e0e0e0', fontWeight: 600 }}>{data.center_order}</td>
                    </tr>
                  )}
                  {data.n_irreps !== undefined && (
                    <tr style={{ borderBottom: '1px solid #2a2a3a' }}>
                      <td style={{ padding: '8px 12px', color: '#8888a0' }}>Irreducible Reps</td>
                      <td style={{ padding: '8px 12px', color: '#e0e0e0', fontWeight: 600 }}>{data.n_irreps}</td>
                    </tr>
                  )}
                  {data.generators && (
                    <tr style={{ borderBottom: '1px solid #2a2a3a' }}>
                      <td style={{ padding: '8px 12px', color: '#8888a0' }}>Generators</td>
                      <td style={{ padding: '8px 12px', color: '#e0e0e0', fontSize: 11 }}>{data.generators}</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {activeTab === 'messages' && isLean && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 12, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Messages</h4>
          {data.messages?.map((msg, i) => (
            <div key={i} style={{ marginBottom: 4, padding: 8, background: '#1a1a28', borderRadius: 4 }}>
              {msg}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'char_table' && isGAP && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 12, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Character Table</h4>
          <pre style={{
            background: '#1a1a28', padding: 16, borderRadius: 4,
            overflowX: 'auto', whiteSpace: 'pre-wrap',
          }}>{data.character_table_text}</pre>
        </div>
      )}

      {activeTab === 'classes' && isGAP && data.conjugacy_classes && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Conjugacy Classes</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #2a2a3a' }}>
                <th style={{ padding: '8px 12px', color: '#8888a0', textAlign: 'left' }}>#</th>
                <th style={{ padding: '8px 12px', color: '#8888a0', textAlign: 'left' }}>Size</th>
                <th style={{ padding: '8px 12px', color: '#8888a0', textAlign: 'left' }}>Representative</th>
              </tr>
            </thead>
            <tbody>
              {data.conjugacy_classes.map((c, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #2a2a3a' }}>
                  <td style={{ padding: '6px 12px', color: ACCENT }}>{i + 1}</td>
                  <td style={{ padding: '6px 12px' }}>{c.size}</td>
                  <td style={{ padding: '6px 12px', fontSize: 11 }}>{c.representative}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'irreps' && isGAP && data.irreducible_representations && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace", overflowY: 'auto', flex: 1 }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Irreducible Representations</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid #2a2a3a' }}>
                <th style={{ padding: '8px 12px', color: '#8888a0', textAlign: 'left' }}>Index</th>
                <th style={{ padding: '8px 12px', color: '#8888a0', textAlign: 'left' }}>Degree</th>
              </tr>
            </thead>
            <tbody>
              {data.irreducible_representations.map((rep, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #2a2a3a' }}>
                  <td style={{ padding: '6px 12px', color: ACCENT }}>{rep.index}</td>
                  <td style={{ padding: '6px 12px' }}>{rep.degree}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'info' && (
        <div style={{ padding: 24, color: '#e0e0e0', fontSize: 13, fontFamily: "'JetBrains Mono', monospace" }}>
          <h4 style={{ color: ACCENT, marginBottom: 12 }}>Info</h4>
          <div>Tool: {data.tool}</div>
          <div>Type: {data.simulation_type}</div>
          {isLean && <div>Verified: {data.verified ? 'Yes' : 'No'}</div>}
          {isGAP && data.group_type && <div>Group: {data.group_type} (n={data.n})</div>}
          {isGAP && data.group_order && <div>Order: {data.group_order}</div>}
        </div>
      )}
    </div>
  );
}
