#!/bin/sh
set -e
mkdir -p public/static
echo "window.API_BASE=\"${BACKEND_URL:-}\";" > public/static/config.js
F="Phase 05- frontend/public"
cp "$F/index.html" public/
cp "$F/styles.css" "$F/app.js" "$F/README.txt" public/static/
