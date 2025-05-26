// Mock/Seed Data for Frontend Development & Tests

export const mockUser = {
  id: 'user-1',
  email: 'alice@example.com',
  username: 'alice',
  full_name: 'Alice Example',
  role: 'participant',
  avatar_url: '/static/default-avatar.svg',
};

export const mockTeams = [
  {
    id: 'team-1',
    name: 'Frontend Ninjas',
    role: 'owner',
    member_count: 4,
    project_count: 2,
  },
  {
    id: 'team-2',
    name: 'Backend Wizards',
    role: 'member',
    member_count: 5,
    project_count: 1,
  },
];

export const mockProjects = [
  {
    id: 'project-1',
    name: 'Hackathon Platform',
    team_id: 'team-1',
    status: 'ACTIVE',
  },
  {
    id: 'project-2',
    name: 'Realtime Chat',
    team_id: 'team-2',
    status: 'COMPLETED',
  },
];

export const mockJudgingScores = [
  {
    id: 'score-1',
    project_id: 'project-1',
    criteria_id: 'crit-1',
    score: 8,
    comment: 'Great UI',
  },
  {
    id: 'score-2',
    project_id: 'project-1',
    criteria_id: 'crit-2',
    score: 7,
    comment: 'Good documentation',
  },
  {
    id: 'score-3',
    project_id: 'project-2',
    criteria_id: 'crit-1',
    score: 9,
    comment: 'Excellent performance',
  },
];
