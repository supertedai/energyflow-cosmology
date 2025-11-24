FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

# copy app folder so that /app/graph_rag exists
COPY app/ /app/

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    neo4j \
    sentence-transformers \
    pydantic \
    numpy

EXPOSE 8082

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
