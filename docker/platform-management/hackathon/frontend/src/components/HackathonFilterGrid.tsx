"use client";
import { useState } from "react";
import HackathonCard from "./HackathonCard";
import type { Hackathon } from "@/types/hackathon";

export default function HackathonFilterGrid({ hackathons }: { hackathons: Hackathon[] }) {
  const [category, setCategory] = useState<string | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  const filtered = hackathons.filter(h =>
    (!category || h.category === category) &&
    (!status || h.status === status)
  );

  return (
    <>
      <div className="flex gap-4 mb-4">
        <select onChange={e => setCategory(e.target.value || null)} className="border rounded p-2">
          <option value="">Alle Kategorien</option>
          <option value="UI/UX">UI/UX</option>
          <option value="Security">Security</option>
        </select>
        <select onChange={e => setStatus(e.target.value || null)} className="border rounded p-2">
          <option value="">Alle Stati</option>
          <option value="active">Active</option>
          <option value="upcoming">Upcoming</option>
          <option value="completed">Completed</option>
        </select>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {filtered.map((h) => (
          <HackathonCard key={h.id} hackathon={h} />
        ))}
      </div>
    </>
  );
}
