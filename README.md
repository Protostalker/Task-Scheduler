# TaskFlow (MVP)

Dockerized multi-company scheduling + task system with roles:
- employee
- admin
- super_admin

Task IDs are sequential (DB sequence) and displayed as `T000010` etc.

## Quick start

1) From this folder:
```bash
docker compose up --build
```

2) Wait for containers to be healthy, then open:
- Web UI: http://localhost:9080
- API: internal only (web reverse-proxies /api to the api container). Health: /api/health

3) Bootstrap super admin
On first run, if no `super_admin` exists, the API creates one:
- username: `root`
- password: written to `./data/bootstrap_superadmin.txt` (host-mounted)

> Admins cannot change a super_admin password via UI/API. DB-only.

## Default ports
- Web: 9080
- API: internal only
- Postgres: internal only (5432)

## Notes
- This is an MVP. Focus is correctness + deployability.
- TLS should be terminated by a reverse proxy in production (Nginx Proxy Manager / Traefik / etc.).
