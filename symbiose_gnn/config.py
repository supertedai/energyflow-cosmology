# symbiose_gnn/config.py

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

config = {
    "neo4j_uri": os.getenv("NEO4J_URI", "neo4j+s://119e751c.databases.neo4j.io"),
    "neo4j_user": os.getenv("NEO4J_USER", "neo4j"),
    "neo4j_password": os.getenv("NEO4J_PASSWORD"),
    "neo4j_database": os.getenv("NEO4J_DATABASE", "neo4j"),
    "output_dir": "symbiose_gnn_output",
    "embedding_dim": 64
}
