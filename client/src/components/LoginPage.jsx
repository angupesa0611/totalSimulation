import React, { useState } from 'react';
import theme from '../theme.json';

export default function LoginPage({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;

    setLoading(true);
    setError('');

    const endpoint = mode === 'login' ? '/api/auth/login' : '/api/auth/register';

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: username.trim(), password }),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || 'Authentication failed');
        setLoading(false);
        return;
      }

      onLogin(data.token);
    } catch {
      setError('Network error — is the server running?');
      setLoading(false);
    }
  };

  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: theme.colors.bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <div style={{
        width: 360,
        maxWidth: '90vw',
        background: theme.colors.bgSecondary,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: 12,
        padding: 32,
      }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: theme.colors.text, margin: 0 }}>
            totalSimulation
          </h1>
          <p style={{ fontSize: 12, color: theme.colors.textSecondary, marginTop: 4 }}>
            Authentication required
          </p>
        </div>

        {/* Mode toggle */}
        <div style={{
          display: 'flex', gap: 2, background: theme.colors.bgTertiary,
          borderRadius: 6, padding: 2, marginBottom: 20,
        }}>
          {['login', 'register'].map(m => (
            <button
              key={m}
              onClick={() => { setMode(m); setError(''); }}
              style={{
                flex: 1, padding: '6px 0',
                background: mode === m ? theme.colors.accent : 'transparent',
                border: 'none', borderRadius: 4,
                color: mode === m ? '#fff' : theme.colors.textSecondary,
                fontSize: 12, cursor: 'pointer', textTransform: 'capitalize',
              }}
            >
              {m}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 11, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoFocus
              style={{
                width: '100%', padding: '8px 12px',
                background: theme.colors.bg,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: 6, color: theme.colors.text,
                fontSize: 14, outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>

          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 11, color: theme.colors.textSecondary, display: 'block', marginBottom: 4 }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              style={{
                width: '100%', padding: '8px 12px',
                background: theme.colors.bg,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: 6, color: theme.colors.text,
                fontSize: 14, outline: 'none', boxSizing: 'border-box',
              }}
            />
          </div>

          {error && (
            <div style={{
              padding: '8px 12px', marginBottom: 12,
              background: '#1a0a0a', border: '1px solid #ef4444',
              borderRadius: 6, fontSize: 12, color: '#ef4444',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '10px 0',
              background: loading ? theme.colors.bgTertiary : theme.colors.accent,
              border: 'none', borderRadius: 6,
              color: '#fff', fontSize: 14, fontWeight: 600,
              cursor: loading ? 'default' : 'pointer',
            }}
          >
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
}
