#!/bin/sh
# Build static output for Vercel. Set BACKEND_URL in Vercel env to proxy API to Railway/backend.
mkdir -p public/static
echo "window.API_BASE=\"${BACKEND_URL:-}\";" > public/static/config.js
cp "Phase 05- frontend/public/index.html" public/
cp "Phase 05- frontend/public/styles.css" "Phase 05- frontend/public/app.js" public/static/
