FROM python:3.11-slim

WORKDIR /app

# kopier hele app-mappen
COPY ./app /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    neo4j

EXPOSE 8082

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
