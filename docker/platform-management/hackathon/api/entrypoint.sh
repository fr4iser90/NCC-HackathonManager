#!/bin/sh
# entrypoint.sh

# Exit on error
set -e

# Run the admin user creation/ensure script
# This assumes the script is in /app/scripts/create_admin.py inside the container
# and that the PYTHONPATH is correctly set for imports within the script.
echo "Attempting to ensure admin user exists..."
python /app/scripts/create_admin.py

echo "Admin user check complete. Starting Uvicorn server..."

# Execute the original CMD (Uvicorn)
# The CMD from the Dockerfile will be passed as arguments to this script ("$@")
exec "$@" 