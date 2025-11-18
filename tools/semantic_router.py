import json
import re
from pathlib import Path

class SemanticRouter:
    def __init__(self, index_path="semantic-search-index.json"):
        self.index_path = Path(index_path)
        self.nodes = self._load_index()

    def _load_index(self):
        if not self.index_path.exists():
            raise FileNotFoundError(f"Index file not found: {self.index_path}")
        with open(self.index_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("nodes", [])

    def _tokenize(self, text):
        return re.findall(r"[a-zA-Z0-9]+", text.lower())

    def _score_node(self, node, query_tokens):
        score = 0

        # Title/ID match
        if "id" in node:
            for token in query_tokens:
                if token in node["id"].lower():
                    score += 4

        # Summary match
        if "summary" in node:
            summary_tokens = self._tokenize(node["summary"])
            score += len(set(query_tokens) & set(summary_tokens)) * 2

        # Tag match
        if "tags" in node:
            score += len(set(query_tokens) & set([t.lower() for t in node["tags"]])) * 3

        # Domain match
        if "domain" in node:
            for token in query_tokens:
                if token == node["domain"].lower():
                    score += 5

        # Layer match
        if "layer" in node:
            for token in query_tokens:
                if token == str(node["layer"]).lower():
                    score += 3

        return score

    def query(self, text, top_k=5):
        query_tokens = self._tokenize(text)

        scored = []
        for node in self.nodes:
            score = self._score_node(node, query_tokens)
            if score > 0:
                scored.append((score, node))

        # Sort: best score first
        scored.sort(key=lambda x: x[0], reverse=True)

        return scored[:top_k]


if __name__ == "__main__":
    router = SemanticRouter()

    print("--- Semantic Router Test ---")
    while True:
        q = input("Query: ").strip()
        if q in ["exit", "quit"]:
            break

        results = router.query(q)
        print("\nResults:")
        for score, node in results:
            print(f"  - {node['id']}  (score={score})  →  {node['path']}")
        print()
