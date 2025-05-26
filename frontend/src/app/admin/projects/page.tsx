'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { fetchProjects, deleteProject } from '@/lib/services/projectService';

// NOTE: If you see JSX linter errors about 'JSX.IntrinsicElements', ensure your environment has the correct React/TypeScript types installed (e.g., @types/react). The code is correct for a Next.js/React project.

interface Project {
  id: string;
  name: string;
  status: string;
  // ... other fields as needed
}

type UserWithRoleAndAccessToken = { role?: string; accessToken?: string };

export default function AdminManageProjectsPage() {
  const { data: session, status: sessionStatus } = useSession();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDelete, setIsLoadingDelete] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const router = useRouter();

  const fetchProjectsHandler = useCallback(async () => {
    if (
      sessionStatus === 'authenticated' &&
      (session?.user as UserWithRoleAndAccessToken)?.role === 'admin'
    ) {
      setIsLoading(true);
      setError(null);
      try {
        const token = (session?.user as UserWithRoleAndAccessToken)
          ?.accessToken;
        if (!token) throw new Error('Token not available');
        const data = await fetchProjects(token);
        setProjects(data);
      } catch (err: unknown) {
        if (
          err &&
          typeof err === 'object' &&
          'message' in err &&
          typeof (err as { message?: string }).message === 'string'
        ) {
          setError((err as { message: string }).message);
        } else {
          setError('Failed to fetch projects.');
        }
      } finally {
        setIsLoading(false);
      }
    }
  }, [session, sessionStatus]);

  useEffect(() => {
    if (sessionStatus === 'authenticated') {
      if ((session?.user as UserWithRoleAndAccessToken)?.role === 'admin') {
        fetchProjectsHandler();
      } else {
        setError(
          'Access Denied: You do not have permission to view this page.',
        );
        setIsLoading(false);
      }
    } else if (sessionStatus === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [sessionStatus, session, router, fetchProjectsHandler]);

  const handleDeleteProject = async (
    projectId: string,
    projectName: string,
  ) => {
    if (
      window.confirm(
        `Are you sure you want to delete project "${projectName}"? This action cannot be undone.`,
      )
    ) {
      setIsLoadingDelete(projectId);
      setError(null);
      setSuccessMessage(null);
      try {
        const token = (session?.user as UserWithRoleAndAccessToken)
          ?.accessToken;
        if (!token) throw new Error('Token not available');
        await deleteProject(token, projectId);
        setSuccessMessage(`Project "${projectName}" deleted successfully.`);
        fetchProjectsHandler();
      } catch (err: unknown) {
        if (
          err &&
          typeof err === 'object' &&
          'message' in err &&
          typeof (err as { message?: string }).message === 'string'
        ) {
          setError((err as { message: string }).message);
        } else {
          setError('Failed to delete project.');
        }
      } finally {
        setIsLoadingDelete(null);
      }
    }
  };

  if (sessionStatus === 'loading' || isLoading) {
    return (
      <div className="container mx-auto p-4 text-center">
        Loading projects...
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 text-center text-red-500">
        Error: {error}
      </div>
    );
  }

  if (
    !session ||
    (session.user as UserWithRoleAndAccessToken)?.role !== 'admin'
  ) {
    return (
      <div className="container mx-auto p-4 text-center">Access Denied.</div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Manage Projects</h1>
      {successMessage && (
        <div className="text-green-600 mb-2">{successMessage}</div>
      )}
      <table className="min-w-full bg-white border border-gray-200">
        <thead>
          <tr>
            <th className="py-2 px-4 border-b">Name</th>
            <th className="py-2 px-4 border-b">Status</th>
            <th className="py-2 px-4 border-b">Actions</th>
          </tr>
        </thead>
        <tbody>
          {projects.map((project) => (
            <tr key={project.id}>
              <td className="py-2 px-4 border-b">{project.name}</td>
              <td className="py-2 px-4 border-b">{project.status}</td>
              <td className="py-2 px-4 border-b">
                <button
                  className="bg-red-500 text-white px-3 py-1 rounded mr-2"
                  onClick={() => handleDeleteProject(project.id, project.name)}
                  disabled={isLoadingDelete === project.id}
                >
                  {isLoadingDelete === project.id ? 'Deleting...' : 'Delete'}
                </button>
                <Link
                  href={`/admin/projects/edit/${project.id}`}
                  className="bg-blue-500 text-white px-3 py-1 rounded"
                >
                  Edit
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
