import HackathonCard from "@/components/HackathonCard";
import type { Hackathon } from "@/types/hackathon";
import HackathonFilterGrid from "@/components/HackathonFilterGrid";

async function getHackathons(): Promise<Hackathon[]> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/hackathons/`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch {
    return [];
  }
}

export default async function HackathonsPage() {
  const hackathons = await getHackathons();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Hackathons</h1>
      <HackathonFilterGrid hackathons={hackathons} />
    </div>
  );
}
