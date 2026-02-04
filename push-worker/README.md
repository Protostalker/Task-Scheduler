# Taskflow Push Worker (scaffold)

This folder exists so `docker compose up` will not fail when `push-worker` is defined in docker-compose.

Next steps (to implement real Web Push):
- Add `push_subscriptions` table in Postgres
- Add API endpoints to save/remove browser Push Subscriptions
- Add code to enqueue jobs into Redis when tasks are assigned
- Update this worker to:
  - fetch subscriptions for a user
  - send push notifications using VAPID keys
  - disable dead subscriptions

Generate VAPID keys (run on your host):

```bash
cd push-worker
npm install
npx web-push generate-vapid-keys
```
