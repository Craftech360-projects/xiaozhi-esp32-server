"""
Test exact embedding match to verify the system works
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


async def test_exact_match():
    """Test with exact same embedding for insert and search"""

    try:
        from src.rag.qdrant_manager import QdrantEducationManager
        from src.rag.embeddings import EmbeddingManager

        # Initialize managers
        qdrant_manager = QdrantEducationManager()
        embedding_manager = EmbeddingManager()

        logger.info("Initializing embedding manager...")
        await embedding_manager.initialize()

        # Create embedding for test content
        test_content = "What is a linear equation?"
        logger.info(f"Generating embedding for: {test_content}")

        text_embedding = await embedding_manager.get_text_embedding(test_content)
        if not text_embedding:
            logger.error("❌ Failed to generate embedding")
            return

        logger.info(f"✅ Generated embedding with {len(text_embedding)} dimensions")

        # Prepare sample data with the SAME embedding as our search query
        sample_chunks = [
            {
                "id": 100,  # Different ID to avoid conflicts
                "text_embedding": text_embedding,  # SAME embedding as query
                "payload": {
                    "content": "A linear equation is an algebraic equation in which each term is either a constant or the product of a constant and a single variable.",
                    "content_type": "definition",
                    "textbook_name": "Sample Mathematics Grade 8",
                    "textbook_author": "Test Author",
                    "grade": 8,
                    "subject": "mathematics",
                    "page_number": 45,
                    "topic": ["linear equations", "algebra"],
                    "keywords": ["linear", "equation", "algebra"],
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

            # Search with the EXACT SAME embedding
            logger.info("Testing search with exact same embedding...")

            # Use search method (works fine despite deprecation warning)
            search_result = qdrant_manager.client.search(
                collection_name=collection_name,
                query_vector=text_embedding,
                limit=3,
                with_payload=True
            )

            if search_result:
                logger.info(f"✅ Search found {len(search_result)} results")
                for i, result in enumerate(search_result):
                    content = result.payload.get('content', 'No content')
                    score = result.score
                    logger.info(f"  Result {i+1} (score: {score:.6f}): {content[:100]}...")

                    # Verify it's our test content
                    if "linear equation" in content.lower():
                        logger.info("✅ Found exact match content!")
                        logger.info("🎉 RAG system is working correctly!")
            else:
                logger.info("❌ Search returned no results - something is wrong")
        else:
            logger.error("❌ Failed to insert content")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main function"""

    logger.info("=== Exact Match Test ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    await test_exact_match()

    logger.info("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())