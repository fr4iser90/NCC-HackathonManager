'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axios from 'axios';

// Assuming TeamRead and ProjectStatus might be needed from their respective schema definitions
// For simplicity, defining inline or using basic types if not complex
interface Team {
    id: string;
    name: string;
}

interface Project {
  id: string;
  name: string;
  description: string | null;
  status: string; // ProjectStatus enum as string
  team_id: string;
  team?: Team; // Populated from backend via ProjectRead schema
  created_at: string;
  updated_at: string;
  repository_url?: string | null;
}

export default function AdminManageProjectsPage() {
  const { data: session, status: sessionStatus } = useSession();
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoadingDelete, setIsLoadingDelete] = useState<string | null>(null);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  const fetchProjects = useCallback(async () => {
    if (sessionStatus === 'authenticated' && (session?.user as any)?.role === 'admin') {
      setIsLoading(true);
      setError(null);
      try {
        const token = (session?.user as any)?.accessToken;
        if (!apiBaseUrl || !token) throw new Error("API/Token not available");

        const response = await axios.get(`${apiBaseUrl}/projects/`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        setProjects(response.data);
      } catch (err: any) {
        console.error("Error fetching projects:", err);
        setError(err.response?.data?.detail || err.message || 'Failed to fetch projects.');
      } finally {
        setIsLoading(false);
      }
    }
  }, [session, sessionStatus, apiBaseUrl]);

  useEffect(() => {
    if (sessionStatus === 'authenticated') {
      if ((session?.user as any)?.role === 'admin') {
        fetchProjects();
      } else {
        setError("Access Denied: You do not have permission to view this page.");
        setIsLoading(false);
      }
    } else if (sessionStatus === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [sessionStatus, session, router, fetchProjects]);

  const handleDeleteProject = async (projectId: string, projectName: string) => {
    if (window.confirm(`Are you sure you want to delete project "${projectName}"? This action cannot be undone.`)) {
      setIsLoadingDelete(projectId);
      setError(null);
      setSuccessMessage(null);
      try {
        const token = (session?.user as any)?.accessToken;
        if (!apiBaseUrl || !token) throw new Error("API/Token not available");

        await axios.delete(`${apiBaseUrl}/projects/${projectId}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        setSuccessMessage(`Project "${projectName}" deleted successfully.`);
        fetchProjects(); // Refresh the project list
      } catch (err: any) {
        console.error("Error deleting project:", err);
        setError(err.response?.data?.detail || err.message || 'Failed to delete project.');
      } finally {
        setIsLoadingDelete(null);
      }
    }
  };

  if (sessionStatus === 'loading' || isLoading) {
    return <div className="container mx-auto p-4 text-center">Loading projects...</div>;
  }

  if (error) {
    return <div className="container mx-auto p-4 text-center text-red-500">Error: {error}</div>;
  }
  
  if (!session || (session.user as any)?.role !== 'admin') {
      return <div className="container mx-auto p-4 text-center">Access Denied.</div>;
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Manage Projects</h1>
        <Link href="/admin" className="text-blue-500 hover:underline">
          &larr; Back to Admin Dashboard
        </Link>
      </div>

      {successMessage && (
        <div className="mb-4 p-3 text-center text-green-700 bg-green-100 border border-green-400 rounded">
          {successMessage}
        </div>
      )}

      {projects.length === 0 && !isLoading && (
        <p>No projects found.</p>
      )}
      {projects.length > 0 && (
        <div className="overflow-x-auto shadow-md sm:rounded-lg">
          <table className="min-w-full text-sm text-left text-gray-500 dark:text-gray-400">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
              <tr>
                <th scope="col" className="px-6 py-3">Name</th>
                <th scope="col" className="px-6 py-3">Description</th>
                <th scope="col" className="px-6 py-3">Team</th>
                <th scope="col" className="px-6 py-3">Status</th>
                <th scope="col" className="px-6 py-3">Created At</th>
                <th scope="col" className="px-6 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id} className="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                  <td className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">{project.name}</td>
                  <td className="px-6 py-4 truncate max-w-xs">{project.description || 'N/A'}</td>
                  <td className="px-6 py-4">{project.team?.name || project.team_id.substring(0,8)+"..." || 'N/A'}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${ project.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : project.status === 'COMPLETED' ? 'bg-blue-100 text-blue-800' : 'bg-yellow-100 text-yellow-800' }`}>
                      {project.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">{new Date(project.created_at).toLocaleDateString()}</td>
                  <td className="px-6 py-4 text-center">
                    <Link href={`/admin/projects/edit/${project.id}`} className="font-medium text-blue-600 dark:text-blue-500 hover:underline mr-3">
                      Edit
                    </Link>
                    <button 
                      onClick={() => handleDeleteProject(project.id, project.name)} 
                      className="font-medium text-red-600 dark:text-red-500 hover:underline"
                      disabled={isLoadingDelete === project.id}
                    >
                      {isLoadingDelete === project.id ? 'Deleting...' : 'Delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
} 