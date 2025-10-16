from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
import os
from dotenv import load_dotenv

load_dotenv()

client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

# Get all Chapter 2 points
points, _ = client.scroll(
    collection_name='grade_06_science',
    scroll_filter=Filter(
        must=[FieldCondition(key='chapter_number', match=MatchValue(value=2))]
    ),
    limit=100,
    with_payload=False
)

ids = [p.id for p in points]

if ids:
    client.delete(
        collection_name='grade_06_science',
        points_selector=ids
    )
    print(f'Deleted {len(ids)} Chapter 2 text points')
else:
    print('No Chapter 2 points found')

# Also check visual collection
try:
    visual_points, _ = client.scroll(
        collection_name='grade_06_science_visual',
        limit=100,
        with_payload=False
    )
    print(f'Visual collection has {len(visual_points)} points (will process new)')
except:
    print('Visual collection empty or not found')
