// Corresponds to backend's HackathonRegistrationRead schema
export type HackathonRegistration = {
  id: string; // Registration ID
  hackathon_id: string;
  project_id: string;
  user_id?: string | null; // Optional: if a solo participant
  team_id?: string | null; // Optional: if a team participant
  registered_at: string; // ISO date string
  status: string; // e.g., "registered", "withdrawn"
  // Add other fields from HackathonRegistrationRead if needed by frontend
};

// Corresponds to backend's HackathonRead schema
export type Hackathon = {
  id: string;
  name: string;
  description?: string | null;
  start_date: string; // ISO date string
  end_date: string;   // ISO date string
  status: string; // e.g., "UPCOMING", "ACTIVE", "COMPLETED", "ARCHIVED"
  mode: string;   // e.g., "SOLO_PRIMARY", "TEAM_RECOMMENDED", "SOLO_ONLY", "TEAM_ONLY"
  location?: string | null;
  organizer_id?: string | null;
  // organizer?: UserRead; // If you decide to send full organizer object
  requirements?: string[];
  category?: string | null;
  tags?: string[] | null;
  max_team_size?: number | null;
  min_team_size?: number | null;
  registration_deadline?: string | null; // ISO date string
  is_public?: boolean;
  banner_image_url?: string | null;
  rules_url?: string | null;
  sponsor?: string | null;
  prizes?: string | null;
  contact_email?: string | null;
  allow_individuals?: boolean;
  allow_multiple_projects_per_team?: boolean;
  custom_fields?: Record<string, any> | null;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  registrations: HackathonRegistration[]; // Added to match backend
};
