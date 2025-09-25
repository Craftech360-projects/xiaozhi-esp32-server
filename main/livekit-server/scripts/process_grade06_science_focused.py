"""
Process Grade 6 Science textbook Markdown files - focused on single collection
Creates grade_06_science collection with activity extraction and enhanced metadata
Deletes existing collection and recreates with markdown content
"""

import asyncio
import logging
import sys
import os
import glob
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the parent directory to the path to enable absolute imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.rag.qdrant_manager import QdrantEducationManager
from src.rag.embeddings import EmbeddingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def delete_existing_collection():
    """Delete existing grade_06_science collection if it exists"""

    try:
        qdrant_manager = QdrantEducationManager()
        collection_name = "grade_06_science"

        logger.info(f"Checking for existing collection: {collection_name}")

        # Check if collection exists
        try:
            existing = await qdrant_manager.get_existing_collections()
            if collection_name in existing:
                logger.info(f"Deleting existing collection: {collection_name}")
                success = await qdrant_manager.delete_collection(collection_name)
                if success:
                    logger.info(f"✅ Successfully deleted collection: {collection_name}")
                    return True
                else:
                    logger.error(f"❌ Failed to delete collection: {collection_name}")
                    return False
            else:
                logger.info(f"Collection {collection_name} does not exist, nothing to delete")
                return True
        except Exception as e:
            logger.warning(f"Error checking existing collections: {e}")
            return True  # Continue if we can't check

    except Exception as e:
        logger.error(f"❌ Error in delete operation: {e}")
        return False


async def create_grade06_science_collection():
    """Create only the grade_06_science collection"""

    try:
        qdrant_manager = QdrantEducationManager()

        collection_name = "grade_06_science"

        logger.info(f"Creating collection: {collection_name}")

        # Create the collection
        success = await qdrant_manager.create_collection(collection_name, "science")

        if success:
            logger.info(f"✅ Successfully created collection: {collection_name}")
            return True
        else:
            logger.error(f"❌ Failed to create collection: {collection_name}")
            return False

    except Exception as e:
        logger.error(f"❌ Error creating collection: {e}")
        return False


def extract_activities_from_markdown(content, chapter_title, chapter_number):
    """Extract activities from markdown content"""
    activities = []

    # Pattern to match activities
    activity_pattern = r'Activity\s+(\d+\.\d+):\s*([^\n]+)'

    # Find all activities
    matches = re.finditer(activity_pattern, content, re.IGNORECASE)

    for match in matches:
        activity_id = match.group(1)
        activity_title = match.group(2).strip()

        # Find the content after the activity title
        start_pos = match.end()

        # Look for the next activity or end of section to determine activity content
        next_activity = re.search(r'Activity\s+\d+\.\d+:', content[start_pos:], re.IGNORECASE)
        if next_activity:
            end_pos = start_pos + next_activity.start()
        else:
            # Look for next major section or take next 1000 characters
            end_pos = min(start_pos + 1000, len(content))

        activity_content = content[start_pos:end_pos].strip()

        activities.append({
            'id': activity_id,
            'title': activity_title,
            'content': activity_content,
            'chapter': chapter_title,
            'chapter_number': chapter_number
        })

    return activities


def split_markdown_into_chunks(content, max_chunk_size=1000):
    """Split markdown content into smaller chunks"""

    # Split by sections first (looking for headers)
    sections = re.split(r'\n#{1,6}\s+', content)

    chunks = []
    current_chunk = ""

    for section in sections:
        if len(current_chunk) + len(section) <= max_chunk_size:
            current_chunk += section + "\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = section + "\n"

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Further split large chunks by paragraphs
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            paragraphs = chunk.split('\n\n')
            current_para_chunk = ""

            for para in paragraphs:
                if len(current_para_chunk) + len(para) <= max_chunk_size:
                    current_para_chunk += para + "\n\n"
                else:
                    if current_para_chunk.strip():
                        final_chunks.append(current_para_chunk.strip())
                    current_para_chunk = para + "\n\n"

            if current_para_chunk.strip():
                final_chunks.append(current_para_chunk.strip())

    return final_chunks


async def process_markdown_to_collection():
    """Process Grade 6 science markdown files directly to the collection"""

    try:
        # Initialize components
        qdrant_manager = QdrantEducationManager()
        embedding_manager = EmbeddingManager()

        logger.info("Initializing embedding manager...")
        await embedding_manager.initialize()

        # Find markdown files
        md_folder = "D:/cheekofinal/xiaozhi-esp32-server/main/livekit-server/scripts/grade_6_science_md"
        md_files = glob.glob(os.path.join(md_folder, "*.md"))

        logger.info(f"Found {len(md_files)} markdown files to process")

        collection_name = "grade_06_science"
        processed_count = 0
        chunk_id_counter = 1

        for md_path in md_files:
            try:
                # Extract chapter info
                filename = Path(md_path).stem
                logger.info(f"Processing: {filename}")

                # Extract chapter number and title from filename
                chapter_match = re.match(r'[Cc]hapter\s*(\d+)\s*(.*?)$', filename)
                if chapter_match:
                    chapter_number = int(chapter_match.group(1))
                    chapter_title = chapter_match.group(2).strip()
                else:
                    # Fallback pattern for different naming conventions
                    chapter_number = 1
                    chapter_title = filename

                logger.info(f"Processing Chapter {chapter_number}: {chapter_title}")

                # Read markdown content
                with open(md_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract activities from content
                activities = extract_activities_from_markdown(content, chapter_title, chapter_number)
                logger.info(f"Found {len(activities)} activities in {filename}")

                # Split content into chunks
                content_chunks_text = split_markdown_into_chunks(content, max_chunk_size=800)

                metadata = {
                    "grade": 6,
                    "subject": "science",
                    "textbook_name": f"Grade 6 Science - {chapter_title}",
                    "textbook_author": "NCERT",
                    "isbn": f"NCERT-06-SCI-CH{chapter_number:02d}",
                    "chapter": chapter_title,
                    "chapter_number": chapter_number
                }

                # Process regular content chunks
                content_chunks = []

                for i, chunk_text in enumerate(content_chunks_text):
                    try:
                        # Generate embedding
                        embedding = await embedding_manager.get_text_embedding(chunk_text)

                        if embedding:
                            content_chunk = {
                                "id": chunk_id_counter,
                                "text_embedding": embedding,
                                "payload": {
                                    "content": chunk_text,
                                    "content_type": "text",
                                    "textbook_name": metadata["textbook_name"],
                                    "textbook_author": metadata["textbook_author"],
                                    "isbn": metadata["isbn"],
                                    "grade": metadata["grade"],
                                    "subject": metadata["subject"],
                                    "page_number": i + 1,
                                    "chapter": metadata["chapter"],
                                    "chapter_number": metadata["chapter_number"],
                                    "topic": [chapter_title.lower(), "science"],
                                    "keywords": [],
                                    "difficulty_level": "beginner",
                                    "cognitive_level": "remember",
                                    "concepts": [chapter_title.lower()],
                                    "is_activity": False
                                }
                            }
                            content_chunks.append(content_chunk)
                            chunk_id_counter += 1

                    except Exception as e:
                        logger.warning(f"Failed to process content chunk {i}: {e}")

                # Process activities with special metadata
                for activity in activities:
                    try:
                        # Generate embedding for activity
                        activity_text = f"Activity {activity['id']}: {activity['title']}\n\n{activity['content']}"
                        embedding = await embedding_manager.get_text_embedding(activity_text)

                        if embedding:
                            activity_chunk = {
                                "id": chunk_id_counter,
                                "text_embedding": embedding,
                                "payload": {
                                    "content": activity_text,
                                    "content_type": "activity",
                                    "textbook_name": metadata["textbook_name"],
                                    "textbook_author": metadata["textbook_author"],
                                    "isbn": metadata["isbn"],
                                    "grade": metadata["grade"],
                                    "subject": metadata["subject"],
                                    "page_number": 1,
                                    "chapter": metadata["chapter"],
                                    "chapter_number": metadata["chapter_number"],
                                    "topic": [chapter_title.lower(), "science", "activity"],
                                    "keywords": ["activity", "experiment", "hands-on"],
                                    "difficulty_level": "intermediate",
                                    "cognitive_level": "apply",
                                    "concepts": [chapter_title.lower(), "practical"],
                                    "is_activity": True,
                                    "activity_id": activity['id'],
                                    "activity_title": activity['title']
                                }
                            }
                            content_chunks.append(activity_chunk)
                            chunk_id_counter += 1

                    except Exception as e:
                        logger.warning(f"Failed to process activity {activity['id']}: {e}")

                # Upload to Qdrant
                if content_chunks:
                    logger.info(f"Uploading {len(content_chunks)} chunks ({len(activities)} activities) to {collection_name}")

                    success = await qdrant_manager.upsert_content(collection_name, content_chunks)

                    if success:
                        logger.info(f"✅ Successfully uploaded {filename}")
                        processed_count += 1
                    else:
                        logger.error(f"❌ Failed to upload {filename}")
                else:
                    logger.warning(f"No valid chunks to upload for {filename}")

                # Small delay between files
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"❌ Error processing {md_path}: {e}")

        logger.info(f"Processing complete! ✅ {processed_count} files processed successfully")
        return processed_count > 0

    except Exception as e:
        logger.error(f"❌ Error in processing: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_grade06_science():
    """Test the Grade 6 science collection"""

    try:
        from src.services.education_service import EducationService

        # Initialize education service
        education_service = EducationService()

        logger.info("Initializing education service for testing...")
        success = await education_service.initialize()

        if not success:
            logger.error("Failed to initialize education service")
            return False

        # Set context for Grade 6 Science
        await education_service.set_student_context(grade=6, subject="science")

        # Test grade 6 science queries
        test_queries = [
            "What is science?",
            "What are living and non-living things?",
            "What should we eat to stay healthy?",
            "What are magnets?",
            "How do we measure length?",
            "What are the different materials around us?",
            "What is temperature?",
            "What are the states of water?"
        ]

        logger.info("\n=== Testing Grade 6 Science Queries ===")

        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n--- Query {i}: {query} ---")

            try:
                result = await education_service.answer_question(query)

                answer = result.get('answer', 'No answer found')
                confidence = result.get('confidence', 0.0)
                sources = result.get('sources', [])

                logger.info(f"Answer: {answer[:200]}...")
                logger.info(f"Confidence: {confidence:.2f}")

                if sources:
                    source = sources[0]
                    textbook = source.get('textbook', 'Unknown')
                    page = source.get('page', 'Unknown')
                    logger.info(f"Source: {textbook}, Page {page}")

                if any(word in answer.lower() for word in ['science', 'living', 'healthy', 'magnet', 'measure', 'material', 'temperature', 'water']):
                    logger.info("✅ Relevant answer found!")

            except Exception as e:
                logger.error(f"Error with query '{query}': {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Error in testing: {e}")
        return False


async def main():
    """Main function"""

    logger.info("=== Grade 6 Science Markdown Collection Processing ===")

    # Check environment variables
    required_env_vars = ["QDRANT_URL", "QDRANT_API_KEY"]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # Step 1: Delete existing collection
    logger.info("Step 1: Deleting existing grade_06_science collection...")
    delete_success = await delete_existing_collection()

    if not delete_success:
        logger.error("Failed to delete existing collection, exiting")
        return

    # Step 2: Create new collection
    logger.info("Step 2: Creating new grade_06_science collection...")
    collection_success = await create_grade06_science_collection()

    if not collection_success:
        logger.error("Failed to create collection, exiting")
        return

    # Step 3: Process Markdown files
    logger.info("Step 3: Processing Grade 6 Science Markdown files...")
    processing_success = await process_markdown_to_collection()

    if processing_success:
        # Step 4: Test
        logger.info("Step 4: Testing Grade 6 Science queries...")
        await test_grade06_science()
    else:
        logger.error("Processing failed, skipping tests")

    logger.info("\n=== Complete! ===")


if __name__ == "__main__":
    asyncio.run(main())