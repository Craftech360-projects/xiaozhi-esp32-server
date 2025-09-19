# Educational RAG System for LiveKit Agent

## Overview

This system implements a comprehensive RAG (Retrieval Augmented Generation) solution for educational content, specifically designed for students in grades 6-12. The system can process textbooks, extract content with rich metadata, and provide intelligent answers to student questions.

## Features

### 🎯 Core Capabilities
- **Multi-Grade Support**: Handles content for grades 6-12
- **Subject-Specific Collections**: Separate Qdrant collections for each grade-subject combination
- **Intelligent Query Understanding**: Analyzes student questions to determine intent and required cognitive level
- **Contextual Retrieval**: Finds relevant content with proper educational context
- **Grade-Appropriate Responses**: Adjusts language complexity based on student grade level

### 📚 Content Processing
- **Advanced PDF Processing**: Extracts text, tables, images, and formulas from textbooks
- **OCR Integration**: Processes images and diagrams with text extraction
- **Table Extraction**: Converts tables to structured formats (markdown, JSON)
- **Formula Recognition**: Handles mathematical equations in LaTeX format
- **Metadata Enrichment**: Automatically extracts topics, difficulty levels, and learning objectives

### 🔍 Smart Retrieval
- **Multi-Collection Search**: Searches across multiple grade-subject collections
- **Prerequisite Awareness**: Can search lower grades for foundational concepts
- **Content Type Filtering**: Finds definitions, examples, exercises, or explanations as needed
- **Visual Aid Integration**: Includes references to figures, tables, and diagrams

## Architecture

```
├── src/
│   ├── rag/                           # Core RAG components
│   │   ├── qdrant_manager.py          # Collection management
│   │   ├── document_processor.py      # PDF processing & chunking
│   │   ├── embeddings.py              # Multi-modal embeddings
│   │   └── retriever.py               # Intelligent search
│   │
│   ├── education/                     # Educational components
│   │   └── textbook_ingestion.py      # Ingestion pipeline
│   │
│   ├── services/
│   │   └── education_service.py       # Main educational service
│   │
│   └── agent/
│       └── educational_agent.py       # LiveKit agent with RAG
```

## Quick Start

### 1. Environment Setup

Create a `.env` file with required credentials:

```env
# Qdrant Configuration
QDRANT_URL=https://your-cluster-url.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

# OpenAI for Embeddings
OPENAI_API_KEY=your-openai-api-key

# Groq for LLM
GROQ_API_KEY=your-groq-api-key

# LiveKit Configuration
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Initialize Collections

The system automatically creates collections for all grade-subject combinations:

- `grade_6_mathematics`, `grade_6_science`, `grade_6_english`, etc.
- `grade_7_mathematics`, `grade_7_science`, etc.
- ... up to grade 12

### 4. Run Agent in Educational Mode

Add this to your `.env` file:
```env
ENABLE_EDUCATION=true
```

Then run:
```bash
python main.py
```

For standard (non-educational) mode, either omit `ENABLE_EDUCATION` or set it to `false`.

## Usage Examples

### Student Interaction

```
Student: "Hi, I'm in grade 8 and need help with linear equations"
Agent: "Great! I've set your grade level to 8 for mathematics. I'm ready to help you with linear equations!"

Student: "What is a linear equation?"
Agent: "A linear equation is an equation in which the highest power of the variable is 1. For example, 2x + 3 = 7 is a linear equation.

Source: Sample Mathematics Grade 8, page 45

Would you like me to show you how to solve linear equations?"

Student: "Yes, can you give me practice problems?"
Agent: "Here are 3 practice problems for linear equations:

Problem 1: Solve the equation 3x - 5 = 10. Show all steps in your solution.
Problem 2: Find the value of x in 2x + 7 = 15.
Problem 3: Solve for y: 4y - 3 = 2y + 5.

Would you like me to show you how to solve any of these problems?"
```

### Available Functions

The educational agent provides these function tools:

- `set_student_context(grade, subject)` - Set student's grade and current subject
- `search_textbook(question, subject, grade)` - Search textbooks for answers
- `explain_concept(concept, subject, detail_level)` - Get concept explanations
- `get_practice_problems(topic, difficulty, count)` - Find practice problems
- `get_step_solution(problem)` - Get step-by-step solutions
- `search_by_topic(topic, content_type)` - Search by specific topics

## Content Ingestion

### Textbook Processing Pipeline

```python
from src.education.textbook_ingestion import TextbookIngestionPipeline

# Initialize pipeline
pipeline = TextbookIngestionPipeline()
await pipeline.initialize()

# Ingest a textbook
success = await pipeline.ingest_textbook(
    pdf_path="path/to/textbook.pdf",
    grade=8,
    subject="mathematics",
    textbook_name="Algebra Fundamentals",
    author="John Smith",
    isbn="978-1234567890"
)
```

### Batch Ingestion

```python
textbooks = [
    {
        "pdf_path": "grade8_math.pdf",
        "grade": 8,
        "subject": "mathematics",
        "textbook_name": "Grade 8 Mathematics",
        "author": "Education Board"
    },
    {
        "pdf_path": "grade8_science.pdf",
        "grade": 8,
        "subject": "science",
        "textbook_name": "Grade 8 Science",
        "author": "Science Publishers"
    }
]

results = await pipeline.ingest_multiple_textbooks(textbooks)
```

## Collection Schema

Each collection stores rich metadata for educational content:

### Core Fields
- `content` - The actual text content
- `content_type` - Type: text, table, formula, diagram, example, exercise
- `textbook_name`, `author`, `isbn` - Source information
- `page_number`, `chapter`, `section` - Location references

### Educational Metadata
- `grade`, `subject` - Academic classification
- `topic`, `subtopic`, `keywords` - Content categorization
- `difficulty_level` - beginner, intermediate, advanced
- `cognitive_level` - Based on Bloom's taxonomy
- `prerequisites` - Required prior knowledge
- `learning_objectives` - What students will learn

### Subject-Specific Fields

**Mathematics:**
- `formula_latex` - LaTeX representation
- `variables` - Mathematical variables
- `theorem_name` - Named theorems
- `problem_category` - Type of math problem

**Sciences (Physics/Chemistry):**
- `formula_latex` - Scientific formulas
- `units` - Measurement units
- `experiment_name` - Lab experiments
- `safety_notes` - Safety information

**Biology:**
- `biological_system` - Body systems, ecosystems
- `organism_type` - Type of organism
- `process_name` - Biological processes

## Testing

### Run Sample Test

```bash
python scripts/ingest_sample_textbook.py
```

This script:
1. Initializes the RAG system
2. Creates sample educational content
3. Tests retrieval with sample queries
4. Validates the responses

### Manual Testing

```python
from src.services.education_service import EducationService

# Initialize service
service = EducationService()
await service.initialize()

# Set context
await service.set_student_context(grade=8, subject="mathematics")

# Ask questions
result = await service.answer_question("What is a linear equation?")
print(result["answer"])
```

## Configuration

### Qdrant Collections

Collections are automatically created with the naming pattern:
- `grade_{number}_{subject}`
- Examples: `grade_8_mathematics`, `grade_12_physics`

### Vector Dimensions
- Text embeddings: 1536 (OpenAI text-embedding-3-small)
- Visual embeddings: 512 (CLIP)
- Formula embeddings: 768 (MPNet)

### Embedding Models
- **Text**: OpenAI text-embedding-3-small (primary) or Sentence Transformers (fallback)
- **Visual**: CLIP ViT-B/32 for image understanding
- **Formula**: all-mpnet-base-v2 for mathematical content

## Advanced Features

### Multi-Modal Content
- Processes images and diagrams with OCR
- Extracts and indexes table content
- Handles mathematical formulas in LaTeX

### Intelligent Chunking
- Preserves semantic boundaries
- Maintains context between chunks
- Links related content (figures, tables, examples)

### Educational Query Analysis
- Detects question types (definition, explanation, problem-solving)
- Identifies required cognitive level
- Determines if examples or visual aids are needed

### Adaptive Responses
- Adjusts language complexity for grade level
- Provides appropriate detail level
- Includes relevant examples and practice problems

## Performance Considerations

### Indexing
- Batch processing for faster ingestion
- Embedding caching to avoid recomputation
- Parallel processing for multiple textbooks

### Search Optimization
- Multi-collection search with grade-based filtering
- Semantic similarity combined with metadata filtering
- Result re-ranking based on educational relevance

### Memory Management
- Streaming for large PDF files
- Chunk-based processing to handle memory constraints
- Cleanup functions for failed ingestions

## Troubleshooting

### Common Issues

1. **Collections not created**
   - Check Qdrant URL and API key
   - Verify network connectivity

2. **No embeddings generated**
   - Verify OpenAI API key
   - Check embedding model availability

3. **PDF processing fails**
   - Ensure PyMuPDF and pdfplumber are installed
   - Check file permissions and format

4. **Poor search results**
   - Verify content has been properly ingested
   - Check if query matches available content
   - Try different query phrasings

### Logging

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

```python
# Check service status
stats = await education_service.get_service_stats()
print(stats)

# Validate content quality
validation = await pipeline.validate_ingested_content(collection_name)
print(validation)
```

## Future Enhancements

### Planned Features
- Support for more file formats (DOCX, EPUB)
- Advanced mathematical equation parsing
- Multi-language support
- Student progress tracking
- Adaptive learning recommendations

### Integration Possibilities
- LMS integration (Canvas, Moodle)
- Assessment generation
- Study plan creation
- Parent/teacher dashboards

## Contributing

When adding new features:

1. **Subject Support**: Add new subjects by extending the `grade_subjects` mapping
2. **Content Types**: Add new content types in the schema definitions
3. **Embedding Models**: Add new embedding models in the `EmbeddingManager`
4. **Query Types**: Extend the `QueryAnalyzer` for new question patterns

## License

This educational RAG system is designed for educational purposes and research. Please ensure compliance with textbook licensing and copyright requirements when ingesting content.


> tell me how to ask question in this??

● To ask questions in this educational RAG system, you need to:

  1. Start the LiveKit server with educational mode enabled:
  python main.py
  2. Connect to the LiveKit room using:
    - A LiveKit client application
    - Web browser with LiveKit web SDK
    - Mobile app with LiveKit SDK
  3. Set your grade and subject context by saying:
    - "I'm in grade 10 studying science"
    - "Set my context to grade 10 science"
  4. Ask questions naturally like:
    - "What is a chemical reaction?"
    - "Explain acids and bases"
    - "How do metals react with oxygen?"
    - "What are the types of chemical reactions?"

  The system will:
  - Search the Grade 10 science textbook content in Qdrant
  - Find relevant chunks using vector similarity
  - Generate answers using the AI model
  - Provide source references (textbook, page numbers)

  Alternative for testing without LiveKit client:
  You can also test directly using the education service script we
   created earlier:
  python scripts/process_grade10_science_focused.py

  This runs the test queries at the end and shows how the system
  responds to Grade 10 science questions.
