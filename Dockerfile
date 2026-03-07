# Backend for Railway: avoid Railpack build issues by using Docker
FROM python:3.11-slim

WORKDIR /app

# Install deps (CPU-only torch to keep image smaller)
COPY requirements-backend.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-backend.txt

# Copy app and all phases needed at runtime
COPY backend_server.py .
COPY "Phase 01- data" "Phase 01- data"
COPY "Phase 02- backend" "Phase 02- backend"
COPY "Phase 03- llm_response" "Phase 03- llm_response"
COPY "Phase 04- safety" "Phase 04- safety"
COPY "Phase 05- frontend" "Phase 05- frontend"

ENV PORT=8000
EXPOSE 8000

CMD ["python", "backend_server.py"]
