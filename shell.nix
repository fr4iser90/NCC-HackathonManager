{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    # Test dependencies
    pytest
    pytest-asyncio
    pytest-cov
    pytest-mock
    httpx
    
    # Core Bot Dependency
    nextcord
    
    # Monitoring Dependency
    psutil
    requests
    pillow
    # Database dependencies
    sqlalchemy
    asyncpg
    alembic
    psycopg2
    
    # Other dependencies
    python-dotenv
    py-cpuinfo
    speedtest-cli
    pyyaml
    email-validator
    
    # Web dependencies
    fastapi
    
    # Security dependencies
    cryptography
    python-jose
    passlib
    bcrypt
    
    # Main application dependencies
    uvicorn
    pydantic
    pydantic-settings
    python-multipart
    
    # Development tools
    black
    mypy
    pylint
  ]);
in
pkgs.mkShell {
  buildInputs = [
    pythonEnv
    pkgs.tree
    pkgs.nodejs_20    # Add Node.js
    pkgs.nodePackages.npm    # Add npm
    pkgs.docker    # Add Docker
    pkgs.docker-compose    # Add Docker Compose
    pkgs.curl    # Add curl for health checks
  ];
  
  shellHook = ''
    # Set PYTHONPATH to include the project root
    export PYTHONPATH="$PWD/docker/platform-management/hackathon/api:$PWD:$PYTHONPATH"
    
    # --- Cache Cleaning Function ---
    clean-caches() {
      echo "Cleaning host caches (__pycache__, .pytest_cache)..."
      # Use rm -rf for directories found, safer than -delete for non-empty dirs
      find . \( -path '*/__pycache__' -o -path '*/.pytest_cache' \) -type d -exec rm -rf {} +
      echo "Host cache cleaning complete."
    }

    # --- Overridden Test Functions with Auto-Cleaning ---

    # Override pytest to clean before and after
    pytest() {
      clean-caches
      echo "Running pytest (locally) with arguments: $@"
      command pytest "$@" # IMPORTANT: Use 'command' to call the real pytest
      local exit_code=$?
      echo "Pytest finished with exit code $exit_code."
      clean-caches
      return $exit_code
    }

    # Check if Docker is running
    check_docker() {
      if ! docker info > /dev/null 2>&1; then
        echo "Docker is not running. Please start Docker and try again."
        return 1
      fi
      return 0
    }

    # Check if node_modules exists in frontend
    check_frontend_deps() {
      if [ ! -d "docker/platform-management/hackathon/frontend/node_modules" ]; then
        echo "Frontend dependencies not found. Installing..."
        install-npm
      fi
    }

    # Check if backend is healthy
    check_backend_health() {
      local max_attempts=30
      local attempt=1
      local wait_time=2

      echo "Checking backend health..."
      while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null; then
          echo "Backend is healthy!"
          return 0
        fi
        echo "Attempt $attempt/$max_attempts: Backend not ready yet, waiting $wait_time seconds..."
        sleep $wait_time
        attempt=$((attempt + 1))
      done
      echo "Backend health check failed after $max_attempts attempts"
      return 1
    }

    # Check if Docker containers are built and running
    check_docker_containers() {
      if ! docker compose -f docker/platform-management/hackathon/docker-compose.yml ps --services --filter "status=running" | grep -q "api"; then
        echo "Docker containers not running. Building and starting..."
        if ! start-backend; then
          echo "Failed to start backend properly. Please check the logs."
          return 1
        fi
        # Wait for backend to be healthy
        if ! check_backend_health; then
          echo "Failed to start backend properly. Please check the logs."
          return 1
        fi
      fi
      return 0
    }

    quick-install() {
      echo "Starting quick installation process..."
      
      # Check and install frontend dependencies
      check_frontend_deps
      
      # Check Docker and build containers
      if check_docker; then
        echo "Building Docker containers..."
        cd docker/platform-management/hackathon/
        docker compose build
        cd -
      fi
      
      echo "Quick installation complete!"
    }

    quick-startup() {
      echo "Starting quick startup process..."
      
      # Check Docker is running
      if ! check_docker; then
        return 1
      fi
      
      # Check and install frontend dependencies if needed
      check_frontend_deps
      
      # Start backend if not running and wait for it to be healthy
      if ! check_docker_containers; then
        echo "Failed to start backend properly. Aborting startup."
        return 1
      fi
      
      # Start frontend in a new terminal
      echo "Starting frontend development server..."
      start-frontend-dev
      
      echo "Quick startup complete! All services should be running."
      echo "Frontend: http://localhost:3000"
      echo "Backend: http://localhost:8000"
    }

    install-npm() {
      echo "Installing npm dependencies for frontend..."
      cd docker/platform-management/hackathon/frontend
      npm install
      cd -
      echo "npm dependencies installation complete."
    }

    start-frontend-dev() {
      echo "Starting frontend development server..."
      cd docker/platform-management/hackathon/frontend
      npm run dev
      cd -
    }

    start-backend() {
      echo "Starting backend server..."
      cd docker/platform-management/hackathon/
      # Run in detached mode
      docker compose up --build -d
      # Wait a moment for containers to start
      sleep 5
      # Check if containers are actually running
      if ! docker compose ps --services --filter "status=running" | grep -q "api"; then
        echo "Failed to start containers. Check logs with: docker compose logs api"
        cd -
        return 1
      fi
      echo "Backend containers started successfully"
      cd -
    }

    echo "Python development environment activated"
    echo "PYTHONPATH set to: $PYTHONPATH"
    echo "Available commands:"
    echo "  pytest              - Run pytest locally (cleans host caches before & after)"
    echo "  clean-caches        - Manually clean host __pycache__ and .pytest_cache directories"
    echo "  db_upgrade          - Apply database migrations using Alembic inside the bot container"
    echo "  update-trees        - Update structure markdown files (web, tests, shared, bot)"
    echo "  install-npm         - Install npm dependencies for the frontend"
    echo "  start-frontend-dev  - Start the frontend development server"
    echo "  start-backend       - Start the backend server using Docker"
    echo "  quick-install       - Install all dependencies and build Docker containers"
    echo "  quick-startup       - Start all services with automatic dependency checks"
  '';
} 
