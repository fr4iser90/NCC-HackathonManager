import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Listbox } from '@headlessui/react';
import { CheckIcon, ChevronUpDownIcon } from '@heroicons/react/20/solid';

const projectSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  hackathon_id: z.string().uuid(),
  project_template_id: z.string().uuid().optional(),
  status: z.enum(['draft', 'active', 'completed', 'archived', 'failed', 'building', 'built', 'deploying', 'deployed']),
  storage_type: z.enum([
    'github', 'gitlab', 'bitbucket', 'local',
    'server', 'docker', 'kubernetes', 'cloud',
    'archive', 'docker_archive', 'backup',
    'hybrid', 'docker_hybrid'
  ]),
  github_url: z.string().url().optional(),
  gitlab_url: z.string().url().optional(),
  bitbucket_url: z.string().url().optional(),
  server_url: z.string().url().optional(),
  docker_url: z.string().url().optional(),
  kubernetes_url: z.string().url().optional(),
  cloud_url: z.string().url().optional(),
  archive_url: z.string().url().optional(),
  docker_archive_url: z.string().url().optional(),
  backup_url: z.string().url().optional(),
  docker_image: z.string().optional(),
  docker_tag: z.string().optional(),
  docker_registry: z.string().optional(),
});

type ProjectFormData = z.infer<typeof projectSchema>;

interface ProjectFormProps {
  onSubmit: (data: ProjectFormData) => void;
  initialData?: Partial<ProjectFormData>;
  hackathons: Array<{ id: string; name: string }>;
  templates?: Array<{ id: string; name: string }>;
}

export function ProjectForm({ onSubmit, initialData, hackathons, templates }: ProjectFormProps) {
  const form = useForm<ProjectFormData>({
    resolver: zodResolver(projectSchema),
    defaultValues: {
      status: 'draft',
      storage_type: 'github',
      ...initialData,
    },
  });

  const [selectedStorageType, setSelectedStorageType] = useState(initialData?.storage_type || 'github');

  const renderStorageFields = () => {
    switch (selectedStorageType) {
      case 'github':
        return (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">GitHub URL</label>
            <input
              type="url"
              {...form.register('github_url')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="https://github.com/username/repo"
            />
          </div>
        );
      case 'gitlab':
        return (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">GitLab URL</label>
            <input
              type="url"
              {...form.register('gitlab_url')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="https://gitlab.com/username/repo"
            />
          </div>
        );
      case 'docker':
      case 'docker_hybrid':
        return (
          <>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">Docker URL</label>
              <input
                type="url"
                {...form.register('docker_url')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="https://docker.hub.com/image"
              />
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">Docker Image</label>
              <input
                type="text"
                {...form.register('docker_image')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="username/image"
              />
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">Docker Tag</label>
              <input
                type="text"
                {...form.register('docker_tag')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="latest"
              />
            </div>
            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700">Docker Registry</label>
              <input
                type="text"
                {...form.register('docker_registry')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="registry.hub.docker.com"
              />
            </div>
          </>
        );
      case 'kubernetes':
        return (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">Kubernetes URL</label>
            <input
              type="url"
              {...form.register('kubernetes_url')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="https://k8s.cluster.com"
            />
          </div>
        );
      case 'cloud':
        return (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">Cloud URL</label>
            <input
              type="url"
              {...form.register('cloud_url')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="https://app.cloud.com"
            />
          </div>
        );
      case 'archive':
      case 'docker_archive':
        return (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700">Archive URL</label>
            <input
              type="url"
              {...form.register('archive_url')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
              placeholder="https://storage.com/archive.zip"
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="bg-white shadow sm:rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <h3 className="text-lg font-medium leading-6 text-gray-900">
          {initialData ? 'Edit Project' : 'Create Project'}
        </h3>
        <form onSubmit={form.handleSubmit(onSubmit)} className="mt-5 space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700">Project Name</label>
            <input
              type="text"
              {...form.register('name')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Description</label>
            <input
              type="text"
              {...form.register('description')}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Hackathon</label>
            <Listbox value={form.watch('hackathon_id')} onChange={(value) => form.setValue('hackathon_id', value)}>
              <div className="relative mt-1">
                <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left border focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 sm:text-sm">
                  <span className="block truncate">
                    {hackathons.find(h => h.id === form.watch('hackathon_id'))?.name || 'Select a hackathon'}
                  </span>
                  <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                    <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                  </span>
                </Listbox.Button>
                <Listbox.Options className="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                  {hackathons.map((hackathon) => (
                    <Listbox.Option
                      key={hackathon.id}
                      value={hackathon.id}
                      className={({ active }) =>
                        `relative cursor-default select-none py-2 pl-10 pr-4 ${
                          active ? 'bg-indigo-100 text-indigo-900' : 'text-gray-900'
                        }`
                      }
                    >
                      {({ selected }) => (
                        <>
                          <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                            {hackathon.name}
                          </span>
                          {selected ? (
                            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-indigo-600">
                              <CheckIcon className="h-5 w-5" aria-hidden="true" />
                            </span>
                          ) : null}
                        </>
                      )}
                    </Listbox.Option>
                  ))}
                </Listbox.Options>
              </div>
            </Listbox>
          </div>

          {templates && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Project Template</label>
              <Listbox value={form.watch('project_template_id')} onChange={(value) => form.setValue('project_template_id', value)}>
                <div className="relative mt-1">
                  <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left border focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 sm:text-sm">
                    <span className="block truncate">
                      {templates.find(t => t.id === form.watch('project_template_id'))?.name || 'Select a template'}
                    </span>
                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                      <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                    </span>
                  </Listbox.Button>
                  <Listbox.Options className="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                    {templates.map((template) => (
                      <Listbox.Option
                        key={template.id}
                        value={template.id}
                        className={({ active }) =>
                          `relative cursor-default select-none py-2 pl-10 pr-4 ${
                            active ? 'bg-indigo-100 text-indigo-900' : 'text-gray-900'
                          }`
                        }
                      >
                        {({ selected }) => (
                          <>
                            <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                              {template.name}
                            </span>
                            {selected ? (
                              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-indigo-600">
                                <CheckIcon className="h-5 w-5" aria-hidden="true" />
                              </span>
                            ) : null}
                          </>
                        )}
                      </Listbox.Option>
                    ))}
                  </Listbox.Options>
                </div>
              </Listbox>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700">Status</label>
            <Listbox value={form.watch('status')} onChange={(value) => form.setValue('status', value)}>
              <div className="relative mt-1">
                <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left border focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 sm:text-sm">
                  <span className="block truncate">{form.watch('status')}</span>
                  <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                    <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                  </span>
                </Listbox.Button>
                <Listbox.Options className="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                  {['draft', 'active', 'completed', 'archived', 'failed', 'building', 'built', 'deploying', 'deployed'].map((status) => (
                    <Listbox.Option
                      key={status}
                      value={status}
                      className={({ active }) =>
                        `relative cursor-default select-none py-2 pl-10 pr-4 ${
                          active ? 'bg-indigo-100 text-indigo-900' : 'text-gray-900'
                        }`
                      }
                    >
                      {({ selected }) => (
                        <>
                          <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                            {status}
                          </span>
                          {selected ? (
                            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-indigo-600">
                              <CheckIcon className="h-5 w-5" aria-hidden="true" />
                            </span>
                          ) : null}
                        </>
                      )}
                    </Listbox.Option>
                  ))}
                </Listbox.Options>
              </div>
            </Listbox>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Storage Type</label>
            <Listbox
              value={form.watch('storage_type')}
              onChange={(value) => {
                form.setValue('storage_type', value);
                setSelectedStorageType(value);
              }}
            >
              <div className="relative mt-1">
                <Listbox.Button className="relative w-full cursor-default rounded-lg bg-white py-2 pl-3 pr-10 text-left border focus:outline-none focus-visible:border-indigo-500 focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-opacity-75 focus-visible:ring-offset-2 focus-visible:ring-offset-orange-300 sm:text-sm">
                  <span className="block truncate">{form.watch('storage_type')}</span>
                  <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                    <ChevronUpDownIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
                  </span>
                </Listbox.Button>
                <Listbox.Options className="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm">
                  {[
                    'github', 'gitlab', 'bitbucket', 'local',
                    'server', 'docker', 'kubernetes', 'cloud',
                    'archive', 'docker_archive', 'backup',
                    'hybrid', 'docker_hybrid'
                  ].map((type) => (
                    <Listbox.Option
                      key={type}
                      value={type}
                      className={({ active }) =>
                        `relative cursor-default select-none py-2 pl-10 pr-4 ${
                          active ? 'bg-indigo-100 text-indigo-900' : 'text-gray-900'
                        }`
                      }
                    >
                      {({ selected }) => (
                        <>
                          <span className={`block truncate ${selected ? 'font-medium' : 'font-normal'}`}>
                            {type}
                          </span>
                          {selected ? (
                            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-indigo-600">
                              <CheckIcon className="h-5 w-5" aria-hidden="true" />
                            </span>
                          ) : null}
                        </>
                      )}
                    </Listbox.Option>
                  ))}
                </Listbox.Options>
              </div>
            </Listbox>
          </div>

          {renderStorageFields()}

          <div className="pt-5">
            <button
              type="submit"
              className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              {initialData ? 'Update Project' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
} 