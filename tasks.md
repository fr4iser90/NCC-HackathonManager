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

## Phase 2: Team System Refactoring

-   **Team System Refactoring**
    -   [DONE] Database Schema Updates:
        -   [DONE] Create hackathon-specific team tables
        -   [DONE] Update user-team relationships
        -   [DONE] Create team history tables
    -   [DONE] API Endpoint Updates:
        -   [DONE] Create hackathon-specific team endpoints
        -   [DONE] Update team-related queries
        -   [DONE] Add team history endpoints
    -   [TODO] Frontend Updates:
        -   [TODO] Update team management UI
        -   [TODO] Modify team creation flow
        -   [TODO] Update team display components
        -   [TODO] Add team history views
    -   [TODO] Testing & Validation:
        -   [TODO] Update unit tests
        -   [TODO] Create integration tests
        -   [TODO] Perform system testing
        -   [TODO] Validate data integrity

## Phase 3: Enhanced Features & User Experience

-   **Team Management (Hackathon-Specific)**
    -   [DONE] Hackathon Team Formation System:
        -   [DONE] Team creation during hackathon registration:
            -   [DONE] Create team with hackathon-specific name and description
            -   [DONE] Set team size limits per hackathon
            -   [DONE] Define team roles for the hackathon duration
            -   [DONE] Team visibility settings
        -   [DONE] Team finder for hackathon:
            -   [DONE] Team join requests
            -   [DONE] Team invitation system
        -   [TODO] Team workspace for hackathon:
            -   [TODO] Project management tools
            -   [TODO] Team chat/announcements
            -   [TODO] Resource sharing
            -   [TODO] Task tracking
    -   [DONE] Post-Hackathon Team Handling:
        -   [DONE] Team archival system
        -   [DONE] Team history preservation
        -   [DONE] Team member history tracking

-   **Hackathon Management (Admin)**
    -   [TODO] Admin dashboard to manage hackathons:
        -   [TODO] Comprehensive hackathon overview:
            -   [TODO] Registration statistics
            -   [TODO] Team formation progress
            -   [TODO] Project submission status
            -   [TODO] Resource usage metrics
        -   [TODO] Participant management:
            -   [TODO] View/manage registrations
            -   [TODO] Handle waitlist
            -   [TODO] Process withdrawals
            -   [TODO] Export participant data
        -   [TODO] Team management:
            -   [TODO] View all teams for specific hackathon
            -   [TODO] Team status tracking
            -   [TODO] Team size monitoring
            -   [TODO] Team merge/split tools
    -   [TODO] Admin ability to manage hackathon themes:
        -   [TODO] Theme creation and editing
        -   [TODO] Theme assignment to hackathons
        -   [TODO] Theme-based team matching
        -   [TODO] Theme resource management
    -   [TODO] Admin ability to manage deadlines:
        -   [TODO] Multiple deadline types:
            -   [TODO] Registration deadlines
            -   [TODO] Team formation deadlines
            -   [TODO] Project submission deadlines
            -   [TODO] Judging deadlines
        -   [TODO] Deadline notifications
        -   [TODO] Deadline extensions
        -   [TODO] Timezone handling
        -   [TODO] Admin ability to manage participant limits:
            -   [TODO] Set overall participant cap
            -   [TODO] Configure team size limits
            -   [TODO] Set minimum team size
            -   [TODO] Handle overflow/waitlist

-   **User Experience & Information**
    -   [TODO] User profiles showing hackathon participation history:
        -   [TODO] Profile dashboard:
            -   [TODO] Participation history with team information
            -   [TODO] Project portfolio
            -   [TODO] Skills showcase
            -   [TODO] Achievements display
        -   [TODO] Activity timeline:
            -   [TODO] Past hackathons with team details
            -   [TODO] Current hackathon participation
            -   [TODO] Future registrations
        -   [TODO] Team history:
            -   [TODO] Past hackathon teams
            -   [TODO] Team achievements
            -   [TODO] Team roles in past hackathons
    -   [TODO] Hackathon-specific team directory:
        -   [TODO] Current hackathon teams:
            -   [TODO] Team profiles
            -   [TODO] Team member list
            -   [TODO] Team project status
            -   [TODO] Team achievements
        -   [TODO] Team finder:
            -   [TODO] Filter by skills
            -   [TODO] Filter by availability
            -   [TODO] Search functionality
            -   [TODO] Team size preferences

## Scoring System & Points

-   [TODO] Backend: Implement scoring schema and models
    -   [TODO] Create `Score` model to track points for users/teams
    -   [TODO] Create `Achievement` model to define different types of achievements:
        -   [TODO] Project-based achievements:
            -   [TODO] First submission bonus
            -   [TODO] Multiple submission milestones
            -   [TODO] Project completion milestones
            -   [TODO] Code quality achievements (if integrated with code analysis)
        -   [TODO] Team-based achievements:
            -   [TODO] Team formation milestones
            -   [TODO] Team size achievements (e.g., full team bonus)
            -   [TODO] Team collaboration milestones
            -   [TODO] Cross-team collaboration points
        -   [TODO] Hackathon participation achievements:
            -   [TODO] Early registration bonus
            -   [TODO] Workshop attendance tracking
            -   [TODO] Mentor interaction points
            -   [TODO] Sponsor challenge completion
        -   [TODO] Judging-based achievements:
            -   [TODO] Category winner points
            -   [TODO] Special recognition awards
            -   [TODO] Judge's choice awards
        -   [TODO] Community achievements:
            -   [TODO] Helping other participants
            -   [TODO] Documentation contributions
            -   [TODO] Resource sharing
    -   [TODO] Define scoring criteria and point allocation rules:
        -   [TODO] Base points for different achievement types
        -   [TODO] Time-based bonuses:
            -   [TODO] Early registration multipliers
            -   [TODO] Early submission bonuses
            -   [TODO] Workshop attendance timing
        -   [TODO] Team-based bonuses:
            -   [TODO] Team size scaling factors
            -   [TODO] Cross-team collaboration multipliers
            -   [TODO] Mentor-mentee relationship points
        -   [TODO] Quality-based multipliers:
            -   [TODO] Code quality scores
            -   [TODO] Documentation completeness
            -   [TODO] Project complexity factors
    -   [TODO] Implement point calculation logic for different achievements
-   [TODO] Backend: Scoring API Endpoints
    -   [TODO] `POST /scores` - Record new scores/points
    -   [TODO] `GET /scores/{user_id}` - Get user's score history
    -   [TODO] `GET /scores/team/{team_id}` - Get team's score history
    -   [TODO] `GET /scores/hackathon/{hackathon_id}` - Get all scores for a hackathon
    -   [TODO] `GET /achievements` - List available achievements
    -   [TODO] `GET /achievements/{user_id}` - Get user's earned achievements
    -   [TODO] `GET /achievements/team/{team_id}` - Get team's earned achievements
    -   [TODO] `GET /scores/leaderboard` - Get current leaderboard
    -   [TODO] `GET /scores/statistics` - Get scoring statistics and trends
-   [TODO] Frontend: Score Display & Management
    -   [TODO] Add score display to user/team profiles
    -   [TODO] Create score history view with detailed breakdown
    -   [TODO] Implement score update notifications
    -   [TODO] Add admin interface for score management:
        -   [TODO] Achievement configuration panel
            -   [TODO] Create/edit achievement types
            -   [TODO] Set point values and conditions
            -   [TODO] Define achievement triggers
            -   [TODO] Configure achievement visibility
        -   [TODO] Score adjustment tools
            -   [TODO] Manual point adjustments with audit log
            -   [TODO] Bulk score updates for specific achievements
            -   [TODO] Score recalculation for specific events
            -   [TODO] Import/export score data
        -   [TODO] Achievement management
            -   [TODO] Award/revoke achievements manually
            -   [TODO] View achievement distribution
            -   [TODO] Generate achievement reports
            -   [TODO] Track achievement progress
        -   [TODO] Scoring rules management
            -   [TODO] Configure scoring multipliers
            -   [TODO] Set time-based bonus rules
            -   [TODO] Define team size bonus rules
            -   [TODO] Set quality-based multipliers
        -   [TODO] Audit and moderation
            -   [TODO] View score change history
            -   [TODO] Review disputed scores
            -   [TODO] Handle score appeals
            -   [TODO] Generate audit reports
-   [TODO] Integration with Existing Features
    -   [TODO] Link scoring system with team management
        -   [TODO] Team role-based score permissions
        -   [TODO] Team leader score management tools
    -   [TODO] Integrate with hackathon management
        -   [TODO] Hackathon-specific achievement rules
        -   [TODO] Custom scoring rules per hackathon
    -   [TODO] Connect with user profiles
        -   [TODO] Display achievements on profiles
        -   [TODO] Show score history and trends
    -   [TODO] Notification system integration
        -   [TODO] Achievement earned notifications
        -   [TODO] Score milestone alerts
        -   [TODO] Leaderboard position changes

## Leaderboards

-   [TODO] Backend: Leaderboard System
    -   [TODO] Create `Leaderboard` model and caching mechanism
    -   [TODO] Implement real-time leaderboard updates
    -   [TODO] Add support for different leaderboard types (overall, hackathon-specific, team-based)
-   [TODO] Backend: Leaderboard API Endpoints
    -   [TODO] `GET /leaderboards` - Get available leaderboards
    -   [TODO] `GET /leaderboards/{type}` - Get specific leaderboard type
    -   [TODO] `GET /leaderboards/hackathon/{hackathon_id}` - Get hackathon-specific leaderboard
-   [TODO] Frontend: Leaderboard Interface
    -   [TODO] Create dedicated leaderboard page with filters
    -   [TODO] Implement real-time updates for live events
    -   [TODO] Add visual indicators for position changes
    -   [TODO] Create leaderboard widgets for dashboard/homepage
    -   [TODO] Add export functionality for leaderboard data

## Judging Module Integration

-   [TODO] Judges can view submitted projects for a hackathon they are assigned to.
-   [TODO] Judges can submit scores based on defined criteria.
-   (Requires further planning of the Judging models and workflow if not already detailed)

## Social Features

-   [TODO] Friends list system.
-   [TODO] Basic messaging system (user-to-user, or within teams).

## Notifications

-   [TODO] Notifications for important events (e.g., registration confirmation, deadline reminders, new messages).

## Technical Debt / Refinements

-   [TODO] Review and refine authorization logic across all new endpoints (e.g., specific permission checks beyond simple roles).
-   [TODO] Comprehensive API documentation updates (Swagger/OpenAPI).
-   [TODO] Unit and integration tests for new features.
-   [TODO] Review `banner_url` import in `routers/hackathons.py` (seems unused).
-   [TODO] Investigate and resolve any Pylance/linter errors (e.g., the previous indentation warning in `routers/projects.py` if it reappears after API stability).
-   [IN PROGRESS] Keep backend and frontend in sync as new features/roles are added.
