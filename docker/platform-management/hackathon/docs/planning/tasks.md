# Tasks – Hackathon Platform

## Gateway & Infrastructure
- [x] Configure Traefik with HTTPS, domain routing, and security headers
- [x] Set up CrowdSec with bouncer and required collections
- [x] Integrate DDNS updater for dynamic DNS
- [x] Create and test Docker Compose files for gateway services
- [x] Write/update environment files for Traefik, CrowdSec, DDNS
- [x] Implement and test update scripts for gateway env/config

## Database
- [ ] Build and run PostgreSQL container
- [ ] Apply and test init.sql for all schemas (auth, teams, projects, judging)
- [ ] Set up database backup and restore scripts

## Backend (FastAPI)
- [ ] Implement user registration, login, and JWT authentication
- [ ] Implement user roles (participant, judge, admin)
- [ ] Implement team creation, joining, leaving, and member roles
- [ ] Implement project creation, assignment, and status updates
- [ ] Implement judging: criteria management, scoring, feedback, results
- [ ] Implement admin endpoints for user, team, project, judge management
- [ ] Integrate backend with PostgreSQL and Redis
- [ ] Write and run backend tests (pytest)
- [ ] Provide OpenAPI documentation

## Frontend (Next.js)
- [ ] Build login and registration pages
- [ ] Build user dashboard (profile, teams, projects)
- [ ] Build team management UI (create, join, manage members)
- [ ] Build project management UI (create, assign, monitor status)
- [ ] Build judging UI (criteria, scoring, feedback, results)
- [ ] Build admin UI (manage users, teams, projects, judges)
- [ ] Connect frontend to backend API (all features)
- [ ] Implement authentication and authorization flows
- [ ] Write and run frontend tests (Jest, React Testing Library)

## Monitoring & DevOps
- [ ] Set up Prometheus container and configure targets (API, frontend, Traefik)
- [ ] Set up Grafana container and import dashboards
- [ ] Add monitoring alerts for key metrics
- [ ] Write and schedule database/config backup scripts
- [ ] Set up CI/CD workflows (GitHub Actions) for backend, frontend, and Docker images
- [ ] Integrate security checks (CrowdSec, dependency audits for Python/Node)
- [ ] Write and maintain setup/init scripts for full stack

## Templates
- [ ] Finalize Node.js project template (dockerized)
- [ ] Finalize Python project template (dockerized)
- [ ] Finalize React Native project template (dockerized)

## Documentation
- [ ] Complete and update masterplan.md
- [ ] Complete and update phases.md
- [ ] Complete and update development.md
- [ ] Complete and update deployment.md
- [ ] Complete and update tech-stack.md
- [ ] Complete and update domain-model.md
- [ ] Write user guide (for participants)
- [ ] Write admin guide
- [ ] Write judge guide
- [ ] Add troubleshooting and FAQ section
