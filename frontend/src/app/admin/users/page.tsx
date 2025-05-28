'use client'; // Required for useState, useEffect, onClick

import React, { useState, useEffect, useCallback } from 'react'; // Added useCallback
import { useSession } from 'next-auth/react';
import axiosInstance from '@/lib/axiosInstance'; // MODIFIED: Corrected import path
import axios from 'axios';
import Link from 'next/link';
import { useRouter } from 'next/navigation'; // Added for potential redirects

// Define a type for the user data we expect from the API
interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  roles: string[];  // Changed from role to roles array
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

type UserWithRoleAndAccessToken = { role?: string; accessToken?: string };

export default function AdminManageUsersPage() {
  // Renamed component
  const { data: session, status } = useSession();
  const router = useRouter(); // Added router
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingDelete, setIsLoadingDelete] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL; // REMOVED: Handled by axiosInstance

  // Wrapped fetchUsers in useCallback as it's in dependency array of useEffect
  const fetchUsers = useCallback(async () => {
    if (
      status === 'authenticated' &&
      (session?.user as UserWithRoleAndAccessToken)?.role === 'admin'
    ) {
      setIsLoading(true);
      setError(null);
      try {
        const token = (session?.user as UserWithRoleAndAccessToken)
          ?.accessToken;
        if (!token) throw new Error('Access token is not available.');

        const response = await axiosInstance.get('/users/', {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUsers(response.data);
      } catch (err: any) { // Changed to any for easier error handling
        console.error('Error fetching users:', err);
        let errorMessage = 'Failed to fetch users.';
        if (axios.isAxiosError(err)) {
          if (err.response?.data?.detail) {
            if (typeof err.response.data.detail === 'string') {
              errorMessage = err.response.data.detail;
            } else {
              // If detail is an object/array (like Pydantic validation errors)
              errorMessage = `Error details: ${JSON.stringify(err.response.data.detail)}`;
            }
          } else if (err.message) {
            errorMessage = err.message;
          }
          // Do not set error for 401, as it might be handled by session status or redirect
          if (err.response?.status !== 401) {
            setError(errorMessage);
          }
        } else if (err instanceof Error) {
          errorMessage = err.message;
          setError(errorMessage);
        } else {
          setError(errorMessage);
        }
      } finally {
        setIsLoading(false);
      }
    }
  }, [session, status]); // REMOVED apiBaseUrl from dependencies

  useEffect(() => {
    if (status === 'authenticated') {
      if ((session?.user as UserWithRoleAndAccessToken)?.role === 'admin') {
        fetchUsers();
      } else {
        setError('Access Denied: You do not have admin privileges.');
        setIsLoading(false);
      }
    } else if (status === 'unauthenticated') {
      // Let NextAuth.js handle redirect via middleware or interceptor will catch 401 if API is hit
      // router.push('/auth/signin'); // Commented out, interceptor + NextAuth should handle
    }
  }, [session, status, router, fetchUsers]);

  const handleDelete = async (userId: string, userEmail: string) => {
    if (
      window.confirm(
        `Are you sure you want to delete user ${userEmail}? This action cannot be undone.`,
      )
    ) {
      setIsLoadingDelete(userId);
      setError(null);
      setSuccessMessage(null);
      try {
        const token = (session?.user as UserWithRoleAndAccessToken)
          ?.accessToken;
        if (!token) throw new Error('Access token is not available.');

        await axiosInstance.delete(`/users/${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSuccessMessage(`User ${userEmail} deleted successfully.`);
        fetchUsers(); // Refresh the user list
      } catch (err: any) { // Changed to any for easier error handling
        console.error('Error deleting user:', err);
        let errorMessage = 'Failed to delete user.';
        if (axios.isAxiosError(err)) {
          if (err.response?.data?.detail) {
            if (typeof err.response.data.detail === 'string') {
              errorMessage = err.response.data.detail;
            } else {
              errorMessage = `Error details: ${JSON.stringify(err.response.data.detail)}`;
            }
          } else if (err.message) {
            errorMessage = err.message;
          }
           // Do not set error for 401
          if (err.response?.status !== 401) {
            setError(errorMessage);
          }
        } else if (err instanceof Error) {
          errorMessage = err.message;
          setError(errorMessage);
        } else {
          setError(errorMessage);
        }
      } finally {
        setIsLoadingDelete(null);
      }
    }
  };

  if (status === 'loading' || isLoading) {
    return (
      <div className="container mx-auto py-8 text-center">
        Loading user data...
      </div>
    ); // Changed message
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 text-center text-red-500">
        Error: {error}
      </div>
    );
  }

  if (
    !session ||
    (session.user as UserWithRoleAndAccessToken)?.role !== 'admin'
  ) {
    return (
      <div className="container mx-auto py-8 text-center">Access Denied.</div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Manage Users</h1>
        <Link href="/admin" className="text-blue-500 hover:underline">
          &larr; Back to Admin Dashboard
        </Link>
      </div>
      {successMessage && (
        <div className="mb-4 p-3 text-center text-green-700 bg-green-100 border border-green-400 rounded">
          {successMessage}
        </div>
      )}
      <h2 className="text-2xl font-semibold mb-4 mt-8">User List</h2>{' '}
      {/* Changed from User Management */}
      {users.length === 0 && !isLoading && (
        <p>No users found.</p> // Simplified message
      )}
      {users.length > 0 && (
        <div className="overflow-x-auto shadow-md sm:rounded-lg">
          <table className="min-w-full text-sm text-left text-gray-500 dark:text-gray-400">
            <thead className="text-xs text-gray-700 uppercase bg-gray-50 dark:bg-gray-700 dark:text-gray-400">
              <tr>
                <th scope="col" className="px-6 py-3">Email</th>
                <th scope="col" className="px-6 py-3">Username</th>
                <th scope="col" className="px-6 py-3">Full Name</th>
                <th scope="col" className="px-6 py-3">Roles</th>
                <th scope="col" className="px-6 py-3">Active</th>
                <th scope="col" className="px-6 py-3">Joined</th>
                <th scope="col" className="px-6 py-3 text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id} className="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600">
                  <td className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap dark:text-white">
                    {user.email}
                  </td>
                  <td className="px-6 py-4">{user.username}</td>
                  <td className="px-6 py-4">{user.full_name || 'N/A'}</td>
                  <td className="px-6 py-4">
                    <div className="flex flex-wrap gap-1">
                      {user.roles.map((role) => (
                        <span
                          key={role}
                          className="px-2 py-1 text-xs font-medium rounded-full"
                          style={{
                            backgroundColor: role === 'admin' ? '#EF4444' : 
                                           role === 'organizer' ? '#3B82F6' :
                                           role === 'judge' ? '#10B981' :
                                           role === 'mentor' ? '#8B5CF6' :
                                           '#6B7280',
                            color: 'white'
                          }}
                        >
                          {role.charAt(0).toUpperCase() + role.slice(1)}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4">{user.is_active ? 'Yes' : 'No'}</td>
                  <td className="px-6 py-4">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-center">
                    <Link
                      href={`/admin/users/edit/${user.id}`}
                      className="font-medium text-blue-600 dark:text-blue-500 hover:underline mr-3"
                    >
                      Edit
                    </Link>
                    <button
                      onClick={() => handleDelete(user.id, user.email)}
                      className="font-medium text-red-600 dark:text-red-500 hover:underline"
                      disabled={isLoadingDelete === user.id}
                    >
                      {isLoadingDelete === user.id ? 'Deleting...' : 'Delete'}
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
