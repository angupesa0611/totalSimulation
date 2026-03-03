import { useState, useEffect, useCallback } from 'react';
import { getProjects, createProject as apiCreateProject, deleteProject as apiDeleteProject } from '../api/client';

const STORAGE_KEY = 'totalSim_activeProject';

export function useProjects() {
  const [projects, setProjects] = useState(['_default']);
  const [activeProject, setActiveProjectState] = useState(
    () => localStorage.getItem(STORAGE_KEY) || '_default'
  );
  const [loading, setLoading] = useState(true);

  const fetchProjects = useCallback(async () => {
    try {
      setLoading(true);
      const list = await getProjects();
      setProjects(list);
      // If active project was deleted, reset to _default
      if (!list.includes(activeProject)) {
        setActiveProjectState('_default');
        localStorage.setItem(STORAGE_KEY, '_default');
      }
    } catch (err) {
      console.error('Failed to fetch projects:', err);
    } finally {
      setLoading(false);
    }
  }, [activeProject]);

  useEffect(() => {
    fetchProjects();
  }, []);

  const setActiveProject = useCallback((name) => {
    setActiveProjectState(name);
    localStorage.setItem(STORAGE_KEY, name);
  }, []);

  const createProject = useCallback(async (name) => {
    await apiCreateProject(name);
    await fetchProjects();
    setActiveProject(name);
  }, [fetchProjects, setActiveProject]);

  const deleteProject = useCallback(async (name) => {
    await apiDeleteProject(name);
    if (activeProject === name) {
      setActiveProject('_default');
    }
    await fetchProjects();
  }, [activeProject, fetchProjects, setActiveProject]);

  return {
    projects,
    activeProject,
    setActiveProject,
    createProject,
    deleteProject,
    loading,
    refresh: fetchProjects,
  };
}
