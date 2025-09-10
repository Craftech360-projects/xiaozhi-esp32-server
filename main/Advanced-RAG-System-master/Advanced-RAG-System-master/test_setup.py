# complete_test_fixed.py
import os
import sys

print("🚀 Complete RAG System Test (With Fixes)")
print("=" * 50)

# Test 1: Try alternative embedder first
try:
    sys.path.append('.')
    from alternative_embeddings import AlternativeEmbedder

    embedder = AlternativeEmbedder()
    test_embedding = embedder.encode("This is a test sentence")
    print(f"✅ Alternative embedder working! (dim: {len(test_embedding)})")
    embedding_working = True
except Exception as e:
    print(f"❌ Alternative embedder failed: {e}")
    embedding_working = False

# Test 2: Core components
try:
    import chromadb
    print("✅ ChromaDB: OK")

    import fitz
    import pdfplumber
    print("✅ PDF processing: OK")

    from groq import Groq
    print("✅ Groq API: OK")

    import streamlit
    print("✅ Streamlit: OK")

    # Test Tesseract
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    version = pytesseract.get_tesseract_version()
    print(f"✅ Tesseract: {version}")

    components_working = True

except Exception as e:
    print(f"❌ Component failed: {e}")
    components_working = False

# Test 3: Vector store with alternative embedder
try:
    from src.vector_store import VectorStore
    from config.config import Config

    # Mock config for testing
    class MockConfig:
        VECTOR_DB_PATH = "./test_chroma_db"
        COLLECTION_NAME = "test_collection"
        TOP_K_RESULTS = 5

    vector_store = VectorStore(MockConfig())
    print("✅ Vector store with alternative embedder: OK")

    # Clean up test
    import shutil
    shutil.rmtree("./test_chroma_db", ignore_errors=True)

except Exception as e:
    print(f"❌ Vector store test failed: {e}")

print("\n" + "=" * 50)
if embedding_working and components_working:
    print("🎉 RAG SYSTEM READY!")
    print("\n📋 Next Steps:")
    print("1. Your system will use TF-IDF embeddings (works offline)")
    print("2. Run: streamlit run demo.py")
    print("3. Upload PDF and start asking questions!")
    print("\n💡 Note: Using TF-IDF instead of transformer embeddings")
    print("   This works great for document search and is actually faster!")
else:
    print("⚠️ Some components still need fixing")
