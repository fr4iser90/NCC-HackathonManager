'use client';

import React, { useState, useEffect } from 'react';
import type { Hackathon } from '@/types/hackathon';
import HackathonFilterGrid from '@/components/HackathonFilterGrid';
import CreateHackathonModal from '@/components/CreateHackathonModal';

export default function HackathonManagerClient() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const fetchHackathons = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/hackathons/`,
        {
          headers: { Accept: 'application/json' },
        }
      );
      if (!res.ok) throw new Error('Failed to fetch hackathons');
      const data = await res.json();
      setHackathons(Array.isArray(data) ? data : []);
    } catch {
      setHackathons([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHackathons();
  }, []);

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
      ) : (
        <HackathonFilterGrid hackathons={hackathons} />
      )}
    </div>
  );
}
