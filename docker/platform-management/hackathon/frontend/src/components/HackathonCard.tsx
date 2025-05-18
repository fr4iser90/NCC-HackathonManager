import React from "react";

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

export default function HackathonCard({ hackathon }: { hackathon: Hackathon }) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md overflow-hidden flex flex-col hover:scale-[1.02] transition-transform">
      {hackathon.banner_image_url && (
        <img
          src={hackathon.banner_image_url}
          alt={hackathon.name}
          className="w-full h-32 object-cover"
        />
      )}
      <div className="p-4 flex flex-col gap-2">
        <div className="flex gap-2 flex-wrap">
          {hackathon.category && (
            <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">{hackathon.category}</span>
          )}
          <span className={`text-xs px-2 py-1 rounded ${hackathon.status === "active" ? "bg-green-100 text-green-800" : "bg-gray-200 text-gray-700"}`}>
            {hackathon.status.toUpperCase()}
          </span>
          {hackathon.tags?.map(tag => (
            <span key={tag} className="bg-slate-200 text-slate-700 text-xs px-2 py-1 rounded">{tag}</span>
          ))}
        </div>
        <h2 className="text-lg font-bold">{hackathon.name}</h2>
        <div className="text-xs text-gray-500">
          {new Date(hackathon.start_date).toLocaleDateString()} - {new Date(hackathon.end_date).toLocaleDateString()}
        </div>
        <div className="text-xs text-gray-500">Modus: {hackathon.mode.replace("_", " ")}</div>
        {hackathon.sponsor && <div className="text-xs text-gray-500">Sponsor: {hackathon.sponsor}</div>}
        <p className="text-sm mt-1 line-clamp-2">{hackathon.description}</p>
        <a
          href={`/hackathons/${hackathon.id}`}
          className="mt-2 inline-block text-blue-600 hover:underline text-sm font-medium"
        >
          Mehr erfahren →
        </a>
      </div>
    </div>
  );
}
