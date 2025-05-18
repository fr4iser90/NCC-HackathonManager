import os
import sys
import uuid
from datetime import datetime

# Adjust path to allow imports from the 'app' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import SessionLocal
from app.models.user import User
from app.models.team import Team, TeamMember, TeamMemberRole, JoinRequest, JoinRequestStatus
from app.models.team import TeamInvite, TeamInviteStatus
from app.models.project import Project
from app.models.judging import Criterion, Score
from app.auth import get_password_hash
from app.models.hackathon import Hackathon
from app.schemas.hackathon import HackathonStatus

# --- Testdaten ---
USERS = [
    {"email": "admin@example.com", "username": "admin", "role": "admin", "password": "adminpass"},
    {"email": "judge@example.com", "username": "judge", "role": "judge", "password": "judgepass"},
    {"email": "user1@example.com", "username": "user1", "role": "user", "password": "userpass1"},
    {"email": "user2@example.com", "username": "user2", "role": "user", "password": "userpass2"},
]

TEAMS = [
    {"name": "Open Team", "description": "A public team", "is_open": True},
    {"name": "Closed Team", "description": "A private team", "is_open": False},
]

HACKATHONS = [
    {"name": "Hackathon #1", "description": "Spring 2025", "start_date": datetime(2025, 5, 1, 10, 0), "end_date": datetime(2025, 5, 3, 18, 0), "status": "RUNNING"},
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

        # --- Teams ---
        team_objs = {}
        for t in TEAMS:
            team = db.query(Team).filter_by(name=t["name"]).first()
            if not team:
                team = Team(
                    id=uuid.uuid4(),
                    name=t["name"],
                    description=t["description"],
                    is_open=t["is_open"]
                )
                db.add(team)
                db.commit()
                db.refresh(team)
            team_objs[t["name"]] = team
        print(f"Teams: {[t.name for t in team_objs.values()]}")

        # --- Team Members ---
        # Admin ist Owner von Open Team, Judge ist Owner von Closed Team, user1 ist Member in beiden
        members = [
            (team_objs["Open Team"], user_objs["admin"], TeamMemberRole.owner),
            (team_objs["Closed Team"], user_objs["judge"], TeamMemberRole.owner),
            (team_objs["Open Team"], user_objs["user1"], TeamMemberRole.member),
            (team_objs["Closed Team"], user_objs["user1"], TeamMemberRole.member),
        ]
        for team, user, role in members:
            exists = db.query(TeamMember).filter_by(team_id=team.id, user_id=user.id).first()
            if not exists:
                db.add(TeamMember(team_id=team.id, user_id=user.id, role=role))
        db.commit()
        print("Team members assigned.")

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
                )
                db.add(hack)
                db.commit()
                db.refresh(hack)
            hackathon_objs[h["name"]] = hack
        print(f"Hackathons: {[h.name for h in hackathon_objs.values()]}")

        # --- Projects ---
        project_objs = {}
        # Zwei Projekte für Hackathon #1, eins ohne Hackathon
        project_defs = [
            {"name": "Test Project 1", "description": "Demo project 1", "status": "ACTIVE", "hackathon": hackathon_objs["Hackathon #1"]},
            {"name": "Test Project 2", "description": "Demo project 2", "status": "DRAFT", "hackathon": hackathon_objs["Hackathon #1"]},
            {"name": "Free Project", "description": "No hackathon", "status": "DRAFT", "hackathon": None},
        ]
        for p in project_defs:
            project = db.query(Project).filter_by(name=p["name"]).first()
            if not project:
                project = Project(
                    id=uuid.uuid4(),
                    name=p["name"],
                    description=p["description"],
                    status=p["status"],
                    team_id=team_objs["Open Team"].id,
                    hackathon_id=p["hackathon"].id if p["hackathon"] else None,
                )
                db.add(project)
                db.commit()
                db.refresh(project)
            project_objs[p["name"]] = project
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
