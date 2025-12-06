FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy entire project structure (for GNN and shared modules)
COPY apis /app/apis
COPY symbiose_gnn /app/symbiose_gnn
COPY symbiose_gnn_output /app/symbiose_gnn_output
COPY requirements-api.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8080

CMD ["uvicorn", "apis.unified_api.main:app", "--host", "0.0.0.0", "--port", "8080"]

