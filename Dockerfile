# Dockerfile for History-Aware Repository Intelligence
# Packages the History-RAG engine, FastAPI backend, and Streamlit developer UI.

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (Git and build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and pre-indexed data
COPY app/ app/
COPY configs/ configs/
COPY data/ data/
COPY scripts/ scripts/
COPY ui/ ui/

# Set Python path
ENV PYTHONPATH=/app
ENV PORT=8000
ENV STREAMLIT_PORT=8501

# Expose API and UI ports
EXPOSE 8000 8501

# Health check against GET /health
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command: launch FastAPI server
CMD ["uvicorn", "app.api.routes:app", "--host", "0.0.0.0", "--port", "8000"]
