FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy unified-api code
COPY apis/unified_api /app/apis/unified_api

# Copy requirements
COPY apis/unified_api/requirements-api.txt /app/requirements.txt

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

EXPOSE 8080

CMD ["uvicorn", "apis.unified_api.main:app", "--host", "0.0.0.0", "--port", "8080"]

