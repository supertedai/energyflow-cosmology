
```
infra/RECOVERY.md
```

---

# ✔ **Final File: `infra/RECOVERY.md`**

````markdown
# Symbiosis – Disaster Recovery Guide (Hetzner Runtime Master)

This guide describes the exact procedure to restore the full Symbiosis runtime after a total server failure on Hetzner.

GitHub is the **code-master**.  
Hetzner is the **runtime-master**.

This process guarantees a clean, reproducible rebuild with minimal steps.

---

# 1. Prepare the server
Install required system packages:

```bash
apt update
apt install -y docker.io docker-compose git
````

Create the base directory:

```bash
mkdir -p /opt/symbiose
cd /opt/symbiose
```

---

# 2. Clone the repository (code-master)

```bash
git clone https://github.com/supertedai/energyflow-cosmology repo
cd repo
```

This gives you:

```
/opt/symbiose/repo/
```

---

# 3. Create the local `.env`

**This file is never stored in Git.**
It must always be created manually on the server.

Location:

```
/opt/symbiose/.env
```

Template:

```dotenv
# ==== Neo4j ====
NEO4J_URI=
NEO4J_USER=
NEO4J_PASSWORD=
NEO4J_DATABASE=neo4j

# ==== Qdrant ====
QDRANT_URL=
QDRANT_API_KEY=
QDRANT_COLLECTION=efc_docs

# ==== Embeddings ====
OPENAI_API_KEY=
EMBEDDING_MODEL=text-embedding-3-small

# ==== Logging ====
LOG_LEVEL=info
```

---

# 4. Create the runtime `docker-compose.yml`

This file must be stored locally on Hetzner:

```
/opt/symbiose/docker-compose.yml
```

It should always match the production version in GitHub.

Start the system:

```bash
docker compose build
docker compose up -d
```

---

# 5. Verify the API

Health:

```bash
curl http://localhost:8080/health
```

Neo4j:

```bash
curl "http://localhost:8080/neo4j/q?query=MATCH%20(n)%20RETURN%20n%20LIMIT%201"
```

RAG:

```bash
curl "http://localhost:8080/rag/search?query=entropy"
```

Unified Query:

```bash
curl -X POST http://localhost:8080/unified_query \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}'
```

---

# 6. Optional: Autostart on boot

Create a systemd service:

```bash
nano /etc/systemd/system/symbiose.service
```

Insert:

```ini
[Unit]
Description=Symbiose Runtime Master
After=docker.service
Requires=docker.service

[Service]
WorkingDirectory=/opt/symbiose
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
Restart=always

[Install]
WantedBy=multi-user.target
```

Activate:

```bash
systemctl daemon-reload
systemctl enable symbiose
systemctl start symbiose
```

---

# 7. What this process restores

Running this recovery process fully restores:

* unified-api service
* complete repo file structure
* Docker runtime
* All API endpoints

  * `/health`
  * `/neo4j/q`
  * `/rag/search`
  * `/graph-rag`
  * `/unified_query`

---

# 8. What is *not* in Git (must be recreated)

These items are intentionally excluded from version control:

* `/opt/symbiose/.env`
* Secret/API tokens
* Hetzner firewall rules
* SSH keys
* systemd units (optional)

---

# 9. Full recovery time

From empty server → full production runtime:
**2–4 minutes total.**

---

# 10. Ensure Hetzner matches GitHub

Always validate:

```bash
cd /opt/symbiose/repo
git pull
```

Hetzner must always reflect the `main` branch.

---

# End of Guide

```

---

# Want to extend it?
I can add:

- **`infra/STRUCTURE.md`** — full directory layout  
- **`infra/RESTORE_CHECKLIST.md`** — one-page runbook  
- **`infra/ARCHITECTURE.md`** — diagram + explanation  
- **`infra/BACKUP.md`** — Git, Neo4j, Qdrant backup strategy  

Just tell me what you want next.
```
