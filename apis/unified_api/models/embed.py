# models/embed.py
#
# Midlertidig stub for embedding.
# Denne brukes KUN som placeholder mens vi låser Neo4j og API-strukturen.

from typing import List


def embed_text(text: str) -> List[float]:
    """
    Returnerer en "dummy"-embedding basert på tekstlengde.
    Dette er KUN for å holde API-et kjørbart uten HuggingFace / modeller.
    """
    length = float(len(text or ""))
    # enkel 3D-vektor bare for form
    return [length, length / 2.0, length / 3.0]

