import { render, screen } from '@testing-library/react';
import Home from '../page'; // Adjust path based on actual file structure relative to __tests__
import { mockUser, mockTeams, mockProjects, mockJudgingScores } from './mockData';

describe('Home Page', () => {
  it('renders the main heading/call to action', () => {
    render(<Home />);

    // Check for the "Get started by editing src/app/page.tsx" text
    // This text is split by a <code> element, so we might need to be flexible
    const instructionText = screen.getByText(/Get started by editing/i);
    expect(instructionText).toBeInTheDocument();

    const fileNameText = screen.getByText(/src\/app\/page\.tsx/i);
    expect(fileNameText).toBeInTheDocument();
  });

  it('renders the "Deploy now" button/link', () => {
    render(<Home />);
    const deployButton = screen.getByRole('link', { name: /Deploy now/i });
    expect(deployButton).toBeInTheDocument();
  });

  it('renders the "Read our docs" button/link', () => {
    render(<Home />);
    const docsButton = screen.getByRole('link', { name: /Read our docs/i });
    expect(docsButton).toBeInTheDocument();
  });
});

describe('Mock/Seed Data', () => {
  it('should provide a valid mock user', () => {
    expect(mockUser).toHaveProperty('id');
    expect(mockUser).toHaveProperty('email');
    expect(mockUser).toHaveProperty('username');
    expect(mockUser).toHaveProperty('role');
  });

  it('should provide at least one mock team', () => {
    expect(Array.isArray(mockTeams)).toBe(true);
    expect(mockTeams.length).toBeGreaterThan(0);
    expect(mockTeams[0]).toHaveProperty('id');
    expect(mockTeams[0]).toHaveProperty('name');
  });

  it('should provide at least one mock project', () => {
    expect(Array.isArray(mockProjects)).toBe(true);
    expect(mockProjects.length).toBeGreaterThan(0);
    expect(mockProjects[0]).toHaveProperty('id');
    expect(mockProjects[0]).toHaveProperty('name');
  });

  it('should provide at least one mock judging score', () => {
    expect(Array.isArray(mockJudgingScores)).toBe(true);
    expect(mockJudgingScores.length).toBeGreaterThan(0);
    expect(mockJudgingScores[0]).toHaveProperty('id');
    expect(mockJudgingScores[0]).toHaveProperty('project_id');
    expect(mockJudgingScores[0]).toHaveProperty('score');
  });
}); 