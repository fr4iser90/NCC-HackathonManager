"use client";
import { useEffect, useState } from "react";
import HackathonCard from "@/components/HackathonCard";
import type { Hackathon } from "@/types/hackathon";

export default function HackathonsPage() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchHackathons() {
      setLoading(true);
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/hackathons/`, {
          cache: "no-store",
          headers: { Accept: "application/json" },
        });
        if (!res.ok) {
          setHackathons([]);
        } else {
          const data = await res.json();
          setHackathons(Array.isArray(data) ? data : []);
        }
      } catch (e) {
        setHackathons([]);
      } finally {
        setLoading(false);
      }
    }
    fetchHackathons();
  }, []);

  const filtered = hackathons.filter((h) => {
    const matchesSearch =
      h.name.toLowerCase().includes(search.toLowerCase()) ||
      (h.tags && h.tags.some((tag) => tag.toLowerCase().includes(search.toLowerCase())));
    const matchesStatus = statusFilter ? h.status === statusFilter : true;
    const matchesCategory = categoryFilter ? h.category === categoryFilter : true;
    return matchesSearch && matchesStatus && matchesCategory;
  });

  const uniqueStatuses = Array.from(new Set(hackathons.map((h) => h.status)));
  const uniqueCategories = Array.from(
    new Set(hackathons.map((h) => h.category).filter((c): c is string => typeof c === "string" && !!c))
  );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Hackathons</h1>
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
      {loading ? (
        <div>Lade Hackathons...</div>
      ) : filtered.length === 0 ? (
        <p>Keine Hackathons gefunden.</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {filtered.map((h: Hackathon) => (
            <HackathonCard key={h.id} hackathon={h} />
          ))}
        </div>
      )}
    </div>
  );
}
