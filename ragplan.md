
● Based on my research, here's a comprehensive plan for implementing RAG for school textbooks in xiaozhi-server:

  RAG Implementation Plan for School Textbooks

  1. Can We Use Mem0 for RAG?

  Yes and No. While Mem0 has some RAG-like capabilities:
  - ✅ It supports semantic search through embeddings
  - ✅ It has a hybrid database system (vector + key-value + graph)
  - ❌ It's designed for conversation memory, not document retrieval
  - ❌ Limited to 1000 free API calls/month
  - ❌ Not optimized for large textbook content

  Recommendation: Use Mem0 as a complementary system for storing learning progress and student interactions, but
  implement a dedicated RAG system for textbook content.

  2. Proposed Architecture

  ┌─────────────────────────────────────────────────────────┐
  │                    xiaozhi-server                       │
  ├─────────────────────────────────────────────────────────┤
  │                                                         │
  │  ┌─────────────────┐       ┌─────────────────┐        │
  │  │  LLM Provider   │       │  Memory Provider │        │
  │  │  (OpenAI, etc.) │       │  (Mem0/Local)    │        │
  │  └────────┬────────┘       └────────┬────────┘        │
  │           │                         │                   │
  │  ┌────────▼─────────────────────────▼────────┐        │
  │  │         Unified Tool Handler              │        │
  │  │  ┌────────────────────────────────────┐  │        │
  │  │  │    NEW: RAG Document Search Plugin │  │        │
  │  │  └────────────────┬───────────────────┘  │        │
  │  └───────────────────┼───────────────────────┘        │
  │                      │                                 │
  │  ┌───────────────────▼───────────────────────┐        │
  │  │         NEW: RAG Provider System          │        │
  │  │  ┌─────────────┐  ┌─────────────────┐   │        │
  │  │  │  Document   │  │  Vector Database │   │        │
  │  │  │  Processor  │  │  (ChromaDB/      │   │        │
  │  │  │             │  │   Qdrant/Local)  │   │        │
  │  │  └─────────────┘  └─────────────────┘   │        │
  │  └───────────────────────────────────────────┘        │
  └─────────────────────────────────────────────────────────┘

  3. Implementation Components

  A. RAG Provider System (New)

  Create a new provider system at /core/providers/rag/:

  1. Base RAG Provider (base.py)
    - Abstract interface for RAG implementations
    - Methods: index_document(), search(), delete_document()
  2. Local RAG Provider (local_rag/)
    - Uses ChromaDB or Qdrant for local vector storage
    - Sentence transformers for embeddings
    - No external API dependencies
  3. Cloud RAG Provider (cloud_rag/) - Optional
    - Integration with Pinecone, Weaviate, etc.
    - For larger deployments

  B. Document Processing Pipeline

  1. Text Extraction
    - PDF parsing (PyPDF2, pdfplumber)
    - OCR support for scanned textbooks
    - Markdown/HTML support
  2. Chunking Strategies
    - Hierarchical chunking for textbook structure
    - Chapter → Section → Subsection → Paragraph
    - Preserve context with overlapping chunks
    - Metadata preservation (chapter, page numbers)
  3. Embedding Generation
    - Use multilingual models (e.g., sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
    - Support for Chinese/English content

  C. RAG Plugin

  Create /plugins_func/functions/rag_textbook_search.py:

  @register_function("search_textbook", function_desc, ToolType.WAIT)
  def search_textbook(query: str, subject: str = None, grade: str = None):
      # Search implementation
      results = rag_provider.search(query, filters={
          "subject": subject,
          "grade": grade
      })
      return ActionResponse(Action.REQLLM, results, None)

  4. Integration with Existing System

  1. Configuration (config.yaml):
  RAG:
    enabled: true
    provider: "local_rag"  # or "cloud_rag"
    local_rag:
      vector_db: "chromadb"
      model: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
      collection_name: "textbooks"
    textbook_path: "./textbooks/"

  2. Memory Integration:
    - Use Mem0 to track what topics the student has studied
    - Store learning progress and difficulties
    - Personalize responses based on past interactions
  3. Context Enhancement:
    - When a student asks a question, first search RAG
    - Combine RAG results with Mem0 memory
    - Pass both to LLM for comprehensive answers

  5. Implementation Steps

  1. Phase 1: Core RAG System (2-3 weeks)
    - Implement base RAG provider interface
    - Create local RAG provider with ChromaDB
    - Build document processing pipeline
    - Basic textbook indexing
  2. Phase 2: Plugin Integration (1 week)
    - Create RAG search plugin
    - Integrate with function calling system
    - Add configuration options
  3. Phase 3: Educational Features (2 weeks)
    - Implement grade/subject filtering
    - Add answer citation (show source page/chapter)
    - Create study progress tracking with Mem0
    - Implement question generation from content
  4. Phase 4: Optimization (1 week)
    - Fine-tune chunking strategies
    - Optimize search relevance
    - Add caching layer
    - Performance testing

  6. Technical Recommendations

  1. Vector Database: Start with ChromaDB (easy setup, good performance)
  2. Embedding Model: Use multilingual sentence transformers
  3. Chunking: 512-1024 tokens with 10-20% overlap
  4. Metadata: Store chapter, section, page number, subject, grade
  5. Reranking: Consider adding a reranking step for better accuracy

  7. Usage Example

  When a child asks: "什么是光合作用？" (What is photosynthesis?)

  1. RAG plugin searches textbook database
  2. Retrieves relevant chunks from biology textbook
  3. Mem0 checks if student has studied this before
  4. LLM generates answer with:
    - Textbook explanation
    - Grade-appropriate language
    - Reference to specific textbook pages
    - Personalized based on learning history

  This implementation provides a robust, scalable solution for integrating textbook content while leveraging the
  existing xiaozhi-server architecture.

● Update Todos
  ⎿  ☒ Research current xiaozhi-server architecture and LLM/memory integration
     ☒ Analyze Mem0 capabilities for RAG implementation
     ☒ Research RAG implementation approaches for educational content
     ☒ Design RAG architecture for textbook integration
     ☒ Create implementation plan with technical details
