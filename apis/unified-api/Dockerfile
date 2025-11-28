FROM python:3.11-slim

# Sett korrekt arbeidsmappe
WORKDIR /app

# Kopier unified-api inn i containeren med riktig mappestruktur
COPY apis/unified-api/ /app/

# Installer avhengigheter
RUN pip install --no-cache-dir -r requirements.txt

# Eksponer porten
EXPOSE 8080

# Start uvicorn med riktig sti
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
