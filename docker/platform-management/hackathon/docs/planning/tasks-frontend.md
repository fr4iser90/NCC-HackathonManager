# Frontend Tasks (Next.js)

## Authentication
- [x] Build login page
- [x] Form validation (email, password)
- [x] Show error on failed login
- [x] Redirect on success
- [x] Acceptance: User can log in, errors shown on failure
- [ ] Build registration page
- [ ] Form validation (email, password, username)
- [ ] Show error on failed registration
- [ ] Redirect on success
- [ ] Acceptance: User can register, errors shown on failure
- [x] Implement JWT-based authentication flow
- [x] Store JWT securely (httpOnly cookie or localStorage)
- [x] Attach JWT to API requests
- [x] Acceptance: Authenticated requests work, JWT not leaked
- [x] Implement protected routes (user must be logged in)
- [x] Redirect to login if not authenticated
- [x] Acceptance: Protected pages not accessible without login

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
- [x] Build team join/leave UI (teilweise)
- [x] List teams, join/leave buttons (Logik vorhanden, UI noch ausbaufähig)
- [x] Acceptance: User can join/leave teams, state updates
- [x] Show team members and roles
- [x] Fetch from API, display
- [x] Acceptance: Team members/roles correct
- [x] Allow team leader to manage members
- [x] Remove/invite members (Remove: ja, Invite: offen)
- [x] Acceptance: Only leader can manage, errors handled
- [x] Show team details and activity
- [x] Acceptance: Team details/activity visible

## Project Management
- [x] Build project creation form
- [x] Form validation, API call
- [x] Acceptance: User can create project, errors handled
- [x] Show list of user/team projects
- [x] Fetch from API, display
- [x] Acceptance: List correct, updates on change
- [x] Show project details (status, resources, links)
- [x] Acceptance: Details match backend
- [x] Allow project assignment to teams
- [x] Acceptance: Only allowed users can assign
- [x] Show project templates and allow selection
- [x] Acceptance: Templates selectable, assignment works

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
- [x] Build admin dashboard
- [x] Acceptance: Only admin can access
- [x] Manage users (list, edit, delete)
- [x] Acceptance: CRUD works, errors handled
- [x] Manage teams (list, edit, delete)
- [x] Acceptance: CRUD works, errors handled
- [x] Manage projects (list, edit, delete)
- [x] Acceptance: CRUD works, errors handled
- [ ] Manage judges and assignments
- [ ] Acceptance: CRUD works, errors handled

## Integration
- [x] Connect all pages to backend API
- [x] Use React Query for data fetching/caching (offen)
- [x] Handle API errors and loading states
- [x] Acceptance: All data loads, errors shown
- [ ] Use React Query for data fetching/caching
- [ ] Acceptance: All data loads, errors shown
- [ ] Use Zod for form validation
- [ ] Acceptance: Invalid input blocked, errors shown
- [x] API contract review with backend
- [x] Acceptance: All endpoints match, no contract errors

## Testing & Quality
- [x] Write unit tests for alle Komponenten (Startseite)
- [ ] Write integration tests for main flows
- [ ] Write E2E tests (Playwright/Cypress)
- [ ] Ensure 80%+ test coverage
- [x] Lint and format code (ESLint, Prettier)
- [ ] All tests pass in CI

## UX & Accessibility
- [x] Ensure responsive design (mobile, tablet, desktop)
- [x] Use TailwindCSS for styling
- [ ] Ensure accessibility (a11y) for all forms and navigation
- [x] Add helpful error and success messages

## Design System
- [ ] Define and document design system (colors, spacing, typography)
- [x] Use consistent components throughout app

## Internationalization (i18n)
- [ ] Add i18n support (if needed)
- [ ] Acceptance: App can be translated, language switch works

## Seed/Test Data
- [ ] Add mock/demo data for development/testing
- [ ] Test all main flows with seed data
- [ ] Acceptance: App works with demo data

## Deployment
- [x] Build and test Docker image for frontend
- [x] Ensure .env works for prod/dev
- [x] Frontend runs in Docker Compose with backend
- [x] Update README with frontend setup and usage

## Error Handling
- [ ] Implement global error boundary/component
- [x] Show user-friendly error messages for all API/UI errors

## Documentation
- [ ] Document all components and pages (JSDoc/TypeDoc)
- [ ] Add usage examples for custom hooks/components
- [x] Update README with frontend setup and usage
- [ ] Acceptance: Docs up to date, new devs can onboard easily