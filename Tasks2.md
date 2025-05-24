# Modern Build & Logging System: Task & File List

**Ziel:**  
Asynchroner Build-Prozess mit Celery, Redis, FastAPI, Live-Logs und robustem Status-API.

---

## 1. Backend (API, Worker, Logging)

### Editieren

- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/app/routers/projects.py`  
  _API-Endpoints umbauen: Build asynchron starten, Status/Logs-API, Rückgabe von Task/Version-IDs_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/app/models/project.py`  
  _ProjectVersion-Model: Logs als Array/JSON, Status-Feld_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/requirements.txt`  
  _Celery, Redis, evtl. neue Dependencies_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/app/main.py`  
  _Celery-Integration, evtl. BackgroundTasks_

### Neu anlegen

- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/app/celery_worker.py`  
  _Celery-Worker-Entry-Point_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/app/tasks/build.py`  
  _Build-Task-Logik, Logging in Redis/DB_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/app/services/log_service.py`  
  _Service für Log-Streaming, Log-Speicherung_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/app/schemas/log.py`  
  _Pydantic-Schema für Log-Objekte_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/docker-compose.override.yml`  
  _Redis-Container für Celery/Logs_

---

## 2. Frontend (Status/Logs anzeigen, Polling/Streaming)

### Editieren

- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/frontend/src/app/projects/submit/page.tsx`  
  _Polling/Streaming für Logs, Statusanzeige_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/frontend/src/app/api/projects/submit/route.ts`  
  _API-Calls an neue Endpoints_

### Neu anlegen

- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/frontend/src/lib/useBuildLogs.ts`  
  _Custom Hook für Log-Streaming/Polling_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/frontend/src/components/BuildLogViewer.tsx`  
  _Komponente für Live-Log-Anzeige_

---

## 3. Datenbank/Migration

### Editieren/Neu

- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/database/init.sql`  
  _Tabelle für Logs, evtl. Anpassung ProjectVersion_
- `/home/fr4iser/Documents/Git/NCC-HackathonManager/docker/platform-management/hackathon/api/database/migrations/`  
  _Neue Migrationen für Log-Tabellen/Status_

---

## 4. Dokumentation/Task-Plan

### Neu

- `/home/fr4iser/Documents/Git/NCC-HackathonManager/Tasks2.md`  
  _Diese vollständige Liste und alle Schritte als Task-Plan_

---

**Nächster Schritt:**  
- Für jeden dieser Punkte kann ein detaillierter Migrations-/Implementierungsplan erstellt werden.
- Sag Bescheid, wenn du für einen Bereich (z.B. Celery-Worker, Log-API, Frontend-Log-Viewer) eine Schritt-für-Schritt-Anleitung willst.
