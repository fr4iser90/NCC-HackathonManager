'use client';

import React, { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import axiosInstance from '@/lib/axiosInstance';
import type { Hackathon } from '@/types/hackathon';
import HackathonFilterGrid from '@/components/HackathonFilterGrid';
import CreateHackathonModal from '@/components/CreateHackathonModal';

export default function HackathonManagerClient() {
  const { data: session, status } = useSession();
  const [hackathons, setHackathons] = useState<Hackathon[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchHackathons = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = (session?.user as any)?.accessToken;
      const response = await axiosInstance.get('/hackathons/', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      setHackathons(Array.isArray(response.data) ? response.data : []);
    } catch (err: any) {
      setHackathons([]);
      let msg = 'Failed to fetch hackathons';
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
      setLoading(false);
    }
  };

  useEffect(() => {
    if (status === 'authenticated' || status === 'unauthenticated') {
      fetchHackathons();
    }
    // Only fetch after session is loaded
  }, [status]);

  const handleSuccess = () => {
    fetchHackathons();
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Hackathons</h1>
        <button
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded"
          onClick={() => setShowModal(true)}
        >
          + Create Hackathon
        </button>
      </div>
      <CreateHackathonModal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onSuccess={handleSuccess}
      />
      {loading ? (
        <p className="text-gray-600 dark:text-gray-300">Loading...</p>
      ) : error ? (
        <p className="text-red-500 dark:text-red-400">{error}</p>
      ) : (
        <HackathonFilterGrid hackathons={hackathons} />
      )}
    </div>
  );
}
