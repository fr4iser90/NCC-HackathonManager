// Judging types for frontend

export interface Criterion {
  id: string;
  name: string;
  description?: string;
  max_score: number;
  weight: number;
  created_at: string;
  updated_at: string;
}

export interface Score {
  id: string;
  project_id: string;
  criteria_id: string;
  judge_id: string;
  score: number;
  comment?: string;
  submitted_at: string;
  updated_at: string;
}

export interface ScoreCreate {
  project_id: string;
  criteria_id: string;
  score: number;
  comment?: string;
}

export interface ScoreUpdate {
  score?: number;
  comment?: string;
} 