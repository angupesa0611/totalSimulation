import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import React from 'react';

const mockResults = [
  {
    job_id: 'job-001',
    tool: 'rebound',
    label: 'inner solar system',
    timestamp: new Date().toISOString(),
    status: 'SUCCESS',
    duration_s: 3.2,
  },
  {
    job_id: 'job-002',
    tool: 'qutip',
    label: 'rabi oscillation',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    status: 'SUCCESS',
    duration_s: 1.1,
  },
  {
    job_id: 'job-003',
    tool: 'openmm',
    label: 'alanine dipeptide',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    status: 'FAILURE',
    duration_s: 12.5,
  },
];

const mockDeleteResult = vi.fn();
const mockSetFilters = vi.fn();
const mockSetPage = vi.fn();
const mockRefresh = vi.fn();

// Mock useResults hook directly to avoid debounce issues
vi.mock('../../hooks/useResults.js', () => ({
  useResults: vi.fn(() => ({
    results: mockResults,
    total: 3,
    loading: false,
    filters: { tool: null, status: null, q: '', sort: 'newest' },
    setFilters: mockSetFilters,
    page: 0,
    setPage: mockSetPage,
    pageCount: 1,
    deleteResult: mockDeleteResult,
    refresh: mockRefresh,
  })),
}));

// Mock theme
vi.mock('../../theme.json', () => ({
  default: {
    colors: {
      bg: '#0a0a0f',
      bgSecondary: '#12121a',
      bgTertiary: '#1a1a28',
      border: '#2a2a3a',
      text: '#e0e0e0',
      textSecondary: '#8888a0',
      accent: '#6366f1',
      success: '#22c55e',
      warning: '#f59e0b',
      error: '#ef4444',
    },
    fonts: {
      sans: 'sans-serif',
      mono: 'monospace',
    },
  },
}));

import ResultsBrowser from '../ResultsBrowser.jsx';
import { useResults } from '../../hooks/useResults.js';

describe('ResultsBrowser', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useResults.mockReturnValue({
      results: mockResults,
      total: 3,
      loading: false,
      filters: { tool: null, status: null, q: '', sort: 'newest' },
      setFilters: mockSetFilters,
      page: 0,
      setPage: mockSetPage,
      pageCount: 1,
      deleteResult: mockDeleteResult,
      refresh: mockRefresh,
    });
  });

  it('renders results list with tool names', () => {
    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={vi.fn()}
        selectedResult={null}
      />
    );

    // Tool names appear in result cards and filter dropdown — use getAllByText
    expect(screen.getAllByText('rebound').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('qutip').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('openmm').length).toBeGreaterThanOrEqual(1);
  });

  it('shows result labels', () => {
    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={vi.fn()}
        selectedResult={null}
      />
    );

    expect(screen.getByText('inner solar system')).toBeDefined();
    expect(screen.getByText('rabi oscillation')).toBeDefined();
    expect(screen.getByText('alanine dipeptide')).toBeDefined();
  });

  it('shows pagination info', () => {
    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={vi.fn()}
        selectedResult={null}
      />
    );

    expect(screen.getByText('1-3 of 3')).toBeDefined();
  });

  it('calls onSelectResult when clicking a result', () => {
    const onSelect = vi.fn();

    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={onSelect}
        selectedResult={null}
      />
    );

    fireEvent.click(screen.getByText('inner solar system'));
    expect(onSelect).toHaveBeenCalledWith(mockResults[0]);
  });

  it('shows no results message when empty', () => {
    useResults.mockReturnValue({
      results: [],
      total: 0,
      loading: false,
      filters: { tool: null, status: null, q: '', sort: 'newest' },
      setFilters: mockSetFilters,
      page: 0,
      setPage: mockSetPage,
      pageCount: 0,
      deleteResult: mockDeleteResult,
      refresh: mockRefresh,
    });

    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={vi.fn()}
        selectedResult={null}
      />
    );

    expect(screen.getByText('No results found')).toBeDefined();
  });

  it('has search input', () => {
    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={vi.fn()}
        selectedResult={null}
      />
    );

    expect(screen.getByPlaceholderText('Search results...')).toBeDefined();
  });

  it('has filter dropdowns', () => {
    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={vi.fn()}
        selectedResult={null}
      />
    );

    expect(screen.getByText('All Tools')).toBeDefined();
    expect(screen.getByText('All Status')).toBeDefined();
    expect(screen.getByText('Newest')).toBeDefined();
  });

  it('delete requires confirmation', () => {
    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={vi.fn()}
        selectedResult={null}
      />
    );

    const deleteButtons = screen.getAllByTitle('Delete result');
    expect(deleteButtons.length).toBe(3);

    // First click shows confirmation
    fireEvent.click(deleteButtons[0]);
    expect(screen.getByText('Confirm?')).toBeDefined();
  });

  it('shows loading state', () => {
    useResults.mockReturnValue({
      results: [],
      total: 0,
      loading: true,
      filters: { tool: null, status: null, q: '', sort: 'newest' },
      setFilters: mockSetFilters,
      page: 0,
      setPage: mockSetPage,
      pageCount: 0,
      deleteResult: mockDeleteResult,
      refresh: mockRefresh,
    });

    render(
      <ResultsBrowser
        project="_default"
        onSelectResult={vi.fn()}
        selectedResult={null}
      />
    );

    expect(screen.getByText('Loading...')).toBeDefined();
  });
});
