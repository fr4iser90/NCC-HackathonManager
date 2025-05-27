'use client';

import React, { useState, useEffect, FormEvent, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import axiosInstance from '@/lib/axiosInstance';

// From schemas/project.py
const ProjectStatusValues = [
  'PENDING',
  'DRAFT',
  'ACTIVE',
  'COMPLETED',
  'ARCHIVED',
  'FAILED',
];

interface ProjectUpdateData {
  name?: string;
  description?: string | null;
  status?: string;
  team_id?: string;
  project_template_id?: string | null;
  repository_url?: string | null;
}

interface ProjectDetails extends ProjectUpdateData {
  // For state holding fetched project data
  id: string;
  // include other fields from ProjectRead if needed for display logic, e.g., created_at
}

interface Team {
  id: string;
  name: string;
}

interface ProjectTemplate {
  id: string;
  name: string;
}

type UserWithRoleAndAccessToken = { role?: string; accessToken?: string };

export default function EditProjectPage() {
  const { data: session, status: sessionStatus } = useSession();
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id as string;

  const [project, setProject] = useState<ProjectDetails | null>(null);
  const [formData, setFormData] = useState<ProjectUpdateData>({});
  const [teams, setTeams] = useState<Team[]>([]);
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchProjectDetails = useCallback(async () => {
    if (
      sessionStatus === 'authenticated' &&
      projectId &&
      (session?.user as UserWithRoleAndAccessToken)?.role === 'admin'
    ) {
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);
      try {
        const token = (session?.user as UserWithRoleAndAccessToken)
          ?.accessToken;
        if (!token) throw new Error('Token not available');

        // Fetch project, teams, and templates in parallel
        const [projectRes, teamsRes, templatesRes] = await Promise.all([
          axiosInstance.get(`/projects/${projectId}`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          axiosInstance.get(`/teams/`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
          axiosInstance.get(`/projects/templates/`, {
            headers: { Authorization: `Bearer ${token}` },
          }),
        ]);

        setProject(projectRes.data);
        setFormData({
          name: projectRes.data.name,
          description: projectRes.data.description || '',
          status: projectRes.data.status,
          team_id: projectRes.data.team_id,
          project_template_id: projectRes.data.project_template_id || '',
          repository_url: projectRes.data.repository_url || '',
        });
        setTeams(teamsRes.data);
        setTemplates(templatesRes.data);
      } catch (err: unknown) {
        console.error('Error fetching project details:', err);
        if (
          err &&
          typeof err === 'object' &&
          'response' in err &&
          typeof (
            err as {
              response?: { status?: number; data?: { detail?: string } };
            }
          ).response === 'object'
        ) {
          const response = (
            err as {
              response?: { status?: number; data?: { detail?: string } };
            }
          ).response;
          if (response?.status !== 401) {
            setError(
              response?.data?.detail ||
                (err &&
                typeof err === 'object' &&
                'message' in err &&
                typeof (err as { message?: string }).message === 'string'
                  ? (err as { message: string }).message
                  : 'Failed to fetch project details.'),
            );
          }
        } else {
          setError(
            err &&
              typeof err === 'object' &&
              'message' in err &&
              typeof (err as { message?: string }).message === 'string'
              ? (err as { message: string }).message
              : 'Failed to fetch project details.',
          );
        }
      } finally {
        setIsLoading(false);
      }
    }
  }, [sessionStatus, projectId, session]);

  useEffect(() => {
    if (sessionStatus === 'authenticated') {
      if ((session?.user as UserWithRoleAndAccessToken)?.role === 'admin') {
        if (projectId) {
          fetchProjectDetails();
        } else {
          setError('Project ID is missing.');
          setIsLoading(false);
        }
      } else {
        setError('Access Denied: You do not have admin privileges.');
        setIsLoading(false);
      }
    } else if (sessionStatus === 'unauthenticated') {
      // router.push('/auth/signin'); // Interceptor should handle
    }
  }, [sessionStatus, session, projectId, router, fetchProjectDetails]);

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value === '' && name === 'project_template_id' ? null : value,
    })); // Set template_id to null if empty string
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);

    if (
      !session ||
      (session?.user as UserWithRoleAndAccessToken)?.role !== 'admin' ||
      !project
    ) {
      setError('Permission denied or project data not loaded.');
      setIsSubmitting(false);
      return;
    }

    try {
      const token = (session?.user as UserWithRoleAndAccessToken)?.accessToken;
      if (!token) throw new Error('Token not available');

      const payload: ProjectUpdateData = {};
      // Only include fields that have actually changed
      if (formData.name !== project.name) payload.name = formData.name;
      if (formData.description !== (project.description || ''))
        payload.description = formData.description;
      if (formData.status !== project.status) payload.status = formData.status;
      if (formData.team_id !== project.team_id)
        payload.team_id = formData.team_id;
      if (formData.repository_url !== (project.repository_url || ''))
        payload.repository_url = formData.repository_url;

      const formTemplateId =
        formData.project_template_id === ''
          ? null
          : formData.project_template_id;
      if (formTemplateId !== project.project_template_id) {
        payload.project_template_id = formTemplateId;
      } else if (
        formData.project_template_id === '' &&
        project.project_template_id !== null
      ) {
        // This case handles explicitly clearing a template if formData.project_template_id is empty string
        // and original project.project_template_id was not null.
        // However, the above (formTemplateId !== project.project_template_id) should cover it if formTemplateId is correctly set to null for empty.
      }

      if (Object.keys(payload).length === 0) {
        setSuccessMessage('No changes detected.');
        setIsSubmitting(false);
        return;
      }

      await axiosInstance.put(`/projects/${projectId}`, payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSuccessMessage('Project updated successfully!');
      fetchProjectDetails();
    } catch (err: unknown) {
      console.error('Error updating project:', err);
      if (
        err &&
        typeof err === 'object' &&
        'response' in err &&
        typeof (
          err as { response?: { status?: number; data?: { detail?: string } } }
        ).response === 'object'
      ) {
        const response = (
          err as { response?: { status?: number; data?: { detail?: string } } }
        ).response;
        if (response?.status !== 401) {
          setError(
            response?.data?.detail ||
              (err &&
              typeof err === 'object' &&
              'message' in err &&
              typeof (err as { message?: string }).message === 'string'
                ? (err as { message: string }).message
                : 'Failed to update project.'),
          );
        }
      } else {
        setError(
          err &&
            typeof err === 'object' &&
            'message' in err &&
            typeof (err as { message?: string }).message === 'string'
            ? (err as { message: string }).message
            : 'Failed to update project.',
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (sessionStatus === 'loading' || isLoading) {
    return (
      <div className="container mx-auto p-4 text-center">
        Loading project data...
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

  if (!project && !isLoading) {
    return (
      <div className="container mx-auto p-4 text-center">
        Project not found or access denied.
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">
          Edit Project: {project?.name || 'Loading...'}
        </h1>
        <Link href="/admin/projects" className="text-blue-500 hover:underline">
          &larr; Back to Project List
        </Link>
      </div>

      {successMessage && (
        <p className="text-green-500 text-sm mt-2 mb-4">{successMessage}</p>
      )}

      {project && (
        <form
          onSubmit={handleSubmit}
          className="space-y-6 bg-white p-8 shadow-md rounded-lg"
        >
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-700"
            >
              Project Name
            </label>
            <input
              type="text"
              name="name"
              id="name"
              value={formData.name || ''}
              onChange={handleChange}
              required
              className="mt-1 block w-full"
            />
          </div>
          <div>
            <label
              htmlFor="description"
              className="block text-sm font-medium text-gray-700"
            >
              Description
            </label>
            <textarea
              name="description"
              id="description"
              rows={4}
              value={formData.description || ''}
              onChange={handleChange}
              className="mt-1 block w-full"
            />
          </div>
          <div>
            <label
              htmlFor="team_id"
              className="block text-sm font-medium text-gray-700"
            >
              Team
            </label>
            <select
              name="team_id"
              id="team_id"
              value={formData.team_id || ''}
              onChange={handleChange}
              required
              className="mt-1 block w-full"
            >
              <option value="" disabled>
                Select a team
              </option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label
              htmlFor="project_template_id"
              className="block text-sm font-medium text-gray-700"
            >
              Project Template (Optional)
            </label>
            <select
              name="project_template_id"
              id="project_template_id"
              value={formData.project_template_id || ''}
              onChange={handleChange}
              className="mt-1 block w-full"
            >
              <option value="">None</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label
              htmlFor="status"
              className="block text-sm font-medium text-gray-700"
            >
              Status
            </label>
            <select
              name="status"
              id="status"
              value={formData.status || ''}
              onChange={handleChange}
              required
              className="mt-1 block w-full"
            >
              {ProjectStatusValues.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label
              htmlFor="repository_url"
              className="block text-sm font-medium text-gray-700"
            >
              Repository URL (Optional)
            </label>
            <input
              type="url"
              name="repository_url"
              id="repository_url"
              value={formData.repository_url || ''}
              onChange={handleChange}
              className="mt-1 block w-full"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isSubmitting ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
