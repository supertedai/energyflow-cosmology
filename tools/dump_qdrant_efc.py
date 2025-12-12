import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()
client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))

print('🔍 Qdrant: efc collection (første 50)')
batch, _ = client.scroll(collection_name='efc', limit=50)
for i, point in enumerate(batch):
    print(f'{i+1}.', point.payload)
