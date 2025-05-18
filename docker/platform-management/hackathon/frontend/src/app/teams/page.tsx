"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import axiosInstance from "@/lib/axiosInstance";
import { Dialog } from '@headlessui/react';

interface Team {
  id: string;
  name: string;
  description?: string;
  is_open?: boolean;
  members?: { user_id: string; role: string }[];
  projects?: { id: string; name: string }[];
  join_requests?: { user_id: string; status: string }[];
}

interface JoinRequest {
  user_id: string;
  status: string;
  created_at: string;
  // Optional: user?: { email?: string; username?: string }
}

export default function TeamsPage() {
  const { data: session, status } = useSession();
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [joining, setJoining] = useState<string | null>(null);
  const [leaving, setLeaving] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTeam, setNewTeam] = useState({ name: '', description: '', is_open: true });
  const [creating, setCreating] = useState(false);
  const [requesting, setRequesting] = useState<string | null>(null);
  const [inviting, setInviting] = useState<string | null>(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [joinRequests, setJoinRequests] = useState<Record<string, JoinRequest[]>>({});
  const [requestFeedback, setRequestFeedback] = useState<Record<string, string>>({});
  const [revoking, setRevoking] = useState<string | null>(null);
  const [myJoinRequests, setMyJoinRequests] = useState<Record<string, JoinRequest | null>>({});

  const userId = (session?.user as any)?.id;

  useEffect(() => {
    const fetchTeams = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = (session?.user as any)?.accessToken;
        const res = await axiosInstance.get("/teams/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setTeams(res.data);
      } catch (err: any) {
        setError(err.message || "Failed to load teams");
      } finally {
        setLoading(false);
      }
    };
    if (status === "authenticated") fetchTeams();
  }, [status, session]);

  useEffect(() => {
    if (status === "authenticated") {
      // Lade alle eigenen Join-Requests EINMAL
      const fetchMyJoinRequests = async () => {
        try {
          const token = (session?.user as any)?.accessToken;
          const res = await axiosInstance.get("/teams/my-join-requests", {
            headers: { Authorization: `Bearer ${token}` },
          });
          // Mappe zu {team_id: JoinRequest}
          const map: Record<string, JoinRequest> = {};
          for (const req of res.data) {
            map[req.team_id] = req;
          }
          setMyJoinRequests(map);
        } catch (err) {
          setMyJoinRequests({});
        }
      };
      fetchMyJoinRequests();
    }
  }, [status, session]);

  const handleJoin = async (teamId: string) => {
    setJoining(teamId);
    try {
      const token = (session?.user as any)?.accessToken;
      await axiosInstance.post(`/teams/${teamId}/join`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTeams((prev) =>
        prev.map((t) =>
          t.id === teamId
            ? {
                ...t,
                members: [...(t.members || []), { user_id: userId, role: "member" }],
              }
            : t
        )
      );
    } catch (err) {
      // Fehlerbehandlung optional
    } finally {
      setJoining(null);
    }
  };

  const handleLeave = async (teamId: string) => {
    setLeaving(teamId);
    try {
      const token = (session?.user as any)?.accessToken;
      await axiosInstance.post(`/teams/${teamId}/leave`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTeams((prev) =>
        prev.map((t) =>
          t.id === teamId
            ? {
                ...t,
                members: (t.members || []).filter((m) => m.user_id !== userId),
              }
            : t
        )
      );
    } catch (err) {
      // Fehlerbehandlung optional
    } finally {
      setLeaving(null);
    }
  };

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      const token = (session?.user as any)?.accessToken;
      const payload = { ...newTeam, is_open: newTeam.is_open };
      const res = await axiosInstance.post('/teams/', payload, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTeams((prev) => [res.data, ...prev]);
      setShowCreateModal(false);
      setNewTeam({ name: '', description: '', is_open: true });
    } catch (err) {
      // Fehlerbehandlung optional
    } finally {
      setCreating(false);
    }
  };

  const myPendingRequest = (team: Team) => joinRequests[team.id]?.find(r => r.user_id === userId && r.status === 'pending');

  const fetchJoinRequests = async (teamId: string) => {
    try {
      const token = (session?.user as any)?.accessToken;
      const res = await axiosInstance.get(`/teams/${teamId}/join-requests`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setJoinRequests((prev) => ({ ...prev, [teamId]: res.data }));
    } catch {}
  };

  const reloadMyJoinRequests = async () => {
    try {
      const token = (session?.user as any)?.accessToken;
      const res = await axiosInstance.get("/teams/my-join-requests", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const map: Record<string, JoinRequest> = {};
      for (const req of res.data) {
        map[req.team_id] = req;
      }
      setMyJoinRequests(map);
    } catch {
      setMyJoinRequests({});
    }
  };

  const handleRequestJoin = async (teamId: string) => {
    setRequesting(teamId);
    setRequestFeedback((prev) => ({ ...prev, [teamId]: '' }));
    try {
      const token = (session?.user as any)?.accessToken;
      await axiosInstance.post(`/teams/${teamId}/request-join`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRequestFeedback((prev) => ({ ...prev, [teamId]: 'Request sent.' }));
      await reloadMyJoinRequests();
    } catch (err: any) {
      setRequestFeedback((prev) => ({ ...prev, [teamId]: err?.response?.data?.detail || 'Error sending request.' }));
      await reloadMyJoinRequests();
    } finally {
      setRequesting(null);
    }
  };

  const handleRevokeRequest = async (teamId: string) => {
    setRevoking(teamId);
    setRequestFeedback((prev) => ({ ...prev, [teamId]: '' }));
    try {
      const token = (session?.user as any)?.accessToken;
      await axiosInstance.delete(`/teams/${teamId}/join-requests/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setRequestFeedback((prev) => ({ ...prev, [teamId]: 'Request revoked.' }));
      await reloadMyJoinRequests();
      setTimeout(() => {
        setRequestFeedback((prev) => ({ ...prev, [teamId]: '' }));
      }, 2000);
    } catch (err: any) {
      setRequestFeedback((prev) => ({ ...prev, [teamId]: err?.response?.data?.detail || 'Error revoking request.' }));
      await reloadMyJoinRequests();
    } finally {
      setRevoking(null);
    }
  };

  const handleInvite = async (teamId: string) => {
    setInviting(teamId);
    try {
      const token = (session?.user as any)?.accessToken;
      await axiosInstance.post(`/teams/${teamId}/invite`, { email: inviteEmail }, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setInviteEmail('');
      // Optional: UI-Feedback für Einladung
    } catch (err) {
      // Fehlerbehandlung optional
    } finally {
      setInviting(null);
    }
  };

  const handleAcceptJoin = async (teamId: string, userIdToAccept: string) => {
    try {
      const token = (session?.user as any)?.accessToken;
      await axiosInstance.post(`/teams/${teamId}/join-requests/${userIdToAccept}/accept`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setJoinRequests((prev) => ({
        ...prev,
        [teamId]: prev[teamId]?.filter((r) => r.user_id !== userIdToAccept) || [],
      }));
    } catch {}
  };

  const handleRejectJoin = async (teamId: string, userIdToReject: string) => {
    try {
      const token = (session?.user as any)?.accessToken;
      await axiosInstance.post(`/teams/${teamId}/join-requests/${userIdToReject}/reject`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setJoinRequests((prev) => ({
        ...prev,
        [teamId]: prev[teamId]?.filter((r) => r.user_id !== userIdToReject) || [],
      }));
    } catch {}
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Teams</h1>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          onClick={() => setShowCreateModal(true)}
        >
          + Create Team
        </button>
      </div>
      {/* Team Creation Modal */}
      <Dialog open={showCreateModal} onClose={() => setShowCreateModal(false)} className="fixed z-10 inset-0 overflow-y-auto">
        <div className="flex items-center justify-center min-h-screen">
          <div className="fixed inset-0 bg-black opacity-30" aria-hidden="true" />
          <div className="relative bg-white rounded-lg shadow-lg p-8 w-full max-w-md z-20">
            <Dialog.Title className="text-lg font-bold mb-4">Create Team</Dialog.Title>
            <form onSubmit={handleCreateTeam} className="space-y-4">
              <div>
                <label className="block text-sm font-medium">Name</label>
                <input type="text" required className="mt-1 block w-full border rounded p-2" value={newTeam.name} onChange={e => setNewTeam(t => ({ ...t, name: e.target.value }))} />
              </div>
              <div>
                <label className="block text-sm font-medium">Description</label>
                <textarea className="mt-1 block w-full border rounded p-2" value={newTeam.description} onChange={e => setNewTeam(t => ({ ...t, description: e.target.value }))} />
              </div>
              <div>
                <label className="block text-sm font-medium">Team Type</label>
                <select className="mt-1 block w-full border rounded p-2" value={newTeam.is_open ? 'open' : 'closed'} onChange={e => setNewTeam(t => ({ ...t, is_open: e.target.value === 'open' }))}>
                  <option value="open">Open (anyone can request to join)</option>
                  <option value="closed">Closed (invite only)</option>
                </select>
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" className="px-4 py-2 bg-gray-200 rounded" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded" disabled={creating}>{creating ? 'Creating...' : 'Create'}</button>
              </div>
            </form>
          </div>
        </div>
      </Dialog>
      {/* Team Cards */}
      {loading ? (
        <div>Loading teams...</div>
      ) : error ? (
        <div className="text-red-500">{error}</div>
      ) : teams.length === 0 ? (
        <div>No teams found.</div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {teams.map((team) => {
            const isMember = team.members?.some((m) => m.user_id === userId);
            const isOwner = team.members?.find((m) => m.user_id === userId)?.role === 'owner';
            return (
              <div key={team.id} className="bg-white border rounded-lg shadow p-4 flex flex-col gap-2">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-12 h-12 bg-slate-200 rounded-full flex items-center justify-center text-slate-400 text-2xl font-bold">
                    <span role="img" aria-label="Team">👥</span>
                  </div>
                  <div>
                    <div className="font-semibold text-lg">{team.name}</div>
                    <div className="text-xs text-gray-500">{team.description || "No description"}</div>
                  </div>
                </div>
                <div className="flex gap-4 text-sm text-gray-700">
                  <div><span className="font-bold">{team.members?.length ?? "—"}</span> Members</div>
                  <div><span className="font-bold">{team.projects?.length ?? "—"}</span> Projects</div>
                  <div><span className="font-bold">Type:</span> {team.is_open ? 'Open' : 'Closed'}</div>
                  {isMember && <div><span className="font-bold">Role:</span> {isOwner ? 'Owner' : 'Member'}</div>}
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-gray-500">
                  <div>Wins: <span className="font-bold">—</span></div>
                  <div>Avg. Score: <span className="font-bold">—</span></div>
                  <div>Submissions: <span className="font-bold">—</span></div>
                  <div>Last Activity: <span className="font-bold">—</span></div>
                </div>
                <div className="mt-3 flex flex-col gap-2">
                  {!isMember && (team.is_open ?? true) === true && !myJoinRequests[team.id] && (
                    <button
                      className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
                      onClick={() => handleRequestJoin(team.id)}
                      disabled={requesting === team.id}
                    >
                      {requesting === team.id ? "Requesting..." : requestFeedback[team.id] || "Request to Join"}
                    </button>
                  )}
                  {!isMember && myJoinRequests[team.id] && (
                    <button
                      className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
                      onClick={() => handleRevokeRequest(team.id)}
                      disabled={revoking === team.id}
                    >
                      {revoking === team.id ? "Revoking..." : requestFeedback[team.id] || "Revoke Request"}
                    </button>
                  )}
                  {requestFeedback[team.id] && (
                    <div className="text-xs text-blue-600 mt-1">{requestFeedback[team.id]}</div>
                  )}
                  {isOwner && !team.is_open && (
                    <form onSubmit={e => { e.preventDefault(); handleInvite(team.id); }} className="flex gap-2">
                      <input type="email" required placeholder="Invite by email" className="border rounded p-1 flex-1" value={inviteEmail} onChange={e => setInviteEmail(e.target.value)} />
                      <button type="submit" className="px-2 py-1 bg-green-600 text-white rounded" disabled={inviting === team.id}>{inviting === team.id ? 'Inviting...' : 'Invite'}</button>
                    </form>
                  )}
                  {isOwner && joinRequests[team.id] && joinRequests[team.id].length > 0 && (
                    <div className="mt-2 bg-slate-50 border rounded p-2">
                      <div className="font-bold text-xs mb-1">Join Requests:</div>
                      <ul className="space-y-1">
                        {joinRequests[team.id].map((req) => (
                          <li key={req.user_id} className="flex items-center gap-2 text-xs">
                            <span>User: {req.user_id}</span>
                            <button className="px-2 py-0.5 bg-green-200 text-green-800 rounded" onClick={() => handleAcceptJoin(team.id, req.user_id)}>Accept</button>
                            <button className="px-2 py-0.5 bg-red-200 text-red-800 rounded" onClick={() => handleRejectJoin(team.id, req.user_id)}>Reject</button>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {isMember && !isOwner && <div className="text-xs text-gray-400">Waiting for owner to manage membership</div>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
} 