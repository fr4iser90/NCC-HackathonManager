import React from 'react';
import { Link } from 'react-router-dom';

interface Project {
  id: string;
  name: string;
  description: string;
  status: string;
  storage_type: string;
  github_url?: string;
  gitlab_url?: string;
  bitbucket_url?: string;
  server_url?: string;
  docker_url?: string;
  kubernetes_url?: string;
  cloud_url?: string;
  archive_url?: string;
  docker_archive_url?: string;
  backup_url?: string;
  docker_image?: string;
  docker_tag?: string;
  docker_registry?: string;
  created_at: string;
  updated_at: string;
}

interface ProjectListProps {
  projects: Project[];
  onDelete?: (id: string) => void;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-500';
    case 'draft':
      return 'bg-gray-500';
    case 'completed':
      return 'bg-blue-500';
    case 'archived':
      return 'bg-yellow-500';
    case 'failed':
      return 'bg-red-500';
    case 'building':
      return 'bg-purple-500';
    case 'built':
      return 'bg-indigo-500';
    case 'deploying':
      return 'bg-pink-500';
    case 'deployed':
      return 'bg-emerald-500';
    default:
      return 'bg-gray-500';
  }
};

const getStorageTypeIcon = (type: string) => {
  switch (type) {
    case 'github':
      return '🐙';
    case 'gitlab':
      return '🦊';
    case 'bitbucket':
      return '🪣';
    case 'docker':
    case 'docker_hybrid':
    case 'docker_archive':
      return '🐳';
    case 'kubernetes':
      return '☸️';
    case 'cloud':
      return '☁️';
    case 'archive':
    case 'backup':
      return '📦';
    default:
      return '📁';
  }
};

const getProjectUrl = (project: Project) => {
  switch (project.storage_type) {
    case 'github':
      return project.github_url;
    case 'gitlab':
      return project.gitlab_url;
    case 'bitbucket':
      return project.bitbucket_url;
    case 'docker':
    case 'docker_hybrid':
      return project.docker_url;
    case 'kubernetes':
      return project.kubernetes_url;
    case 'cloud':
      return project.cloud_url;
    case 'archive':
      return project.archive_url;
    case 'docker_archive':
      return project.docker_archive_url;
    case 'backup':
      return project.backup_url;
    default:
      return null;
  }
};

export function ProjectList({ projects, onDelete }: ProjectListProps) {
  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg font-medium leading-6 text-gray-900">Projects</h3>
        <div className="mt-5">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Storage
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    URL
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Docker Info
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {projects.map((project) => (
                  <tr key={project.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{project.name}</div>
                      <div className="text-sm text-gray-500">{project.description}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(project.status)} text-white`}>
                        {project.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="mr-2">{getStorageTypeIcon(project.storage_type)}</span>
                        <span className="text-sm text-gray-900">{project.storage_type}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getProjectUrl(project) && (
                        <a
                          href={getProjectUrl(project) || undefined}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          View Project
                        </a>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {project.docker_image && (
                        <div className="text-sm text-gray-900">
                          <div>Image: {project.docker_image}</div>
                          {project.docker_tag && <div>Tag: {project.docker_tag}</div>}
                          {project.docker_registry && <div>Registry: {project.docker_registry}</div>}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-2">
                        <Link
                          to={`/projects/${project.id}`}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          View
                        </Link>
                        <Link
                          to={`/projects/${project.id}/edit`}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          Edit
                        </Link>
                        {onDelete && (
                          <button
                            onClick={() => onDelete(project.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
} 