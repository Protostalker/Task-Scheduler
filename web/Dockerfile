# V6 web: build with Vite, then serve with nginx and include /public assets
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
RUN npm run build

FROM nginx:1.29-alpine
# Replace default nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy built app
COPY --from=build /app/dist/ /usr/share/nginx/html/
# Ensure PWA assets exist under /public (Vite copies /public to dist root, but we enforce it)
RUN mkdir -p /usr/share/nginx/html/public
COPY public/ /usr/share/nginx/html/public/
# Also copy to root as fallback
COPY public/service-worker.js /usr/share/nginx/html/service-worker.js
COPY public/manifest.webmanifest /usr/share/nginx/html/manifest.webmanifest
# Fix permissions so nginx (user nginx) can read PWA assets
RUN chmod 644 /usr/share/nginx/html/public/manifest.webmanifest /usr/share/nginx/html/public/service-worker.js     /usr/share/nginx/html/manifest.webmanifest /usr/share/nginx/html/service-worker.js || true

