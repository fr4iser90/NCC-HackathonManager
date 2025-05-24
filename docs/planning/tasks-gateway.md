## Traefik
- [x] Write and validate traefik.yml configuration (entrypoints, routers, services)
- [x] Configure HTTPS with Let's Encrypt (acme_letsencrypt.json)
- [x] Set up domain routing for all required subdomains
- [x] Add security headers and rate limiting
- [x] Integrate Traefik with Docker network (proxy)
- [ ] Test Traefik dashboard access and security

## CrowdSec
- [x] Write and validate crowdsec.env configuration
- [x] Set up CrowdSec container with required collections
- [x] Configure and test bouncer integration with Traefik
- [ ] Test blocking and allowlisting rules
- [x] Update and test update-crowdsec-env.sh script

## DDNS Updater
- [x] Write and validate ddns-updater.env configuration
- [x] Configure DDNS provider credentials
- [ ] Test DDNS updates for domain/IP changes
- [x] Update and test update-ddns-env.sh and update-ddns-config.sh scripts

## Portainer
- [x] Write and validate portainer docker-compose.yml
- [x] Configure Portainer to use Docker socket securely
- [x] Integrate Portainer with Traefik (labels, routing)
- [ ] Test Portainer dashboard access and security

## Networking
- [x] Set up and test Docker networks (proxy, crowdsec)
- [x] Ensure all containers are reachable as required
- [ ] Test port forwarding and firewall rules

## Automation & Scripts
- [x] Write and test setup/init scripts for all gateway services
- [x] Write and test cleanup scripts for gateway stack
- [x] Automate environment file updates for all gateway services

## Security & Monitoring
- [ ] Enable and test Traefik/CrowdSec logging
- [ ] Set up monitoring for gateway containers (Prometheus targets)
- [ ] Review and test all security settings (TLS, headers, bouncer)

## Documentation
- [ ] Document all gateway setup steps
- [ ] Add troubleshooting and FAQ for gateway stack
- [ ] Update README with gateway usage and maintenance 