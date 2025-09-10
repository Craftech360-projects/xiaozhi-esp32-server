# Enhanced Educational RAG System Setup Guide

## Overview

The Enhanced Educational RAG System adds advanced PDF processing capabilities to xiaozhi-server, combining the best features from both sample projects:

### **Key Features:**
- **Multi-format PDF content extraction** (text, tables, images with OCR)
- **Educational metadata extraction** (chapters, topics, content classification)
- **Smart content chunking** with educational categorization
- **Batch document processing** for textbook collections
- **Intelligent retrieval** with query-type awareness
- **Integration with existing educational RAG** memory provider

## Prerequisites

### Required Dependencies

Install the enhanced educational RAG requirements:

```bash
pip install -r educational_rag_requirements.txt
```

### Optional OCR Setup (Recommended)

For full image processing capabilities, install Tesseract OCR:

**Windows:**
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install and add to PATH
3. Verify: `tesseract --version`

**Linux/macOS:**
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Vector Database Setup

The system supports multiple vector databases:

**Option 1: Qdrant Cloud (Recommended)**
- Uses existing Qdrant configuration in `.config.yaml`
- No additional setup required

**Option 2: Local Qdrant**
```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or install locally
# See: https://qdrant.tech/documentation/quick-start/
```

**Option 3: ChromaDB (Fallback)**
- Automatically used if Qdrant is unavailable
- File-based storage, no additional setup required

## Configuration

Update your `.config.yaml` to include educational RAG settings:

```yaml
Memory:
  educational_rag:
    type: educational_rag
    
    # Vector Database Configuration
    qdrant_url: "https://your-qdrant-url"
    qdrant_api_key: "your-qdrant-api-key"
    
    # Embedding Configuration
    embedding_model: "sentence-transformers/all-MiniLM-L6-v2"
    
    # Document Processing Configuration
    chunk_size: 800
    chunk_overlap: 100
    batch_size: 50
    
    # Subject Configuration
    subjects:
      mathematics:
        collection_name: "class-6-mathematics"
        enabled: true
        agent_class: "MathematicsAgent"
      science:
        collection_name: "class-6-science"
        enabled: true
        agent_class: "ScienceAgent"
    
    # Processing Options
    multi_subject_support: true
    enable_cache: true
    cache_ttl: 3600
    score_threshold: 0.2
    max_results: 5
    include_sources: true
    include_related_topics: true
```

## New Function Calls

The enhanced system adds three new function calls:

### 1. `educational_document_upload`

Upload and process a single educational document:

```python
# Example usage in xiaozhi-server
educational_document_upload(
    file_path="/path/to/textbook.pdf",
    grade="class-6",
    subject="mathematics",
    document_name="Chapter 1 - Numbers"
)
```

**Parameters:**
- `file_path` (required): Path to PDF, TXT, or MD file
- `grade` (default: "class-6"): Educational grade level
- `subject` (default: "mathematics"): Subject area
- `document_name` (optional): Custom name for the document

### 2. `educational_document_batch_upload`

Upload multiple documents from a directory:

```python
# Example usage
educational_document_batch_upload(
    directory_path="/path/to/textbooks/",
    grade="class-6",
    subject="mathematics",
    file_pattern="*.pdf"
)
```

**Parameters:**
- `directory_path` (required): Directory containing documents
- `grade` (default: "class-6"): Educational grade level
- `subject` (default: "mathematics"): Subject area
- `file_pattern` (default: "*.pdf"): File pattern to match

### 3. `educational_collection_info`

Get information about document collections:

```python
# List all collections
educational_collection_info(action="list")

# Get specific collection info
educational_collection_info(
    action="info",
    grade="class-6",
    subject="mathematics"
)
```

**Parameters:**
- `action` (default: "list"): "list" for all collections, "info" for specific
- `grade` (default: "class-6"): Grade level for specific collection
- `subject` (default: "mathematics"): Subject for specific collection

## Usage Examples

### Basic Document Upload

```python
# Upload a single textbook
result = educational_document_upload(
    file_path="/home/user/textbooks/class6_math_chapter1.pdf",
    grade="class-6",
    subject="mathematics"
)
```

### Batch Upload Entire Subject

```python
# Upload all mathematics PDFs from a directory
result = educational_document_batch_upload(
    directory_path="/home/user/textbooks/class6_mathematics/",
    grade="class-6",
    subject="mathematics",
    file_pattern="*.pdf"
)
```

### Check Available Content

```python
# List all available collections
collections = educational_collection_info(action="list")

# Get detailed info about mathematics collection
math_info = educational_collection_info(
    action="info",
    grade="class-6", 
    subject="mathematics"
)
```

### Query Educational Content

After uploading documents, use the existing educational RAG query:

```python
# Ask questions about uploaded content
response = educational_rag_query(
    query="What are fractions and how do you add them?"
)
```

## Content Processing Features

### Automatic Content Extraction

The system automatically extracts and processes:

1. **Text Content**
   - Clean text with mathematical expression normalization
   - Intelligent chunking with overlap
   - Educational content classification

2. **Table Content**
   - Structured data extraction from PDF tables
   - Multiple format representations (text + CSV)
   - Mathematical data detection

3. **Image Content** (with OCR)
   - Text extraction from diagrams and figures
   - Confidence scoring for OCR accuracy
   - Image resizing for processing efficiency

### Educational Metadata Extraction

Each content chunk includes comprehensive metadata:

- **Basic Info**: Grade, subject, page number, chunk index
- **Chapter Info**: Chapter number, title, topics
- **Content Classification**: Definition, example, exercise, formula, etc.
- **Learning Metadata**: Difficulty level, learning objectives
- **Content Analysis**: Word count, mathematical content detection

### Content Categories

The system automatically classifies content into categories:

- **Definition**: Concept definitions and explanations
- **Example**: Worked examples and illustrations
- **Exercise**: Problems and practice questions
- **Formula**: Mathematical formulas and rules
- **Key Concept**: Important points and reminders
- **Table**: Structured data and information
- **Concept**: General educational content

## Monitoring and Maintenance

### Check System Status

```python
# Get collection statistics
info = educational_collection_info(action="info", grade="class-6", subject="mathematics")

# Check processing results
result = educational_document_upload("test.pdf")
print(result.statistics)
```

### Log Monitoring

Monitor these log tags for system health:

- `[ENHANCED-DOC-PROC]`: Document processing activities
- `[DOC-INGESTION]`: Vector database ingestion
- `[EDU-RAG]`: Educational RAG system operations
- `[EDU-DOC-UPLOAD]`: Function call activities

### Troubleshooting

**Common Issues:**

1. **PDF Processing Fails**
   - Check file permissions and path
   - Verify PDF is not password protected
   - Ensure PyMuPDF and pdfplumber are installed

2. **OCR Not Working**
   - Install Tesseract OCR system dependency
   - Check pytesseract and Pillow versions
   - Verify image quality in PDFs

3. **Vector Database Connection Issues**
   - Verify Qdrant URL and API key
   - Check network connectivity
   - Consider using ChromaDB fallback

4. **Memory Issues with Large PDFs**
   - Reduce batch_size in configuration
   - Process documents individually
   - Monitor system resources

## Performance Optimization

### For Large Document Collections

1. **Batch Processing**: Use `educational_document_batch_upload` for efficiency
2. **Chunk Size**: Adjust chunk_size based on content complexity
3. **Embedding Model**: Use smaller models for faster processing
4. **Vector Database**: Use local Qdrant for better performance

### For Better Search Results

1. **Content Quality**: Upload high-quality, well-structured PDFs
2. **Metadata**: Use descriptive document names and consistent grade/subject labeling
3. **Collection Organization**: Separate collections by grade and subject
4. **Query Optimization**: Use educational keywords in queries

## Integration with Existing System

The enhanced educational RAG system is fully compatible with:

- **Existing Memory Provider Interface**: No changes needed
- **Educational RAG Query Function**: Works with uploaded documents
- **Agent System**: Mathematics and Science agents use uploaded content
- **Configuration System**: Uses existing `.config.yaml` structure

## Next Steps

1. **Install Dependencies**: Run `pip install -r educational_rag_requirements.txt`
2. **Configure System**: Update `.config.yaml` with your settings
3. **Upload Test Document**: Try uploading a sample PDF
4. **Verify Processing**: Check logs and collection info
5. **Start Querying**: Ask educational questions about uploaded content

For additional support, check the xiaozhi-server logs and ensure all dependencies are properly installed.