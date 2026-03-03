import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useAuth } from '../useAuth';

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
    global.fetch = vi.fn().mockResolvedValue({
      json: async () => ({ auth_enabled: false }),
    });
  });

  it('starts with no token when localStorage is empty', async () => {
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.token).toBeNull();
  });

  it('loads existing token from localStorage', async () => {
    localStorage.setItem('totalSim_token', 'saved-jwt');
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.token).toBe('saved-jwt');
  });

  it('setToken persists to localStorage', async () => {
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => result.current.setToken('new-jwt'));
    expect(result.current.token).toBe('new-jwt');
    expect(localStorage.getItem('totalSim_token')).toBe('new-jwt');
  });

  it('logout clears token', async () => {
    localStorage.setItem('totalSim_token', 'old-jwt');
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));

    act(() => result.current.logout());
    expect(result.current.token).toBeNull();
    expect(localStorage.getItem('totalSim_token')).toBeNull();
  });

  it('needsLogin is true when auth required and no token', async () => {
    global.fetch.mockResolvedValueOnce({
      json: async () => ({ auth_enabled: true }),
    });
    const { result } = renderHook(() => useAuth());
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.needsLogin).toBe(true);
  });
});
