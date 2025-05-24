'use client';

import React, { useState, useEffect, FormEvent, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import axiosInstance from '../../../../../lib/axiosInstance';

interface TeamUpdateData {
  name?: string;
  description?: string | null;
}

interface Team extends TeamUpdateData { // For state holding fetched team data
    id: string;
    // Add other fields if needed from TeamRead, like created_at, etc.
}

export default function EditTeamPage() {
  const { data: session, status: sessionStatus } = useSession();
  const params = useParams();
  const router = useRouter();
  const teamId = params?.id as string;

  const [team, setTeam] = useState<Team | null>(null); // Full team data for reference
  const [formData, setFormData] = useState<TeamUpdateData>({ name: '', description: '' });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchTeam = useCallback(async () => {
    if (sessionStatus === 'authenticated' && teamId && (session?.user as any)?.role === 'admin') {
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);
      try {
        const token = (session?.user as any)?.accessToken;
        if (!token) throw new Error("Token not available");

        const response = await axiosInstance.get(`/teams/${teamId}`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        setTeam(response.data); // Store full fetched team data
        setFormData({ // Initialize form with fetched data
          name: response.data.name,
          description: response.data.description || '',
        });
      } catch (err: any) {
        console.error("Error fetching team:", err);
        if (err.response?.status !== 401) {
            setError(err.response?.data?.detail || err.message || 'Failed to fetch team details.');
        }
      } finally {
        setIsLoading(false);
      }
    }
  }, [sessionStatus, teamId, session]);

  useEffect(() => {
    if (sessionStatus === 'authenticated') {
      if ((session?.user as any)?.role === 'admin') {
        if (teamId) {
          fetchTeam();
        } else {
          setError("Team ID is missing.");
          setIsLoading(false);
        }
      } else {
        setError("Access Denied: You do not have admin privileges.");
        setIsLoading(false);
      }
    } else if (sessionStatus === 'unauthenticated') {
      // router.push('/auth/signin'); // Interceptor should handle
    }
  }, [sessionStatus, session, teamId, router, fetchTeam]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!session || (session?.user as any)?.role !== 'admin' || !team) {
      setError("Permission denied or team data not loaded.");
      return;
    }
    
    setIsLoading(true);

    try {
      const token = (session?.user as any)?.accessToken;
      if (!token) throw new Error("Token not available");

      const payload: TeamUpdateData = {};
      if (formData.name !== team.name) payload.name = formData.name;
      if (formData.description !== (team.description || '')) payload.description = formData.description;

      if (Object.keys(payload).length === 0) {
        setSuccessMessage("No changes detected.");
        setIsLoading(false);
        return;
      }

      await axiosInstance.put(`/teams/${teamId}`, payload, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      setSuccessMessage('Team updated successfully!');
      fetchTeam();
    } catch (err: any) {
      console.error("Error updating team:", err);
      if (err.response?.status !== 401) {
        setError(err.response?.data?.detail || err.message || 'Failed to update team.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (sessionStatus === 'loading' || (isLoading && !error && !successMessage)) {
    return <div className="container mx-auto p-4 text-center">Loading team data...</div>;
  }

  if (error) {
    return <div className="container mx-auto p-4 text-center text-red-500">Error: {error}</div>;
  }

  if (!team && !isLoading) { // If not loading and team is still null
    return <div className="container mx-auto p-4 text-center">Team not found or access denied.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
         <h1 className="text-2xl font-bold">Edit Team: {team?.name || 'Loading...'}</h1>
         <Link href="/admin/teams" className="text-blue-500 hover:underline">
            &larr; Back to Team List
         </Link>
      </div>
      
      {successMessage && <p className="text-green-500 text-sm mt-2 mb-4">{successMessage}</p>}

      {team && (
        <form onSubmit={handleSubmit} className="space-y-6 bg-white p-8 shadow-md rounded-lg">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700">Team Name</label>
            <input
              type="text"
              name="name"
              id="name"
              value={formData.name || ''}
              onChange={handleChange}
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700">Description</label>
            <textarea
              name="description"
              id="description"
              rows={4}
              value={formData.description || ''}
              onChange={handleChange}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
} 