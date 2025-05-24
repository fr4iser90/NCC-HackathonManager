-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS projects;
CREATE SCHEMA IF NOT EXISTS teams;
CREATE SCHEMA IF NOT EXISTS judging;
CREATE SCHEMA IF NOT EXISTS hackathons;

-- Auth schema
CREATE TABLE auth.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(100) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(50) NOT NULL DEFAULT 'participant',
    github_id VARCHAR(255) UNIQUE,
    avatar_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE auth.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    token VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hackathons schema
CREATE TABLE hackathons.hackathons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'upcoming',
    mode VARCHAR(32) NOT NULL DEFAULT 'TEAM_RECOMMENDED',
    requirements JSONB DEFAULT '[]'::jsonb,
    category VARCHAR(64),
    tags JSONB DEFAULT '[]'::jsonb,
    max_team_size INTEGER,
    min_team_size INTEGER,
    registration_deadline TIMESTAMPTZ,
    is_public BOOLEAN DEFAULT TRUE,
    banner_image_url VARCHAR(255),
    rules_url VARCHAR(255),
    sponsor VARCHAR(255),
    prizes TEXT,
    contact_email VARCHAR(255),
    allow_individuals BOOLEAN DEFAULT TRUE,
    allow_multiple_projects_per_team BOOLEAN DEFAULT FALSE,
    voting_type VARCHAR(32) NOT NULL DEFAULT 'judges_only',
    judging_criteria JSONB,
    voting_start TIMESTAMPTZ,
    voting_end TIMESTAMPTZ,
    anonymous_votes BOOLEAN NOT NULL DEFAULT TRUE,
    allow_multiple_votes BOOLEAN NOT NULL DEFAULT FALSE,
    custom_fields JSONB,
    location VARCHAR(255),
    organizer_id UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Teams schema (All teams are hackathon-specific)
CREATE TABLE teams.teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hackathon_id UUID REFERENCES hackathons.hackathons(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_open BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    UNIQUE(hackathon_id, name)
);

CREATE TABLE teams.members (
    team_id UUID REFERENCES teams.teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (team_id, user_id)
);

CREATE TABLE teams.team_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID REFERENCES teams.teams(id) ON DELETE CASCADE,
    hackathon_id UUID REFERENCES hackathons.hackathons(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    archived_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE teams.member_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_history_id UUID REFERENCES teams.team_history(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    joined_at TIMESTAMPTZ NOT NULL,
    left_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE teams.join_requests (
    team_id UUID REFERENCES teams.teams(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    recipient_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (team_id, sender_id)
);

CREATE TABLE teams.invites (
    team_id UUID REFERENCES teams.teams(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    sender_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    recipient_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    token VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (team_id, email)
);

-- Projects schema
CREATE TABLE projects.templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    tech_stack VARCHAR(100)[] NOT NULL,
    resources JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE projects.projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_template_id UUID REFERENCES projects.templates(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    
    -- Neue Felder für Storage und Deployment
    storage_type VARCHAR(50) NOT NULL DEFAULT 'github',
    
    -- Repository URLs
    github_url VARCHAR(255),
    gitlab_url VARCHAR(255),
    bitbucket_url VARCHAR(255),
    
    -- Deployment URLs
    server_url VARCHAR(255),
    docker_url VARCHAR(255),
    kubernetes_url VARCHAR(255),
    cloud_url VARCHAR(255),
    
    -- Archive URLs
    archive_url VARCHAR(255),
    docker_archive_url VARCHAR(255),
    backup_url VARCHAR(255),
    
    -- Docker-spezifische Felder
    docker_image VARCHAR(255),
    docker_tag VARCHAR(100),
    docker_registry VARCHAR(255),
    
    -- Deployment-Status
    build_status VARCHAR(50),
    last_build_date TIMESTAMPTZ,
    last_deploy_date TIMESTAMPTZ,
    
    -- Bestehende Felder
    hackathon_id UUID NOT NULL REFERENCES hackathons.hackathons(id),
    owner_id UUID NOT NULL REFERENCES auth.users(id),
    team_id UUID REFERENCES teams.teams(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE projects.submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects.projects(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    content_value TEXT NOT NULL,
    description TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Judging schema
CREATE TABLE judging.criteria (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    max_score INTEGER NOT NULL,
    weight DECIMAL NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE judging.scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects.projects(id) ON DELETE CASCADE,
    criteria_id UUID REFERENCES judging.criteria(id) ON DELETE CASCADE,
    judge_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    comment TEXT,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (project_id, criteria_id, judge_id)
);

CREATE TABLE hackathons.hackathon_registrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hackathon_id UUID REFERENCES hackathons.hackathons(id) ON DELETE CASCADE NOT NULL,
    project_id UUID REFERENCES projects.projects(id) ON DELETE RESTRICT NOT NULL UNIQUE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    team_id UUID REFERENCES teams.teams(id) ON DELETE CASCADE,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'registered',
    CONSTRAINT chk_participant_type CHECK (
        (user_id IS NOT NULL AND team_id IS NULL) OR
        (user_id IS NULL AND team_id IS NOT NULL)
    )
);

-- Create project versions table
CREATE TABLE projects.project_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects.projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    version_notes TEXT,
    submitted_by UUID NOT NULL REFERENCES auth.users(id),
    status VARCHAR(50) DEFAULT 'pending',
    build_logs TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_sessions_token ON auth.sessions(token);
CREATE INDEX idx_teams_hackathon_id ON teams.teams(hackathon_id);
CREATE INDEX idx_teams_name ON teams.teams(name);
CREATE INDEX idx_scores_project ON judging.scores(project_id);
CREATE INDEX idx_hackathons_name ON hackathons.hackathons(name);
CREATE INDEX idx_team_history_hackathon_id ON teams.team_history(hackathon_id);
CREATE INDEX idx_team_history_team_id ON teams.team_history(team_id);
CREATE INDEX idx_member_history_team_history_id ON teams.member_history(team_history_id);
CREATE INDEX idx_member_history_user_id ON teams.member_history(user_id);
CREATE INDEX idx_join_requests_team ON teams.join_requests(team_id);
CREATE INDEX idx_invites_team ON teams.invites(team_id);
CREATE INDEX idx_hackathon_registrations_hackathon_id ON hackathons.hackathon_registrations(hackathon_id);
CREATE INDEX idx_hackathon_registrations_project_id ON hackathons.hackathon_registrations(project_id);
CREATE INDEX idx_hackathon_registrations_user_id ON hackathons.hackathon_registrations(user_id);
CREATE INDEX idx_hackathon_registrations_team_id ON hackathons.hackathon_registrations(team_id);
CREATE INDEX idx_project_versions_project_id ON projects.project_versions(project_id);
CREATE INDEX idx_project_versions_submitted_by ON projects.project_versions(submitted_by);

-- Create functions
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_teams_updated_at
    BEFORE UPDATE ON teams.teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON projects.projects
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_scores_updated_at
    BEFORE UPDATE ON judging.scores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_hackathons_updated_at
    BEFORE UPDATE ON hackathons.hackathons
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_project_versions_updated_at
    BEFORE UPDATE ON projects.project_versions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
