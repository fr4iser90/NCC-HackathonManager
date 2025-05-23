import os
import sys
import uuid
from datetime import datetime

# Adjust path to allow imports from the 'app' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.user import User
from app.models.team import Team, TeamMember, TeamMemberRole, JoinRequest, JoinRequestStatus, TeamStatus
from app.models.team import TeamInvite, TeamInviteStatus
from app.models.project import Project
from app.models.judging import Criterion, Score
from app.auth import get_password_hash
from app.models.hackathon import Hackathon
from app.schemas.hackathon import HackathonStatus, HackathonMode
from app.schemas.project import ProjectStatus
from app.models.hackathon_registration import HackathonRegistration

# --- Testdaten ---
USERS = [
    {"email": "admin@example.com", "username": "admin", "role": "admin", "password": "adminpass"},
    {"email": "judge@example.com", "username": "judge", "role": "judge", "password": "judgepass"},
    {"email": "user1@example.com", "username": "user1", "role": "user", "password": "userpass1"},
    {"email": "user2@example.com", "username": "user2", "role": "user", "password": "userpass2"},
]

# Teams are now defined per hackathon
TEAMS = {
    "Solo Hackathon": [
        {"name": "Solo Team 1", "description": "A solo participant team", "is_open": True},
    ],
    "Team Hackathon": [
        {"name": "Open Team", "description": "A public team", "is_open": True},
        {"name": "Closed Team", "description": "A private team", "is_open": False},
    ]
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
        "prizes": "1st: 1000€, 2nd: 500€",
        "contact_email": "orga@hackathon.com",
        "allow_individuals": True,
        "allow_multiple_projects_per_team": False,
        "custom_fields": {"special_award": "Best UI"}
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
        "allow_individuals": False
    },
    {"name": "Hackathon Completed", "description": "Herbst 2025", "start_date": datetime(2025, 9, 1, 10, 0), "end_date": datetime(2025, 9, 3, 18, 0), "status": "COMPLETED", "category": "General"},
    {"name": "Hackathon Archived", "description": "Winter 2025", "start_date": datetime(2025, 12, 1, 10, 0), "end_date": datetime(2025, 12, 3, 18, 0), "status": "ARCHIVED", "category": "General"},
]

PROJECTS = [
    {"name": "Test Project 1", "description": "Demo project 1", "status": "ACTIVE"},
    {"name": "Test Project 2", "description": "Demo project 2", "status": "DRAFT"},
]

CRITERIA = [
    {"name": "Innovation", "description": "How innovative is the project?", "max_score": 10, "weight": 1.0},
    {"name": "Technical Quality", "description": "How technically sound is the project?", "max_score": 10, "weight": 1.0},
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
                    id=uuid.uuid4(),
                    email=u["email"],
                    username=u["username"],
                    hashed_password=get_password_hash(u["password"]),
                    role=u["role"]
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            user_objs[u["username"]] = user
        print(f"Users: {[u.email for u in user_objs.values()]}")

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
                    mode=h.get("mode", "TEAM_RECOMMENDED"),
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
                    allow_multiple_projects_per_team=h.get("allow_multiple_projects_per_team", False),
                    custom_fields=h.get("custom_fields"),
                )
                db.add(hack)
                db.commit()
                db.refresh(hack)
            hackathon_objs[h["name"]] = hack
        print(f"Hackathons: {[h.name for h in hackathon_objs.values()]}")

        # --- Teams ---
        team_objs = {}
        for hackathon_name, teams in TEAMS.items():
            hackathon = hackathon_objs[hackathon_name]
            for t in teams:
                team = db.query(Team).filter_by(name=t["name"], hackathon_id=hackathon.id).first()
                if not team:
                    team = Team(
                        id=uuid.uuid4(),
                        name=t["name"],
                        description=t["description"],
                        is_open=t["is_open"],
                        hackathon_id=hackathon.id,
                        status=TeamStatus.active
                    )
                    db.add(team)
                    db.commit()
                    db.refresh(team)
                team_objs[f"{hackathon_name}_{t['name']}"] = team
        print(f"Teams: {[t.name for t in team_objs.values()]}")

        # --- Team Members ---
        # Admin is owner of Open Team in Team Hackathon
        # Judge is owner of Closed Team in Team Hackathon
        # user1 is member in both teams in Team Hackathon
        members = [
            (team_objs["Team Hackathon_Open Team"], user_objs["admin"], TeamMemberRole.owner),
            (team_objs["Team Hackathon_Closed Team"], user_objs["judge"], TeamMemberRole.owner),
            (team_objs["Team Hackathon_Open Team"], user_objs["user1"], TeamMemberRole.member),
            (team_objs["Team Hackathon_Closed Team"], user_objs["user1"], TeamMemberRole.member),
            (team_objs["Solo Hackathon_Solo Team 1"], user_objs["user1"], TeamMemberRole.owner),
        ]
        for team, user, role in members:
            exists = db.query(TeamMember).filter_by(team_id=team.id, user_id=user.id).first()
            if not exists:
                db.add(TeamMember(team_id=team.id, user_id=user.id, role=role))
        db.commit()
        print("Team members assigned.")

        # --- Projects ---
        project_objs = {}
        # Projects for different hackathons
        project_defs = [
            {
                "name": "Test Project 1", 
                "description": "Demo project 1", 
                "status": ProjectStatus.ACTIVE,
                "hackathon": hackathon_objs["Solo Hackathon"],
                "user_id": user_objs["user1"].id  # Für Solo Hackathon
            },
            {
                "name": "Test Project 2", 
                "description": "Demo project 2", 
                "status": ProjectStatus.DRAFT,
                "hackathon": hackathon_objs["Team Hackathon"],
                "team_id": team_objs["Team Hackathon_Open Team"].id  # Für Team Hackathon
            }
        ]

        for p_def in project_defs:
            # Erstelle das Projekt
            project = Project(
                id=uuid.uuid4(),
                name=p_def["name"],
                description=p_def["description"],
                status=p_def["status"],
                hackathon_id=p_def["hackathon"].id  # Direkte Verknüpfung mit Hackathon
            )
            db.add(project)
            db.commit()
            db.refresh(project)

            # Erstelle die Registration
            registration = HackathonRegistration(
                hackathon_id=p_def["hackathon"].id,
                project_id=project.id,
                user_id=p_def.get("user_id"),  # Optional für Solo-Projekte
                team_id=p_def.get("team_id"),  # Optional für Team-Projekte
                status="registered"
            )
            db.add(registration)
            db.commit()

            project_objs[p_def["name"]] = project
        print(f"Projects: {[p.name for p in project_objs.values()]}")

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
        print(f"Criteria: {[c.name for c in crit_objs.values()]}")

        # --- Judging Scores (user: judge bewertet project 1) ---
        judge = user_objs["judge"]
        project = project_objs["Test Project 1"]
        for crit in crit_objs.values():
            score = db.query(Score).filter_by(judge_id=judge.id, project_id=project.id, criteria_id=crit.id).first()
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
        print("Judging scores created.")

        print("Test data setup complete.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
