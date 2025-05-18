import HackathonCard from "@/components/HackathonCard";
import type { Hackathon } from "@/types/hackathon";
// ...API call to fetch hackathons...

export default function HackathonListPage({ hackathons }: { hackathons: Hackathon[] }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
      {hackathons.map((h: Hackathon) => (
        <HackathonCard key={h.id} hackathon={h} />
      ))}
    </div>
  );
}
