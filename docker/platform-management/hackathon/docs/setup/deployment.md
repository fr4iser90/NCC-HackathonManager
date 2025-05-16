# Deployment Guide

## Prerequisites

### System Requirements
- NixOS or Linux system
- Docker & Docker Compose
- Domain name with DNS access
- SSL certificates (Let's Encrypt)
- Minimum 4GB RAM, 2 CPU cores

### Security Requirements
- Firewall configured
- SSH access secured
- CrowdSec installed
- Regular backups enabled

## Production Setup

### 1. Initial Server Setup

```bash
# Update system
sudo nixos-rebuild switch

# Install required packages
nix-env -iA nixos.docker nixos.docker-compose nixos.git
```

### 2. Clone Repository

```bash
# Clone to /etc/nixos/hackathon
cd /etc/nixos
git clone https://github.com/your-org/hackathon-platform.git hackathon
```

### 3. Environment Configuration

```bash
# Create production environment files
cd /etc/nixos/hackathon

# Gateway environment
cat > gateway/.env << EOF
DOMAIN=your-domain.com
ADMIN_EMAIL=admin@your-domain.com
EOF

# Database environment
cat > services/.env << EOF
POSTGRES_USER=hackathon
POSTGRES_PASSWORD=$(openssl rand -base64 32)
POSTGRES_DB=hackathon
EOF

# API environment
cat > api/.env << EOF
DATABASE_URL=postgresql://hackathon:${POSTGRES_PASSWORD}@postgres:5432/hackathon
JWT_SECRET=$(openssl rand -base64 32)
ADMIN_EMAIL=admin@your-domain.com
EOF
```

### 4. Docker Networks

```bash
# Create required networks
docker network create proxy
docker network create crowdsec
```

### 5. Deploy Services

```bash
# Deploy Gateway (Traefik + CrowdSec)
cd gateway
docker-compose up -d

# Deploy Core Services
cd ../services
docker-compose up -d
```

## Monitoring Setup

### 1. Prometheus & Grafana

```bash
# Deploy monitoring stack
cd monitoring
docker-compose up -d

# Import dashboards
docker cp dashboards/. grafana:/etc/grafana/provisioning/dashboards/
```

### 2. Configure Alerts

```bash
# Edit alert rules
vim monitoring/prometheus/alert.rules.yml

# Reload Prometheus
docker restart prometheus
```

## Backup Strategy

### 1. Database Backups

```bash
# Create backup script
cat > scripts/backup-db.sh << EOF
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec postgres pg_dump -U hackathon > backup_${DATE}.sql
EOF

# Add to crontab
0 2 * * * /etc/nixos/hackathon/scripts/backup-db.sh
```

### 2. Configuration Backups

```bash
# Backup all configurations
tar -czf config_backup.tar.gz \
    gateway/traefik \
    gateway/crowdsec \
    services/.env \
    monitoring/prometheus
```

## Security Hardening

### 1. CrowdSec Configuration

```bash
# Update bouncer configuration
vim gateway/crowdsec/bouncers/traefik.yaml

# Reload configuration
docker restart crowdsec
```

### 2. SSL/TLS Settings

```yaml
# In traefik.yml
tls:
  options:
    default:
      minVersion: VersionTLS12
      cipherSuites:
        - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
```

## Maintenance

### Regular Tasks

1. **Daily**
   - Check logs
   - Monitor resources
   - Verify backups

2. **Weekly**
   - Update containers
   - Check security alerts
   - Review metrics

3. **Monthly**
   - Rotate secrets
   - Full backup
   - Security audit

### Update Procedure

```bash
# Pull latest changes
git pull origin main

# Update containers
docker-compose pull
docker-compose up -d

# Check logs
docker-compose logs -f
```

## Troubleshooting

### Common Issues

1. **Database Connection**
```bash
# Check database status
docker exec postgres pg_isready

# View logs
docker logs postgres
```

2. **Traefik Issues**
```bash
# Check certificates
docker exec traefik traefik show certificates

# View access logs
tail -f /var/log/traefik/access.log
```

3. **API Issues**
```bash
# Check API health
curl -I https://api.your-domain.com/health

# View logs
docker logs api
```

### Recovery Procedures

1. **Database Recovery**
```bash
# Restore from backup
cat backup.sql | docker exec -i postgres psql -U hackathon
```

2. **Service Recovery**
```bash
# Restart all services
docker-compose down
docker-compose up -d
```
