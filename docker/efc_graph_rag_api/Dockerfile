FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Copy the whole app folder
COPY app/ /app/app/

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    neo4j \
    sentence-transformers \
    pydantic \
    numpy

EXPOSE 8082

# Start FastAPI from main.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082"]
