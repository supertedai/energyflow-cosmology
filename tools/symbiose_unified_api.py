# ---------------------------------------------
# HELPERS → NEO4J
# ---------------------------------------------
def neo4j_query(text: str):
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    db = os.getenv("NEO4J_DATABASE", "neo4j")

    if GraphDatabase is None:
        return {"enabled": False, "reason": "neo4j-driver missing", "matches": []}

    if not (uri and user and password):
        return {"enabled": False, "reason": "Missing env vars", "matches": []}

    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session(database=db) as session:
            q = """
            CALL db.index.fulltext.queryNodes('efc_index', $q)
            YIELD node, score
            RETURN node.title AS title, node.slug AS slug, node.keywords AS keywords, score
            ORDER BY score DESC LIMIT 5
            """
            rows = session.run(q, parameters={"q": text})
            data = [r.data() for r in rows]

        driver.close()
        return {"enabled": True, "matches": data}

    except Exception as e:
        return {"enabled": False, "reason": str(e), "matches": []}


# ---------------------------------------------
# HELPERS → QDRANT (RAG)
# ---------------------------------------------
def qdrant_search(text: str, limit=5):
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    collection = os.getenv("QDRANT_COLLECTION", "efc")

    if QdrantClient is None:
        return {"enabled": False, "reason": "qdrant-client missing", "matches": []}

    try:
        client = QdrantClient(url=url, api_key=api_key)

        # Dummy embedding
        emb = [0.1] * 1536

        result = client.search(
            collection_name=collection,
            vector=emb,
            limit=limit
        )

        return {
            "enabled": True,
            "matches": [
                {
                    "text": h.payload.get("text"),
                    "paper": h.payload.get("paper_title"),
                    "slug": h.payload.get("slug"),
                    "score": h.score
                }
                for h in result
            ]
        }

    except Exception as e:
        return {"enabled": False, "reason": str(e), "matches": []}
