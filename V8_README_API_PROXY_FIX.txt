V8 Fix: Login 405 (nginx/1.29.4) after PWA fixes

Cause:
- /api/* requests were hitting the web nginx (static) instead of being proxied to the FastAPI container.
- Static nginx returns 405 on POST, breaking login.

Fix:
- web/nginx.conf now includes:
    location ^~ /api/ { proxy_pass http://api:8000; }
- Includes a proper 'map' in http context for Upgrade/Connection.

Deploy:
  docker compose build --no-cache web
  docker compose up -d

Verify:
  curl -k -i https://task.stalkernas.ddns.net/api/me | head -n 20
  docker compose logs -f api   # while attempting login
