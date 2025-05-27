import os
import sys
import uuid
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("test_data")

# Adjust path to allow imports from the 'app' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.user import User, UserRole, UserRoleAssociation
from app.models.team import (
    Team,
    TeamMember,
    TeamMemberRole,
    JoinRequest,
    JoinRequestStatus,
    TeamStatus,
)
from app.models.team import TeamInvite, TeamInviteStatus
from app.models.project import Project
from app.models.judging import Criterion, Score
from app.auth import get_password_hash
from app.models.hackathon import Hackathon
from app.schemas.hackathon import HackathonStatus, HackathonMode
from app.schemas.project import ProjectStatus, ProjectStorageType
from app.models.hackathon_registration import HackathonRegistration

# --- Judging Criteria ---
CRITERIA = [
    {
        "name": "Innovation",
        "description": "How innovative is the project?",
        "max_score": 10,
        "weight": 1.0,
    },
    {
        "name": "Technical Quality",
        "description": "How technically sound is the project?",
        "max_score": 10,
        "weight": 1.0,
    },
]

# --- Testdaten ---
USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "role": UserRole.ADMIN,
        "password": "adminpass",
        "github_id": "admin-github",
    },
    {
        "email": "judge@example.com",
        "username": "judge",
        "role": UserRole.JUDGE,
        "password": "judgepass",
        "github_id": "judge-github",
    },
    {
        "email": "mentor@example.com",
        "username": "mentor",
        "role": UserRole.MENTOR,
        "password": "mentorpass",
        "github_id": "mentor-github",
    },
    {
        "email": "user1@example.com",
        "username": "user1",
        "role": UserRole.PARTICIPANT,
        "password": "userpass1",
        "github_id": "user1-github",
    },
    {
        "email": "user2@example.com",
        "username": "user2",
        "role": UserRole.PARTICIPANT,
        "password": "userpass2",
        "github_id": "user2-github",
    },
]

# Teams are now defined per hackathon
TEAMS = {
    "Solo Hackathon": [
        {
            "name": "Solo Team 1",
            "description": "A solo participant team",
            "is_open": True,
        },
    ],
    "Team Hackathon": [
        {"name": "Open Team", "description": "A public team", "is_open": True},
        {"name": "Closed Team", "description": "A private team", "is_open": False},
    ],
}

HACKATHONS = [
    {
        "name": "Solo Hackathon",
        "description": "Nur Einzelteilnehmer",
        "start_date": datetime(2025, 5, 1, 10, 0),
        "end_date": datetime(2025, 5, 3, 18, 0),
        "status": "ACTIVE",
        "mode": "SOLO_ONLY",
        "requirements": ["UI"],
        "category": "UI/UX",
        "tags": ["Beginner", "Remote"],
        "max_team_size": 1,
        "min_team_size": 1,
        "registration_deadline": datetime(2025, 4, 25, 23, 59),
        "is_public": True,
        "banner_image_url": "https://example.com/banner1.png",
        "rules_url": "https://example.com/rules1.pdf",
        "sponsor": "Company X",
        "prizes": "1st: 1000Points, 2nd: 500Points",
        "contact_email": "orga@hackathon.com",
        "allow_individuals": True,
        "allow_multiple_projects_per_team": False,
        "custom_fields": {"special_award": "Best UI"},
        "voting_type": "users",
        "judging_criteria": CRITERIA,
        "voting_start": datetime(2025, 5, 4, 10, 0),
        "voting_end": datetime(2025, 5, 11, 18, 0),
        "anonymous_votes": True,
        "allow_multiple_votes": False,
    },
    {
        "name": "Team Hackathon",
        "description": "Nur Teams",
        "start_date": datetime(2025, 6, 1, 10, 0),
        "end_date": datetime(2025, 6, 3, 18, 0),
        "status": "ACTIVE",
        "mode": "TEAM_ONLY",
        "requirements": ["Security", "Backend"],
        "category": "Security",
        "max_team_size": 4,
        "min_team_size": 2,
        "allow_individuals": False,
        "voting_type": "judges_only",
        "judging_criteria": CRITERIA,
        "voting_start": datetime(2025, 6, 4, 10, 0),
        "voting_end": datetime(2025, 6, 11, 18, 0),
        "anonymous_votes": False,
        "allow_multiple_votes": False,
    },
    {
        "name": "Hackathon Completed",
        "description": "Herbst 2025",
        "start_date": datetime(2025, 9, 1, 10, 0),
        "end_date": datetime(2025, 9, 3, 18, 0),
        "status": "COMPLETED",
        "category": "General",
        "voting_type": "public",
        "judging_criteria": CRITERIA,
        "voting_start": datetime(2025, 9, 4, 10, 0),
        "voting_end": datetime(2025, 9, 11, 18, 0),
        "anonymous_votes": True,
        "allow_multiple_votes": True,
    },
    {
        "name": "Hackathon Archived",
        "description": "Winter 2025",
        "start_date": datetime(2025, 12, 1, 10, 0),
        "end_date": datetime(2025, 12, 3, 18, 0),
        "status": "ARCHIVED",
        "category": "General",
        "voting_type": "public",
        "judging_criteria": CRITERIA,
        "voting_start": datetime(2025, 12, 4, 10, 0),
        "voting_end": datetime(2025, 12, 11, 18, 0),
        "anonymous_votes": True,
        "allow_multiple_votes": True,
    },
]

PROJECTS = [
    {"name": "Test Project 1", "description": "Demo project 1", "status": "ACTIVE"},
    {"name": "Test Project 2", "description": "Demo project 2", "status": "DRAFT"},
]


def main():
    db = SessionLocal()
    try:
        # --- Users ---
        user_objs = {}
        for u in USERS:
            user = db.query(User).filter_by(email=u["email"]).first()
            if not user:
                user = User(
                    email=u["email"],
                    username=u["username"],
                    hashed_password=get_password_hash(u["password"]),
                    full_name=u.get("full_name"),
                    github_id=u.get("github_id"),
                    avatar_url=u.get("avatar_url"),
                    is_active=True,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            # Rolle setzen, falls noch nicht vorhanden
            if u.get("role"):
                has_role = (
                    db.query(UserRoleAssociation)
                    .filter_by(user_id=user.id, role=u["role"])
                    .first()
                )
                if not has_role:
                    db.add(UserRoleAssociation(user_id=user.id, role=u["role"]))
                    db.commit()
            user_objs[u["username"]] = user
        logger.info(f"Users: {[u.email for u in user_objs.values()]}")

        # --- Hackathons ---
        hackathon_objs = {}
        for h in HACKATHONS:
            hack = db.query(Hackathon).filter_by(name=h["name"]).first()
            if not hack:
                hack = Hackathon(
                    id=uuid.uuid4(),
                    name=h["name"],
                    description=h["description"],
                    start_date=h["start_date"],
                    end_date=h["end_date"],
                    status=HackathonStatus[h["status"]],
                    mode=h.get("mode", "TEAM_ONLY"),
                    requirements=h.get("requirements", []),
                    category=h.get("category"),
                    tags=h.get("tags", []),
                    max_team_size=h.get("max_team_size"),
                    min_team_size=h.get("min_team_size"),
                    registration_deadline=h.get("registration_deadline"),
                    is_public=h.get("is_public", True),
                    banner_image_url=h.get("banner_image_url"),
                    rules_url=h.get("rules_url"),
                    sponsor=h.get("sponsor"),
                    prizes=h.get("prizes"),
                    contact_email=h.get("contact_email"),
                    allow_individuals=h.get("allow_individuals", True),
                    allow_multiple_projects_per_team=h.get(
                        "allow_multiple_projects_per_team", False
                    ),
                    custom_fields=h.get("custom_fields"),
                    voting_type=h.get("voting_type", "judges_only"),
                    judging_criteria=h.get("judging_criteria"),
                    voting_start=h.get("voting_start"),
                    voting_end=h.get("voting_end"),
                    anonymous_votes=h.get("anonymous_votes", True),
                    allow_multiple_votes=h.get("allow_multiple_votes", False),
                )
                db.add(hack)
                db.commit()
                db.refresh(hack)
            hackathon_objs[h["name"]] = hack
        logger.info(f"Hackathons: {[h.name for h in hackathon_objs.values()]}")

        # --- Teams ---
        team_objs = {}
        for hackathon_name, teams in TEAMS.items():
            hackathon = hackathon_objs[hackathon_name]
            for t in teams:
                team = (
                    db.query(Team)
                    .filter_by(name=t["name"], hackathon_id=hackathon.id)
                    .first()
                )
                if not team:
                    team = Team(
                        id=uuid.uuid4(),
                        name=t["name"],
                        description=t["description"],
                        is_open=t["is_open"],
                        hackathon_id=hackathon.id,
                        status=TeamStatus.active,
                    )
                    db.add(team)
                    db.commit()
                    db.refresh(team)
                team_objs[f"{hackathon_name}_{t['name']}"] = team
        logger.info(f"Teams: {[t.name for t in team_objs.values()]}")

        # --- Team Members ---
        # Admin is owner of Open Team in Team Hackathon
        # Judge is owner of Closed Team in Team Hackathon
        # user1 is member in both teams in Team Hackathon
        members = [
            (
                team_objs["Team Hackathon_Open Team"],
                user_objs["admin"],
                TeamMemberRole.owner,
            ),
            (
                team_objs["Team Hackathon_Closed Team"],
                user_objs["judge"],
                TeamMemberRole.owner,
            ),
            (
                team_objs["Team Hackathon_Open Team"],
                user_objs["user1"],
                TeamMemberRole.member,
            ),
            (
                team_objs["Team Hackathon_Closed Team"],
                user_objs["user1"],
                TeamMemberRole.member,
            ),
            (
                team_objs["Solo Hackathon_Solo Team 1"],
                user_objs["user1"],
                TeamMemberRole.owner,
            ),
        ]
        for team, user, role in members:
            exists = (
                db.query(TeamMember).filter_by(team_id=team.id, user_id=user.id).first()
            )
            if not exists:
                db.add(TeamMember(team_id=team.id, user_id=user.id, role=role))
        db.commit()
        logger.info("Team members assigned.")

        # --- Projects ---
        project_objs = {}
        # Projects for different hackathons
        project_defs = [
            {
                "name": "Docker Web App",
                "description": "Full stack web application in Docker",
                "status": ProjectStatus.ACTIVE,
                "storage_type": ProjectStorageType.DOCKER_HYBRID,
                "hackathon": hackathon_objs["Team Hackathon"],
                "team_id": team_objs["Team Hackathon_Open Team"].id,
                "owner_id": user_objs["admin"].id,
                "github_url": "https://github.com/hackathon/webapp1",
                "docker_url": "https://docker.hackathon.com/webapp1",
                "docker_image": "hackathon/webapp1",
                "docker_tag": "latest",
                "docker_registry": "hackathon-registry.com",
            },
            {
                "name": "Kubernetes Microservice",
                "description": "Microservice running on K8s",
                "status": ProjectStatus.DEPLOYED,
                "storage_type": ProjectStorageType.KUBERNETES,
                "hackathon": hackathon_objs["Team Hackathon"],
                "team_id": team_objs["Team Hackathon_Closed Team"].id,
                "owner_id": user_objs["judge"].id,
                "kubernetes_url": "https://k8s.hackathon.com/microservice1",
                "docker_image": "hackathon/microservice1",
                "docker_tag": "v1.0.0",
            },
            {
                "name": "Cloud Native App",
                "description": "Deployed to cloud",
                "status": ProjectStatus.DEPLOYED,
                "storage_type": ProjectStorageType.CLOUD,
                "hackathon": hackathon_objs["Solo Hackathon"],
                "user_id": user_objs["user1"].id,
                "owner_id": user_objs["user1"].id,
                "cloud_url": "https://app.hackathon.com",
                "github_url": "https://github.com/hackathon/cloudapp1",
            },
            {
                "name": "Archived Docker Project",
                "description": "Docker image archived",
                "status": ProjectStatus.ARCHIVED,
                "storage_type": ProjectStorageType.DOCKER_ARCHIVE,
                "hackathon": hackathon_objs["Hackathon Completed"],
                "team_id": team_objs["Team Hackathon_Open Team"].id,
                "owner_id": user_objs["admin"].id,
                "docker_archive_url": "https://storage.hackathon.com/docker/archived1.tar",
                "docker_image": "hackathon/archived1",
                "docker_tag": "archive",
            },
            {
                "name": "GitLab Project",
                "description": "Stored on GitLab",
                "status": ProjectStatus.ACTIVE,
                "storage_type": ProjectStorageType.GITLAB,
                "hackathon": hackathon_objs["Team Hackathon"],
                "team_id": team_objs["Team Hackathon_Closed Team"].id,
                "owner_id": user_objs["judge"].id,
                "gitlab_url": "https://gitlab.com/hackathon/project1",
            },
        ]

        for p_def in project_defs:
            # Erstelle das Projekt
            project = Project(
                id=uuid.uuid4(),
                name=p_def["name"],
                description=p_def["description"],
                status=p_def["status"],
                hackathon_id=p_def["hackathon"].id,
                storage_type=p_def["storage_type"],
                owner_id=p_def["owner_id"],
                github_url=p_def.get("github_url"),
                gitlab_url=p_def.get("gitlab_url"),
                bitbucket_url=p_def.get("bitbucket_url"),
                server_url=p_def.get("server_url"),
                docker_url=p_def.get("docker_url"),
                kubernetes_url=p_def.get("kubernetes_url"),
                cloud_url=p_def.get("cloud_url"),
                archive_url=p_def.get("archive_url"),
                docker_archive_url=p_def.get("docker_archive_url"),
                backup_url=p_def.get("backup_url"),
                docker_image=p_def.get("docker_image"),
                docker_tag=p_def.get("docker_tag"),
                docker_registry=p_def.get("docker_registry"),
            )
            db.add(project)
            db.commit()
            db.refresh(project)

            # Erstelle die Registration
            registration = HackathonRegistration(
                hackathon_id=p_def["hackathon"].id,
                project_id=project.id,
                user_id=p_def.get("user_id"),
                team_id=p_def.get("team_id"),
                status="registered",
            )
            db.add(registration)
            db.commit()

            project_objs[p_def["name"]] = project
        logger.info(f"Projects: {[p.name for p in project_objs.values()]}")

        # --- Judging Criteria ---
        crit_objs = {}
        for c in CRITERIA:
            crit = db.query(Criterion).filter_by(name=c["name"]).first()
            if not crit:
                crit = Criterion(
                    id=uuid.uuid4(),
                    name=c["name"],
                    description=c["description"],
                    max_score=c["max_score"],
                    weight=c["weight"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(crit)
                db.commit()
                db.refresh(crit)
            crit_objs[c["name"]] = crit
        logger.info(f"Criteria: {[c.name for c in crit_objs.values()]}")

        # --- Judging Scores (user: judge bewertet project 1) ---
        judge = user_objs["judge"]
        project = project_objs["Docker Web App"]
        for crit in crit_objs.values():
            score = (
                db.query(Score)
                .filter_by(
                    judge_id=judge.id, project_id=project.id, criteria_id=crit.id
                )
                .first()
            )
            if not score:
                score = Score(
                    id=uuid.uuid4(),
                    judge_id=judge.id,
                    project_id=project.id,
                    criteria_id=crit.id,
                    score=8,
                    comment="Good work!",
                    submitted_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(score)
        db.commit()
        logger.info("Judging scores created.")

        logger.info("Test data setup complete.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
