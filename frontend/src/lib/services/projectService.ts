import axiosInstance from '../axiosInstance';

/**
 * Fetch all projects (admin only).
 */
export async function fetchProjects(token: string) {
  const res = await axiosInstance.get('/projects/', {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

/**
 * Create a new project.
 */
export async function createProject(token: string, payload: unknown) {
  const res = await axiosInstance.post('/projects/', payload, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

/**
 * Delete a project by ID.
 */
export async function deleteProject(token: string, projectId: string) {
  const res = await axiosInstance.delete(`/projects/${projectId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}

/**
 * Fetch a single project by ID.
 */
export async function fetchProject(token: string, projectId: string) {
  const res = await axiosInstance.get(`/projects/${projectId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return res.data;
}
