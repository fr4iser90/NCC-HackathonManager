"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import axiosInstance from "@/lib/axiosInstance";
import { Criterion, Score, ScoreCreate, ScoreUpdate } from "@/types/judging";
import Link from "next/link";

interface Project {
  id: string;
  name: string;
  team_id: string;
  team?: { id: string; name: string };
}

export default function JudgingDashboard() {
  const { data: session, status } = useSession();
  const [projects, setProjects] = useState<Project[]>([]);
  const [criteria, setCriteria] = useState<Criterion[]>([]);
  const [scores, setScores] = useState<Record<string, Score[]>>({}); // projectId -> Score[]
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [scoreInputs, setScoreInputs] = useState<Record<string, { score: number; comment: string }>>({}); // criterionId -> input
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const userRole = (session?.user as any)?.role;
  const judgeId = (session?.user as any)?.id;
  const token = (session?.user as any)?.accessToken;

  // Auth check
  useEffect(() => {
    if (status === "authenticated" && userRole !== "judge" && userRole !== "admin") {
      window.location.href = "/";
    }
  }, [status, userRole]);

  // Fetch projects
  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axiosInstance.get("/projects/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setProjects(res.data);
      } catch (err: any) {
        setError("Failed to load projects");
      } finally {
        setLoading(false);
      }
    };
    if (status === "authenticated") fetchProjects();
  }, [status, token]);

  // Fetch criteria
  useEffect(() => {
    const fetchCriteria = async () => {
      try {
        const res = await axiosInstance.get("/judging/criteria/", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setCriteria(res.data);
      } catch {}
    };
    if (status === "authenticated") fetchCriteria();
  }, [status, token]);

  // Fetch scores for all projects (for this judge)
  useEffect(() => {
    const fetchScores = async () => {
      if (!judgeId) return;
      try {
        for (const project of projects) {
          const res = await axiosInstance.get(`/judging/scores/project/${project.id}`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          setScores((prev) => ({ ...prev, [project.id]: res.data.filter((s: Score) => s.judge_id === judgeId) }));
        }
      } catch {}
    };
    if (status === "authenticated" && projects.length > 0) fetchScores();
  }, [status, projects, judgeId, token]);

  // Open scoring dialog for a project
  const openScoring = (project: Project) => {
    setActiveProject(project);
    // Pre-fill with existing scores if any
    const projectScores = scores[project.id] || [];
    const inputs: Record<string, { score: number; comment: string }> = {};
    for (const criterion of criteria) {
      const existing = projectScores.find((s) => s.criteria_id === criterion.id);
      inputs[criterion.id] = {
        score: existing?.score ?? 0,
        comment: existing?.comment ?? "",
      };
    }
    setScoreInputs(inputs);
    setFeedback(null);
  };

  // Handle input change
  const handleInput = (criterionId: string, field: "score" | "comment", value: any) => {
    setScoreInputs((prev) => ({
      ...prev,
      [criterionId]: { ...prev[criterionId], [field]: value },
    }));
  };

  // Submit scores for a project
  const handleSubmitScores = async () => {
    if (!activeProject) return;
    setSubmitting(true);
    setFeedback(null);
    try {
      for (const criterion of criteria) {
        const input = scoreInputs[criterion.id];
        if (input.score < 0 || input.score > criterion.max_score) {
          setFeedback(`Score for ${criterion.name} must be between 0 and ${criterion.max_score}`);
          setSubmitting(false);
          return;
        }
        const existing = (scores[activeProject.id] || []).find((s) => s.criteria_id === criterion.id);
        if (existing) {
          // Update
          await axiosInstance.put(`/judging/scores/${existing.id}`, {
            score: input.score,
            comment: input.comment,
          }, {
            headers: { Authorization: `Bearer ${token}` },
          });
        } else {
          // Create
          await axiosInstance.post(`/judging/scores/`, {
            project_id: activeProject.id,
            criteria_id: criterion.id,
            score: input.score,
            comment: input.comment,
          }, {
            headers: { Authorization: `Bearer ${token}` },
          });
        }
      }
      setFeedback("Scores submitted successfully.");
      setActiveProject(null);
      // Refetch scores
      const res = await axiosInstance.get(`/judging/scores/project/${activeProject.id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setScores((prev) => ({ ...prev, [activeProject.id]: res.data.filter((s: Score) => s.judge_id === judgeId) }));
    } catch (err: any) {
      setFeedback(err?.response?.data?.detail || "Error submitting scores.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-6">Judging Dashboard</h1>
      {error && <div className="mb-4 p-3 text-center text-red-700 bg-red-100 border border-red-400 rounded">{error}</div>}
      {loading ? (
        <div>Loading projects...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div key={project.id} className="bg-white border border-gray-200 rounded-lg shadow p-6 flex flex-col gap-2">
              <div className="font-bold text-lg">{project.name}</div>
              <div className="text-gray-600 text-sm">Team: {project.team?.name || project.team_id}</div>
              <button
                className="mt-2 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                onClick={() => openScoring(project)}
              >
                Score Project
              </button>
              <div className="mt-2 text-xs text-gray-500">
                {scores[project.id]?.length ? `${scores[project.id].length} criteria scored` : "Not yet scored"}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Scoring Dialog */}
      {activeProject && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-8 w-full max-w-lg relative">
            <button className="absolute top-2 right-2 text-gray-400 hover:text-gray-700" onClick={() => setActiveProject(null)}>&times;</button>
            <h2 className="text-xl font-bold mb-4">Score: {activeProject.name}</h2>
            {criteria.map((criterion) => (
              <div key={criterion.id} className="mb-4">
                <div className="font-semibold">{criterion.name} <span className="text-xs text-gray-500">(max {criterion.max_score})</span></div>
                <input
                  type="number"
                  min={0}
                  max={criterion.max_score}
                  value={scoreInputs[criterion.id]?.score ?? 0}
                  onChange={e => handleInput(criterion.id, "score", Number(e.target.value))}
                  className="mt-1 block w-full border rounded px-2 py-1"
                />
                <textarea
                  placeholder="Comment (optional)"
                  value={scoreInputs[criterion.id]?.comment ?? ""}
                  onChange={e => handleInput(criterion.id, "comment", e.target.value)}
                  className="mt-1 block w-full border rounded px-2 py-1"
                />
              </div>
            ))}
            {feedback && <div className="mb-2 text-center text-red-600">{feedback}</div>}
            <button
              className="w-full py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 mt-2"
              onClick={handleSubmitScores}
              disabled={submitting}
            >
              {submitting ? "Submitting..." : "Submit Scores"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
} 