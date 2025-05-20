import HackathonCard from "@/components/HackathonCard";
import type { Hackathon } from "@/types/hackathon";

async function getHackathons(): Promise<Hackathon[]> {
  try {
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/hackathons/`, { 
      cache: 'no-store',
      headers: {
        'Accept': 'application/json',
      }
    });

    if (!res.ok) {
      console.error("Failed to fetch hackathons:", res.status, res.statusText);
      // Optionally, log res.text() if you expect more details in the body for errors
      // const errorBody = await res.text();
      // console.error("Error body:", errorBody);
      return []; // Return empty array on error to prevent .map error
    }
    
    const data = await res.json();
    return data as Hackathon[]; // Assume API returns Hackathon[]
  } catch (error) {
    console.error("Error fetching hackathons:", error);
    return []; // Return empty array on network error or JSON parsing error
  }
}

export default async function HackathonsPage() { // Renamed and made async
  console.log("NEXT_PUBLIC_API_BASE_URL:", process.env.NEXT_PUBLIC_API_BASE_URL); // Log the env var
  const fetchedHackathons = await getHackathons();

  // Ensure hackathons is always an array, even if getHackathons somehow returns undefined
  const hackathonsToRender = Array.isArray(fetchedHackathons) ? fetchedHackathons : [];

  if (hackathonsToRender.length === 0) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Hackathons</h1>
        <p>No hackathons found or failed to load. Check server console for API errors.</p>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Hackathons</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
        {hackathonsToRender.map((h: Hackathon) => (
          <HackathonCard key={h.id} hackathon={h} />
        ))}
      </div>
    </div>
  );
}
