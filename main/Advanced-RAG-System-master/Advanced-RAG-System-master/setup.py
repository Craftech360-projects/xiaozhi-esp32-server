# setup.py
import os
import subprocess
import sys

def create_directories():
    """Create necessary directories"""
    directories = [
        "data/pdfs",
        "data/processed",
        "data/chroma_db",
        "src",
        "config"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✅ Requirements installed successfully")

def setup_environment():
    """Setup environment file"""
    env_content = """# RAG System Configuration
GROQ_API_KEY=your_groq_api_key_here

# Optional: Add other API keys if needed
# OPENAI_API_KEY=your_openai_key_here
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file - Please add your API keys")
    else:
        print("ℹ️ .env file already exists")

def main():
    print("🚀 Setting up RAG System...")
    
    create_directories()
    install_requirements()
    setup_environment()
    
    print("""
    🎉 Setup completed successfully!
    
    Next steps:
    1. Add your GROQ API key to the .env file
    2. Run the demo: streamlit run demo.py
    3. Upload PDF documents and start asking questions!
    
    For command line usage:
    python -c "
    from config.config import Config
    from src.rag_system import RAGSystem
    
    rag = RAGSystem(Config())
    result = rag.add_document('path/to/your/document.pdf')
    print(result)
    
    response = rag.query('Your question here')
    print(response['answer'])
    "
    """)

if __name__ == "__main__":
    main()
