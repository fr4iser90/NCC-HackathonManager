'use client';

import React, { useState } from 'react';
import { useSession } from 'next-auth/react';
import axiosInstance from '../lib/axiosInstance';

type HackathonMode = 'SOLO_ONLY' | 'TEAM_ONLY';

interface CreateHackathonModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export default function CreateHackathonModal({
  isOpen,
  onClose,
  onSuccess,
}: CreateHackathonModalProps) {
  const { data: session, status } = useSession();

  // Basic fields
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [mode, setMode] = useState<HackathonMode>('SOLO_ONLY');
  const [location, setLocation] = useState('');
  const [requirements, setRequirements] = useState('');
  const [category, setCategory] = useState('');
  const [tags, setTags] = useState('');
  const [maxTeamSize, setMaxTeamSize] = useState('');
  const [minTeamSize, setMinTeamSize] = useState('');
  const [registrationDeadline, setRegistrationDeadline] = useState('');
  const [isPublic, setIsPublic] = useState(true);
  const [bannerImageUrl, setBannerImageUrl] = useState('');
  const [rulesUrl, setRulesUrl] = useState('');
  const [sponsor, setSponsor] = useState('');
  const [prizes, setPrizes] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [allowIndividuals, setAllowIndividuals] = useState(true);
  const [allowMultipleProjects, setAllowMultipleProjects] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim() || !startDate || !endDate) {
      setError('Please fill in all required fields.');
      return;
    }
    if (new Date(startDate) >= new Date(endDate)) {
      setError('Start date must be before end date.');
      return;
    }

    if (status !== 'authenticated') {
      setError('You must be logged in to create a hackathon.');
      return;
    }

    setIsLoading(true);
    try {
      const token = (session?.user as any)?.accessToken;
      if (!token) throw new Error('No access token found.');

      const payload = {
        name,
        description: description || null,
        start_date: startDate,
        end_date: endDate,
        status: "upcoming",
        mode,
        location: location || null,
        requirements: requirements
          ? requirements.split('\n').map((r) => r.trim()).filter(Boolean)
          : [],
        category: category || null,
        tags: tags
          ? tags.split(',').map((t) => t.trim()).filter(Boolean)
          : [],
        max_team_size: mode === 'TEAM_ONLY' && maxTeamSize ? Number(maxTeamSize) : null,
        min_team_size: mode === 'TEAM_ONLY' && minTeamSize ? Number(minTeamSize) : null,
        registration_deadline: registrationDeadline || null,
        is_public: isPublic,
        banner_image_url: bannerImageUrl || null,
        rules_url: rulesUrl || null,
        sponsor: sponsor || null,
        prizes: prizes || null,
        contact_email: contactEmail || null,
        allow_individuals: allowIndividuals,
        allow_multiple_projects_per_team: allowMultipleProjects,
        custom_fields: null,
      };

      await axiosInstance.post(
        '/hackathons/',
        payload,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      setSuccess(true);
      if (onSuccess) onSuccess();
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 1500);
    } catch (err: any) {
      let msg = 'An error occurred';
      if (err?.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          msg = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail) && err.response.data.detail.length > 0) {
          msg = JSON.stringify(err.response.data.detail);
        }
      } else if (typeof err?.message === 'string') {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50 overflow-y-auto">
      <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-xl w-full max-w-2xl max-h-[95vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            Create New Hackathon
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
            disabled={isLoading}
          >
            &times;
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="name">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                id="name"
                type="text"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                disabled={isLoading}
                maxLength={255}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="category">
                Category
              </label>
              <input
                id="category"
                type="text"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="start">
                Start Date <span className="text-red-500">*</span>
              </label>
              <input
                id="start"
                type="datetime-local"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="end">
                End Date <span className="text-red-500">*</span>
              </label>
              <input
                id="end"
                type="datetime-local"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="mode">
                Mode <span className="text-red-500">*</span>
              </label>
              <select
                id="mode"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={mode}
                onChange={(e) => setMode(e.target.value as HackathonMode)}
                disabled={isLoading}
                required
              >
                <option value="SOLO_ONLY">Solo</option>
                <option value="TEAM_ONLY">Team</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="location">
                Location
              </label>
              <input
                id="location"
                type="text"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="registrationDeadline">
                Registration Deadline
              </label>
              <input
                id="registrationDeadline"
                type="datetime-local"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={registrationDeadline}
                onChange={(e) => setRegistrationDeadline(e.target.value)}
                disabled={isLoading}
              />
            </div>
            {mode === "TEAM_ONLY" && (
              <>
                <div>
                  <label className="block text-sm font-medium mb-1" htmlFor="maxTeamSize">
                    Max Team Size
                  </label>
                  <input
                    id="maxTeamSize"
                    type="number"
                    min="1"
                    className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                    value={maxTeamSize}
                    onChange={(e) => setMaxTeamSize(e.target.value)}
                    disabled={isLoading}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1" htmlFor="minTeamSize">
                    Min Team Size
                  </label>
                  <input
                    id="minTeamSize"
                    type="number"
                    min="1"
                    className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                    value={minTeamSize}
                    onChange={(e) => setMinTeamSize(e.target.value)}
                    disabled={isLoading}
                  />
                </div>
              </>
            )}
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="tags">
                Tags (comma separated)
              </label>
              <input
                id="tags"
                type="text"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div className="flex items-center gap-2 mt-6">
              <input
                id="isPublic"
                type="checkbox"
                checked={isPublic}
                onChange={(e) => setIsPublic(e.target.checked)}
                disabled={isLoading}
              />
              <label htmlFor="isPublic" className="text-sm font-medium">
                Public
              </label>
            </div>
          </div>
          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="description">
              Description
            </label>
            <textarea
              id="description"
              className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              disabled={isLoading}
            />
          </div>
          {/* Requirements */}
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="requirements">
              Requirements (one per line)
            </label>
            <textarea
              id="requirements"
              className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              rows={2}
              disabled={isLoading}
            />
          </div>
          {/* Media & Links */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="bannerImageUrl">
                Banner Image URL
              </label>
              <input
                id="bannerImageUrl"
                type="text"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={bannerImageUrl}
                onChange={(e) => setBannerImageUrl(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="rulesUrl">
                Rules URL
              </label>
              <input
                id="rulesUrl"
                type="text"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={rulesUrl}
                onChange={(e) => setRulesUrl(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="sponsor">
                Sponsor
              </label>
              <input
                id="sponsor"
                type="text"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={sponsor}
                onChange={(e) => setSponsor(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="prizes">
                Prizes
              </label>
              <input
                id="prizes"
                type="text"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={prizes}
                onChange={(e) => setPrizes(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1" htmlFor="contactEmail">
                Contact Email
              </label>
              <input
                id="contactEmail"
                type="email"
                className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white"
                value={contactEmail}
                onChange={(e) => setContactEmail(e.target.value)}
                disabled={isLoading}
              />
            </div>
            <div className="flex items-center gap-2 mt-6">
              <input
                id="allowIndividuals"
                type="checkbox"
                checked={allowIndividuals}
                onChange={(e) => setAllowIndividuals(e.target.checked)}
                disabled={isLoading}
              />
              <label htmlFor="allowIndividuals" className="text-sm font-medium">
                Allow Individuals
              </label>
            </div>
            <div className="flex items-center gap-2 mt-6">
              <input
                id="allowMultipleProjects"
                type="checkbox"
                checked={allowMultipleProjects}
                onChange={(e) => setAllowMultipleProjects(e.target.checked)}
                disabled={isLoading}
              />
              <label htmlFor="allowMultipleProjects" className="text-sm font-medium">
                Allow Multiple Projects per Team
              </label>
            </div>
          </div>
          {error && (
            <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
          )}
          {success && (
            <p className="text-sm text-green-600 dark:text-green-400">
              Hackathon created!
            </p>
          )}
          <div className="flex justify-end gap-2 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md dark:bg-slate-700 dark:text-gray-300 dark:hover:bg-slate-600"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-70"
              disabled={isLoading}
            >
              {isLoading ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
