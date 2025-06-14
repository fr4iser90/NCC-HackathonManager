{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: with ps; [
    # Test dependencies
    pytest
    pytest-asyncio
    pytest-cov
    pytest-mock
    httpx
    
    structlog
    colorama
    
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
    pkgs.lsof
    pkgs.tmux    # Add tmux for terminal sessions
  ];
  
  shellHook = ''
    # Set PYTHONPATH to include the project root
    export PYTHONPATH="$PWD/api:$PWD:$PYTHONPATH"
    echo "Für produktionsnahe Tests: Stelle sicher, dass die PostgreSQL-Testdatenbank (test-db) per Docker läuft!"
    
    # --- Cache Cleaning Function ---
    clean-caches() {
      echo "Cleaning host caches (__pycache__, .pytest_cache)..."
      # Use rm -rf for directories found, safer than -delete for non-empty dirs
      find . \( -path '*/__pycache__' -o -path '*/.pytest_cache' \) -type d -exec rm -rf {} +
      echo "Host cache cleaning complete."
    }

    # --- Overridden Test Functions with Auto-Cleaning ---

    # --- Start/Stop Functions ---

    # Start/Stop Production/Dev Backend (API + DB)
    start-backend-dev() {
      echo "Starting production/dev API and DB containers..."
      docker compose -f docker-compose.yml up -d hackathon-api hackathon-db
    }
    stop-backend-dev() {
      echo "Stopping production/dev API and DB containers..."
      docker compose -f docker-compose.yml stop hackathon-api hackathon-db
      docker compose -f docker-compose.yml rm -f hackathon-api hackathon-db
      docker volume rm hackathon-db-data || true
    }

    # Start/Stop Test Backend (Test-API + Test-DB)
    start-backend-test() {
      echo "Starting test API and test DB containers..."
      docker compose -f docker-compose.override.test.yml up -d hackathon-api test-db
    }
    stop-backend-test() {
      echo "Stopping test API and test DB containers..."
      docker compose -f docker-compose.override.test.yml stop hackathon-api test-db
      docker compose -f docker-compose.override.test.yml rm -f hackathon-api test-db
      docker volume rm hackathon-db-data || true
    }

    # Override pytest to clean before and after
    pytest() {
      check_docker || return 1
      clean-caches
      start-backend-test || return 1
      sleep 5
      echo "Running pytest (locally) with arguments: $@"
      command pytest "$@"
      local exit_code=$?
      echo "Pytest finished with exit code $exit_code."
      clean-caches
      stop-backend-test
      return $exit_code
    }

    # Minimal log pytest function
    pytest-minimal-log() {
      check_docker || return 1
      clean-caches
      start-backend-test || return 1
      sleep 5
      echo "Running pytest with minimal log (short tracebacks, warnings disabled, max 10 fails)..."
      command pytest --maxfail=30 --disable-warnings --tb=short > test_report.txt || true
      local exit_code=$?
      echo "Pytest finished with exit code $exit_code. See test_report.txt for results."
      clean-caches
      stop-backend-test
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
      if [ ! -d " frontend/node_modules" ]; then
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
      if ! docker compose -f  docker-compose.yml ps --services --filter "status=running" | grep -q "hackathon-api"; then
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
        docker compose build
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
      cd  frontend
      npm install
      cd -
      echo "npm dependencies installation complete."
    }

    start-frontend-dev() {
      echo "Starting frontend development server..."
      cd  frontend
      npm run dev
      cd -
    }
    
    start-frontend-tmux() {
      echo "Starting frontend development server in tmux session..."
      # Create a new tmux session named 'hackathon-frontend' if it doesn't exist
      if ! tmux has-session -t hackathon-frontend 2>/dev/null; then
        tmux new-session -d -s hackathon-frontend
      fi
      
      # Send commands to the tmux session
      tmux send-keys -t hackathon-frontend "cd $(pwd)/ frontend" C-m
      tmux send-keys -t hackathon-frontend "npm run dev" C-m
      
      echo "Frontend server started in tmux session 'hackathon-frontend'"
      echo "To attach to the session: tmux attach -t hackathon-frontend"
      echo "To detach from session: press Ctrl+B then D"
    }

    start-backend() {
      echo "Starting backend server..."
      # Run in detached mode
      docker compose up --build -d
      # Wait a moment for containers to start
      sleep 5
      # Check if containers are actually running
      if ! docker compose ps --services --filter "status=running" | grep -q "api"; then
        echo "Failed to start containers. Check logs with: docker compose logs api"
        return 1
      fi
      echo "Backend containers started successfully"
    }

    rebuild-backend() {
      echo "Stopping and removing all containers and volumes..."
      docker compose down -v
      echo "Rebuilding and starting containers in background..."
      docker compose up --build -d
      echo "Rebuild complete!"
    }

    rebuild-frontend() {
      echo "Removing node_modules, package-lock.json, and .next in the frontend..."
      cd  frontend
      rm -rf node_modules package-lock.json .next
      echo "Cleaning npm cache..."
      npm cache clean --force
      echo "Reinstalling npm dependencies..."
      npm install
      cd -
      echo "Frontend dependencies have been completely reinstalled!"
      start-frontend-dev
    }

    # --- Improved Port Management Functions ---
    
    # Detect processes using a specific port (using multiple methods)
    detect_port_process() {
      local port=$1
      local pids=""
      
      # Method 1: lsof (most common)
      if command -v lsof &>/dev/null; then
        # Exclude Firefox processes
        pids=$(lsof -t -i ":$port" 2>/dev/null | while read pid; do
          if ! ps -p "$pid" -o comm= | grep -q "firefox"; then
            echo "$pid"
          fi
        done)
      fi
      
      # Method 2: netstat if lsof found nothing
      if [ -z "$pids" ] && command -v netstat &>/dev/null; then
        pids=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | grep -v "-" | sort -u | while read pid; do
          if ! ps -p "$pid" -o comm= | grep -q "firefox"; then
            echo "$pid"
          fi
        done)
      fi
      
      # Method 3: ss (modern netstat replacement)
      if [ -z "$pids" ] && command -v ss &>/dev/null; then
        pids=$(ss -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2 | grep -v "-" | sort -u | while read pid; do
          if ! ps -p "$pid" -o comm= | grep -q "firefox"; then
            echo "$pid"
          fi
        done)
      fi
      
      # Method 4: fuser (another approach)
      if [ -z "$pids" ] && command -v fuser &>/dev/null; then
        pids=$(fuser -n tcp "$port" 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i+0>0) print $i}' | while read pid; do
          if ! ps -p "$pid" -o comm= | grep -q "firefox"; then
            echo "$pid"
          fi
        done)
      fi
      
      echo "$pids"
    }

    # Check if port is in use by any process
    is_port_in_use() {
      local port=$1
      
      # Try multiple detection methods
      if command -v lsof &>/dev/null && lsof -i ":$port" &>/dev/null; then
        return 0  # Port is in use
      fi
      
      if command -v netstat &>/dev/null && netstat -tuln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
      fi
      
      if command -v ss &>/dev/null && ss -tuln 2>/dev/null | grep -q ":$port "; then
        return 0  # Port is in use
      fi
      
      if command -v fuser &>/dev/null && fuser -n tcp "$port" 2>/dev/null | grep -q "$port"; then
        return 0  # Port is in use
      fi
      
      # Try direct connection test as last resort
      if command -v nc &>/dev/null; then
        nc -z localhost "$port" &>/dev/null && return 0
      elif command -v timeout &>/dev/null; then
        timeout 1 bash -c "</dev/tcp/localhost/$port" &>/dev/null && return 0
      fi
      
      return 1  # Port is free
    }

    # Kill processes using a specific port
    kill_port_process() {
      local port=$1
      local force=$2
      local pids=$(detect_port_process "$port")
      local killed=false
      
      if [ -n "$pids" ]; then
        echo "Found process(es) on port $port (excluding Firefox): $pids"
        
        # Try normal kill first unless force is specified
        if [ "$force" != "force" ]; then
          echo "Attempting graceful termination..."
          for pid in $pids; do
            # Double check it's not Firefox before killing
            if ! ps -p "$pid" -o comm= | grep -q "firefox"; then
              kill "$pid" 2>/dev/null
              killed=true
            fi
          done
          
          # Give processes time to terminate
          sleep 1
        fi
        
        # Check if still running or force kill requested
        if [ "$force" = "force" ] || is_port_in_use "$port"; then
          echo "Using force termination (kill -9)..."
          for pid in $pids; do
            # Double check it's not Firefox before force killing
            if ! ps -p "$pid" -o comm= | grep -q "firefox"; then
              kill -9 "$pid" 2>/dev/null
              killed=true
            fi
          done
          sleep 1
        fi
        
        # Final check
        if is_port_in_use "$port"; then
          echo "WARNING: Port $port is still in use after kill attempts!"
          return 1
        else
          echo "Successfully freed port $port"
          return 0
        fi
      else
        echo "No process found using port $port (excluding Firefox)"
        if is_port_in_use "$port"; then
          echo "WARNING: Port $port appears to be in use, but couldn't identify the process"
          return 1
        fi
        return 0
      fi
    }

    # Wait for a port to become free
    wait_for_port_free() {
      local port=$1
      local max_attempts=10
      local wait_time=1
      # Set max_attempts if provided
      if [ -n "$2" ]; then
        max_attempts=$2
      fi
      # Set wait_time if provided
      if [ -n "$3" ]; then
        wait_time=$3
      fi
      local attempt=1
      while [ $attempt -le $max_attempts ]; do
        if ! is_port_in_use "$port"; then
          echo "Port $port is now free."
          return 0
        fi
        echo "Port $port is still in use, waiting... (attempt $attempt/$max_attempts)"
        sleep $wait_time
        attempt=$((attempt + 1))
      done
      echo "WARNING: Port $port is STILL in use after $max_attempts attempts!"
      return 1
    }

    # Kill frontend port using improved functions
    kill-frontend-port() {
      local port=$(get-frontend-port)
      echo "Checking for processes using frontend port $port..."
      
      # First try: Kill by port
      kill_port_process "$port"
      
      # Second try: Kill specific Next.js processes if port is still in use
      if is_port_in_use "$port"; then
        echo "Port still in use, checking for Next.js processes..."
        local next_pids=$(ps aux | grep -i "next dev" | grep -v grep | awk '{print $2}')
        if [ -n "$next_pids" ]; then
          echo "Found Next.js processes: $next_pids"
          for pid in $next_pids; do
            kill "$pid" 2>/dev/null
          done
          sleep 1
        fi
      fi
      
      # Final try: Force kill if still in use
      if is_port_in_use "$port"; then
        echo "Still in use, trying force kill..."
        kill_port_process "$port" "force"
      fi
    }

    # Clean multiple ports
    clean-ports() {
      for port in "$@"; do
        echo "Cleaning port $port..."
        kill_port_process "$port"
        # If first attempt failed, try with force
        if is_port_in_use "$port"; then
          echo "First attempt failed, trying force kill for port $port..."
          kill_port_process "$port" "force"
        fi
      done
    }

    clean-frontend() {
      kill-frontend-port
      echo "Removing node_modules, package-lock.json, and .next in the frontend..."
      cd  frontend
      rm -rf node_modules package-lock.json .next
      cd -
      echo "Frontend has been cleaned!"
    }

    rebuild-all() {
      echo ">>> Stopping and removing all containers and volumes..."
      local frontend_port=$(get-frontend-port)
      # Kill frontend processes and wait for port to be free
      kill-frontend-port
      if ! wait_for_port_free "$frontend_port" 15 2; then
        echo "WARNING: Could not free port $frontend_port after multiple attempts."
        echo "You may need to manually identify and kill the process using this port."
        echo "Continuing with rebuild anyway..."
      fi
      docker compose down -v
      echo ">>> Cleaning up frontend..."
      cd  frontend
      rm -rf node_modules package-lock.json .next
      echo ">>> Cleaning npm cache..."
      npm cache clean --force
      echo ">>> Installing dependencies..."
      npm install
      cd -
      echo ">>> Rebuilding and starting backend containers..."
      docker compose up --build -d
      echo ">>> Starting frontend development server..."
      cd  frontend
      npm run dev &
      cd -
      echo ">>> Everything has been rebuilt and started!"
      echo "Frontend: http://localhost:3000"
      echo "Backend:  http://localhost:8000"
    }

    clean-all() {
      clean-caches
      kill-frontend-port
      clean-frontend
      echo "Everything has been cleaned!"
    }

    get-frontend-port() {
      local env_file=" frontend/.env.local"
      if [ -f "$env_file" ]; then
        # Try to find a line like PORT=3050 or NEXTAUTH_URL=http://localhost:3050
        local port
        port=$(grep -E '^PORT=' "$env_file" | cut -d'=' -f2)
        if [ -z "$port" ]; then
          # Try to extract from NEXTAUTH_URL or similar
          port=$(grep -E '^NEXTAUTH_URL=' "$env_file" | sed -E 's/.*:([0-9]+).*/\1/')
        fi
        # Fallback to 3000 if nothing found
        if [ -z "$port" ]; then
          port=3000
        fi
        echo "$port"
      else
        echo "3000"
      fi
    }
    
    get-frontend-tree() {
      tree  frontend -I 'node_modules|.next|.swc'
    }

    get-backend-tree() {
      tree  api -I 'node_modules|.next|.swc'
    }   

    trivy() {
      nix-shell -p trivy --run "trivy fs --scanners vuln,secret,misconfig --exit-code 0 --format table --ignore-unfixed ."
    }

    lint-fix() {
      echo "Running black auto-fix..."
      black .
      echo "Running pylint auto-fix..."
      pylint --generate-rcfile > .pylintrc
      pylint --disable=C0111,C0103,C0303,W0311,W0603,W0621,R0903,R0913,R0914,R0915 --output-format=colorized .
      echo "Linting complete!"
    }

    close-kill-clean-all() {
      echo ">>> Stopping and removing all backend containers and volumes (project only)..."
      docker compose down -v
      echo ">>> Killing frontend dev server and freeing its port..."
      kill-frontend-port
      if ! wait_for_port_free "$(get-frontend-port)" 10 2; then
        echo "WARNING: Could not free frontend port after multiple attempts."
      fi
      echo ">>> Removing frontend build artifacts and dependencies..."
      cd  frontend
      rm -rf node_modules package-lock.json .next
      cd -
      echo ">>> Cleaning Python caches (__pycache__, .pytest_cache)..."
      clean-caches
      # --- Remove ONLY the project-specific Docker network ---
      echo ">>> Removing project-specific Docker network (if exists)..."
      docker network rm ncc-hackathonmanager_default 2>/dev/null || true
      echo ">>> All project apps stopped and all caches/artifacts cleaned!"
      echo "If you want to start fresh, use: quick-startup"
    }

    start-test-db() {
      # Remove old test-db container if exists (any state)
      docker rm -f hackathon-test-db 2>/dev/null || true
      # Remove old test network if exists (optional, only if not used by other containers)
      docker network rm ncc-hackathonmanager_default 2>/dev/null || true
      echo "Starte PostgreSQL-Testdatenbank..."
      docker compose -f docker-compose.yml -f docker-compose.override.test.yml up -d --force-recreate test-db
      # Warten bis healthy
      for i in {1..20}; do
        status=$(docker inspect --format='{{.State.Health.Status}}' hackathon-test-db 2>/dev/null)
        if [ "$status" = "healthy" ]; then
          echo "Test-DB ist healthy!"
          # Add small delay to ensure DB is fully ready
          sleep 2
          return 0
        fi
        echo "Warte auf Test-DB ($i/20)..."
        sleep 1
      done
      echo "Test-DB wurde nicht healthy!"
      docker logs hackathon-test-db || true
      return 1
    }

    stop-test-db() {
      echo "Stoppe PostgreSQL-Testdatenbank..."
      docker stop hackathon-test-db 2>/dev/null || true
      docker rm hackathon-test-db 2>/dev/null || true
      # Optional: docker network rm ncc-hackathonmanager_default 2>/dev/null || true
    }

    pytest-with-testdb() {
      start-test-db || return 1
      pytest "$@"
      stop-test-db
    }

    echo "Python development environment activated"
    echo "PYTHONPATH set to: $PYTHONPATH"
    echo "Available commands:"
    echo "  quick-startup       - Start all services with automatic dependency checks"
    echo "  quick-install       - Install all dependencies and build Docker containers"
    echo "  install-npm         - Install npm dependencies for the frontend"
    echo "  start-frontend-dev  - Start the frontend development server"
    echo "  start-frontend-tmux - Start the frontend development server in a tmux session"
    echo "  start-backend       - Start the backend server using Docker"
    echo "  rebuild-all         - Stop all containers, remove frontend dependencies, rebuild backend, and start frontend development server"
    echo "  rebuild-backend     - Remove all containers & volumes, rebuild and start backend fresh"
    echo "  rebuild-frontend    - Remove node_modules and package-lock.json in the frontend and reinstall npm dependencies"
    echo "  pytest              - Run pytest locally (cleans host caches before & after)"
    echo "  pytest-minimal-log  - Run pytest with minimal log, exported to test_report.txt "
    echo "  clean-caches        - Manually clean host __pycache__ and .pytest_cache directories"
    echo "  clean-frontend      - Remove node_modules, package-lock.json, and .next in the frontend"
    echo "  clean-all           - Clean both Python and frontend caches/artifacts"
    echo "  close-kill-clean-all - Stop all backend/frontend, remove all caches, Docker volumes, and frontend artifacts"
  '';
}
