FROM python:3.11-slim

# Arbeidsmappe i container
WORKDIR /app

# Kopier unified_api inn i containeren
COPY . /app

# Installer Python dependencies
RUN pip install --no-cache-dir -r apis/unified_api/requirements.txt

# Eksponer porten unified-api kjører på
EXPOSE 8080

# Start FastAPI app
CMD ["uvicorn", "apis.unified_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
