# apis/unified_api/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Global toggles (lag-1a)
ENABLE_QDRANT = os.getenv("ENABLE_QDRANT", "0") == "1"
ENABLE_NEO4J  = os.getenv("ENABLE_NEO4J", "0") == "1"
ENABLE_EMBED  = os.getenv("ENABLE_EMBED", "0") == "1"

