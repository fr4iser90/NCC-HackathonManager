# Development Setup

## Prerequisites

### Required Software
- Docker & Docker Compose
- Node.js 20+
- Python 3.11+
- Git
- VS Code (recommended)

### VS Code Extensions
- Python
- ESLint
- Prettier
- Docker
- GitLens
- Remote Containers

## Initial Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/hackathon-platform.git
cd hackathon-platform
```

### 2. Environment Setup

#### Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Install dependencies
cd backend
pip install -r requirements.txt
```

#### Frontend
```bash
# Install dependencies
cd frontend
npm install
```

### 3. Database Setup
```bash
# Start PostgreSQL
docker-compose up -d postgres

# Run migrations
cd backend
alembic upgrade head
```

### 4. Configuration

#### Environment Variables
Create `.env` files:

```bash
# backend/.env
DATABASE_URL=postgresql://hackathon:hackathon@localhost:5432/hackathon
JWT_SECRET=your-secret-key
DEBUG=true

# frontend/.env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Development Workflow

### Running Services

#### Backend
```bash
# Start FastAPI server
cd backend
uvicorn app.main:app --reload

# Run tests
pytest
```

#### Frontend
```bash
# Start Next.js dev server
cd frontend
npm run dev

# Run tests
npm test
```

### Docker Development

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f

# Rebuild services
docker-compose build
```

## Code Quality

### Backend
```bash
# Format code
black .
isort .

# Type checking
mypy .

# Linting
flake8
```

### Frontend
```bash
# Format code
npm run format

# Type checking
npm run type-check

# Linting
npm run lint
```

## Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test
pytest tests/test_auth.py -k "test_login"
```

### Frontend Tests
```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Debugging

### Backend
- Use VS Code Python debugger
- Set breakpoints in code
- Use `debug=True` in FastAPI

### Frontend
- Use Chrome DevTools
- React Developer Tools
- Redux DevTools (if used)

## Documentation

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Documentation
```bash
# Generate TypeDoc
npm run docs
```

## Common Issues

### Database Connections
- Check PostgreSQL is running
- Verify connection string
- Check port availability

### Docker Issues
- Clean up old containers
- Check disk space
- Verify network settings

### Frontend Build
- Clear `.next` directory
- Update dependencies
- Check Node.js version
