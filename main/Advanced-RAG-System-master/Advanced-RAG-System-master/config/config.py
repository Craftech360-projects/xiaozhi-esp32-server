# config/config.py
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

    # Model Configuration
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    LLM_MODEL = "llama-3.1-8b-instant"  # Groq model

    # Vector Database
    VECTOR_DB_PATH = "./data/chroma_db"
    COLLECTION_NAME = "pdf_documents"

    # PDF Processing
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_IMAGE_SIZE = (800, 600)

    # Retrieval
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.7

    # Paths
    PDF_UPLOAD_DIR = "./data/pdfs"
    PROCESSED_DATA_DIR = "./data/processed"
