'use client';

import React, { useState, useEffect, FormEvent } from 'react';
import { useSession } from 'next-auth/react';
import { useParams, useRouter } from 'next/navigation'; // For accessing route params and navigation
import axios from 'axios';

interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
}

// Define a type for the updatable fields
interface UserUpdateData {
  username?: string;
  full_name?: string | null;
  role?: string;
  is_active?: boolean;
}

export default function EditUserPage() {
  const { data: session, status: sessionStatus } = useSession();
  const params = useParams(); // { id: '...' }
  const router = useRouter(); // For navigation
  const userId = params?.id as string;

  const [user, setUser] = useState<User | null>(null);
  const [formData, setFormData] = useState<UserUpdateData>({
    username: '',
    full_name: '',
    role: 'participant', // Default role
    is_active: true,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;

  useEffect(() => {
    if (sessionStatus === 'authenticated' && userId && (session?.user as any)?.role === 'admin') {
      const fetchUser = async () => {
        setIsLoading(true);
        setError(null);
        setSuccessMessage(null);
        try {
          const token = (session?.user as any)?.accessToken;
          if (!apiBaseUrl) throw new Error("API base URL is not configured.");
          if (!token) throw new Error("Access token is not available.");

          const response = await axios.get(`${apiBaseUrl}/users/${userId}`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          setUser(response.data);
          // Initialize form data with fetched user data
          setFormData({
            username: response.data.username,
            full_name: response.data.full_name || '',
            role: response.data.role,
            is_active: response.data.is_active,
          });
        } catch (err: any) {
          console.error("Error fetching user:", err);
          setError(err.response?.data?.detail || err.message || 'Failed to fetch user details.');
        } finally {
          setIsLoading(false);
        }
      };
      fetchUser();
    } else if (sessionStatus === 'loading') {
        // Wait for session to load
    } else if (!userId) {
        setError("User ID is missing.");
        setIsLoading(false);
    }
    else {
      setError("Access Denied or Session expired.");
      setIsLoading(false);
    }
  }, [sessionStatus, userId, session, apiBaseUrl]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
        const { checked } = e.target as HTMLInputElement;
        setFormData(prev => ({ ...prev, [name]: checked }));
    } else {
        setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);

    if (!session || (session?.user as any)?.role !== 'admin' || !user) {
      setError("Permission denied or user data not loaded.");
      setIsLoading(false);
      return;
    }

    try {
      const token = (session?.user as any)?.accessToken;
      if (!apiBaseUrl) throw new Error("API base URL is not configured.");
      if (!token) throw new Error("Access token is not available.");

      // Construct the payload, only send fields that have changed or are part of UserUpdateData
      const payload: UserUpdateData = {};
      if (formData.username !== user.username) payload.username = formData.username;
      if (formData.full_name !== user.full_name) payload.full_name = formData.full_name;
      if (formData.role !== user.role) payload.role = formData.role;
      if (formData.is_active !== user.is_active) payload.is_active = formData.is_active;
      
      // Do not send empty payload
      if (Object.keys(payload).length === 0) {
        setSuccessMessage("No changes detected.");
        setIsLoading(false);
        return;
      }

      await axios.put(`${apiBaseUrl}/users/${userId}`, payload, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      setSuccessMessage('User updated successfully!');
      // Optionally, refresh user data or navigate away
      // router.push('/admin'); 
    } catch (err: any) {
      console.error("Error updating user:", err);
      setError(err.response?.data?.detail || err.message || 'Failed to update user.');
    } finally {
      setIsLoading(false);
    }
  };

  if (sessionStatus === 'loading' || (isLoading && !error)) { // Show loading if session is loading OR if fetching data and no error yet
    return <div className="container mx-auto p-4 text-center">Loading user data...</div>;
  }

  if (error) {
    return <div className="container mx-auto p-4 text-center text-red-500">Error: {error}</div>;
  }

  if (!user) {
    return <div className="container mx-auto p-4 text-center">User not found or not loaded.</div>;
  }
  
  if ((session?.user as any)?.role !== 'admin') {
    return <div className="container mx-auto p-4 text-center text-red-500">Access Denied. You are not an admin.</div>;
  }

  return (
    <div className="container mx-auto p-4">
      <button onClick={() => router.back()} className="mb-4 text-blue-500 hover:underline">
        &larr; Back to User List
      </button>
      <h1 className="text-2xl font-bold mb-6">Edit User: {user.email}</h1>

      <form onSubmit={handleSubmit} className="space-y-6 bg-white p-8 shadow-md rounded-lg">
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username</label>
          <input
            type="text"
            name="username"
            id="username"
            value={formData.username}
            onChange={handleChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div>
          <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">Full Name</label>
          <input
            type="text"
            name="full_name"
            id="full_name"
            value={formData.full_name || ''}
            onChange={handleChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div>
          <label htmlFor="role" className="block text-sm font-medium text-gray-700">Role</label>
          <select
            name="role"
            id="role"
            value={formData.role}
            onChange={handleChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          >
            <option value="participant">Participant</option>
            <option value="admin">Admin</option>
            {/* Add other roles as needed */}
          </select>
        </div>
        <div className="flex items-center">
          <input
            id="is_active"
            name="is_active"
            type="checkbox"
            checked={formData.is_active}
            onChange={handleChange}
            className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
          />
          <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
            Active
          </label>
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
        {successMessage && <p className="text-green-500 text-sm mt-2">{successMessage}</p>}
      </form>
    </div>
  );
} 