FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

COPY app/efc_graph_rag_api.py /app/app/efc_graph_rag_api.py

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    neo4j \
    sentence-transformers \
    pydantic \
    numpy

EXPOSE 8082

CMD ["uvicorn", "app.efc_graph_rag_api:app", "--host", "0.0.0.0", "--port", "8082"]
