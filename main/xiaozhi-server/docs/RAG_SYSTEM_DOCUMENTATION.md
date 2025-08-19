# RAG System Documentation for Xiaozhi-Server

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [How It Works](#how-it-works)
5. [Implementation Details](#implementation-details)
6. [Usage Guide](#usage-guide)
7. [Troubleshooting](#troubleshooting)
8. [Future Enhancements](#future-enhancements)

## Overview

The RAG (Retrieval-Augmented Generation) system in xiaozhi-server enables intelligent textbook search and educational content retrieval. It allows the AI assistant to access and reference specific textbook content when answering student questions.

### Key Features
- 📚 PDF textbook indexing and search
- 🔍 Semantic search using multilingual embeddings
- 🎯 Filtered search by subject and grade
- 💬 Integration with LLM through function calling
- 📄 Source citation with page numbers
- 🌍 Multilingual support (English, Hindi, Spanish, etc.)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
│                 "What is extrinsic semiconductor?"          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM with Function Calling                │
│  Recognizes educational query → Calls search_textbook()    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  search_textbook Plugin                     │
│  Processes query, applies filters, formats results         │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    SimpleRAGProvider                        │
│  Generates embeddings, searches vector database            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      ChromaDB                               │
│  Vector database storing document embeddings & metadata    │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. RAG Provider System (`/core/providers/rag/`)

#### Base Provider (`base.py`)
```python
class RAGProviderBase(ABC):
    """Abstract base class defining RAG interface"""
    
    @abstractmethod
    def add_document(self, text: str, metadata: Dict[str, Any]) -> bool
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None)
```

#### Simple RAG Provider (`simple_rag.py`)
- **Vector Database**: ChromaDB (persistent local storage)
- **Embedding Model**: `paraphrase-multilingual-MiniLM-L12-v2`
- **Key Methods**:
  - `add_document()`: Index single document
  - `add_documents()`: Batch indexing
  - `search()`: Semantic search with filtering

### 2. Textbook Indexing Script (`/scripts/index_textbook.py`)

**Purpose**: Extract and index textbook content from PDFs

**Process**:
1. Extract text from PDF pages using PyPDF2
2. Chunk text with configurable size and overlap
3. Generate embeddings for each chunk
4. Store in ChromaDB with metadata

**Usage**:
```bash
python scripts/index_textbook.py <pdf_path> <subject> <grade> [options]
```

### 3. Search Plugin (`/plugins_func/functions/search_textbook.py`)

**Function Registration**:
```python
@register_function("search_textbook", function_desc, ToolType.WAIT)
def search_textbook(query: str, subject: str = None, grade: str = None)
```

**Features**:
- Automatic grade format conversion (e.g., "12" → "Class-12")
- Fallback search without filters if filtered search fails
- English-language prompts and responses
- Proper error handling

### 4. Configuration

#### In `.config.yaml`:
```yaml
RAG:
  enabled: true
  db_path: "./rag_db"
  collection_name: "textbooks"
  model_name: "paraphrase-multilingual-MiniLM-L12-v2"
  chunk_size: 500
  chunk_overlap: 50

Intent:
  function_call:
    functions:
      - search_textbook  # Must be included for function calling
```

## How It Works

### 1. Indexing Phase

```mermaid
graph LR
    A[PDF File] --> B[Text Extraction]
    B --> C[Text Chunking]
    C --> D[Embedding Generation]
    D --> E[ChromaDB Storage]
```

**Detailed Steps**:
1. **PDF Processing**: PyPDF2 extracts text page by page
2. **Chunking**: Text split into overlapping chunks (500 chars default)
3. **Embedding**: Sentence transformer converts chunks to vectors
4. **Storage**: ChromaDB stores embeddings with metadata

**Metadata Structure**:
```python
{
    'page': 95,              # Page number
    'chunk_index': 2,        # Chunk position on page
    'subject': 'Physics',    # Subject name
    'grade': 'Class-12',     # Grade level
    'source': 'NCERT-Class-12-Physics-Part-1.pdf',
    'full_path': '/path/to/textbook.pdf'
}
```

### 2. Search Phase

**Query Processing Flow**:

1. **User Query**: "What is extrinsic semiconductor?"

2. **LLM Function Calling**:
   ```json
   {
     "function": "search_textbook",
     "arguments": {
       "query": "extrinsic semiconductor",
       "subject": "Physics",
       "grade": "12"
     }
   }
   ```

3. **Plugin Processing**:
   - Grade conversion: "12" → "Class-12"
   - Build ChromaDB filters
   - Call RAG provider search

4. **Vector Search**:
   - Query embedding generation
   - Similarity search in ChromaDB
   - Filter by metadata if specified

5. **Result Formatting**:
   ```
   [Physics Class-12 - NCERT-Class-12-Physics-Part-1.pdf Page 475]
   An extrinsic semiconductor is a semiconductor that has been 
   doped with impurities to modify its electrical properties...
   ```

### 3. Response Generation

The plugin returns an `ActionResponse` with formatted content:
```python
prompt = f"""Based on the following textbook content, answer the student's question...

Textbook Content:
[Physics Class-12 - Source Page 475]
Content about extrinsic semiconductors...

Student Question: What is extrinsic semiconductor?

Please note:
1. Use simple language
2. Provide examples
3. Encourage understanding
"""
```

## Implementation Details

### ChromaDB Configuration

```python
self.client = chromadb.PersistentClient(
    path=self.db_path,
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)
```

### Filter Syntax for Multiple Conditions

```python
# ChromaDB requires specific format for multiple filters
if len(conditions) == 1:
    where_clause = conditions[0]  # {"subject": {"$eq": "Physics"}}
elif len(conditions) > 1:
    where_clause = {"$and": conditions}  # {"$and": [...]}
```

### Embedding Model Selection

The `paraphrase-multilingual-MiniLM-L12-v2` model is chosen for:
- Multilingual support (100+ languages)
- Compact size (120MB)
- Good performance for educational content
- Fast inference speed

## Usage Guide

### 1. Initial Setup

```bash
# Install dependencies
pip install chromadb sentence-transformers PyPDF2

# Index a textbook
python scripts/index_textbook.py ./textbooks/physics.pdf "Physics" "Class-12"

# Index multiple textbooks
python scripts/index_textbook.py ./math.pdf "Mathematics" "Class-10"
python scripts/index_textbook.py ./chemistry.pdf "Chemistry" "Class-12"
```

### 2. Configuration

Add to your `.config.yaml`:
```yaml
Intent:
  function_call:
    functions:
      - search_textbook  # Enable the search function
```

### 3. Testing

```python
# Test the system
python test_rag_system.py

# Test specific queries
python test_extrinsic_semiconductor.py
```

### 4. Example Queries

- "What is electromagnetic induction?"
- "Explain Newton's laws of motion"
- "How does photosynthesis work?"
- "What are the properties of triangles?"

## Troubleshooting

### Common Issues

1. **"No module named 'chromadb'"**
   ```bash
   pip install chromadb sentence-transformers PyPDF2
   ```

2. **"Search failed: Expected where to have exactly one operator"**
   - Fixed in latest version with proper filter syntax

3. **No results found**
   - Check if textbooks are indexed: `python test_rag_system.py`
   - Try broader search terms
   - Verify grade format matches indexed data

4. **Function not being called**
   - Ensure `search_textbook` is in config functions list
   - Restart server after config changes
   - Check if LLM supports function calling

### Debug Logging

Enable debug logging to see detailed information:
```yaml
log:
  log_level: DEBUG
```

Look for these log entries:
```
[core.providers.tools.unified_tool_handler]-DEBUG-Calling function: search_textbook
[plugins_func.functions.search_textbook]-INFO-Searching for: 'query' with filters: {...}
[core.providers.rag.simple_rag]-DEBUG-Search query: 'query' returned X results
```

## Future Enhancements

### Short Term
1. **OCR Support**: For scanned PDFs using Tesseract
2. **Better Chunking**: Hierarchical chunking preserving document structure
3. **Caching**: Add result caching for frequent queries
4. **Multi-format Support**: DOCX, EPUB, HTML textbooks

### Medium Term
1. **Advanced Filtering**: Chapter/section level filtering
2. **Query Expansion**: Automatic synonym and related term search
3. **Relevance Scoring**: Re-ranking results based on relevance
4. **Multi-modal**: Support for diagrams and equations

### Long Term
1. **Distributed Storage**: Support for larger document collections
2. **Fine-tuned Embeddings**: Domain-specific embedding models
3. **Learning Analytics**: Track what topics students search for
4. **Personalization**: Adapt responses based on student level

## Performance Considerations

### Indexing Performance
- PDF Processing: ~2-5 seconds per page
- Embedding Generation: ~0.1 seconds per chunk
- Database Insertion: ~0.01 seconds per chunk

### Search Performance
- Query Embedding: ~0.1 seconds
- Vector Search: ~0.05-0.2 seconds (depends on collection size)
- Result Formatting: ~0.01 seconds

### Storage Requirements
- Embeddings: ~2KB per chunk
- Metadata: ~0.5KB per chunk
- 100-page textbook: ~50-100MB in database

## API Reference

### RAGProviderBase Methods

```python
add_document(text: str, metadata: Dict[str, Any]) -> bool
# Add single document to RAG database

add_documents(texts: List[str], metadatas: List[Dict[str, Any]]) -> bool
# Batch add multiple documents

search(query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> Dict[str, Any]
# Search for relevant documents

delete_collection(collection_name: str = None) -> bool
# Delete or reset collection

get_collection_info() -> Dict[str, Any]
# Get collection statistics
```

### Plugin Function

```python
search_textbook(query: str, subject: str = None, grade: str = None) -> ActionResponse
# LLM-callable function for textbook search
```

## Conclusion

The RAG system provides a robust foundation for educational content retrieval in xiaozhi-server. By combining semantic search with LLM function calling, it enables accurate, contextual answers from textbook sources while maintaining simplicity and extensibility.