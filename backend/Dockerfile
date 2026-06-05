FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project structure
COPY . .

# Set PYTHONPATH to include /app so imports work correctly
ENV PYTHONPATH=/app

EXPOSE 8000

# Run uvicorn from /app pointing to backend.main.
# Cloud hosts commonly provide PORT; default to 8000 for local Docker.
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
