#!/usr/bin/env bash
set -euo pipefail

# 0. Vorherige Container und Volumes entfernen (immer sauberer Start)
docker compose -f docker-compose.yml -f docker-compose.override.test.yml down -v

# 1. Test-DB und API-Container starten
docker compose -f docker-compose.yml -f docker-compose.override.test.yml up -d test-db api

# 2. Warten bis DB healthy
for i in {1..20}; do
  status=$(docker inspect --format='{{.State.Health.Status}}' hackathon-test-db 2>/dev/null || echo "none")
  if [ "$status" = "healthy" ]; then
    echo "Test-DB ist healthy!"
    break
  fi
  echo "Warte auf Test-DB ($i/20)..."
  sleep 1
done
if [ "$status" != "healthy" ]; then
  echo "Test-DB wurde nicht healthy!"
  docker logs hackathon-test-db || true
  exit 1
fi

echo "Attempting to ensure admin user exists..."
python /app/scripts/create_admin.py
echo "Attempting to ensure test data exists..."
python /app/scripts/test_data.py

# 5. E2E-Setup (legt alle E2E-User per API an, vergibt Rollen)
python /api/scripts/setup_e2e_users.py'

# 6. Alle Tests/E2E-Tests ausführen
nix-shell --run 'pytest --maxfail=20 --disable-warnings --tb=short > test_report.txt || true'
cat test_report.txt

# 7. Test-DB und API stoppen und entfernen
docker stop hackathon-test-db hackathon-api 2>/dev/null || true
docker rm hackathon-test-db hackathon-api 2>/dev/null || true 