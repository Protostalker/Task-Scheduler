# Task-Scheduler

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
- Web: 8002
- API: internal only
- Postgres: internal only (5432)

## Notes
After saving the env file, you can docker compose up, and it should build the scheduler.

The default user (root) will be generated on first launch.
The password is written to the data folder in a file called:

bootstrap_superadmin


Log in, change that password, and delete the file once you’re done. Don’t be that guy.

How it works

Features include the freedom to bend the platform to your favor.

From the Admin menu, you can:

Create and manage companies

Control which users can see which companies

Enable or disable notifications

Adjust how tasks are grouped and displayed

There are no dropdown previews for tasks.
You must explicitly open a company to see its tasks — this is intentional and keeps things HIPAA-safe.

Tasks & workflow

Tasks are tied to companies, not users.

You can:

Create tasks per company

Assign categories and priorities

Mark tasks complete when finished

Hide completed tasks to keep things clean

Notifications
Browser notifications are supported if the user allows them.

They:
Tell you when tasks are waiting
Mention the company (never patients)
Don’t leak task details
Can be tested with the Test notify button
If notifications don’t fire, check browser permissions first. It’s almost always that.

Themes

Light and dark mode are both supported.
Theme choice is stored locally in the browser.

Dark mode uses neutral grays instead of neon blues so your eyes don’t melt after 10 hours.

Final notes

This project assumes:

You know what Docker is

You’re comfortable editing env files

You don’t want a bloated SaaS telling you how to run your own shit

If something breaks, check the logs.
If it still breaks, it’s probably your env file.

- This is an MVP. Focus is correctness + deployability.
- TLS should be terminated by a reverse proxy in production (Nginx Proxy Manager / Traefik / etc.).
