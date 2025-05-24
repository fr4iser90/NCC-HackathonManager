#!/bin/bash

# Farben
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Konfiguration
HACKATHON_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_DIR="$HACKATHON_DIR/docker"

# Prüfe ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker ist nicht installiert. Bitte installiere Docker zuerst.${NC}"
    exit 1
fi

# Prüfe ob Docker Compose installiert ist
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose ist nicht installiert. Bitte installiere Docker Compose zuerst.${NC}"
    exit 1
fi

echo -e "${YELLOW}Initialisiere Hackathon-Plattform...${NC}"

# Erstelle Docker-Netzwerk, falls es nicht existiert
if ! docker network ls | grep -q hackathon; then
    echo -e "${YELLOW}Erstelle Docker-Netzwerk 'hackathon'...${NC}"
    docker network create --subnet=172.60.0.0/16 --gateway=172.60.0.1 hackathon
fi

# Wechsle ins Docker-Verzeichnis
cd "$DOCKER_DIR"

# Starte die Container
echo -e "${YELLOW}Starte Hackathon-Container...${NC}"
docker-compose up -d

# Warte auf die Datenbank
echo -e "${YELLOW}Warte auf Datenbank-Initialisierung...${NC}"
sleep 10

# Initialisiere Admin-Benutzer
echo -e "${YELLOW}Initialisiere Admin-Benutzer...${NC}"
docker-compose exec -T api python -c "
from app.models.user import create_admin_user
from app.database import get_db
db = next(get_db())
create_admin_user(db, '${ADMIN_EMAIL:-admin@example.com}', 'admin', 'password')
"

echo -e "${GREEN}Hackathon-Plattform erfolgreich initialisiert!${NC}"
echo -e "${YELLOW}Admin-Zugangsdaten:${NC}"
echo -e "  Email: ${ADMIN_EMAIL:-admin@example.com}"
echo -e "  Passwort: password"
echo -e "${YELLOW}Bitte ändere das Passwort nach dem ersten Login!${NC}"
echo -e "${YELLOW}Zugriff auf die Plattform:${NC}"
echo -e "  Admin-Interface: https://${DOMAIN}"
echo -e "  API: https://api.${DOMAIN}"
echo -e "  Traefik-Dashboard: https://traefik.${DOMAIN}"
echo -e "  Prometheus: https://prometheus.${DOMAIN}"
echo -e "  Grafana: https://grafana.${DOMAIN}"
