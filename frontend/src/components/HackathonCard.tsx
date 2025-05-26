'use client';

import React, { useState, useEffect } from 'react';
import type { Hackathon } from '../types/hackathon';
import RegistrationModal from './RegistrationModal';
import { useSession } from 'next-auth/react';
import { useApiClient } from '../lib/useApiClient'; // Corrected path
import Image from 'next/image';

// Simplified local type for Team, ideally from a shared types file
interface UserTeam {
  id: string;
  name: string;
}

type UserWithId = { id: string };

export default function HackathonCard({ hackathon }: { hackathon: Hackathon }) {
  const { data: session } = useSession();
  const currentUser = session?.user as UserWithId | undefined;
  const apiFetch = useApiClient();

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isCurrentUserRegistered, setIsCurrentUserRegistered] = useState(false);
  const [userProjectId, setUserProjectId] = useState<string | null>(null);
  // const [registrationDetails, setCurrentRegistrationDetails] = useState<HackathonRegistration | null>(null); // Not strictly needed by card itself if modal handles details
  const [userTeams, setUserTeams] = useState<UserTeam[]>([]);
  const [isLoadingTeams, setIsLoadingTeams] = useState(false); // For team fetching state

  const participantCount = hackathon.registrations?.length || 0;
  const now = new Date();
  const registrationDeadline = hackathon.registration_deadline
    ? new Date(hackathon.registration_deadline)
    : null;

  const isHackathonOpenForRegistration =
    (hackathon.status === 'upcoming' || hackathon.status === 'active') &&
    (!registrationDeadline || now < registrationDeadline);

  useEffect(() => {
    let isMounted = true;

    const checkRegistrationStatus = async () => {
      if (!currentUser || !hackathon.registrations) {
        if (isMounted) setIsCurrentUserRegistered(false);
        return;
      }

      // 1. Check for solo registration
      let foundReg = hackathon.registrations.find(
        (reg) => reg.user_id === currentUser?.id,
      );

      // 2. If not found solo, and hackathon allows teams, check for team registration
      if (!foundReg && hackathon.mode !== 'SOLO_ONLY') {
        setIsLoadingTeams(true);
        try {
          // Fetch user's teams if not already fetched
          // This check could be optimized if userTeams is stable from a context
          let currentTeams = userTeams;
          if (currentTeams.length === 0 && session) {
            // Fetch only if logged in and teams not loaded
            const teamsRes = await apiFetch(
              `${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me/teams`,
            );
            if (teamsRes.ok) {
              const teamsData: UserTeam[] = await teamsRes.json();
              if (isMounted) {
                setUserTeams(teamsData);
                currentTeams = teamsData; // Use freshly fetched data
              }
            } else {
              console.error(
                'Failed to fetch user teams for card status check:',
                teamsRes.statusText,
              );
            }
          }

          const userTeamIds = currentTeams.map((t) => t.id);
          if (userTeamIds.length > 0) {
            foundReg = hackathon.registrations.find(
              (reg) => reg.team_id && userTeamIds.includes(reg.team_id),
            );
          }
        } catch (error) {
          console.error('Error fetching user teams for card:', error);
        } finally {
          if (isMounted) setIsLoadingTeams(false);
        }
      }

      if (isMounted) {
        setIsCurrentUserRegistered(!!foundReg);
        setUserProjectId(foundReg?.project_id || null);
        // setCurrentRegistrationDetails(foundReg || null); // Modal can handle fetching its own details if needed
      }
    };

    checkRegistrationStatus();

    return () => {
      isMounted = false;
    };
  }, [currentUser, hackathon, apiFetch, session, userTeams]);

  const handleModalOpen = () => {
    if (!currentUser) {
      alert('Please log in to register or view registration details.');
      return;
    }
    setIsModalOpen(true);
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-lg shadow-md overflow-hidden flex flex-col hover:scale-[1.02] transition-transform h-full">
      {hackathon.banner_image_url && (
        <Image
          src={hackathon.banner_image_url}
          alt={hackathon.name}
          className="w-full h-32 object-cover"
          width={600}
          height={128}
          style={{ width: '100%', height: '8rem', objectFit: 'cover' }}
          priority
        />
      )}
      <div className="p-4 flex flex-col gap-2 flex-grow">
        <div className="flex gap-2 flex-wrap items-center">
          {hackathon.category && (
            <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300">
              {hackathon.category}
            </span>
          )}
          <span
            className={`text-xs font-medium px-2.5 py-0.5 rounded 
            ${
              hackathon.status === 'active'
                ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                : hackathon.status === 'upcoming'
                  ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
                  : hackathon.status === 'completed'
                    ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
            }`}
          >
            {hackathon.status.toUpperCase()}
          </span>
          {hackathon.tags?.map((tag) => (
            <span
              key={tag}
              className="bg-slate-200 text-slate-700 text-xs font-medium px-2.5 py-0.5 rounded dark:bg-slate-700 dark:text-slate-300"
            >
              {tag}
            </span>
          ))}
        </div>
        <h2 className="text-lg font-bold text-gray-900 dark:text-white">
          {hackathon.name}
        </h2>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          {new Date(hackathon.start_date).toLocaleDateString()} -{' '}
          {new Date(hackathon.end_date).toLocaleDateString()}
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          Modus: {hackathon.mode.replace(/_/g, ' ')}
        </div>
        {hackathon.sponsor && (
          <div className="text-xs text-gray-500 dark:text-gray-400">
            Sponsor: {hackathon.sponsor}
          </div>
        )}
        <p className="text-sm text-gray-700 dark:text-gray-300 mt-1 line-clamp-3 flex-grow">
          {hackathon.description}
        </p>

        <div className="mt-auto pt-2">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              Teilnehmer: {participantCount}
            </span>
          </div>

          {isLoadingTeams ? (
            <div className="w-full text-center py-2 text-xs text-gray-500 dark:text-gray-400">
              Checking status...
            </div>
          ) : isCurrentUserRegistered ? (
            <>
              <button
                onClick={handleModalOpen}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded text-sm transition-colors"
              >
                Angemeldet (Details)
              </button>
              {userProjectId && (
                <a
                  href={`/projects/${userProjectId}/submit`}
                  className="w-full mt-2 block bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded text-sm text-center transition-colors"
                >
                  Projekt einreichen
                </a>
              )}
            </>
          ) : isHackathonOpenForRegistration ? (
            <button
              onClick={handleModalOpen}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded text-sm transition-colors"
            >
              Registrieren
            </button>
          ) : null}

          {!isHackathonOpenForRegistration &&
            hackathon.status === 'completed' && (
              <button
                onClick={() => alert(`Ergebnisse für ${hackathon.name} (TODO)`)}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded text-sm transition-colors mt-2"
              >
                Ergebnisse ansehen
              </button>
            )}
          {!isHackathonOpenForRegistration &&
            hackathon.status === 'archived' && (
              <span className="mt-2 block text-center text-xs text-gray-400 dark:text-gray-500 italic">
                Archiviert
              </span>
            )}
          <a
            href={`/hackathons/${hackathon.id}`}
            className="mt-2 block text-center text-blue-600 dark:text-blue-400 hover:underline text-sm font-medium"
          >
            Mehr erfahren →
          </a>
        </div>
      </div>
      <RegistrationModal
        hackathon={hackathon}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}
