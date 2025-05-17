# Frontend Tasks (Next.js)

## Authentication
- [ ] Build login page
  - [ ] Form validation (email, password)
  - [ ] Show error on failed login
  - [ ] Redirect on success
  - [ ] Acceptance: User can log in, errors shown on failure
- [ ] Build registration page
  - [ ] Form validation (email, password, username)
  - [ ] Show error on failed registration
  - [ ] Redirect on success
  - [ ] Acceptance: User can register, errors shown on failure
- [ ] Implement JWT-based authentication flow
  - [ ] Store JWT securely (httpOnly cookie or localStorage)
  - [ ] Attach JWT to API requests
  - [ ] Acceptance: Authenticated requests work, JWT not leaked
- [ ] Implement protected routes (user must be logged in)
  - [ ] Redirect to login if not authenticated
  - [ ] Acceptance: Protected pages not accessible without login

## User Dashboard
- [ ] Build user profile page (view/edit profile)
  - [ ] Form for editing profile
  - [ ] Show user info from API
  - [ ] Acceptance: User can view/edit profile, changes saved
- [ ] Show user's teams and projects
  - [ ] Fetch from API, display in dashboard
  - [ ] Acceptance: User sees correct teams/projects
- [ ] Show judging assignments (if judge)
  - [ ] Only for users with judge role
  - [ ] Acceptance: Judges see assignments, others do nicht

## Team Management
- [ ] Build team creation form
  - [ ] Form validation, API call
  - [ ] Acceptance: User can create team, errors handled
- [ ] Build team join/leave UI
  - [ ] List teams, join/leave buttons
  - [ ] Acceptance: User can join/leave teams, state updates
- [ ] Show team members and roles
  - [ ] Fetch from API, display
  - [ ] Acceptance: Team members/roles correct
- [ ] Allow team leader to manage members
  - [ ] Remove/invite members
  - [ ] Acceptance: Only leader can manage, errors handled
- [ ] Show team details and activity
  - [ ] Acceptance: Team details/activity visible

## Project Management
- [ ] Build project creation form
  - [ ] Form validation, API call
  - [ ] Acceptance: User can create project, errors handled
- [ ] Show list of user/team projects
  - [ ] Fetch from API, display
  - [ ] Acceptance: List correct, updates on change
- [ ] Show project details (status, resources, links)
  - [ ] Acceptance: Details match backend
- [ ] Allow project assignment to teams
  - [ ] Acceptance: Only allowed users can assign
- [ ] Show project templates and allow selection
  - [ ] Acceptance: Templates selectable, assignment works

## Judging System
- [ ] Build judging dashboard for judges
  - [ ] List assigned projects
  - [ ] Acceptance: Judges see only their assignments
- [ ] Build criteria scoring UI
  - [ ] Form for each criterion, validation
  - [ ] Acceptance: Scores submitted, errors handled
- [ ] Build feedback form for judges
  - [ ] Acceptance: Feedback submitted, errors handled
- [ ] Show results and feedback to participants
  - [ ] Acceptance: Results/feedback visible to correct users

## Admin UI
- [ ] Build admin dashboard
  - [ ] Acceptance: Only admin can access
- [ ] Manage users (list, edit, delete)
  - [ ] Acceptance: CRUD works, errors handled
- [ ] Manage teams (list, edit, delete)
  - [ ] Acceptance: CRUD works, errors handled
- [ ] Manage projects (list, edit, delete)
  - [ ] Acceptance: CRUD works, errors handled
- [ ] Manage judges and assignments
  - [ ] Acceptance: CRUD works, errors handled

## Integration
- [ ] Connect all pages to backend API
  - [ ] Use React Query for data fetching/caching
  - [ ] Handle API errors and loading states
  - [ ] Acceptance: All data loads, errors shown
- [ ] Use Zod for form validation
  - [ ] Acceptance: Invalid input blocked, errors shown
- [ ] API contract review with backend
  - [ ] Acceptance: All endpoints match, no contract errors

## Testing & Quality
- [ ] Write unit tests for all components (Jest, RTL)
- [ ] Write integration tests for main flows
- [ ] Write E2E tests (Playwright/Cypress)
- [ ] Ensure 80%+ test coverage
- [ ] Lint and format code (ESLint, Prettier)
- [ ] All tests pass in CI
- [ ] Acceptance: All main flows covered by tests

## UX & Accessibility
- [ ] Ensure responsive design (mobile, tablet, desktop)
- [ ] Use TailwindCSS for styling
- [ ] Ensure accessibility (a11y) for all forms and navigation
- [ ] Add helpful error and success messages
- [ ] Acceptance: App usable on all devices, a11y checks pass

## Design System
- [ ] Define and document design system (colors, spacing, typography)
- [ ] Use consistent components throughout app
- [ ] Acceptance: All pages/components follow design system

## Internationalization (i18n)
- [ ] Add i18n support (if needed)
- [ ] Acceptance: App can be translated, language switch works

## Seed/Test Data
- [ ] Add mock/demo data for development/testing
- [ ] Test all main flows with seed data
- [ ] Acceptance: App works with demo data

## Deployment
- [ ] Build and test Docker image for frontend
- [ ] Ensure .env works for prod/dev
- [ ] Frontend runs in Docker Compose with backend
- [ ] Acceptance: Frontend reachable, all pages work in Docker
- [ ] Update README with frontend setup and usage

## Error Handling
- [ ] Implement global error boundary/component
- [ ] Show user-friendly error messages for all API/UI errors
- [ ] Acceptance: No unhandled errors, user always sees helpful message

## Documentation
- [ ] Document all components and pages (JSDoc/TypeDoc)
- [ ] Add usage examples for custom hooks/components
- [ ] Update README with frontend setup and usage
- [ ] Acceptance: Docs up to date, new devs can onboard easily