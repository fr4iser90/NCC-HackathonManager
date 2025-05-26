'use client';
import { useState } from 'react';
import HackathonCard from './HackathonCard';
import type { Hackathon } from '@/types/hackathon';

export default function HackathonFilterGrid({
  hackathons,
}: {
  hackathons: Hackathon[];
}) {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');

  const filtered = hackathons.filter((h) => {
    const matchesSearch =
      h.name.toLowerCase().includes(search.toLowerCase()) ||
      (h.tags &&
        h.tags.some((tag) => tag.toLowerCase().includes(search.toLowerCase())));
    const matchesStatus = statusFilter ? h.status === statusFilter : true;
    const matchesCategory = categoryFilter
      ? h.category === categoryFilter
      : true;
    return matchesSearch && matchesStatus && matchesCategory;
  });

  const uniqueStatuses = Array.from(new Set(hackathons.map((h) => h.status)));
  const uniqueCategories = Array.from(
    new Set(
      hackathons
        .map((h) => h.category)
        .filter((c): c is string => typeof c === 'string' && !!c),
    ),
  );

  return (
    <>
      <div className="flex flex-wrap gap-4 mb-6">
        <input
          type="text"
          placeholder="Suche nach Name oder Tag..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border p-2 rounded w-64"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border p-2 rounded"
        >
          <option value="">Status (alle)</option>
          {uniqueStatuses.map((s) => (
            <option key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </option>
          ))}
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="border p-2 rounded"
        >
          <option value="">Kategorie (alle)</option>
          {uniqueCategories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>
      {filtered.length === 0 ? (
        <p>Keine Hackathons gefunden.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {filtered.map((h: Hackathon) => (
            <HackathonCard key={h.id} hackathon={h} />
          ))}
        </div>
      )}
    </>
  );
}
