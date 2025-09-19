"""
Complete test flow: insert content with real embeddings and test search
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path to enable absolute imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_complete_flow():
    """Test complete flow with real embeddings"""

    try:
        from src.rag.qdrant_manager import QdrantEducationManager
        from src.rag.embeddings import EmbeddingManager

        # Initialize managers
        qdrant_manager = QdrantEducationManager()
        embedding_manager = EmbeddingManager()

        logger.info("Initializing embedding manager...")
        await embedding_manager.initialize()

        # Create real embedding for test content
        test_content = "A linear equation is an equation in which the highest power of the variable is 1."
        logger.info("Generating embedding for test content...")

        text_embedding = await embedding_manager.get_text_embedding(test_content)
        if not text_embedding:
            logger.error("❌ Failed to generate embedding")
            return

        logger.info(f"✅ Generated embedding with {len(text_embedding)} dimensions")

        # Prepare sample data with real embedding
        sample_chunks = [
            {
                "id": 1,
                "vector": text_embedding,  # Real embedding
                "payload": {
                    "content": test_content,
                    "content_type": "definition",
                    "textbook_name": "Sample Mathematics Grade 8",
                    "textbook_author": "Test Author",
                    "isbn": "123-456-789",
                    "grade": 8,
                    "subject": "mathematics",
                    "page_number": 45,
                    "chapter": "Chapter 3: Linear Equations",
                    "section": "3.1 Introduction to Linear Equations",
                    "topic": ["linear equations", "algebra"],
                    "keywords": ["linear", "equation", "variable", "power"],
                    "difficulty_level": "intermediate",
                    "cognitive_level": "understand",
                    "concepts": ["linear equations", "algebraic expressions"]
                }
            }
        ]

        collection_name = "grade_8_mathematics"
        logger.info(f"Inserting test content into {collection_name}...")

        # Insert content
        success = await qdrant_manager.upsert_content(collection_name, sample_chunks)

        if success:
            logger.info("✅ Content inserted successfully")

            # Test search with real query
            logger.info("Testing search with real query...")

            query_text = "What is a linear equation?"
            query_embedding = await embedding_manager.get_text_embedding(query_text)

            if query_embedding:
                # Search with semantic similarity
                search_result = qdrant_manager.client.search(
                    collection_name=collection_name,
                    query_vector=query_embedding,
                    limit=3,
                    with_payload=True
                )

                if search_result:
                    logger.info(f"✅ Search found {len(search_result)} results")
                    for i, result in enumerate(search_result):
                        content = result.payload.get('content', 'No content')
                        score = result.score
                        logger.info(f"  Result {i+1} (score: {score:.3f}): {content}")

                        # Check if it's our test content
                        if "linear equation" in content.lower():
                            logger.info("✅ Found relevant content!")
                else:
                    logger.info("❌ Search returned no results")
            else:
                logger.error("❌ Failed to generate query embedding")
        else:
            logger.error("❌ Failed to insert content")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""

    logger.info("=== Complete Flow Test ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    await test_complete_flow()

    logger.info("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())