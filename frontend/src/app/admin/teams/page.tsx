'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import axiosInstance from '@/lib/axiosInstance';

interface TeamMember {
  user_id: string;
  role: string;
  // Add other relevant TeamMember fields if needed for display, e.g., user email/name
}

interface Team {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  members: TeamMember[]; // Assuming members are part of TeamRead schema as per schema file
}

type UserWithRoleAndAccessToken = { role?: string; accessToken?: string };

export default function AdminManageTeamsPage() {
  const { data: session, status: sessionStatus } = useSession();
  const router = useRouter();
  const [teams, setTeams] = useState<Team[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [isLoadingDelete, setIsLoadingDelete] = useState<string | null>(null);

  const fetchTeams = useCallback(async () => {
    if (sessionStatus === 'authenticated') {
      setIsLoading(true);
      setError(null);
      try {
        const token = (session?.user as UserWithRoleAndAccessToken)
          ?.accessToken;
        const response = await axiosInstance.get('/teams/', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setTeams(response.data);
      } catch (err: unknown) {
        console.error('Error fetching teams:', err);
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
                  : 'Failed to fetch teams.'),
            );
          }
        } else {
          setError(
            err &&
              typeof err === 'object' &&
              'message' in err &&
              typeof (err as { message?: string }).message === 'string'
              ? (err as { message: string }).message
              : 'Failed to fetch teams.',
          );
        }
      } finally {
        setIsLoading(false);
      }
    }
  }, [session, sessionStatus]);

  useEffect(() => {
    if (sessionStatus === 'authenticated') {
      if ((session?.user as UserWithRoleAndAccessToken)?.role === 'admin') {
        fetchTeams();
      } else {
        setError(
          'Access Denied: You do not have permission to view this page.',
        );
        setIsLoading(false);
      }
    } else if (sessionStatus === 'unauthenticated') {
      // router.push('/auth/signin');
    }
  }, [sessionStatus, session, router, fetchTeams]);

  const handleDeleteTeam = async (teamId: string, teamName: string) => {
    if (
      window.confirm(
        `Are you sure you want to delete team "${teamName}"? This action cannot be undone.`,
      )
    ) {
      setIsLoadingDelete(teamId);
      setError(null);
      setSuccessMessage(null);
      try {
        const token = (session?.user as UserWithRoleAndAccessToken)
          ?.accessToken;
        if (!token) throw new Error('Token not available');

        await axiosInstance.delete(`/teams/${teamId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSuccessMessage(`Team "${teamName}" deleted successfully.`);
        fetchTeams();
      } catch (err: unknown) {
        console.error('Error deleting team:', err);
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
                  : 'Failed to delete team.'),
            );
          }
        } else {
          setError(
            err &&
              typeof err === 'object' &&
              'message' in err &&
              typeof (err as { message?: string }).message === 'string'
              ? (err as { message: string }).message
              : 'Failed to delete team.',
          );
        }
      } finally {
        setIsLoadingDelete(null);
      }
    }
  };

  if (sessionStatus === 'loading' || isLoading) {
    return (
      <div className="container mx-auto p-4 text-center">Loading teams...</div>
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
    // This should be caught by useEffect redirect or error, but as a fallback:
    return (
      <div className="container mx-auto p-4 text-center">Access Denied.</div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Manage Teams</h1>
        <Link href="/admin" className="text-blue-500 hover:underline">
          &larr; Back to Admin Dashboard
        </Link>
      </div>

      {successMessage && (
        <div className="mb-4 p-3 text-center text-green-700 bg-green-100 border border-green-400 rounded">
          {successMessage}
        </div>
      )}

      {/* Optional: Add Team Button 
      <div className="mb-4">
        <Link href="/admin/teams/create" legacyBehavior>
          <a className="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded">
            Create New Team
          </a>
        </Link>
      </div>
      */}

      {teams.length === 0 ? (
        <p>No teams found.</p>
      ) : (
        <div className="overflow-x-auto shadow-md sm:rounded-lg">
          <table className="min-w-full text-sm text-left text-gray-500 dark:text-gray-400">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
              <tr>
                <th scope="col" className="px-6 py-3">
                  Name
                </th>
                <th scope="col" className="px-6 py-3">
                  Description
                </th>
                <th scope="col" className="px-6 py-3">
                  Members
                </th>
                <th scope="col" className="px-6 py-3">
                  Created At
                </th>
                <th scope="col" className="px-6 py-3">
                  Updated At
                </th>
                <th scope="col" className="px-6 py-3 text-center">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team) => (
                <tr
                  key={team.id}
                  className="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                  <td className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    {team.name}
                  </td>
                  <td className="px-6 py-4">{team.description || 'N/A'}</td>
                  <td className="px-6 py-4">{team.members?.length || 0}</td>
                  <td className="px-6 py-4">
                    {new Date(team.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4">
                    {new Date(team.updated_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Link
                      href={`/admin/teams/edit/${team.id}`}
                      className="font-medium text-blue-600 dark:text-blue-500 hover:underline mr-3"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDeleteTeam(team.id, team.name)}
                      className="font-medium text-red-600 dark:text-red-500 hover:underline"
                      disabled={isLoadingDelete === team.id}
                    >
                      {isLoadingDelete === team.id ? 'Deleting...' : 'Delete'}
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
