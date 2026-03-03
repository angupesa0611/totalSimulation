import { useState, useEffect, useCallback, useRef } from 'react';
import { searchResults, deleteResult as apiDeleteResult } from '../api/client';

export function useResults(project = '_default') {
  const [results, setResults] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    tool: null,
    status: null,
    q: '',
    sort: 'newest',
  });
  const [page, setPage] = useState(0);
  const limit = 20;
  const debounceRef = useRef(null);

  const fetchResults = useCallback(async () => {
    try {
      setLoading(true);
      const data = await searchResults({
        project,
        tool: filters.tool,
        status: filters.status,
        q: filters.q || undefined,
        sort: filters.sort,
        offset: page * limit,
        limit,
      });
      setResults(data.results || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Failed to fetch results:', err);
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [project, filters, page]);

  // Debounce search query, fetch immediately for other filter changes
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(fetchResults, filters.q ? 300 : 0);
    return () => clearTimeout(debounceRef.current);
  }, [fetchResults]);

  // Reset page when filters or project change
  useEffect(() => {
    setPage(0);
  }, [project, filters.tool, filters.status, filters.q, filters.sort]);

  const deleteResult = useCallback(async (jobId) => {
    await apiDeleteResult(jobId, project);
    await fetchResults();
  }, [project, fetchResults]);

  const refresh = useCallback(() => {
    fetchResults();
  }, [fetchResults]);

  return {
    results,
    total,
    loading,
    filters,
    setFilters,
    page,
    setPage,
    pageCount: Math.ceil(total / limit),
    deleteResult,
    refresh,
  };
}
