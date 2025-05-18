import Image from "next/image";
import HackathonCard from "@/components/HackathonCard";
import { Suspense } from "react";
import HackathonFilterGrid from "@/components/HackathonFilterGrid";

type Hackathon = {
  id: string;
  name: string;
  description?: string;
  start_date: string;
  end_date: string;
  status: string;
  mode: string;
  category?: string;
  tags?: string[];
  banner_image_url?: string;
  sponsor?: string;
};

type Project = {
  id: string;
  name: string;
  description?: string;
  team?: { name: string };
  hackathon?: { name: string };
  banner_image_url?: string;
};

async function fetchHackathons(): Promise<Hackathon[]> {
  const res = await fetch(process.env.NEXT_PUBLIC_API_BASE_URL + "/hackathons", {
    cache: "no-store",
  });
  if (!res.ok) return [];
  return res.json();
}

async function fetchFeaturedProject(): Promise<Project | null> {
  const res = await fetch(process.env.NEXT_PUBLIC_API_BASE_URL + "/projects/featured", { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export default async function HomePage() {
  const hackathons = await fetchHackathons();
  const featuredProject = await fetchFeaturedProject();
  const featured = hackathons[0];
  const rest = hackathons.slice(1);

  return (
    <div className="flex flex-col gap-12">
      {/* Showcase/Highlight */}
      {featured && (
        <section className="bg-gradient-to-r from-indigo-500 to-blue-500 rounded-xl shadow-lg p-8 flex flex-col md:flex-row items-center gap-8 text-white">
          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-bold mb-2">{featured.name}</h1>
            <div className="mb-2 text-lg">{featured.description}</div>
            <div className="mb-2">
              <span className="bg-white/20 px-3 py-1 rounded mr-2">{featured.category}</span>
              <span className="bg-white/20 px-3 py-1 rounded">{featured.status.toUpperCase()}</span>
            </div>
            <div className="mb-4 text-sm">
              {new Date(featured.start_date).toLocaleDateString()} - {new Date(featured.end_date).toLocaleDateString()}
            </div>
            <a
              href={`/hackathons/${featured.id}`}
              className="inline-block bg-white text-indigo-700 font-semibold px-5 py-2 rounded shadow hover:bg-indigo-100 transition"
            >
              Mehr erfahren
            </a>
          </div>
          <img
            src={featured.banner_image_url || `${process.env.NEXT_PUBLIC_API_BASE_URL}/static/default-banner.svg`}
            alt={featured.name}
            className="w-64 h-40 object-cover rounded-lg shadow-lg"
          />
        </section>
      )}

      {featuredProject && (
        <section className="bg-gradient-to-r from-pink-500 to-yellow-500 rounded-xl shadow-lg p-8 flex flex-col md:flex-row items-center gap-8 text-white my-8">
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">Featured Project: {featuredProject.name}</h2>
            <div className="mb-2">{featuredProject.description}</div>
            <div className="mb-2 text-sm">
              Team: {featuredProject.team?.name} | Hackathon: {featuredProject.hackathon?.name}
            </div>
            <a
              href={`/projects/${featuredProject.id}`}
              className="inline-block bg-white text-pink-700 font-semibold px-5 py-2 rounded shadow hover:bg-pink-100 transition"
            >
              Projekt ansehen
            </a>
          </div>
          <img
            src={featuredProject.banner_image_url || `${process.env.NEXT_PUBLIC_API_BASE_URL}/static/default-banner.svg`}
            alt={featuredProject.name}
            className="w-64 h-40 object-cover rounded-lg shadow-lg"
          />
        </section>
      )}

      {/* Call to Action */}
      <section className="text-center">
        <h2 className="text-2xl font-bold mb-2">Mach mit beim nächsten Hackathon!</h2>
        <p className="mb-4 text-gray-600 dark:text-gray-300">
          Entdecke spannende Projekte, finde Teams und gewinne tolle Preise.
        </p>
        <a
          href="/auth/signup"
          className="inline-block bg-indigo-600 text-white font-semibold px-6 py-2 rounded shadow hover:bg-indigo-700 transition"
        >
          Jetzt registrieren & mitmachen
        </a>
      </section>

      {/* Filter + Grid als Client-Komponente */}
      <section>
        <h2 className="text-xl font-bold mb-4">Alle Hackathons</h2>
        <HackathonFilterGrid hackathons={hackathons} />
      </section>

      <section className="my-12 text-center">
        <h2 className="text-xl font-bold mb-4">Unsere Partner</h2>
        <div className="flex flex-wrap gap-8 justify-center items-center">
          <img
            src={`${process.env.NEXT_PUBLIC_API_BASE_URL}/static/partners/partner1.svg`}
            alt="Partner 1"
            className="h-12"
          />
          <img
            src={`${process.env.NEXT_PUBLIC_API_BASE_URL}/static/partners/partner2.svg`}
            alt="Partner 2"
            className="h-12"
          />
          {/* ... */}
        </div>
      </section>

      <section className="my-12 max-w-2xl mx-auto">
        <h2 className="text-xl font-bold mb-4">FAQ</h2>
        <details className="mb-2">
          <summary className="font-semibold cursor-pointer">Wie kann ich teilnehmen?</summary>
          <div className="pl-4 mt-1 text-gray-600">Registriere dich und tritt einem Team bei oder starte solo!</div>
        </details>
        <details className="mb-2">
          <summary className="font-semibold cursor-pointer">Was kostet die Teilnahme?</summary>
          <div className="pl-4 mt-1 text-gray-600">Die Teilnahme ist kostenlos.</div>
        </details>
        {/* ... */}
      </section>
    </div>
  );
}
