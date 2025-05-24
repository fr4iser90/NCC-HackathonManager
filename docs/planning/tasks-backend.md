# Backend Tasks (FastAPI)

## User Management
- [ ] Design user model/schema in SQLAlchemy
  - [ ] Fields: id, email, username, hashed_password, role, created_at, updated_at
  - [ ] Migration script created and tested
  - [ ] Acceptance: User table exists, migration runs without error
- [ ] Implement /api/users/register endpoint
  - [ ] Validate input (email, password, username)
  - [ ] Hash password securely (argon2/bcrypt)
  - [ ] Store user in database
  - [ ] Return JWT on success
  - [ ] Handle duplicate email/username errors
  - [ ] Acceptance: Registration returns 201, user in DB, JWT valid, errors handled
- [ ] Implement /api/users/login endpoint
  - [ ] Validate credentials
  - [ ] Return JWT on success
  - [ ] Handle invalid credentials error
  - [ ] Acceptance: Login returns 200, JWT valid, wrong password returns 401
- [ ] Implement JWT authentication dependency
  - [ ] Protect all private endpoints
  - [ ] Acceptance: Unauthorized access returns 401
- [ ] Implement user profile endpoint (/api/users/me)
  - [ ] Returns user info for current JWT
  - [ ] Acceptance: Returns correct user, 401 if not logged in
- [ ] Implement user role management (participant, judge, admin)
  - [ ] Role field in DB, role-based access in endpoints
  - [ ] Acceptance: Only admin can access admin endpoints, roles enforced
- [ ] Implement password reset (optional)
  - [ ] Endpoint to request password reset (email notification)
  - [ ] Endpoint to reset password with token
  - [ ] Acceptance: Password reset flow works, emails sent
- [ ] Write tests for all user endpoints (pytest, coverage > 80%)

## Team Management
- [ ] Design team and membership models (team, team_members)
  - [ ] Migration script created and tested
  - [ ] Acceptance: Team and membership tables exist, migration runs
- [ ] Implement /api/teams/create endpoint
  - [ ] Only logged-in users
  - [ ] Acceptance: Team created, user is leader
- [ ] Implement /api/teams/join and /api/teams/leave endpoints
  - [ ] Handle already member/not member errors
  - [ ] Acceptance: User can join/leave, cannot join twice, errors handled
- [ ] Implement team member role management (leader, member)
  - [ ] Only leader can remove members
  - [ ] Acceptance: Role logic enforced, only leader can remove
- [ ] Implement team listing and detail endpoints
  - [ ] Acceptance: List returns all teams, detail returns members
- [ ] Write tests for all team endpoints

## Project Management
- [ ] Design project and template models
  - [ ] Migration script created and tested
  - [ ] Acceptance: Project and template tables exist, migration runs
- [ ] Implement /api/projects/create endpoint
  - [ ] Only team leaders
  - [ ] Acceptance: Project created, linked to team
- [ ] Implement /api/projects/assign endpoint
  - [ ] Assign template to project
  - [ ] Acceptance: Assignment works, only allowed users
- [ ] Implement project status update endpoint
  - [ ] Status: draft, pending, running, finished
  - [ ] Acceptance: Status changes, only allowed users
- [ ] Implement project listing and detail endpoints
  - [ ] Acceptance: List returns all projects, detail returns info
- [ ] Write tests for all project endpoints

## Judging System
- [ ] Design criteria, score, and feedback models
  - [ ] Migration script created and tested
  - [ ] Acceptance: Criteria, score, feedback tables exist, migration runs
- [ ] Implement /api/judging/criteria endpoints (CRUD)
  - [ ] Only admin can create/edit/delete
  - [ ] Acceptance: CRUD works, permissions enforced
- [ ] Implement /api/judging/score endpoint
  - [ ] Judges can score projects
  - [ ] Acceptance: Score saved, only once per judge/project/criteria
- [ ] Implement /api/judging/feedback endpoint
  - [ ] Judges can leave feedback
  - [ ] Acceptance: Feedback saved, only once per judge/project
- [ ] Implement results calculation endpoint
  - [ ] Aggregate scores, weighted by criteria
  - [ ] Acceptance: Results correct, matches manual calculation
- [ ] Write tests for all judging endpoints

## Admin Management
- [ ] Implement admin endpoints for user, team, project, judge management
  - [ ] List, edit, delete for each entity
  - [ ] Acceptance: Only admin can access, CRUD works
- [ ] Write tests for all admin endpoints

## Integration
- [ ] Integrate backend with PostgreSQL (env, connection, migrations)
- [ ] Integrate backend with Redis (if used for sessions/cache)
- [ ] Provide OpenAPI documentation for all endpoints
  - [ ] Swagger UI reachable at /docs
  - [ ] Acceptance: All endpoints documented, tested via Swagger

## Error Handling
- [ ] Implement global error handler for API
- [ ] Return consistent error responses (JSON, status code, message)
- [ ] Acceptance: All errors handled, no stack traces in response

## Testing & Quality
- [ ] Write unit and integration tests (pytest)
- [ ] Set up test database (pytest fixture)
- [ ] Ensure 80%+ test coverage (pytest --cov)
- [ ] Lint and format code (black, isort)
- [ ] All tests pass in CI

## Security
- [ ] Implement password hashing (argon2/bcrypt)
- [ ] Validate all user input (pydantic)
- [ ] Add rate limiting to auth endpoints
- [ ] Review for common vulnerabilities (OWASP)
- [ ] Test: No sensitive data in error messages
- [ ] Security review before production

## Email/Notifications
- [ ] Set up email sending (SMTP or service)
- [ ] Send email on registration (optional)
- [ ] Send email for password reset
- [ ] Acceptance: Emails sent, errors handled

## Seed/Test Data
- [ ] Write script to create demo users, teams, projects, judges
- [ ] Test: System works with seed data

## Deployment
- [ ] Build and test Docker image for backend
- [ ] Ensure .env works for prod/dev
- [ ] Backend runs in Docker Compose with DB
- [ ] Acceptance: Backend reachable, all endpoints work in Docker