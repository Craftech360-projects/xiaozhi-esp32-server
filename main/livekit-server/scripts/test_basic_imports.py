"""
Basic import test for the RAG system components
Tests imports without heavy ML dependencies
"""

import sys
import os

# Add the parent directory to the path to enable absolute imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def test_basic_imports():
    """Test basic imports without ML dependencies"""
    print("Testing basic imports...")

    try:
        # Test Qdrant manager (no ML dependencies)
        from src.rag.qdrant_manager import QdrantEducationManager
        print("✓ QdrantEducationManager imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import QdrantEducationManager: {e}")
        return False

    try:
        # Test education service
        from src.services.education_service import EducationService
        print("✓ EducationService imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import EducationService: {e}")
        return False

    print("✓ All basic imports successful!")
    return True

def test_environment():
    """Test environment variables"""
    print("\nTesting environment variables...")

    required_vars = ["QDRANT_URL", "QDRANT_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✓ {var} is set")

    if missing_vars:
        print(f"✗ Missing environment variables: {missing_vars}")
        print("Please set these in your .env file")
        return False

    print("✓ All required environment variables are set!")
    return True

def main():
    """Main test function"""
    print("=== RAG System Basic Test ===")

    # Test imports
    imports_ok = test_basic_imports()

    # Test environment
    env_ok = test_environment()

    if imports_ok and env_ok:
        print("\n✓ Basic system test passed!")
        print("The system is ready for testing with ML dependencies.")
        print("To install compatible dependencies, run:")
        print("pip install numpy<2.0")
        print("pip install --force-reinstall sentence-transformers")
    else:
        print("\n✗ Basic system test failed!")
        print("Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main()