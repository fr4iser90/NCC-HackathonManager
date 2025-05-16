# Hackathon Platform

A modern, scalable platform for managing hackathon events, built with NixOS, Docker, and modern web technologies.

## Features

- **User Management**
  - Authentication & Authorization
  - Team Formation
  - Profile Management

- **Project Management**
  - Template-based Project Creation
  - Resource Allocation
  - Deployment Automation

- **Judging System**
  - Criteria Management
  - Scoring System
  - Feedback Collection

- **Infrastructure**
  - Container Orchestration
  - Automatic SSL/TLS
  - Security with CrowdSec
  - Monitoring & Metrics

## Tech Stack

- **Frontend**: Next.js, TypeScript, TailwindCSS
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL, Redis
- **Infrastructure**: Docker, Traefik, CrowdSec
- **Monitoring**: Prometheus, Grafana

## Quick Start

### Prerequisites
- NixOS or Linux system
- Docker & Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/hackathon-platform.git
cd hackathon-platform
```

2. Set up environment:
```bash
# Copy example environment files
cp .env.example .env

# Start services
docker-compose up -d
```

3. Initialize database:
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create admin user
docker-compose exec api python scripts/create_admin.py
```

4. Access the platform:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Admin: http://localhost:3000/admin

## Documentation

- [Development Setup](docs/setup/development.md)
- [Deployment Guide](docs/setup/deployment.md)
- [Architecture](docs/architecture/tech-stack.md)
- [Domain Model](docs/architecture/domain-model.md)
- [Project Phases](docs/planning/phases.md)

## Development

### Backend Development
```bash
# Start backend services
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
# Start frontend development server
cd frontend
npm install
npm run dev
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Deployment

See [Deployment Guide](docs/setup/deployment.md) for detailed instructions.

Quick deployment:
```bash
# 1. Configure environment
cp .env.example .env
vim .env

# 2. Start services
docker-compose -f docker-compose.prod.yml up -d

# 3. Initialize database
docker-compose exec api alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- NixOS Community
- Docker Community
- FastAPI
- Next.js
- All contributors
