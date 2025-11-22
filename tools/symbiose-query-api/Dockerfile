# ---- Base image ----
FROM python:3.11-slim

# ---- Prevent Python from writing .pyc files ----
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ---- Set workdir ----
WORKDIR /app

# ---- Install system deps ----
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ---- Copy API code ----
COPY . /app

# ---- Install Python deps ----
RUN pip install --no-cache-dir -r requirements.txt

# ---- Expose port ----
EXPOSE 8082

# ---- Run the API ----
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
