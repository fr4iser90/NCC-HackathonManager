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

    # --- Original Helper Functions (Keep for reference or other scripts if needed) ---
    # Database upgrade alias
    alias db_upgrade='docker exec -it foundrycord-bot /bin/sh -c "alembic -c /app/shared/infrastructure/database/migrations/alembic/alembic.ini upgrade head"'

    # --- Function to update a single tree file ---
    _update_tree_file() {
      local target_dir="$1"
      local output_file="$2"
      # Exclude common irrelevant directories/files
      local exclude_pattern='__pycache__|.git|.idea|.vscode|.cursor|node_modules|.pytest_cache' 

      echo "Updating tree in $output_file for directory $target_dir..."
      # Overwrite file with header
      echo '```tree' > "$output_file"
      # Append tree output, excluding patterns
      tree -I "$exclude_pattern" "$target_dir" >> "$output_file"
      # Append footer
      echo '```' >> "$output_file"
      echo "Done updating $output_file."
    }

    # --- Alias to update all structure files ---
    alias update-trees='_update_tree_file app/web docs/3_developer_guides/02_architecture/web_structure.md && _update_tree_file app/tests docs/3_developer_guides/02_architecture/tests_structure.md && _update_tree_file app/shared docs/3_developer_guides/02_architecture/shared_structure.md && _update_tree_file app/bot docs/3_developer_guides/02_architecture/bot_structure.md'
    
    echo "Python development environment activated"
    echo "PYTHONPATH set to: $PYTHONPATH"
    echo "Available commands:"
    echo "  pytest              - Run pytest locally (cleans host caches before & after)"
    echo "  clean-caches        - Manually clean host __pycache__ and .pytest_cache directories"
    echo "  db_upgrade          - Apply database migrations using Alembic inside the bot container"
    echo "  update-trees        - Update structure markdown files (web, tests, shared, bot)"
  '';
} 