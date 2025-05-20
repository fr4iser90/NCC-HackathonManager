# Hackathon Platform Feature Roadmap & Tasks

This document tracks planned features, improvements, and tasks for the Hackathon Platform.

## Phase 1: Core Hackathon Workflow (Backend Implemented, Frontend Integration Pending)

-   **[DONE] Backend: Hackathon Participant Registration (Solo & Team)**
    -   [DONE] Database schema for `hackathon_registrations` (links Hackathons to Projects, and to *either* a User for solo participation *or* a Team).
    -   [DONE] SQLAlchemy models updated (`Hackathon`, `Team`, `User`, `Project`, new `HackathonRegistration`).
    -   [DONE] API Endpoint: `POST /hackathons/{hackathon_id}/register` now handles both solo (via `user_id` in body) and team (via `team_id` in body) registration.
        -   Registers an individual or a team for a hackathon.
        -   Automatically creates a `Project` linked to the registration.
-   **[DONE] Backend: Hackathon-Aware Project Submission**
    -   [DONE] API Endpoint: `POST /projects/{project_id}/submit_version`
        -   Submits a new version for an existing project (linked to a hackathon).
        -   Validates hackathon status, deadlines, user permissions.
        -   Creates a `Submission` record with Docker image tag.
        -   Updates `Project` status.
-   **[DONE] Frontend: Hackathon Registration**
    -   **Hackathons Page:**
        -   [DONE] Dedicated, filterable page to list hackathons.
        -   [DONE] Display for each hackathon card:
            - Name, dates, status (with visual cues), mode, category, tags, sponsor, description.
            - Participant count (from `registrations`).
            - Conditional "Register" button for open hackathons (opens Registration Modal).
            - Conditional "View Results" button for completed hackathons.
            - Indication for archived hackathons.
    -   **Registration Process (Frontend):**
        -   [DONE] Registration Modal opens from Hackathon Card.
        -   [DONE] Modal fetches current user data and user's teams.
        -   [DONE] Modal dynamically displays solo/team registration options.
        -   [DONE] Modal allows selection of user's teams for team registration.
        -   [DONE] Modal calls the generalized registration API.
        -   [DONE] More sophisticated UI for team selection if user has many teams.
        -   [DONE] Allow creating a new team from the modal.
    -   **Feedback:**
        -   [DONE] Modal displays loading/error states for data fetching and registration API calls.
        -   [DONE] Success/failure of registration is shown via inline messages (alert replaced).
        -   [TODO] Integrate with a notification system for popups.
-   **[DONE] Frontend: Project Submission for Hackathon**
    -   [DONE] Allow registered participants (solo/team) to navigate to their project for a specific hackathon.
    -   [DONE] Provide an interface to upload a ZIP file for their project, including an optional description for the submission.
    -   [DONE] Call `POST /projects/{project_id}/submit_version` API.
    -   [DONE] Display build logs and submission status.
-   **[DONE] Frontend: Withdraw Registration**
    -   [DONE] Allow registered participants to withdraw their registration (before a deadline).
    -   [DONE] Requires backend endpoint for withdrawal.


## Phase 2: Enhanced Features & User Experience

-   **Team Management (within Hackathon Context)**
    -   [TODO] Team leader can manage project upload permissions for team members (for the specific hackathon project).
    -   [TODO] Team leader can transfer leadership role.
    -   [TODO] Mechanisms for team formation (e.g., users looking for a team, teams looking for members for a specific hackathon).
    -   [IN PROGRESS] Team roles: owner, admin, member, viewer (backend and schema updated; frontend management pending).
-   **Hackathon Management (Admin)**
    -   [TODO] Admin dashboard to manage hackathons (CRUD already exists, but more detailed views/controls).
    -   [TODO] Admin ability to manage hackathon themes, specific submission deadlines (if different from end_date).
    -   [TODO] Admin ability to manage participant limits per hackathon (e.g., max 200 participants).
    -   [TODO] Admin ability to view/manage registered teams and their projects.
-   **User Experience & Information**
    -   [TODO] Users can see a list of participants/teams registered for a hackathon.
    -   [TODO] Clear display of hackathon rules, themes, deadlines, and participant count/limit.
    -   [TODO] User profiles showing hackathon participation history, projects.
    -   [TODO] Improve project/team detail pages for better navigation and context.
-   **Judging Module Integration**
    -   [TODO] Judges can view submitted projects for a hackathon they are assigned to.
    -   [TODO] Judges can submit scores based on defined criteria.
    -   (Requires further planning of the Judging models and workflow if not already detailed)
-   **Leaderboards**
    -   [TODO] Display leaderboards for hackathons (based on judging scores).
    -   [TODO] Filterable leaderboards (e.g., per hackathon, overall user/team rankings).

## Phase 3: Social & Advanced Features

-   **Social Features**
    -   [TODO] Friends list system.
    -   [TODO] Basic messaging system (user-to-user, or within teams).
-   **Notifications**
    -   [TODO] Notifications for important events (e.g., registration confirmation, deadline reminders, new messages).

## Technical Debt / Refinements

-   [TODO] Review and refine authorization logic across all new endpoints (e.g., specific permission checks beyond simple roles).
-   [TODO] Comprehensive API documentation updates (Swagger/OpenAPI).
-   [TODO] Unit and integration tests for new features.
-   [TODO] Review `banner_url` import in `routers/hackathons.py` (seems unused).
-   [TODO] Investigate and resolve any Pylance/linter errors (e.g., the previous indentation warning in `routers/projects.py` if it reappears after API stability).
-   [IN PROGRESS] Keep backend and frontend in sync as new features/roles are added.
