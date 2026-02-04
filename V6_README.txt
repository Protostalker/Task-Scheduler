V6 (make it work, Docker-side)

What changed:
- web/Dockerfile rebuilt as a clean Vite -> nginx pipeline.
- nginx.conf serves:
    /public/service-worker.js
    /public/manifest.webmanifest
  as real files (NOT index.html), and blocks SPA fallback for /public/*
  Also serves /service-worker.js and /manifest.webmanifest if you later un-block them.
- Adds required Service-Worker-Allowed: / header for SW.
- web/public contains SW + manifest and is copied into runtime image.

Deploy:
1) Unzip this over your repo.
2) Rebuild web and restart:
   docker compose build --no-cache web
   docker compose up -d

Verify:
- docker compose exec web sh -lc 'ls -lah /usr/share/nginx/html/public'
- curl -k -I https://task.stalkernas.ddns.net/public/manifest.webmanifest | egrep -i "HTTP/|content-type"
- curl -k -I https://task.stalkernas.ddns.net/public/service-worker.js | egrep -i "HTTP/|content-type|service-worker-allowed"

Then re-subscribe and check DB push_subscriptions.
