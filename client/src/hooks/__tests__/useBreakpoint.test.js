import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';
import { useBreakpoint } from '../useBreakpoint';

describe('useBreakpoint', () => {
  const setWidth = (w) => {
    Object.defineProperty(window, 'innerWidth', { value: w, writable: true });
    window.dispatchEvent(new Event('resize'));
  };

  beforeEach(() => {
    Object.defineProperty(window, 'innerWidth', { value: 1280, writable: true });
  });

  it('returns desktop for wide viewports', () => {
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current.breakpoint).toBe('desktop');
    expect(result.current.isDesktop).toBe(true);
    expect(result.current.isMobile).toBe(false);
  });

  it('returns tablet for mid-range viewports', () => {
    Object.defineProperty(window, 'innerWidth', { value: 900, writable: true });
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current.breakpoint).toBe('tablet');
    expect(result.current.isTablet).toBe(true);
  });

  it('returns mobile for narrow viewports', () => {
    Object.defineProperty(window, 'innerWidth', { value: 400, writable: true });
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current.breakpoint).toBe('mobile');
    expect(result.current.isMobile).toBe(true);
  });

  it('updates on window resize', () => {
    const { result } = renderHook(() => useBreakpoint());
    expect(result.current.isDesktop).toBe(true);

    act(() => setWidth(500));
    expect(result.current.isMobile).toBe(true);
  });
});
