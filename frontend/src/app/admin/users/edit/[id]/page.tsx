'use client';

import React, { useState, useEffect, FormEvent, useCallback } from 'react';
import { useSession } from 'next-auth/react';
import { useParams, useRouter } from 'next/navigation';
import axiosInstance from '@/lib/axiosInstance'; // MODIFIED: Use axiosInstance with path alias

interface User {
  id: string;
  email: string;
  username: string;
  full_name: string | null;
  roles: string[];
  is_active: boolean;
}

interface UserUpdateData {
  username?: string;
  full_name?: string | null;
  // roles field is no longer sent in the PUT request for user update
  is_active?: boolean;
}

interface AvailableRole {
  name: string;
  description?: string; // Assuming backend might provide descriptions, or we use a default
}

// Role descriptions for the UI (can be a fallback or merged with fetched data)
const ROLE_UI_DESCRIPTIONS: { [key: string]: string } = {
  admin: "Full system access",
  organizer: "Can manage hackathons and participants",
  judge: "Can evaluate projects and assign scores",
  mentor: "Can provide guidance to participants",
  participant: "Regular user who can join hackathons"
};

type UserWithRoleAndAccessToken = { role?: string; accessToken?: string };

export default function EditUserPage() {
  const { data: session, status: sessionStatus } = useSession();
  const params = useParams();
  const router = useRouter();
  const userId = params?.id as string;

  const [user, setUser] = useState<User | null>(null);
  const [initialRoles, setInitialRoles] = useState<string[]>([]);
  const [formData, setFormData] = useState<{
    username: string;
    full_name: string | null;
    roles: string[];
    is_active: boolean;
  }>({
    username: '',
    full_name: '',
    roles: [],
    is_active: true,
  });
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchUserData = useCallback(async () => {
    if (
      sessionStatus === 'authenticated' &&
      userId &&
      (session?.user as UserWithRoleAndAccessToken)?.role === 'admin'
    ) {
      setIsLoading(true);
      setError(null);
      setSuccessMessage(null);
      try {
        // axiosInstance should handle token if configured, otherwise pass manually
        const token = (session?.user as UserWithRoleAndAccessToken)?.accessToken;

        const userResponse = await axiosInstance.get(`/users/${userId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setUser(userResponse.data);
        setInitialRoles(userResponse.data.roles || []);
        setFormData({
          username: userResponse.data.username,
          full_name: userResponse.data.full_name || '',
          roles: userResponse.data.roles || [],
          is_active: userResponse.data.is_active,
        });

        const rolesResponse = await axiosInstance.get('/users/roles', {
            headers: { Authorization: `Bearer ${token}` },
        });
        setAvailableRoles(rolesResponse.data || []);

      } catch (err: any) {
        console.error('Error fetching data:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to fetch user details or roles.');
      } finally {
        setIsLoading(false);
      }
    } else if (sessionStatus === 'loading') {
      // Wait
    } else if (!userId) {
      setError('User ID is missing.');
      setIsLoading(false);
    } else {
      setError('Access Denied or Session expired.');
      setIsLoading(false);
    }
  }, [sessionStatus, userId, session]);

  useEffect(() => {
    fetchUserData();
  }, [fetchUserData]);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value, type } = e.target;

    if (type === 'checkbox' && name === 'is_active') { // Specific handling for is_active
      const { checked } = e.target as HTMLInputElement;
      setFormData((prev) => ({ ...prev, is_active: checked }));
    } else if (name === 'roles') { // This case should not happen with current checkbox setup
        // Role checkboxes are handled by handleRoleChange
    }
    else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleRoleChange = (role: string, isChecked: boolean) => {
    setFormData((prev) => {
      const newRoles = isChecked
        ? [...prev.roles, role]
        : prev.roles.filter((r) => r !== role);
      return { ...prev, roles: newRoles };
    });
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    if (
      !session ||
      (session?.user as UserWithRoleAndAccessToken)?.role !== 'admin' ||
      !user
    ) {
      setError('Permission denied or user data not loaded.');
      setIsSaving(false);
      return;
    }

    const token = (session?.user as UserWithRoleAndAccessToken)?.accessToken;
    if (!token) {
        setError('Access token not available.');
        setIsSaving(false);
        return;
    }

    try {
      // 1. Update basic user info (username, full_name, is_active)
      const profileUpdatePayload: UserUpdateData = {};
      if (formData.username !== user.username)
        profileUpdatePayload.username = formData.username;
      if (formData.full_name !== user.full_name)
        profileUpdatePayload.full_name = formData.full_name;
      if (formData.is_active !== user.is_active)
        profileUpdatePayload.is_active = formData.is_active;
      
      if (Object.keys(profileUpdatePayload).length > 0) {
        await axiosInstance.put(`/users/${userId}`, profileUpdatePayload, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }

      // 2. Update roles
      const rolesToAdd = formData.roles.filter(r => !initialRoles.includes(r));
      const rolesToRemove = initialRoles.filter(r => !formData.roles.includes(r));

      for (const role of rolesToAdd) {
        await axiosInstance.post(`/users/${userId}/roles`, { role }, { // Backend expects { "role": "rolename" }
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      for (const role of rolesToRemove) {
        // For DELETE, data is often in the body for FastAPI if using Pydantic model
        await axiosInstance.delete(`/users/${userId}/roles`, {
          headers: { Authorization: `Bearer ${token}` },
          data: { role }, // Backend expects { "role": "rolename" }
        });
      }
      
      setSuccessMessage('User updated successfully!');
      fetchUserData(); // Refresh data to show updated state and reset initialRoles

    } catch (err: any) {
      console.error('Error updating user:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to update user.');
    } finally {
      setIsSaving(false);
    }
  };

  if (sessionStatus === 'loading' || (isLoading && !error)) {
    return (
      <div className="container mx-auto p-4 text-center">
        Loading user data...
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

  if (!user) {
    return (
      <div className="container mx-auto p-4 text-center">
        User not found or not loaded.
      </div>
    );
  }

  if ((session?.user as UserWithRoleAndAccessToken)?.role !== 'admin') {
    return (
      <div className="container mx-auto p-4 text-center text-red-500">
        Access Denied. You are not an admin.
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <button
        onClick={() => router.back()}
        className="mb-4 text-blue-500 hover:underline"
      >
        &larr; Back to User List
      </button>
      <h1 className="text-2xl font-bold mb-6">Edit User: {user.email}</h1>

      <form
        onSubmit={handleSubmit}
        className="space-y-6 bg-white p-8 shadow-md rounded-lg"
      >
        <div>
          <label
            htmlFor="username"
            className="block text-sm font-medium text-gray-700"
          >
            Username
          </label>
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
          <label
            htmlFor="full_name"
            className="block text-sm font-medium text-gray-700"
          >
            Full Name
          </label>
          <input
            type="text"
            name="full_name"
            id="full_name"
            value={formData.full_name || ''}
            onChange={handleChange}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
          />
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Roles
            </label>
            <div className="space-y-2">
              {availableRoles.length > 0 ? availableRoles.map((role) => (
                <div key={role} className="flex items-start">
                  <div className="flex items-center h-5">
                    <input
                      id={`role-${role}`}
                      name="roles" // Name is "roles" to group them, but individual changes are handled
                      type="checkbox"
                      checked={formData.roles.includes(role)}
                      onChange={(e) => handleRoleChange(role, e.target.checked)}
                      className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
                    />
                  </div>
                  <div className="ml-3 text-sm">
                    <label htmlFor={`role-${role}`} className="font-medium text-gray-700">
                      {role.charAt(0).toUpperCase() + role.slice(1)}
                    </label>
                    <p className="text-gray-500">{ROLE_UI_DESCRIPTIONS[role] || 'Standard role'}</p>
                  </div>
                </div>
              )) : <p>Loading roles...</p>}
            </div>
          </div>
        </div>
        <div className="flex items-center">
          <input
            id="is_active"
            name="is_active" // Corrected name to match state and handleChange
            type="checkbox"
            checked={formData.is_active}
            onChange={handleChange} // General handleChange can handle this now
            className="h-4 w-4 text-indigo-600 border-gray-300 rounded focus:ring-indigo-500"
          />
          <label
            htmlFor="is_active"
            className="ml-2 block text-sm text-gray-900"
          >
            Active
          </label>
        </div>
        <div>
          <button
            type="submit"
            disabled={isSaving || isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
        {successMessage && (
          <p className="text-green-500 text-sm mt-2">{successMessage}</p>
        )}
      </form>
    </div>
  );
}
