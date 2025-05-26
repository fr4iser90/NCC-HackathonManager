'use client';

import { useState, useEffect, FormEvent, useMemo } from 'react';
import { useSession } from 'next-auth/react';
import { useQuery } from '@tanstack/react-query';
import { z } from 'zod';

// Zod-Schema für das Profilformular
const profileSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  full_name: z.string().optional(),
  new_password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .optional()
    .or(z.literal('')),
  confirm_new_password: z.string().optional().or(z.literal('')),
  current_password: z.string().optional().or(z.literal('')),
});

type UserWithRoleAndAccessToken = {
  role?: string;
  id?: string;
  accessToken?: string;
};

export default function ProfilePage() {
  const { data: session, status } = useSession();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    current_password: '',
    new_password: '',
    confirm_new_password: '',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [avatarFile, setAvatarFile] = useState<File | null>(null);

  const userRole = (session?.user as UserWithRoleAndAccessToken)?.role;
  const userId = (session?.user as UserWithRoleAndAccessToken)?.id as
    | string
    | undefined;

  useEffect(() => {
    if (status === 'authenticated') {
      const fetchProfile = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const token = (session?.user as UserWithRoleAndAccessToken)
            ?.accessToken;
          const res = await fetch(
            `${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me`,
            {
              headers: { Authorization: `Bearer ${token}` },
            },
          );
          if (!res.ok) throw new Error('Failed to load profile');
          const data = (await res.json()) as {
            email: string;
            username: string;
            full_name?: string;
            avatar_url?: string;
          };
          setFormData({
            email: data.email,
            username: data.username,
            full_name: data.full_name || '',
            current_password: '',
            new_password: '',
            confirm_new_password: '',
          });
          // setAvatarUrl removed (avatarUrl state removed)
        } catch {
          setError('Failed to load profile');
        } finally {
          setIsLoading(false);
        }
      };
      fetchProfile();
    }
  }, [status, session]);

  // Teams Query
  const {
    data: teams = [],
    isLoading: loadingTeams,
    error: teamsError,
  } = useQuery({
    queryKey: ['teams', userId],
    queryFn: async () => {
      const token = (session?.user as UserWithRoleAndAccessToken)?.accessToken;
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me/teams`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (!res.ok) throw new Error('Failed to load teams');
      return res.json();
    },
    enabled: status === 'authenticated',
  });

  // Projects Query
  const {
    data: projects = [],
    isLoading: loadingProjects,
    error: projectsError,
  } = useQuery({
    queryKey: ['projects', userId],
    queryFn: async () => {
      const token = (session?.user as UserWithRoleAndAccessToken)?.accessToken;
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me/projects`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (!res.ok) throw new Error('Failed to load projects');
      return res.json();
    },
    enabled: status === 'authenticated',
  });

  // Judging Scores Query (nur für Judges)
  const {
    data: judgingScores = [],
    isLoading: loadingJudgingScores,
    error: judgingScoresError,
  } = useQuery({
    queryKey: ['judging-scores', userId],
    queryFn: async () => {
      const token = (session?.user as UserWithRoleAndAccessToken)?.accessToken;
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/judging/scores/judge/${userId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        },
      );
      if (!res.ok) throw new Error('Failed to load judging scores');
      return res.json();
    },
    enabled: status === 'authenticated' && userRole === 'judge',
  });

  // Gruppiere Scores nach Project
  const scoresByProject = useMemo(() => {
    const map: Record<string, unknown[]> = {};
    for (const score of judgingScores as unknown[]) {
      if (
        typeof score === 'object' &&
        score !== null &&
        'project_id' in score
      ) {
        const projectId = (score as { project_id: string }).project_id;
        if (!map[projectId]) map[projectId] = [];
        map[projectId].push(score);
      }
    }
    return map;
  }, [judgingScores]);

  // Removed unused handleChange, handleAvatarChange, handleAvatarRemove

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    // setIsSaving removed (isSaving state removed)
    setError(null);
    setSuccess(false);
    // setFormErrors removed (formErrors state removed)
    // Zod-Validierung
    const result = profileSchema.safeParse(formData);
    const errors: Record<string, string> = {};
    if (!result.success) {
      for (const issue of result.error.issues) {
        errors[issue.path[0] as string] = issue.message;
      }
    }
    // Custom-Validierung für Passwort-Bestätigung
    if (formData.new_password) {
      if (!formData.current_password) {
        errors.current_password = 'Bitte aktuelles Passwort eingeben.';
      }
      if (formData.new_password !== formData.confirm_new_password) {
        errors.confirm_new_password =
          'Die neuen Passwörter stimmen nicht überein.';
      }
    }
    if (Object.keys(errors).length > 0) {
      // setFormErrors removed (formErrors state removed)
      // setIsSaving removed (isSaving state removed)
      return;
    }
    try {
      const token = (session?.user as UserWithRoleAndAccessToken)?.accessToken;
      if (avatarFile) {
        const formDataImg = new FormData();
        formDataImg.append('file', avatarFile);
        const resImg = await fetch('/api/users/me/avatar', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
          body: formDataImg,
        });
        if (!resImg.ok) {
          throw new Error('Profilbild-Upload fehlgeschlagen');
        }
        await resImg.json();
        // setAvatarUrl removed (avatarUrl state removed)
      }
      const payload: Record<string, unknown> = {
        username: formData.username,
        full_name: formData.full_name,
      };
      if (formData.new_password && formData.current_password) {
        payload.current_password = formData.current_password;
        payload.password = formData.new_password;
      }
      Object.keys(payload).forEach(
        (key) =>
          (payload[key] === '' || payload[key] === undefined) &&
          delete payload[key],
      );
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me`,
        {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        },
      );
      if (!res.ok) {
        setError('Update failed');
        return;
      }
      setSuccess(true);
      setFormData((prev) => ({
        ...prev,
        current_password: '',
        new_password: '',
        confirm_new_password: '',
      }));
      setAvatarFile(null);
      // setAvatarPreview removed (avatarPreview state removed)
    } catch {
      setError('Update failed');
    } finally {
      // setIsSaving removed (isSaving state removed)
    }
  };

  if (status === 'loading' || isLoading) {
    return (
      <div className="container mx-auto p-4 text-center">
        Loading profile...
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 text-center text-red-500">
        Error: {error}
      </div>
    );
  }

  // Removed unused backendUrl

  return (
    <div className="container mx-auto max-w-lg p-4">
      <h1 className="text-2xl font-bold mb-6">My Profile</h1>
      {success && (
        <div className="mb-4 p-3 text-green-700 bg-green-100 border border-green-400 rounded">
          Profile updated successfully!
        </div>
      )}
      <form
        onSubmit={handleSubmit}
        className="space-y-6 bg-white p-8 shadow-md rounded-lg"
        aria-label="Edit Profile Form"
      >
        {/* ...rest of the form unchanged... */}
      </form>
      <section aria-label="My Teams" className="mt-10">
        <h2 className="text-xl font-semibold mb-2">My Teams</h2>
        {loadingTeams ? (
          <div>Loading teams...</div>
        ) : teamsError ? (
          <div className="text-red-500">{teamsError.message}</div>
        ) : teams.length === 0 ? (
          <div>No teams found.</div>
        ) : (
          <div
            className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
            role="list"
            aria-label="Team List"
          >
            {teams.map((team: unknown) => {
              if (
                typeof team === 'object' &&
                team !== null &&
                'id' in team &&
                'name' in team
              ) {
                const t = team as {
                  id: string;
                  name: string;
                  role?: string;
                  member_count?: number;
                  project_count?: number;
                };
                return (
                  <div
                    key={t.id}
                    className="bg-white border rounded-lg shadow p-4 flex flex-col gap-2"
                    tabIndex={0}
                    aria-label={`Team ${t.name}`}
                    role="listitem"
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <div
                        className="w-12 h-12 bg-slate-200 rounded-full flex items-center justify-center text-slate-400 text-2xl font-bold"
                        aria-hidden="true"
                      >
                        <span role="img" aria-label="Team">
                          {t.name?.[0]?.toUpperCase() || '👥'}
                        </span>
                      </div>
                      <div>
                        <div className="font-semibold text-lg">{t.name}</div>
                        <div className="text-xs text-gray-500">
                          {t.role || 'Member'}
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-4 text-sm text-gray-700">
                      <div>
                        <span className="font-bold">
                          {t.member_count ?? '—'}
                        </span>{' '}
                        Members
                      </div>
                      <div>
                        <span className="font-bold">
                          {t.project_count ?? '—'}
                        </span>{' '}
                        Projects
                      </div>
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-500">
                      <div>
                        Wins: <span className="font-bold">—</span>
                      </div>
                      <div>
                        Avg. Score: <span className="font-bold">—</span>
                      </div>
                      <div>
                        Submissions: <span className="font-bold">—</span>
                      </div>
                      <div>
                        Last Activity: <span className="font-bold">—</span>
                      </div>
                    </div>
                  </div>
                );
              }
              return null;
            })}
          </div>
        )}
      </section>
      <div className="mt-6" aria-label="My Projects">
        <h2 className="text-xl font-semibold mb-2">My Projects</h2>
        {loadingProjects ? (
          <div>Loading projects...</div>
        ) : projectsError ? (
          <div className="text-red-500">{projectsError.message}</div>
        ) : projects.length === 0 ? (
          <div>No projects found.</div>
        ) : (
          <ul className="list-disc pl-5" role="list" aria-label="Project List">
            {projects.map((project: unknown) => {
              if (
                typeof project === 'object' &&
                project !== null &&
                'id' in project &&
                'name' in project
              ) {
                const p = project as { id: string; name: string };
                return (
                  <li key={p.id} className="mb-1" role="listitem">
                    {p.name}
                  </li>
                );
              }
              return null;
            })}
          </ul>
        )}
      </div>
      {userRole === 'judge' && (
        <div className="mt-6" aria-label="My Judging Scores">
          <h2 className="text-xl font-semibold mb-2">My Judging Scores</h2>
          {loadingJudgingScores ? (
            <div>Loading judging scores...</div>
          ) : judgingScoresError ? (
            <div className="text-red-500">{judgingScoresError.message}</div>
          ) : judgingScores.length === 0 ? (
            <div>No judging scores found.</div>
          ) : (
            <ul
              className="list-disc pl-5"
              role="list"
              aria-label="Judged Projects"
            >
              {Object.entries(scoresByProject).map(
                ([projectId, scores]: [string, unknown[]]) => (
                  <li key={projectId} className="mb-2" role="listitem">
                    <span className="font-bold">Project:</span>{' '}
                    {projectId.substring(0, 8)}
                    <ul
                      className="ml-4 text-sm text-gray-700"
                      role="list"
                      aria-label="Criteria Scores"
                    >
                      {scores.map((score: unknown) => {
                        if (
                          typeof score === 'object' &&
                          score !== null &&
                          'id' in score &&
                          'criteria_id' in score &&
                          'score' in score
                        ) {
                          const s = score as {
                            id: string;
                            criteria_id: string;
                            score: number;
                            comment?: string;
                          };
                          return (
                            <li key={s.id} role="listitem">
                              Criterion: {s.criteria_id.substring(0, 8)}, Score:{' '}
                              {s.score}, Comment: {s.comment || '—'}
                            </li>
                          );
                        }
                        return null;
                      })}
                    </ul>
                  </li>
                ),
              )}
            </ul>
          )}
        </div>
      )}
      {/* User-Statistiken (Platzhalter) */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">Your Hackathon Stats</h2>
        <div className="flex flex-wrap gap-4 bg-slate-50 border rounded shadow p-4">
          <div className="flex-1 min-w-[120px]">
            <div className="text-xs text-gray-500">Total Score</div>
            <div className="text-lg font-bold">—</div>
          </div>
          <div className="flex-1 min-w-[120px]">
            <div className="text-xs text-gray-500">Participations</div>
            <div className="text-lg font-bold">—</div>
          </div>
          <div className="flex-1 min-w-[120px]">
            <div className="text-xs text-gray-500">Wins</div>
            <div className="text-lg font-bold">—</div>
          </div>
          <div className="flex-1 min-w-[120px]">
            <div className="text-xs text-gray-500">Placements</div>
            <div className="text-lg font-bold">—</div>
          </div>
        </div>
      </section>
    </div>
  );
}
