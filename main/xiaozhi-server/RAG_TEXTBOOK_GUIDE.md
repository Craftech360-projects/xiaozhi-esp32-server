# RAG Textbook Integration Guide

This guide explains how to use the RAG (Retrieval-Augmented Generation) system for textbook integration in xiaozhi-server.

## Installation

1. Install required dependencies:
```bash
cd main/xiaozhi-server
pip install chromadb sentence-transformers PyPDF2
```

## Usage

### 1. Index a Textbook

Use the indexing script to add a textbook to the RAG database:

```bash
cd main/xiaozhi-server
python scripts/index_textbook.py <pdf_path> <subject> <grade>

# Example:
python scripts/index_textbook.py ./textbooks/math_grade5.pdf "Mathematics" "Grade-5"
```

Options:
- `--chunk-size`: Size of text chunks (default: 500 characters)
- `--reset`: Reset the collection before indexing

### 2. Test the System

Run the test script to verify everything is working:

```bash
python test_rag_system.py
```

### 3. Using in Conversation

Once indexed, the system will automatically use the textbook content when answering related questions. Examples:

- "What is a fraction?"
- "Please explain photosynthesis"
- "How to do division in 5th grade math?"
- "What is the water cycle?"
- "Explain Newton's laws of motion"

The system will:
1. Search relevant textbook content
2. Provide answers based on the textbook
3. Include source information (subject, grade, page number)

## Directory Structure

```
main/xiaozhi-server/
├── core/providers/rag/          # RAG implementation
│   ├── base.py                  # Base RAG provider class
│   └── simple_rag.py            # ChromaDB implementation
├── plugins_func/functions/
│   └── search_textbook.py       # LLM function for textbook search
├── scripts/
│   └── index_textbook.py        # Textbook indexing script
├── rag_db/                      # Vector database storage (auto-created)
└── textbooks/                   # Place your PDF textbooks here
```

## Configuration

The RAG system is configured in `config.yaml`:

```yaml
RAG:
  enabled: true
  db_path: "./rag_db"
  collection_name: "textbooks"
  model_name: "paraphrase-multilingual-MiniLM-L12-v2"
  chunk_size: 500
  chunk_overlap: 50
```

## Adding Multiple Textbooks

You can index multiple textbooks by running the script multiple times:

```bash
# Math textbook
python scripts/index_textbook.py ./textbooks/math_grade5.pdf "Mathematics" "Grade-5"

# English textbook
python scripts/index_textbook.py ./textbooks/english_grade5.pdf "English" "Grade-5"

# Science textbook
python scripts/index_textbook.py ./textbooks/science_grade5.pdf "Science" "Grade-5"

# Physics textbook (for higher grades)
python scripts/index_textbook.py ./textbooks/physics_grade12.pdf "Physics" "Class-12"
```

## Troubleshooting

1. **"No module named 'chromadb'"**: Install dependencies with `pip install chromadb sentence-transformers PyPDF2`

2. **"Failed to initialize RAG provider"**: Check if you have write permissions in the current directory

3. **"No text extracted from PDF"**: Ensure the PDF contains text (not scanned images). For scanned PDFs, OCR support will be needed.

4. **Low quality results**: Try adjusting chunk_size in the configuration or when running the indexing script

## Future Enhancements

- OCR support for scanned textbooks
- Advanced chunking strategies for better context preservation
- Multi-language embedding models
- Web UI for textbook management
- Integration with Mem0 for learning progress tracking