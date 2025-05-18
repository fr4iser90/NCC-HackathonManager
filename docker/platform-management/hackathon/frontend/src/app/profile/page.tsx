'use client';

import { useState, useEffect, FormEvent, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

// Utility: Entfernt leere Felder aus dem Payload
function cleanPayload(obj: Record<string, any>) {
  return Object.fromEntries(
    Object.entries(obj).filter(([_, v]) => v !== '' && v !== undefined && v !== null)
  );
}

export default function ProfilePage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    current_password: '',
    new_password: '',
    confirm_new_password: '',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (status === 'authenticated') {
      const fetchProfile = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const token = (session?.user as any)?.accessToken;
          const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me`, {
            headers: { 'Authorization': `Bearer ${token}` },
          });
          if (!res.ok) throw new Error('Failed to load profile');
          const data: any = await res.json();
          setFormData({
            email: data.email,
            username: data.username,
            full_name: data.full_name || '',
            current_password: '',
            new_password: '',
            confirm_new_password: '',
          });
          if (data.avatar_url) {
            setAvatarUrl(data.avatar_url);
          } else {
            setAvatarUrl(null);
          }
        } catch (err: any) {
          setError(err.message || 'Failed to load profile');
        } finally {
          setIsLoading(false);
        }
      };
      fetchProfile();
    }
  }, [status, session]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (["current_password", "new_password", "confirm_new_password"].includes(name)) {
      setError(null);
      setSuccess(false);
    }
  };

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAvatarFile(file);
      setAvatarPreview(URL.createObjectURL(file));
    }
  };

  const handleAvatarRemove = () => {
    setAvatarFile(null);
    setAvatarPreview(null);
    setAvatarUrl(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError(null);
    setSuccess(false);
    if (formData.new_password) {
      if (!formData.current_password) {
        setError('Bitte aktuelles Passwort eingeben.');
        setIsSaving(false);
        return;
      }
      if (formData.new_password !== formData.confirm_new_password) {
        setError('Die neuen Passwörter stimmen nicht überein.');
        setIsSaving(false);
        return;
      }
    }
    try {
      const token = (session?.user as any)?.accessToken;
      if (avatarFile) {
        const formDataImg = new FormData();
        formDataImg.append('file', avatarFile);
        const resImg = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me/avatar`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
          body: formDataImg,
        });
        if (!resImg.ok) {
          throw new Error('Profilbild-Upload fehlgeschlagen');
        }
        const imgData = await resImg.json();
        setAvatarUrl(imgData.avatar_url);
      }
      let payload: any = {
        username: formData.username,
        full_name: formData.full_name,
      };
      if (formData.new_password && formData.current_password) {
        payload.current_password = formData.current_password;
        payload.password = formData.new_password;
      }
      Object.keys(payload).forEach(
        (key) => (payload[key] === '' || payload[key] === undefined) && delete payload[key]
      );
      console.log('Profile update payload:', payload);
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        let errorMsg = 'Update failed';
        let data: any = {};
        try {
          data = await res.json();
        } catch {}
        if (data && typeof data.detail === 'string') errorMsg = data.detail;
        else if (data && typeof data.detail === 'object') errorMsg = JSON.stringify(data.detail, null, 2);
        else errorMsg = `Fehler: ${res.status} ${res.statusText}`;
        if (res.status === 401 || res.status === 403) {
          setError('Session abgelaufen oder keine Berechtigung. Bitte neu einloggen.');
          // Optional: router.push('/auth/signin');
        } else {
          setError(errorMsg);
        }
        console.error('Profile update error:', { status: res.status, data });
        return;
      }
      setSuccess(true);
      setFormData((prev) => ({
        ...prev,
        current_password: '',
        new_password: '',
        confirm_new_password: '',
      }));
      setAvatarFile(null);
      setAvatarPreview(null);
    } catch (err: any) {
      setError(err.message || 'Update failed');
      console.error('Profile update exception:', err);
    } finally {
      setIsSaving(false);
    }
  };

  if (status === 'loading' || isLoading) {
    return <div className="container mx-auto p-4 text-center">Loading profile...</div>;
  }

  if (error) {
    return <div className="container mx-auto p-4 text-center text-red-500">Error: {error}</div>;
  }

  return (
    <div className="container mx-auto max-w-lg p-4">
      <h1 className="text-2xl font-bold mb-6">My Profile</h1>
      {success && (
        <div className="mb-4 p-3 text-green-700 bg-green-100 border border-green-400 rounded">Profile updated successfully!</div>
      )}
      <form onSubmit={handleSubmit} className="space-y-6 bg-white p-8 shadow-md rounded-lg">
        <div className="flex flex-col items-center mb-6">
          <div className="relative w-24 h-24 mb-2">
            <img
              src={avatarPreview || avatarUrl || `${process.env.NEXT_PUBLIC_API_BASE_URL}/static/default-avatar.svg`}
              alt="Profilbild"
              className="w-24 h-24 rounded-full object-cover border border-gray-300"
            />
            {(avatarUrl || avatarPreview) && (
              <button type="button" onClick={handleAvatarRemove} className="absolute top-0 right-0 bg-white rounded-full p-1 shadow hover:bg-red-100" title="Profilbild entfernen">
                <span className="text-red-500">✕</span>
              </button>
            )}
          </div>
          <input
            type="file"
            accept="image/*"
            ref={fileInputRef}
            onChange={handleAvatarChange}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 text-sm"
          >
            {avatarFile ? 'Anderes Bild wählen' : 'Profilbild ändern'}
          </button>
          {avatarFile && (
            <span className="text-xs text-gray-500 mt-1">Vorschau aktiv – Änderungen speichern nicht vergessen!</span>
          )}
        </div>
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email (read-only)</label>
          <input
            type="email"
            name="email"
            id="email"
            value={formData.email}
            readOnly
            className="mt-1 block w-full bg-gray-100 cursor-not-allowed"
          />
        </div>
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username</label>
          <input
            type="text"
            name="username"
            id="username"
            value={formData.username}
            onChange={handleChange}
            required
            className="mt-1 block w-full"
          />
        </div>
        <div>
          <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">Full Name</label>
          <input
            type="text"
            name="full_name"
            id="full_name"
            value={formData.full_name}
            onChange={handleChange}
            className="mt-1 block w-full"
          />
        </div>
        <div>
          <label htmlFor="new_password" className="block text-sm font-medium text-gray-700">Neues Passwort</label>
          <input
            type="password"
            name="new_password"
            id="new_password"
            value={formData.new_password}
            onChange={handleChange}
            className="mt-1 block w-full"
            autoComplete="new-password"
          />
        </div>
        {formData.new_password && (
          <>
            <div>
              <label htmlFor="confirm_new_password" className="block text-sm font-medium text-gray-700">Neues Passwort bestätigen</label>
              <input
                type="password"
                name="confirm_new_password"
                id="confirm_new_password"
                value={formData.confirm_new_password}
                onChange={handleChange}
                className="mt-1 block w-full"
                autoComplete="new-password"
              />
            </div>
            <div>
              <label htmlFor="current_password" className="block text-sm font-medium text-gray-700">Aktuelles Passwort</label>
              <input
                type="password"
                name="current_password"
                id="current_password"
                value={formData.current_password}
                onChange={handleChange}
                className="mt-1 block w-full"
                autoComplete="current-password"
                required={!!formData.new_password}
              />
            </div>
          </>
        )}
        <div>
          <button
            type="submit"
            disabled={isSaving}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </div>
  );
} 