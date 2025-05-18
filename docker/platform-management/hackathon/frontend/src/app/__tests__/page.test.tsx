import { render, screen } from '@testing-library/react';
import Home from '../page'; // Adjust path based on actual file structure relative to __tests__

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