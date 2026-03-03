import { useState, useEffect, useCallback } from 'react';

const TOKEN_KEY = 'totalSim_token';

export function useAuth() {
  const [token, setTokenState] = useState(() => localStorage.getItem(TOKEN_KEY));
  const [authRequired, setAuthRequired] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/auth/status')
      .then(res => res.json())
      .then(data => {
        setAuthRequired(data.auth_enabled);
        setLoading(false);
      })
      .catch(() => {
        setAuthRequired(false);
        setLoading(false);
      });
  }, []);

  const setToken = useCallback((newToken) => {
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken);
    } else {
      localStorage.removeItem(TOKEN_KEY);
    }
    setTokenState(newToken);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    setTokenState(null);
  }, []);

  const isAuthenticated = !authRequired || !!token;
  const needsLogin = authRequired && !token;

  return {
    token,
    setToken,
    logout,
    authRequired,
    isAuthenticated,
    needsLogin,
    loading,
  };
}
