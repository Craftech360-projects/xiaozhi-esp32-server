#!/usr/bin/env python3
"""
Stories Metadata Indexing Script for Semantic Search
Run this script to index all stories metadata into Qdrant vector database
Usage: python index_stories.py [--clear] [--verify]
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import hashlib
from ruamel.yaml import YAML

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class IndexingStats:
    """Statistics for indexing operation"""
    total_categories: int = 0
    total_stories: int = 0
    stories_indexed: int = 0
    stories_failed: int = 0
    time_taken: float = 0
    categories_processed: List[str] = None

    def __post_init__(self):
        if self.categories_processed is None:
            self.categories_processed = []

class StoriesIndexer:
    """Handles indexing of stories metadata into Qdrant"""

    def __init__(self, config_path: str = "data/.config.yaml"):
        """Initialize the indexer with configuration"""
        self.config = self._load_config(config_path)
        self.stats = IndexingStats()

        # Get semantic search config
        self.semantic_config = self.config.get('semantic_search', {})
        if not self.semantic_config.get('enabled', False):
            logger.warning("Semantic search is disabled in configuration!")

        # Qdrant settings
        self.qdrant_url = self.semantic_config.get('qdrant_url')
        self.qdrant_api_key = self.semantic_config.get('qdrant_api_key')
        self.collection_name = 'xiaozhi_stories'  # Fixed collection name for stories

        # Embedding settings
        self.model_name = self.semantic_config.get('embedding_model', 'all-MiniLM-L6-v2')

        # Stories directory settings
        self.stories_dir = Path('./stories')  # Stories directory
        self.stories_ext = ('.mp3', '.wav', '.p3')

        # Initialize clients
        self.qdrant_client = None
        self.embedding_model = None

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file"""
        yaml = YAML()
        yaml.preserve_quotes = True

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)

    def initialize(self) -> bool:
        """Initialize Qdrant client and embedding model"""
        try:
            # Initialize Qdrant client
            logger.info(f"Connecting to Qdrant at {self.qdrant_url}...")
            self.qdrant_client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key,
                timeout=60  # Increased timeout
            )

            # Test connection
            collections = self.qdrant_client.get_collections()
            logger.info(f"Connected to Qdrant. Found {len(collections.collections)} collections")

            # Initialize embedding model
            logger.info(f"Loading embedding model: {self.model_name}...")
            self.embedding_model = SentenceTransformer(self.model_name)
            self.embedding_size = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded. Dimension: {self.embedding_size}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            return False

    def create_collection(self, recreate: bool = False) -> bool:
        """Create or recreate the Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            exists = any(c.name == self.collection_name for c in collections.collections)

            if exists:
                if recreate:
                    logger.info(f"Deleting existing collection '{self.collection_name}'...")
                    self.qdrant_client.delete_collection(self.collection_name)
                    logger.info("Collection deleted")
                else:
                    logger.info(f"Collection '{self.collection_name}' already exists")
                    return True

            # Create new collection
            logger.info(f"Creating collection '{self.collection_name}'...")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_size,
                    distance=models.Distance.COSINE
                ),
            )
            logger.info("Collection created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False

    def load_stories_metadata(self) -> Dict[str, Dict]:
        """Load all stories metadata from the stories directory"""
        metadata_cache = {}

        if not self.stories_dir.exists():
            logger.error(f"Stories directory does not exist: {self.stories_dir}")
            return metadata_cache

        logger.info(f"Scanning stories directory: {self.stories_dir}")

        for category_folder in self.stories_dir.iterdir():
            if not category_folder.is_dir():
                continue

            category_name = category_folder.name
            metadata_file = category_folder / "metadata.json"

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    metadata_cache[category_name] = {
                        'metadata': metadata,
                        'folder_path': str(category_folder)
                    }

                    self.stats.total_stories += len(metadata)
                    self.stats.categories_processed.append(category_name)
                    logger.info(f"Loaded {len(metadata)} stories from {category_name}")

                except Exception as e:
                    logger.error(f"Failed to load metadata from {metadata_file}: {e}")
            else:
                # Scan for actual story files if no metadata.json
                story_files = []
                for ext in self.stories_ext:
                    story_files.extend(category_folder.glob(f"*{ext}"))

                if story_files:
                    logger.warning(f"No metadata.json in {category_name}, found {len(story_files)} story files")
                    # Create basic metadata from filenames
                    metadata = {}
                    for file in story_files:
                        story_name = file.stem
                        metadata[story_name] = {
                            'filename': file.name,
                            'romanized': story_name
                        }

                    metadata_cache[category_name] = {
                        'metadata': metadata,
                        'folder_path': str(category_folder)
                    }

                    self.stats.total_stories += len(metadata)
                    self.stats.categories_processed.append(category_name)

        self.stats.total_categories = len(metadata_cache)
        logger.info(f"Total: {self.stats.total_categories} categories, {self.stats.total_stories} stories")
        return metadata_cache

    def index_metadata(self, metadata_cache: Dict[str, Dict]) -> bool:
        """Index all metadata into Qdrant"""
        if not metadata_cache:
            logger.warning("No metadata to index")
            return False

        try:
            points = []
            point_id = 0

            logger.info("Generating embeddings and preparing data...")

            for category, category_data in metadata_cache.items():
                metadata = category_data.get('metadata', {})

                for story_title, story_info in metadata.items():
                    try:
                        # Prepare searchable text
                        searchable_texts = [
                            story_title,
                            story_info.get('romanized', ''),
                        ]

                        # Add alternatives
                        alternatives = story_info.get('alternatives', [])
                        if isinstance(alternatives, list):
                            searchable_texts.extend(alternatives)

                        # Add keywords
                        keywords = story_info.get('keywords', [])
                        if isinstance(keywords, list):
                            searchable_texts.extend(keywords)

                        # Add category context
                        searchable_texts.append(category)

                        # Combine all text
                        combined_text = " ".join(filter(None, searchable_texts)).strip()

                        if not combined_text:
                            logger.warning(f"Skipping {story_title} - no searchable text")
                            continue

                        # Generate embedding
                        embedding = self.embedding_model.encode(combined_text).tolist()

                        # Prepare payload
                        payload = {
                            'title': story_title,
                            'category': category,  # Use 'category' instead of 'language' for stories
                            'romanized': story_info.get('romanized', story_title),
                            'alternatives': alternatives,
                            'keywords': keywords,
                            'filename': story_info.get('filename', f"{story_title}.mp3"),
                            'file_path': f"{category}/{story_info.get('filename', f'{story_title}.mp3')}",
                            'searchable_text': combined_text,
                            'metadata': story_info
                        }

                        points.append(
                            models.PointStruct(
                                id=point_id,
                                vector=embedding,
                                payload=payload
                            )
                        )
                        point_id += 1
                        self.stats.stories_indexed += 1

                        if point_id % 20 == 0:
                            logger.info(f"Processed {point_id} stories...")

                    except Exception as e:
                        logger.error(f"Failed to process {story_title}: {e}")
                        self.stats.stories_failed += 1

            # Upload to Qdrant in batches
            if points:
                logger.info(f"Uploading {len(points)} stories to Qdrant...")
                batch_size = 50

                for i in range(0, len(points), batch_size):
                    batch = points[i:i+batch_size]
                    self.qdrant_client.upsert(
                        collection_name=self.collection_name,
                        points=batch,
                        wait=True  # Wait for indexing to complete
                    )
                    logger.info(f"Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")

                logger.info(f"Successfully indexed {len(points)} stories")
                return True
            else:
                logger.warning("No valid stories to index")
                return False

        except Exception as e:
            logger.error(f"Failed to index metadata: {e}")
            return False

    def verify_indexing(self) -> bool:
        """Verify that indexing was successful"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            point_count = collection_info.points_count

            logger.info(f"Collection '{self.collection_name}' contains {point_count} stories")

            # Try a sample search
            test_queries = ["sleeping beauty", "hansel gretel", "honest jack", "monkey story"]
            logger.info("Testing searches with sample queries...")

            for test_query in test_queries:
                query_embedding = self.embedding_model.encode(test_query).tolist()
                results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=2
                )

                if results:
                    logger.info(f"Query '{test_query}' found {len(results)} results:")
                    for i, hit in enumerate(results, 1):
                        logger.info(f"  {i}. {hit.payload['title']} ({hit.payload['category']}) - Score: {hit.score:.3f}")
                else:
                    logger.warning(f"No results found for test query: '{test_query}'")

            return point_count > 0

        except Exception as e:
            logger.error(f"Failed to verify indexing: {e}")
            return False

    def run(self, clear: bool = False, verify_only: bool = False):
        """Run the indexing process"""
        start_time = time.time()

        # Initialize
        if not self.initialize():
            logger.error("Initialization failed")
            return False

        if verify_only:
            # Just verify existing index
            success = self.verify_indexing()
            if success:
                logger.info("✅ Verification successful")
            else:
                logger.error("❌ Verification failed")
            return success

        # Create/recreate collection
        if not self.create_collection(recreate=clear):
            logger.error("Failed to create collection")
            return False

        # Load metadata
        metadata_cache = self.load_stories_metadata()
        if not metadata_cache:
            logger.error("No metadata found")
            return False

        # Index metadata
        success = self.index_metadata(metadata_cache)

        # Calculate stats
        self.stats.time_taken = time.time() - start_time

        # Print summary
        logger.info("=" * 60)
        logger.info("STORIES INDEXING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Categories processed: {self.stats.total_categories}")
        logger.info(f"Total stories found: {self.stats.total_stories}")
        logger.info(f"Stories indexed: {self.stats.stories_indexed}")
        logger.info(f"Stories failed: {self.stats.stories_failed}")
        logger.info(f"Time taken: {self.stats.time_taken:.2f} seconds")
        logger.info(f"Categories: {', '.join(self.stats.categories_processed)}")
        logger.info("=" * 60)

        if success:
            logger.info("✅ Stories indexing completed successfully!")
            # Verify the indexing
            self.verify_indexing()
        else:
            logger.error("❌ Stories indexing failed")

        return success

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Index stories metadata for semantic search')
    parser.add_argument('--clear', action='store_true', help='Clear existing index before indexing')
    parser.add_argument('--verify', action='store_true', help='Only verify existing index')
    parser.add_argument('--config', default='data/.config.yaml', help='Path to configuration file')

    args = parser.parse_args()

    # Print header
    print("=" * 60)
    print("STORIES METADATA INDEXER FOR XIAOZHI")
    print("=" * 60)
    print(f"Config file: {args.config}")
    print(f"Clear existing: {args.clear}")
    print(f"Verify only: {args.verify}")
    print("=" * 60)
    print()

    # Run indexer
    indexer = StoriesIndexer(config_path=args.config)
    success = indexer.run(clear=args.clear, verify_only=args.verify)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()