V7 Fix: 403 Forbidden on /public/* despite files existing

Cause (hard fact):
- Files in /usr/share/nginx/html/public are mode 600 (rw-------) owned by root.
- nginx runs as user 'nginx' (see nginx.conf: user nginx;), so it cannot read them -> 403.

Fix:
- Dockerfile now chmod 644 on manifest/service-worker (both /public and root copies) during image build.

Deploy:
  docker compose build --no-cache web
  docker compose up -d

Verify inside container:
  docker compose exec web sh -lc 'ls -lah /usr/share/nginx/html/public; stat -c "%a %U:%G %n" /usr/share/nginx/html/public/*'

Verify externally:
  curl -k -I https://task.stalkernas.ddns.net/public/manifest.webmanifest | egrep -i "HTTP/|content-type|content-length"
  curl -k -I https://task.stalkernas.ddns.net/public/service-worker.js | egrep -i "HTTP/|content-type|service-worker-allowed"
