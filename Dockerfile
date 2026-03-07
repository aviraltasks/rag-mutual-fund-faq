# Backend for Railway: avoid Railpack build issues by using Docker
FROM python:3.11-slim

WORKDIR /app

# Install deps (CPU-only torch to keep image smaller)
COPY requirements-backend.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements-backend.txt

# Copy app (single COPY avoids quoting issues with folder names that have spaces)
COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["python", "backend_server.py"]
