#!/usr/bin/env bash
set -euo pipefail

# 1. Test-DB Container starten
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1
echo "[1/6] Starte Test-DB..."
docker compose -f docker-compose.yml -f docker-compose.override.test.yml up -d test-db

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

# 3. Migration/Init-SQL anwenden
PGPASSWORD=testpass psql -h localhost -p 5433 -U testuser -d testdb -f database/init.sql

# 4. Testdaten und User anlegen

nix-shell --run 'python3 api/scripts/test_data_testdb.py'

# 5. Alle Tests/E2E-Tests ausführen
nix-shell --run 'pytest --maxfail=20 --disable-warnings --tb=short > test_report.txt || true'
cat test_report.txt

# 6. Test-DB stoppen
docker stop hackathon-test-db 2>/dev/null || true
docker rm hackathon-test-db 2>/dev/null || true 