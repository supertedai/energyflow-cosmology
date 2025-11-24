FROM python:3.11-slim

WORKDIR /app

# Kopier hele app-mappen (slik din API faktisk er strukturert)
COPY ./app /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    neo4j

EXPOSE 8082

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
