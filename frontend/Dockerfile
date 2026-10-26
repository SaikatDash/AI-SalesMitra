FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend ./frontend

EXPOSE 8501

# Render provides PORT at runtime; keep 8501 as the local Docker default.
CMD ["sh", "-c", "streamlit run frontend/sample.py --server.address=0.0.0.0 --server.port=${PORT:-8501}"]
