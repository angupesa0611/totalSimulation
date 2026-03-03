import React, { useState } from 'react';
import theme from '../theme.json';

export default function ProjectSelector({ projects, activeProject, onSelect, onCreate, compact }) {
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState('');

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    try {
      await onCreate(name);
      setNewName('');
      setCreating(false);
      setOpen(false);
    } catch (err) {
      console.error('Failed to create project:', err);
    }
  };

  return (
    <div style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          padding: '4px 10px',
          background: theme.colors.bgTertiary,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: 4,
          color: theme.colors.text,
          fontSize: 11,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: 4,
        }}
      >
        {!compact && <span style={{ color: theme.colors.textSecondary }}>Project:</span>}
        {activeProject}
        <span style={{ fontSize: 8, marginLeft: 2 }}>{open ? '\u25B2' : '\u25BC'}</span>
      </button>

      {open && (
        <div style={{
          position: 'absolute',
          top: '100%',
          right: 0,
          marginTop: 4,
          background: theme.colors.bgSecondary,
          border: `1px solid ${theme.colors.border}`,
          borderRadius: 6,
          minWidth: 160,
          zIndex: 1000,
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        }}>
          {projects.map(p => (
            <button
              key={p}
              onClick={() => { onSelect(p); setOpen(false); }}
              style={{
                display: 'block',
                width: '100%',
                padding: '6px 12px',
                background: p === activeProject ? theme.colors.accent + '22' : 'transparent',
                border: 'none',
                borderBottom: `1px solid ${theme.colors.border}`,
                color: p === activeProject ? theme.colors.accent : theme.colors.text,
                fontSize: 12,
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              {p}
            </button>
          ))}

          {creating ? (
            <div style={{ padding: '6px 8px', display: 'flex', gap: 4 }}>
              <input
                value={newName}
                onChange={e => setNewName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleCreate()}
                placeholder="Project name"
                autoFocus
                style={{
                  flex: 1,
                  padding: '3px 6px',
                  background: theme.colors.bg,
                  border: `1px solid ${theme.colors.border}`,
                  borderRadius: 3,
                  color: theme.colors.text,
                  fontSize: 11,
                  outline: 'none',
                }}
              />
              <button
                onClick={handleCreate}
                style={{
                  padding: '3px 8px',
                  background: theme.colors.accent,
                  border: 'none',
                  borderRadius: 3,
                  color: '#fff',
                  fontSize: 10,
                  cursor: 'pointer',
                }}
              >
                Add
              </button>
            </div>
          ) : (
            <button
              onClick={() => setCreating(true)}
              style={{
                display: 'block',
                width: '100%',
                padding: '6px 12px',
                background: 'transparent',
                border: 'none',
                color: theme.colors.accent,
                fontSize: 11,
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              + New Project
            </button>
          )}
        </div>
      )}
    </div>
  );
}
