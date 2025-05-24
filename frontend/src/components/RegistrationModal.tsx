"use client"; // Add this directive

import React, { useState, useEffect } from 'react';
import type { Hackathon } from '../types/hackathon';
import { useApiClient } from '../lib/useApiClient'; // Assuming this path is correct

// Simplified local types, ideally these would come from a shared types directory
interface User {
  id: string;
  username: string;
  // Add other fields if needed by the modal, e.g., email
}

interface Team {
  id: string;
  name: string;
  // Add other fields if needed
}

interface RegistrationModalProps {
  hackathon: Hackathon | null;
  isOpen: boolean;
  onClose: () => void;
}

export default function RegistrationModal({ hackathon, isOpen, onClose }: RegistrationModalProps) {
  const apiFetch = useApiClient();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [userTeams, setUserTeams] = useState<Team[]>([]);
  const [selectedTeamId, setSelectedTeamId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAlreadyRegistered, setIsAlreadyRegistered] = useState(false);
  const [currentRegistrationId, setCurrentRegistrationId] = useState<string | null>(null);

  // For team search in large lists
  const [teamSearch, setTeamSearch] = useState("");

  // --- New state for create team modal
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [newTeamName, setNewTeamName] = useState('');
  const [newTeamDescription, setNewTeamDescription] = useState('');
  const [newTeamIsOpen, setNewTeamIsOpen] = useState(true);
  const [isCreatingTeam, setIsCreatingTeam] = useState(false);

  useEffect(() => {
    if (isOpen && hackathon) {
      setIsLoading(true);
      setIsAlreadyRegistered(false);
      setCurrentRegistrationId(null);
      setError(null);
      setSelectedTeamId(''); // Reset selected team

      const fetchData = async () => {
        try {
          // Fetch current user
          const userRes = await apiFetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me`, {
            headers: { 'Accept': 'application/json' }
          });
          if (!userRes.ok) throw new Error('Failed to fetch user data');
          const userData: User = await userRes.json();
          setCurrentUser(userData);

          // Check if this user is already registered solo
          const soloReg = hackathon.registrations.find(r => r.user_id === userData.id);
          if (soloReg) {
            setIsAlreadyRegistered(true);
            setCurrentRegistrationId(soloReg.id);
            // If registered solo, no need to check teams for this specific registration action
            // but we still fetch teams for the dropdown if team mode is an option.
          }

          // Fetch user's teams if team participation is relevant
          if (hackathon.mode !== 'SOLO_ONLY') {
            const teamsRes = await apiFetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/users/me/teams`, {
              headers: { 'Accept': 'application/json' }
            });
            if (!teamsRes.ok) throw new Error('Failed to fetch user teams');
            const teamsData: Team[] = await teamsRes.json();
            setUserTeams(teamsData);

            // If not already registered solo, check if any of their teams are registered
            if (!soloReg) {
              for (const team of teamsData) {
                const teamReg = hackathon.registrations.find(r => r.team_id === team.id);
                if (teamReg) {
                  setIsAlreadyRegistered(true); // User is part of an already registered team
                  setCurrentRegistrationId(teamReg.id);
                  setSelectedTeamId(team.id); // Pre-select this team
                  break; 
                }
              }
            }
          }
        } catch (err: any) {
          setError(err.message || 'An error occurred while fetching data.');
          console.error(err);
        } finally {
          setIsLoading(false);
        }
      };
      fetchData();
    }
  }, [isOpen, hackathon, apiFetch]); // apiFetch added as per previous fix

  if (!isOpen || !hackathon) {
    return null;
  }

  const handleActualRegister = async (payload: { user_id?: string; team_id?: string }) => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/hackathons/${hackathon.id}/register`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Registration failed with status: ' + res.status }));
        throw new Error(errorData.detail || 'Registration failed');
      }
      const registrationData = await res.json();
      setSuccessMessage(`Successfully registered for ${hackathon.name}!`);
      setTimeout(() => {
        setSuccessMessage(null);
        onClose();
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during registration.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSolo = () => {
    if (!currentUser) {
      setError("User data not loaded. Cannot register solo.");
      return;
    }
    handleActualRegister({ user_id: currentUser.id });
  };

  const handleRegisterTeam = () => {
    if (!selectedTeamId) {
      setError("Please select a team to register.");
      return;
    }
    handleActualRegister({ team_id: selectedTeamId });
  };

  const handleWithdrawRegistration = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await apiFetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/hackathons/${hackathon?.id}/registration`,
        { method: "DELETE" }
      );
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: "Withdrawal failed" }));
        throw new Error(errorData.detail || "Withdrawal failed");
      }
      setSuccessMessage(`Registration withdrawn successfully.`);
      setIsAlreadyRegistered(false);
      setCurrentRegistrationId(null);
      setTimeout(() => {
        setSuccessMessage(null);
        onClose();
      }, 2000);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during withdrawal.");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // --- New: success message state
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-slate-800 p-6 rounded-lg shadow-xl w-full max-w-md">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Register for {hackathon.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 disabled:opacity-50"
            disabled={isLoading}
          >
            &times; {/* Close icon */}
          </button>
        </div>

        {isLoading && <p className="text-sm text-gray-700 dark:text-gray-300">Loading user data...</p>}
        {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
        {successMessage && <p className="text-sm text-green-600 dark:text-green-400">{successMessage}</p>}

        {!isLoading && !error && currentUser && (
          <div className="space-y-4">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              Mode: {hackathon.mode.replace(/_/g, " ")}
            </p>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              Logged in as: {currentUser.username}
            </p>

            {isAlreadyRegistered ? (
              <div>
                <p className="text-sm text-green-600 dark:text-green-400 mb-4">
                  You (or your selected/a team you are in) are already registered for this hackathon.
                </p>
                <button
                  onClick={handleWithdrawRegistration}
                  disabled={isLoading}
                  className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:opacity-70"
                >
                  Withdraw Registration (TODO: Backend)
                </button>
              </div>
            ) : (
              <>
                {/* Solo Registration Option */}
                {(hackathon.mode === 'SOLO_ONLY' || (hackathon.allow_individuals && hackathon.mode !== 'TEAM_ONLY')) && (
                  <button
                    onClick={handleRegisterSolo}
                    disabled={isLoading}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:opacity-70"
                  >
                    Register as {currentUser.username} (Solo)
                  </button>
                )}

                {/* Team Registration Option */}
                {hackathon.mode !== 'SOLO_ONLY' && (
                  <div className={ (hackathon.mode === 'SOLO_ONLY' || (hackathon.allow_individuals && hackathon.mode !== 'TEAM_ONLY')) ? "mt-4" : ""}>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">Or register with a team:</p>
                    {showCreateTeam ? (
                      <form
                        onSubmit={async (e) => {
                          e.preventDefault();
                          setIsCreatingTeam(true);
                          setError(null);
                          try {
                            const res = await apiFetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/teams`, {
                              method: "POST",
                              headers: {
                                "Content-Type": "application/json",
                                "Accept": "application/json"
                              },
                              body: JSON.stringify({
                                name: newTeamName,
                                description: newTeamDescription,
                                is_open: newTeamIsOpen
                              })
                            });
                            if (!res.ok) {
                              const errorData = await res.json().catch(() => ({ detail: "Failed to create team" }));
                              throw new Error(errorData.detail || "Failed to create team");
                            }
                            const createdTeam = await res.json();
                            setUserTeams((prev) => [...prev, createdTeam]);
                            setSelectedTeamId(createdTeam.id);
                            setShowCreateTeam(false);
                            setNewTeamName("");
                            setNewTeamDescription("");
                            setNewTeamIsOpen(true);
                          } catch (err: any) {
                            setError(err.message || "An error occurred while creating the team.");
                          } finally {
                            setIsCreatingTeam(false);
                          }
                        }}
                        className="mb-2"
                      >
                        <input
                          type="text"
                          value={newTeamName}
                          onChange={(e) => setNewTeamName(e.target.value)}
                          placeholder="Team Name"
                          required
                          className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white mb-2"
                          disabled={isCreatingTeam}
                        />
                        <input
                          type="text"
                          value={newTeamDescription}
                          onChange={(e) => setNewTeamDescription(e.target.value)}
                          placeholder="Description (optional)"
                          className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white mb-2"
                          disabled={isCreatingTeam}
                        />
                        <label className="flex items-center mb-2">
                          <input
                            type="checkbox"
                            checked={newTeamIsOpen}
                            onChange={(e) => setNewTeamIsOpen(e.target.checked)}
                            className="mr-2"
                            disabled={isCreatingTeam}
                          />
                          <span className="text-xs text-gray-700 dark:text-gray-300">Team is open to join requests</span>
                        </label>
                        <div className="flex gap-2">
                          <button
                            type="submit"
                            disabled={isCreatingTeam || !newTeamName}
                            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:opacity-70"
                          >
                            {isCreatingTeam ? "Creating..." : "Create Team"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setShowCreateTeam(false)}
                            disabled={isCreatingTeam}
                            className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded transition-colors disabled:opacity-70"
                          >
                            Cancel
                          </button>
                        </div>
                      </form>
                    ) : userTeams.length > 0 ? (
                      <>
                        {userTeams.length > 5 ? (
                          <>
                            <input
                              type="text"
                              placeholder="Search teams..."
                              value={teamSearch}
                              onChange={e => setTeamSearch(e.target.value)}
                              className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white mb-2"
                              disabled={isLoading}
                            />
                            <div className="max-h-40 overflow-y-auto border rounded mb-2">
                              {userTeams
                                .filter(team => team.name.toLowerCase().includes(teamSearch.toLowerCase()))
                                .map(team => (
                                  <div
                                    key={team.id}
                                    className={`p-2 cursor-pointer ${selectedTeamId === team.id ? "bg-blue-100 dark:bg-blue-900" : ""}`}
                                    onClick={() => setSelectedTeamId(team.id)}
                                  >
                                    {team.name}
                                  </div>
                                ))}
                            </div>
                          </>
                        ) : (
                          <select
                            value={selectedTeamId}
                            onChange={(e) => setSelectedTeamId(e.target.value)}
                            disabled={isLoading}
                            className="w-full p-2 border rounded dark:bg-slate-700 dark:border-slate-600 dark:text-white mb-2 disabled:opacity-70"
                          >
                            <option value="">Select a team</option>
                            {userTeams.map(team => (
                              <option key={team.id} value={team.id}>{team.name}</option>
                            ))}
                          </select>
                        )}
                        <button
                          onClick={handleRegisterTeam}
                          disabled={isLoading || !selectedTeamId}
                          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition-colors disabled:opacity-70"
                        >
                          Register with Selected Team
                        </button>
                        <button
                          type="button"
                          onClick={() => setShowCreateTeam(true)}
                          disabled={isLoading}
                          className="w-full mt-2 bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded transition-colors disabled:opacity-70"
                        >
                          + Create New Team
                        </button>
                      </>
                    ) : (
                      <p className="text-xs text-gray-500 dark:text-gray-400">You are not a member of any teams, or team data could not be loaded for selection.</p>
                    )}
                  </div>
                )}
                
                {hackathon.mode === 'TEAM_ONLY' && !hackathon.allow_individuals && (
                   <p className="text-xs text-red-500 dark:text-red-400">This hackathon is TEAM ONLY. Solo participation is not allowed.</p>
                )}
              </>
            )}
          </div>
        )}
        {!isLoading && !currentUser && !error && (
            <p className="text-sm text-yellow-600 dark:text-yellow-400">Please log in to register.</p>
        )}

        <div className="mt-6 text-right">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md dark:bg-slate-700 dark:text-gray-300 dark:hover:bg-slate-600"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
