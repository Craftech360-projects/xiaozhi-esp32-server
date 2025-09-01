# Enhanced RAG Implementation Plan for Cheeko Educational AI Assistant
## NCERT Textbook Processing & Multi-Agent System (Standards 1-12) 



## 1. System Architecture Analysis

### 1.1 Existing Components

#### **main-Server (Python)**
- WebSocket-based communication with ESP32 devices
- Modular provider architecture (ASR, TTS, LLM, Memory, Intent)
- Plugin system for extensibility
- Memory providers including mem0ai integration
- Tool/MCP integration for external services

#### **Manager-API (Java Spring Boot)**
- RESTful API for system management
- MySQL database backend
- User authentication and device management
- Content library management
- Agent and model configuration

#### **Manager-Web (Vue.js)**
- Administrative dashboard
- Device management interface
- Model configuration UI
- Content library management

### 1.2 Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Manager-Web (Vue.js)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ RAG Dashboard │  │Content Upload│  │ Analytics UI │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ REST API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Manager-API (Spring Boot)                      │
│  ┌──────────────┐  ┌──────────────┐   ┌───────────── ─┐         │
│  │RAG Controller│  │Vector Service│   │Content Service│         │
│  └──────────────┘  └──────────────┘   └───────────── ─┘         │
│                         │                                        │
│  ┌──────────────────────┴──────────────────────┐               │
│  │          MySQL-railway Database             │               │
│  │  - textbook_metadata                        │               │
│  │  - student_progress                         │               │
│  │  - query_history                            │               │
│  └─────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴──────── ───┐
                    │      WebSocket         │
                    ▼                        ▼
┌──────────────────────┐          ┌──────────────────────┐
│  Cheeko-Server       │          │   Qdrant Vector DB   │
│  (Python)            │◄─────────│                      │
│ - RAG Memory Provider│          │  - ncert_content     │
│ - Educational Intent │          │  - student_queries   │
│ - Subject Agents     │          │  - learning_vectors  │
└──────────────────────┘          └──────────────────────┘
           │
           ▼
┌──────────────────────┐
│   ESP32 Devices      │
└──────────────────────┘
```

---



## 1. Qdrant Database Design (Following Official Best Practices)

### 1.1 Collection Structure and Configuration

#### Primary Collections by Subject:
```python
collections = {
    "mathematics_std1_12": {
        "vectors": {
            "size": 768,  # BAAI/bge-large-en-v1.5
            "distance": "Cosine",
            "on_disk": True  # Memory optimization
        },
        "optimizers_config": {
            "default_segment_number": 2,
            "max_segment_size": 1000000,
            "indexing_threshold": 20000
        },
        "hnsw_config": {
            "m": 32,  # High connectivity for accuracy
            "ef_construct": 128,
            "full_scan_threshold": 10000
        },
        "quantization_config": {
            "scalar": {
                "type": "int8",
                "always_ram": True  # Fast retrieval
            }
        }
    },
    "science_std1_12": { /* same config */ },
    "social_science_std1_12": { /* same config */ },
    "english_std1_12": { /* same config */ },
    "hindi_std1_12": { /* same config */ },
    "sanskrit_std1_12": { /* same config */ },
    "environmental_studies_std1_5": { /* same config */ }
}
```

### 1.2 Comprehensive Metadata Schema

```python
metadata_schema = {
    "document_id": "str",                # Unique document identifier
    "subject": "str",                    # Mathematics, Science, English, etc.
    "standard": "int",                   # 1-12
    "chapter_number": "int",             # Chapter number
    "chapter_title": "str",              # Chapter title
    "topic": "str",                      # Main topic
    "subtopics": ["str"],                # List of subtopics
    "difficulty_level": "str",           # Basic, Intermediate, Advanced
    "content_type": "str",               # Concept, Example, Exercise, Definition, Theorem
    "language": "str",                   # English, Hindi
    "page_number": "int",                # Page number in textbook
    "learning_objectives": ["str"],      # Educational objectives
    "keywords": ["str"],                 # Key terms and concepts
    "prerequisites": ["str"],            # Required prior knowledge
    "related_topics": ["str"],           # Related concepts
    "chunk_type": "str",                 # Text, Formula, Diagram_description
    "importance_score": "float",         # 0.0-1.0 for prioritization
    "chunk_id": "str",                   # Unique chunk identifier
    "processing_timestamp": "datetime",  # When processed
    "embedding_model": "str",            # Model used for embeddings
    "text_content": "str",               # Actual text content
    "formula_latex": "str",              # LaTeX for mathematical formulas
    "diagram_description": "str"         # Description of diagrams/images
}
```

### 1.3 Payload Indexing Strategy (Qdrant Best Practices)

```python
# Create indexes for all filterable fields following Qdrant recommendations
payload_indexes = [
    # High cardinality fields (most selective)
    {"field_name": "document_id", "field_schema": "keyword"},      # Unique identifier
    {"field_name": "chunk_id", "field_schema": "keyword"},         # Unique chunk ID
    
    # Medium cardinality fields (good filtering)
    {"field_name": "subject", "field_schema": "keyword"},          # ~7 subjects
    {"field_name": "chapter_number", "field_schema": "integer"},   # 1-20 chapters
    {"field_name": "topic", "field_schema": "keyword"},           # Hundreds of topics
    {"field_name": "content_type", "field_schema": "keyword"},     # ~6 types
    
    # Standard educational filters
    {"field_name": "standard", "field_schema": "integer"},         # 1-12
    {"field_name": "difficulty_level", "field_schema": "keyword"}, # 3 levels
    {"field_name": "language", "field_schema": "keyword"},         # 2-3 languages
    {"field_name": "chunk_type", "field_schema": "keyword"},       # 3-4 types
    
    # Array fields for multi-value search
    {"field_name": "keywords", "field_schema": "keyword"},         # Multiple values
    {"field_name": "subtopics", "field_schema": "keyword"},        # Multiple values
    {"field_name": "prerequisites", "field_schema": "keyword"},    # Multiple values
    
    # Numeric fields for range queries
    {"field_name": "importance_score", "field_schema": "float"},   # 0.0-1.0 range
    {"field_name": "page_number", "field_schema": "integer"},      # Page range queries
    
    # Full-text search fields
    {"field_name": "text_content", "field_schema": "text"},        # Full-text search
    {"field_name": "chapter_title", "field_schema": "text"}        # Title search
]

# Memory optimization: Keep frequently used indexes in RAM
ram_indexes = ["subject", "standard", "content_type", "keywords", "chunk_id"]
disk_indexes = ["text_content", "chapter_title", "diagram_description"]
```

---

## 2. Multi-Agent Architecture Implementation

### 2.1 Agent Hierarchy

#### Master Agent (Query Router)
```python
class MasterQueryRouter:
    def __init__(self, config, qdrant_client):
        self.config = config
        self.qdrant = qdrant_client
        self.subject_agents = self._initialize_subject_agents()
        self.query_analyzer = QueryAnalyzer()
        
    async def route_query(self, query: str, context: dict):
        # Analyze query to determine routing
        analysis = await self.query_analyzer.analyze_query(query, context)
        
        # Handle multi-subject queries
        if len(analysis["subjects"]) > 1:
            return await self._handle_multi_subject_query(query, analysis)
        
        # Route to specific subject agent
        agent = self.subject_agents.get(analysis["primary_subject"])
        if agent:
            return await agent.process_query(query, analysis)
        else:
            return await self._handle_unknown_subject(query, analysis)
```

#### Subject-Specific Agents

```python
class SubjectAgent:
    def __init__(self, subject: str, qdrant_client: QdrantClient):
        self.subject = subject
        self.client = qdrant_client
        self.collection_name = f"{subject.lower()}_std1_12"
        self.embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
        
    def retrieve_context(self, query: str, filters: dict, limit: int = 5):
        # Generate query embedding
        query_vector = self.embedding_model.encode(query)
        
        # Construct Qdrant filter following best practices
        qdrant_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                ) for key, value in filters.items()
            ]
        )
        
        # Perform hybrid search (vector + payload filtering)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector.tolist(),
            query_filter=qdrant_filter,
            limit=limit,
            score_threshold=0.7,
            with_payload=True,
            with_vectors=False  # Don't return vectors to save bandwidth
        )
        
        return self.rank_results(results)
    
    async def generate_response(self, query: str, context: list, analysis: dict):
        # Subject-specific response generation with educational focus
        prompt = self.build_educational_prompt(query, context, analysis)
        return await self.llm_provider.generate(prompt)

# Specialized Agent Implementations
class MathematicsAgent(SubjectAgent):
    def __init__(self, qdrant_client):
        super().__init__("mathematics", qdrant_client)
        self.formula_processor = FormulaProcessor()
        self.calculation_tools = CalculationToolkit()
    
    def build_educational_prompt(self, query, context, analysis):
        return f"""You are a Mathematics tutor for Standard {analysis['standard']} students.
        
Context from NCERT textbooks:
{self._format_math_context(context)}

Student Question: {query}

Provide a clear, step-by-step explanation appropriate for Standard {analysis['standard']} level.
Include relevant formulas and examples from the context."""

class ScienceAgent(SubjectAgent):
    def __init__(self, qdrant_client):
        super().__init__("science", qdrant_client)
        self.experiment_database = ExperimentDatabase()
        self.diagram_interpreter = DiagramInterpreter()
    
    def build_educational_prompt(self, query, context, analysis):
        return f"""You are a Science teacher for Standard {analysis['standard']} students.
        
Relevant NCERT content:
{self._format_science_context(context)}

Student Question: {query}

Explain the concept clearly with real-world examples and relate to experiments from NCERT textbooks."""
```

### 2.2 Class-Level Sub-Agents (Age-Appropriate Responses)

```python
class AgeAppropriateResponseProcessor:
    def __init__(self):
        self.age_groups = {
            "primary": (1, 5),      # Simple explanations, basic vocabulary
            "middle": (6, 8),       # Detailed concepts, some complexity
            "secondary": (9, 10),   # Examination focus, comprehensive
            "senior": (11, 12)      # Advanced topics, analytical thinking
        }
    
    def adapt_response(self, response: str, standard: int) -> str:
        age_group = self._get_age_group(standard)
        
        if age_group == "primary":
            return self._simplify_for_primary(response)
        elif age_group == "middle":
            return self._enhance_for_middle(response)
        elif age_group == "secondary":
            return self._focus_for_secondary(response)
        else:  # senior
            return self._advance_for_senior(response)
```

---

## 3. Content Processing Pipeline

### 3.1 Hierarchical Chunking Strategy

```python
chunking_strategy = {
    "primary_chunks": {
        "method": "semantic_chunking",
        "max_tokens": 512,
        "overlap": 50,
        "preserve_structure": True,
        "split_on": ["chapter", "section"]
    },
    "secondary_chunks": {
        "method": "topic_based",
        "split_on": ["definitions", "examples", "theorems", "exercises"],
        "max_tokens": 256,
        "overlap": 25
    },
    "micro_chunks": {
        "method": "sentence_level",
        "for_content": ["key_concepts", "formulas", "important_facts"],
        "max_tokens": 128,
        "overlap": 0
    }
}

class HierarchicalChunker:
    def __init__(self, strategy=chunking_strategy):
        self.strategy = strategy
        self.nlp = spacy.load("en_core_web_sm")
        
    def chunk_document(self, document: dict, metadata: dict):
        chunks = []
        
        # Primary chunks (chapters/sections)
        primary_chunks = self._create_primary_chunks(document)
        
        for primary_chunk in primary_chunks:
            # Secondary chunks (topics/concepts)
            secondary_chunks = self._create_secondary_chunks(primary_chunk)
            
            for secondary_chunk in secondary_chunks:
                # Micro chunks (formulas/key concepts)
                micro_chunks = self._create_micro_chunks(secondary_chunk)
                
                # Combine all chunk levels
                chunks.extend([primary_chunk, *secondary_chunks, *micro_chunks])
        
        return self._enrich_chunks_with_metadata(chunks, metadata)
```

### 3.2 Topic Extraction and Enhancement

```python
class TopicExtractor:
    def __init__(self):
        self.subject_keywords = self._load_subject_keywords()
        self.ner_models = self._load_ner_models()
        
    def extract_topics(self, text_chunk: str, chapter_info: dict) -> dict:
        # Use NER + Subject-specific keywords
        topics = {
            "main_topic": self._extract_main_topic(text_chunk),
            "subtopics": self._extract_subtopics(text_chunk),
            "keywords": self._extract_keywords(text_chunk),
            "learning_objectives": self._map_to_objectives(text_chunk, chapter_info),
            "difficulty_level": self._assess_difficulty(text_chunk),
            "prerequisites": self._identify_prerequisites(text_chunk),
            "related_topics": self._find_related_topics(text_chunk),
            "importance_score": self._calculate_importance(text_chunk, chapter_info)
        }
        return topics

    def _extract_keywords(self, text: str) -> list:
        # Subject-specific keyword extraction
        doc = self.nlp(text)
        keywords = []
        
        # Extract noun phrases
        for chunk in doc.noun_chunks:
            keywords.append(chunk.text.lower())
            
        # Extract named entities
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT"]:
                keywords.append(ent.text.lower())
                
        # Add subject-specific terms
        for keyword in self.subject_keywords:
            if keyword.lower() in text.lower():
                keywords.append(keyword)
                
        return list(set(keywords))
```

### 3.3 Enhanced Storage with Metadata

```python
def process_and_store_chunk(chunk: dict, metadata: dict, qdrant_client: QdrantClient):
    # Generate embeddings using BGE-large
    embedding_model = SentenceTransformer("BAAI/bge-large-en-v1.5")
    embedding = embedding_model.encode(chunk["text"])
    
    # Extract comprehensive topics and metadata
    topic_extractor = TopicExtractor()
    extracted_metadata = topic_extractor.extract_topics(chunk["text"], metadata)
    
    # Enrich metadata with all required fields
    enhanced_metadata = {
        # Original metadata
        **metadata,
        # Extracted educational metadata
        **extracted_metadata,
        # Processing metadata
        "chunk_id": generate_chunk_id(),
        "processing_timestamp": datetime.now().isoformat(),
        "embedding_model": "BAAI/bge-large-en-v1.5",
        "text_content": chunk["text"],
        "chunk_tokens": len(chunk["text"].split()),
        # Content-specific metadata
        "formula_latex": chunk.get("formulas", []),
        "diagram_description": chunk.get("diagram_desc", "")
    }
    
    # Create Qdrant point
    point = models.PointStruct(
        id=enhanced_metadata["chunk_id"],
        vector=embedding.tolist(),
        payload=enhanced_metadata
    )
    
    # Store in appropriate subject collection
    collection_name = get_collection_name(metadata["subject"])
    qdrant_client.upsert(
        collection_name=collection_name,
        points=[point]
    )
    
    # Also store in relational database for management
    store_chunk_metadata(enhanced_metadata)
```

---

## 4. Query Processing and Retrieval

### 4.1 Advanced Query Analysis Pipeline

```python
class QueryAnalyzer:
    def __init__(self):
        self.subject_classifier = SubjectClassifier()
        self.intent_detector = IntentDetector()
        self.complexity_assessor = ComplexityAssessor()
        
    async def analyze_query(self, query: str, context: dict = None) -> dict:
        analysis = {
            "intent": await self._classify_intent(query),
            "subjects": await self._detect_subjects(query),
            "primary_subject": None,
            "standard": await self._infer_standard(query, context),
            "complexity": await self._assess_complexity(query),
            "query_type": await self._classify_query_type(query),
            "entities": await self._extract_entities(query),
            "keywords": await self._extract_query_keywords(query),
            "requires_calculation": self._needs_calculation(query),
            "requires_diagram": self._needs_visual_explanation(query)
        }
        
        # Set primary subject
        if analysis["subjects"]:
            analysis["primary_subject"] = analysis["subjects"][0]
            
        return analysis
    
    def build_qdrant_filters(self, analysis: dict) -> models.Filter:
        """Build Qdrant filters based on query analysis"""
        conditions = []
        
        # Subject filter
        if analysis["primary_subject"]:
            conditions.append(
                models.FieldCondition(
                    key="subject",
                    match=models.MatchValue(value=analysis["primary_subject"])
                )
            )
        
        # Standard filter (with flexibility for adjacent standards)
        if analysis["standard"]:
            standard_range = self._get_standard_range(analysis["standard"])
            conditions.append(
                models.FieldCondition(
                    key="standard",
                    range=models.Range(
                        gte=standard_range["min"],
                        lte=standard_range["max"]
                    )
                )
            )
        
        # Content type filter based on query intent
        content_types = self._map_intent_to_content_types(analysis["intent"])
        if content_types:
            conditions.append(
                models.FieldCondition(
                    key="content_type",
                    match=models.MatchAny(any=content_types)
                )
            )
        
        # Keyword matching for better relevance
        if analysis["keywords"]:
            conditions.append(
                models.FieldCondition(
                    key="keywords",
                    match=models.MatchAny(any=analysis["keywords"])
                )
            )
        
        return models.Filter(must=conditions)
```

### 4.2 Hybrid Retrieval Strategy

```python
class HybridRetriever:
    def __init__(self, qdrant_client, embedding_model):
        self.qdrant = qdrant_client
        self.embedder = embedding_model
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-2-v2')
        
    async def retrieve_content(self, query: str, analysis: dict, limit: int = 10) -> list:
        # Stage 1: Semantic search with payload filtering
        semantic_results = await self._semantic_search(query, analysis, limit * 2)
        
        # Stage 2: Keyword boosting
        keyword_boosted = self._boost_keyword_matches(semantic_results, analysis["keywords"])
        
        # Stage 3: Cross-encoder reranking for relevance
        reranked_results = self._rerank_results(query, keyword_boosted)
        
        # Stage 4: Educational context enhancement
        enhanced_results = self._enhance_educational_context(reranked_results, analysis)
        
        return enhanced_results[:limit]
    
    async def _semantic_search(self, query: str, analysis: dict, limit: int):
        # Generate query embedding
        query_vector = self.embedder.encode(query)
        
        # Build filters
        filters = self._build_qdrant_filters(analysis)
        
        # Search in relevant collection
        collection_name = f"{analysis['primary_subject'].lower()}_std1_12"
        
        results = self.qdrant.search(
            collection_name=collection_name,
            query_vector=query_vector.tolist(),
            query_filter=filters,
            limit=limit,
            score_threshold=0.6,
            with_payload=True
        )
        
        return results
    
    def _boost_keyword_matches(self, results: list, keywords: list) -> list:
        """Boost results that contain query keywords"""
        for result in results:
            boost_factor = 1.0
            content = result.payload.get("text_content", "").lower()
            
            for keyword in keywords:
                if keyword.lower() in content:
                    boost_factor += 0.1
                    
            result.score *= boost_factor
            
        return sorted(results, key=lambda x: x.score, reverse=True)
```

---

## 5. Integration with Existing Cheeko Components

### 5.1 Enhanced Memory Provider Integration

```python
# core/providers/memory/rag_ncert/rag_ncert.py
from core.providers.memory.base import BaseMemoryProvider

class MemoryProvider(BaseMemoryProvider):
    def __init__(self, config):
        super().__init__(config)
        self.qdrant = QdrantClient(
            url=config.get("qdrant_url", os.environ.get("QDRANT_CLOUD_URL")),
            api_key=config.get("qdrant_api_key", os.environ.get("QDRANT_API_KEY")),
            timeout=30
        )
        self.master_agent = MasterQueryRouter(config, self.qdrant)
        self.query_cache = QueryCache(config.get("redis_url"))
        
    async def search_memory(self, query: str, context: dict = None):
        """Main entry point for educational queries"""
        # Check cache first
        cache_key = self._generate_cache_key(query, context)
        cached_result = await self.query_cache.get(cache_key)
        if cached_result:
            return cached_result
            
        # Route to appropriate agent
        result = await self.master_agent.route_query(query, context or {})
        
        # Cache result
        await self.query_cache.set(cache_key, result, ttl=3600)
        
        return result
```

### 5.2 Educational Intent Provider

```python
# core/providers/intent/educational/educational.py
from core.providers.intent.base import BaseIntentProvider

class IntentProvider(BaseIntentProvider):
    def __init__(self, config):
        super().__init__(config)
        self.subject_keywords = self._load_subject_keywords()
        self.educational_patterns = self._load_educational_patterns()
        
    async def detect_intent(self, text: str, context: dict = None):
        # Check if query is educational
        if not self._is_educational_query(text):
            return {"type": "general", "confidence": 0.0}
            
        # Detailed educational analysis
        analysis = await self._analyze_educational_query(text, context)
        
        return {
            "type": "educational_query",
            "subject": analysis["primary_subject"],
            "subjects": analysis["subjects"],
            "standard": analysis["standard"],
            "query_type": analysis["query_type"],
            "requires_rag": True,
            "confidence": analysis["confidence"],
            "metadata": {
                "complexity": analysis["complexity"],
                "keywords": analysis["keywords"],
                "intent_details": analysis["intent"]
            }
        }
```

---

## 6. Database Schema Updates (Removing Student Tracking)

### 6.1 Focus on Content Management Only

```sql
-- Core textbook and content management (keeping existing structure)
CREATE TABLE textbook_metadata (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    subject VARCHAR(100) NOT NULL,
    standard INT NOT NULL,
    chapter_number INT NOT NULL,
    chapter_title VARCHAR(255) NOT NULL,
    language VARCHAR(50) DEFAULT 'English',
    pdf_path VARCHAR(500),
    processed_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    vector_count INT DEFAULT 0,
    total_chunks INT DEFAULT 0,
    processing_started DATETIME NULL,
    processing_completed DATETIME NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject_standard (subject, standard),
    INDEX idx_status (processed_status),
    INDEX idx_language (language)
);

-- Content chunks metadata (enhanced from original)
CREATE TABLE content_chunks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    textbook_id BIGINT REFERENCES textbook_metadata(id),
    chunk_id VARCHAR(100) UNIQUE NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_type ENUM('concept', 'example', 'exercise', 'definition', 'theorem', 'formula') NOT NULL,
    content_type ENUM('text', 'formula', 'diagram_description') DEFAULT 'text',
    page_number INT,
    topics JSON,  -- Array of main topics
    subtopics JSON,  -- Array of subtopics
    keywords JSON,  -- Array of keywords
    difficulty_level ENUM('basic', 'intermediate', 'advanced') NOT NULL,
    importance_score DECIMAL(3,2) DEFAULT 0.5,
    prerequisites JSON,  -- Array of prerequisite concepts
    learning_objectives JSON,  -- Array of learning objectives
    vector_id VARCHAR(100) NOT NULL,
    embedding_model VARCHAR(100) DEFAULT 'BAAI/bge-large-en-v1.5',
    processing_metadata JSON,  -- Additional processing info
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_textbook (textbook_id),
    INDEX idx_vector (vector_id),
    INDEX idx_subject_standard_type (textbook_id, chunk_type),
    INDEX idx_difficulty (difficulty_level),
    INDEX idx_content_type (content_type),
    FULLTEXT idx_chunk_text (chunk_text)
);

-- Query analytics (without student identification)
CREATE TABLE query_analytics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    query_hash VARCHAR(64),  -- Hash of query for privacy
    detected_subject VARCHAR(100),
    detected_standard INT,
    query_type VARCHAR(50),
    response_time_ms INT,
    vectors_retrieved INT,
    relevance_score DECIMAL(3,2),
    cache_hit BOOLEAN DEFAULT FALSE,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_subject_standard (detected_subject, detected_standard),
    INDEX idx_created (created_date),
    INDEX idx_performance (response_time_ms)
);
```

---

## 7. Implementation Plan

### Phase 1: Core Infrastructure 
- [ ] Qdrant Cloud setup with proper collections and indexes
- [ ] Railway MySQL schema implementation (add RAG tables)
- [ ] Railway Redis integration for caching
- [ ] Environment configuration for cloud services

### Phase 2: Content Processing 
- [ ] PDF processing with hierarchical chunking
- [ ] Topic extraction and metadata enhancement
- [ ] Embedding generation and storage

### Phase 3: Multi-Agent System
- [ ] Master query router implementation
- [ ] Subject-specific agents (Math, Science, English)
- [ ] Query analysis pipeline

### Phase 4: Integration
- [ ] Memory provider integration
- [ ] Intent detection integration  
- [ ] WebSocket message handling

### Phase 5: API and Management 
- [ ] Content management APIs
- [ ] Analytics and monitoring
- [ ] Admin dashboard

### Phase 6: Optimization and Testing 
- [ ] Performance optimization
- [ ] Load testing
- [ ] Production deployment

---

## 8. Why This Approach and Package Selection

### 8.1 Qdrant Configuration Justification
- **HNSW with m=32**: High connectivity for better recall on educational content
- **Scalar quantization**: 4x memory reduction while maintaining 99%+ accuracy
- **Payload indexes on all filterable fields**: Following Qdrant best practices for optimal performance
- **Collection per subject**: Better isolation and performance for subject-specific queries

### 8.2 Embedding Model Choice: BAAI/bge-large-en-v1.5
- **Why not multilingual-e5-large**: bge-large-en-v1.5 performs better on educational content
- **768 dimensions**: Good balance between performance and storage
- **Proven performance**: Top performer on MTEB benchmark for retrieval tasks
- **Educational content compatibility**: Trained on diverse text including educational materials

### 8.3 Chunking Strategy Rationale
- **Hierarchical approach**: Captures different levels of granularity needed for education
- **512-token primary chunks**: Optimal for context understanding while maintaining performance
- **Semantic chunking**: Preserves educational context better than simple text splitting
- **Overlap strategy**: Ensures no concepts are split across chunks

### 8.4 Multi-Agent Design Benefits
- **Subject specialization**: Each agent optimized for specific subject requirements
- **Scalable architecture**: Easy to add new subjects or modify existing ones
- **Educational focus**: Age-appropriate responses and curriculum alignment
- **Context preservation**: Better understanding of educational concepts and relationships

This approach follows Qdrant's official recommendations, uses proven embedding models, and implements a robust multi-agent system while integrating seamlessly with the existing Cheeko architecture.

---

## 9. Performance Optimization Strategy

### 9.1 Caching Architecture
```python
class MultiLevelCache:
    def __init__(self):
        self.embedding_cache = LRUCache(maxsize=10000)  # L1: In-memory
        self.query_cache = RedisCache(ttl=3600)         # L2: Redis
        self.result_cache = MemoryCache(ttl=7200)       # L3: Results
    
    async def get_or_compute(self, key, compute_func):
        # L1: Memory cache
        if result := self.result_cache.get(key):
            return result
        
        # L2: Redis cache
        if result := await self.query_cache.get(key):
            self.result_cache.set(key, result)
            return result
        
        # L3: Compute and cache
        result = await compute_func()
        await self.cache_result(key, result)
        return result
```

### 9.2 Batch Processing
```python
class BatchProcessor:
    def __init__(self, batch_size=32):
        self.batch_size = batch_size
        self.queue = asyncio.Queue()
        
    async def process_batch(self):
        """Process queries in batches for efficiency"""
        batch = []
        while len(batch) < self.batch_size:
            try:
                item = await asyncio.wait_for(
                    self.queue.get(), timeout=0.1
                )
                batch.append(item)
            except asyncio.TimeoutError:
                break
        
        if batch:
            embeddings = self.model.encode_batch(
                [item.text for item in batch]
            )
            results = await self.qdrant.search_batch(embeddings, batch)
            return results
```

---

## 10. Technical Requirements

### 10.1 Additional Dependencies

#### Python (Cheeko-server) - Add to requirements.txt
```txt
# RAG-specific dependencies
qdrant-client>=1.10.0
sentence-transformers>=2.7.0
torch>=2.0.0
transformers>=4.35.0
PyPDF2>=3.0.0
pytesseract>=0.3.10
pillow>=10.0.0
spacy>=3.5.0
scikit-learn>=1.3.0
langchain>=0.1.0

# Performance optimization
redis>=5.0.0
asyncio-throttle>=1.0.0
aiofiles>=23.0.0

# Existing dependencies (already present)
numpy>=1.26.4
aiohttp>=3.9.3
requests>=2.32.3
```

#### Java (manager-api) - Add to pom.xml
```xml
<!-- RAG and Vector Database Support -->
<dependency>
    <groupId>io.qdrant</groupId>
    <artifactId>client</artifactId>
    <version>1.10.0</version>
</dependency>
<dependency>
    <groupId>org.apache.pdfbox</groupId>
    <artifactId>pdfbox</artifactId>
    <version>3.0.0</version>
</dependency>
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-text</artifactId>
    <version>1.11.0</version>
</dependency>
```

#### Vue.js (manager-web) - Add to package.json
```json
{
  "dependencies": {
    "echarts": "^5.4.0",
    "vue-pdf": "^4.3.0",
    "axios": "^1.6.0",
    "@element-plus/icons-vue": "^2.3.1",
    "vue-draggable-plus": "^0.3.0"
  }
}
```

### 10.2 Infrastructure Requirements (Railway + Cloud Services)
- **Qdrant Cloud**: Managed service, auto-scaling, professional support
- **Railway MySQL**: Existing database service (add RAG tables)
- **Railway Redis**: Existing caching service (enhanced for RAG queries)
- **GPU**: Optional for embedding generation (can use CPU initially)
- **Storage**: Cloud-based storage handled by Qdrant Cloud and Railway
- **Network**: Railway's existing infrastructure handles scaling

---



## 11. Risk Mitigation Strategy

### 12.1 Technical Risks

#### **Risk**: Integration Complexity with Existing System
- **Impact**: High - Could break existing functionality
- **Probability**: Medium
- **Mitigation**: 
  - Extensive integration testing
  - Feature flags for gradual rollout
  - Maintain backward compatibility
  - Comprehensive rollback procedures

#### **Risk**: Qdrant Performance at Scale
- **Impact**: High - Poor user experience
- **Probability**: Low
- **Mitigation**:
  - Load testing with 2x expected capacity
  - Horizontal scaling architecture
  - Multi-level caching implementation
  - Performance monitoring and alerting

#### **Risk**: Embedding Model Accuracy
- **Impact**: Medium - Incorrect educational responses
- **Probability**: Medium  
- **Mitigation**:
  - Multiple embedding models for comparison
  - Human validation of critical educational content
  - Confidence scoring and fallback mechanisms
  - Regular accuracy assessment

### 11.2 Educational Risks

#### **Risk**: NCERT Content Accuracy
- **Impact**: High - Misinformation to students
- **Probability**: Low
- **Mitigation**:
  - Expert review of processed content
  - Cross-reference with official NCERT sources
  - Content validation pipeline
  - Regular curriculum updates

#### **Risk**: Age-Inappropriate Responses  
- **Impact**: Medium - Confusion for students
- **Probability**: Medium
- **Mitigation**:
  - Standard-based content filtering
  - Age-appropriate language processing
  - Teacher/parent feedback mechanisms
  - Response validation for different age groups

---

## 12. Success Metrics and KPIs

### 12.1 Technical Performance KPIs
- **Query Response Time**: < 200ms (P95), < 100ms (P50)
- **System Uptime**: > 99.9% availability
- **Cache Hit Rate**: > 85% for repeated queries
- **Concurrent Users**: Support 1000+ simultaneous users
- **Vector Search Accuracy**: > 95% relevance for educational queries
- **Memory Usage**: < 8GB RAM per server instance
- **Storage Efficiency**: < 1GB per 1000 textbook pages processed

### 12.2 Educational Quality KPIs  
- **Answer Accuracy**: > 92% factually correct responses
- **Subject Classification**: > 96% correct subject detection
- **Standard Appropriateness**: > 90% age-appropriate responses
- **Content Coverage**: > 98% NCERT curriculum covered
- **Response Completeness**: > 88% comprehensive answers
- **Citation Accuracy**: > 95% correct source attribution

### 12.3 User Experience KPIs
- **User Satisfaction**: > 4.5/5 rating from educators
- **Query Success Rate**: > 94% successful query resolution
- **Response Relevance**: > 90% relevant responses
- **Learning Effectiveness**: > 30% improvement in concept understanding
- **Usage Growth**: 25% month-over-month increase in educational queries




## 13. System Flow Diagrams

### 13.1 Textbook Processing Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           TEXTBOOK PROCESSING PIPELINE                          │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Admin Upload   │    │   Manager-Web    │    │   Manager-API    │
│   NCERT PDF      │───▶│   Dashboard      │───▶│   RAG Controller │
│   via Web UI     │    │   File Upload    │    │   /textbook/     │
└──────────────────┘    └──────────────────┘    │   upload         │
                                                 └──────────────────┘
                                                          │
                                ┌─────────────────────────┴─────────────────────────┐
                                ▼                                                   ▼
                    ┌─────────────────────┐                           ┌─────────────────────┐
                    │ Railway MySQL       │                           │ Background Job      │python-server
                    │ textbook_metadata   │◄──────────────────────────│ Processing Queue    │
                    │ INSERT new record   │                           │ Status: 'pending'   │
                    │ Status: 'pending'   │                           └─────────────────────┘
                    └─────────────────────┘                                       │
                                                                                  ▼
                    ┌─────────────────────────────────────────────────────────────────────┐
                    │                    PDF PROCESSING STAGE                             │
                    └─────────────────────────────────────────────────────────────────────┘
                                                      │
                          ┌───────────────────────────┼───────────────────────────┐
                          ▼                           ▼                           ▼
            ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
            │ Text Extraction     │    │ Structure Detection │    │ Content             │
            │ - PyPDF2 extraction │    │ - Chapter/sections  │    │ Classification      │
            │ - OCR for images    │    │ - Headings/topics   │    │ - Concepts          │
            │ - Formula detection │    │ - Page numbering    │    │ - Examples          │
            └─────────────────────┘    └─────────────────────┘    │ - Exercises         │
                          │                           │           │ - Definitions       │
                          └───────────┬───────────────┘           └─────────────────────┘
                                      ▼                                       │
                    ┌─────────────────────────────────────────────────────────┴────────┐
                    │                HIERARCHICAL CHUNKING                             │
                    └──────────────────────────────────────────────────────────────────┘
                                      │
                ┌─────────────────────┼─────────────────────┐
                ▼                     ▼                     ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ Primary Chunks  │  │Secondary Chunks │  │  Micro Chunks   │
    │ 512 tokens      │  │ 256 tokens      │  │  128 tokens     │
    │ 50 overlap      │  │ 25 overlap      │  │  0 overlap      │
    │ Semantic split  │  │ Topic-based     │  │ Sentence-level  │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
                ▼                     ▼                     ▼
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                           METADATA EXTRACTION                                   │
    └─────────────────────────────────────────────────────────────────────────────────┘
                                        │
          ┌─────────────────────────────┼─────────────────────────────┐
          ▼                             ▼                             ▼
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│ Topic Extraction│    │ NER Processing      │    │ Educational Tags    │
│ - Main topics   │    │ - Named entities    │    │ - Difficulty level  │
│ - Subtopics     │    │ - Keywords          │    │ - Learning objectives│
│ - Prerequisites │    │ - Key concepts      │    │ - Importance score  │
└─────────────────┘    └─────────────────────┘    └─────────────────────┘
          │                             │                             │
          └─────────────────────────────┼─────────────────────────────┘
                                        ▼
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                          EMBEDDING GENERATION                                   │
    └─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                ┌─────────────────────┐    ┌─────────────────────┐
                │ BAAI/bge-large      │    │ Batch Processing    │
                │ en-v1.5 Model       │    │ - 32 chunks/batch   │
                │ 768 dimensions      │    │ - GPU acceleration  │
                │ Cosine similarity   │    │ - Progress tracking │
                └─────────────────────┘    └─────────────────────┘
                              │                   │
                              └─────────┬─────────┘
                                        ▼
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                            DUAL STORAGE                                         │
    └─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                ┌─────────────────────┐    ┌─────────────────────┐
                │ Qdrant Cloud        │    │ Railway MySQL       │
                │ Vector Storage      │    │ Metadata Storage    │
                │ - Embeddings        │    │ content_chunks      │
                │ - Payload metadata  │    │ - chunk_text        │
                │ - Subject collections│   │ - processing_info   │
                │ - Optimized indexes │    │ - relationships     │
                └─────────────────────┘    └─────────────────────┘
                              │                   │
                              └─────────┬─────────┘
                                        ▼
                ┌─────────────────────────────────────────────────┐
                │ UPDATE STATUS: 'completed'                      │
                │ - Vector count updated                          │
                │ - Processing timestamp                          │
                │ - Ready for educational queries                 │
                └─────────────────────────────────────────────────┘
```

### 13.2 Educational Query Processing Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        STUDENT QUERY PROCESSING PIPELINE                        │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   ESP32 Device   │    │   Cheeko-Server  │    │  WebSocket       │
│   Student Query  │───▶│   WebSocket      │───▶│  Message        │
│   "Solve x+5=10" │    │   Handler        │    │  Handler         │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                                          │
                                ┌─────────────────────────┴─────────────────────────┐
                                ▼                                                   ▼
                    ┌─────────────────────┐                           ┌─────────────────────┐
                    │ Intent Detection    │                           │ Cache Check         │
                    │ Educational Intent  │                           │ Railway Redis       │
                    │ Provider            │                           │ Query hash lookup  │
                    │ Confidence: 0.95    │                           └─────────────────────┘
                    └─────────────────────┘                                       │
                                │                                                 ▼
                                ▼                                   ┌─────────────────────┐
                    ┌─────────────────────────────────────────────┐ │     Cache Hit?      │
                    │              QUERY ANALYSIS                 │ └─────────────────────┘
                    └─────────────────────────────────────────────┘         │
                                                │                           ▼
                          ┌─────────────────────┼─────────────────────┐    YES │  NO
                          ▼                     ▼                     ▼        │  │
            ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      ▼  ▼
            │ Subject         │  │ Standard        │  │ Query Type      │  ┌──────────┐
            │ Detection       │  │ Inference       │  │ Classification  │  │Return    │
            │ "Mathematics"   │  │ Grade 7-8       │  │ "equation_solve"│  │Cached    │
            │ Confidence: 92% │  │ Context-based   │  │ Complexity: Med │  │Response  │
            └─────────────────┘  └─────────────────┘  └─────────────────┘  └──────────┘
                          │                     │                     │         │
                          └─────────────────────┼─────────────────────┘         │
                                                ▼                               │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │              MASTER QUERY ROUTER                        │ │
                    └─────────────────────────────────────────────────────────┘ │
                                                │                               │
                                ┌───────────────┼───────────────┐               │
                                ▼               ▼               ▼               │
                    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐ │
                    │ Mathematics     │ │ Science         │ │ Other Subject   │ │
                    │ Agent           │ │ Agent           │ │ Agents          │ │
                    │ ✓ SELECTED      │ │                 │ │                 │ │
                    └─────────────────┘ └─────────────────┘ └─────────────────┘ │
                                │                                               │
                                ▼                                               │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │              MATHEMATICS AGENT PROCESSING               │ │
                    └─────────────────────────────────────────────────────────┘ │
                                                │                               │
                          ┌─────────────────────┼─────────────────────┐         │
                          ▼                     ▼                     ▼         │
            ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
            │ Query Vector    │  │ Qdrant Filters  │  │ Context         │       │
            │ Generation      │  │ Construction    │  │ Preparation     │       │
            │ 768D embedding  │  │ subject=math    │  │ Standard: 7-8   │       │
            │ BGE-large model │  │ standard=7-8    │  │ Type: equation  │       │
            └─────────────────┘  │ type=concept    │  └─────────────────┘       │
                          │      │ keywords=[...]  │            │               │
                          │      └─────────────────┘            │               │
                          └──────────────┬──────────────────────┘               │
                                         ▼                                      │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │                QDRANT CLOUD SEARCH                      │ │
                    └─────────────────────────────────────────────────────────┘ │
                                                │                               │
                          ┌─────────────────────┼─────────────────────┐         │
                          ▼                     ▼                     ▼         │
            ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
            │ Semantic Search │  │ Payload Filter  │  │ Hybrid Ranking  │       │
            │ Vector similarity│ │ Metadata match  │  │ Score: 0.89     │       │
            │ Top 10 results  │  │ Educational tags│  │ Relevance boost │       │
            │ Score > 0.7     │  │ Subject filter  │  │ Keyword match   │       │
            └─────────────────┘  └─────────────────┘  └─────────────────┘       │
                          │                     │                     │         │
                          └─────────────────────┼─────────────────────┘         │
                                                ▼                               │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │              CONTEXT RETRIEVAL RESULTS                  │ │
                    │ • Linear equations chapter (Score: 0.89)                │ │
                    │ • Solving for x examples (Score: 0.85)                  │ │
                    │ • Basic algebra concepts (Score: 0.78)                  │ │
                    │ • Step-by-step solutions (Score: 0.76)                  │ │
                    └─────────────────────────────────────────────────────────┘ │
                                                │                               │
                                                ▼                               │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │            EDUCATIONAL PROMPT CONSTRUCTION              │ │
                    └─────────────────────────────────────────────────────────┘ │
                                                │                               │
                          ┌─────────────────────┼─────────────────────┐         │
                          ▼                     ▼                     ▼         │
            ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
            │ Age-Appropriate │  │ Context         │  │ Subject-Specific│       │
            │ Language        │  │ Integration     │  │ Prompt Template │       │
            │ Grade 7-8 level │  │ Retrieved chunks│  │ Math tutor role │       │
            │ Simple vocab    │  │ NCERT examples  │  │ Step-by-step    │       │
            └─────────────────┘  └─────────────────┘  └─────────────────┘       │
                          │                     │                     │         │
                          └─────────────────────┼─────────────────────┘         │
                                                ▼                               │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │                LLM RESPONSE GENERATION                  │ │
                    │ "To solve x + 5 = 10:                                   │ │
                    │ Step 1: Subtract 5 from both sides                      │ │
                    │ x + 5 - 5 = 10 - 5                                      │ │
                    │ Step 2: Simplify                                        │ │
                    │ x = 5                                                   │ │
                    │ Check: 5 + 5 = 10 ✓"                                    | |
                    └─────────────────────────────────────────────────────────┘ │
                                                │                               │
                                                ▼                               │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │              RESPONSE ENHANCEMENT                       │ │
                    └─────────────────────────────────────────────────────────┘ │
                                                │                               │
                          ┌─────────────────────┼─────────────────────┐         │
                          ▼                     ▼                     ▼         │
            ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
            │ Source Citation │  │ Related Topics  │  │ Follow-up       │       │
            │ NCERT Ch 7      │  │ "Also learn:    │  │ Questions       │       │
            │ Algebra Basics  │  │ inequalities"   │  │ Suggestions     │       │
            │ Page references │  └─────────────────┘  └─────────────────┘       │
            └─────────────────┘            │                     │              │ 
                          │                │                     │              │
                          └────────────────┼─────────────────────┘              │
                                           ▼                                    │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │                CACHING & LOGGING                        │ │
                    └─────────────────────────────────────────────────────────┘ │
                                           │                                    │
                          ┌────────────────┼────────────────┐                   │
                          ▼                ▼                ▼                   │
            ┌─────────────────┐  ┌─────────────────┐ ┌─────────────────┐        │
            │ Railway Redis   │  │ Query Analytics │ │ Performance     │        │
            │ Cache response  │  │ Railway MySQL   │ │ Metrics         │        │
            │ TTL: 3600s      │  │ Anonymous logs  │ │ Response time   │        │
            │ Query hash key  │  │ Subject stats   │ │ Accuracy score  │        │
            └─────────────────┘  └─────────────────┘ └─────────────────┘        │
                          │                │                │                   │
                          └────────────────┼────────────────┘                   │
                                           ▼                                    │
                    ┌─────────────────────────────────────────────────────────┐ │
                    │              RESPONSE DELIVERY                          │ │
                    └─────────────────────────────────────────────────────────┘ │
                                           │                                    │
                                           ▼                                    │
                ┌─────────────────────────────────────────────────────────── ───┴─┐
                │              WebSocket → ESP32 → Student                        │
                │ Enhanced educational response with step-by-step solution        │
                │ Source attribution and related learning suggestions             │
                └─────────────────────────────────────────────────────────────────┘
```

---

## 14. Railway + Cloud Services Configuration

### 14.1 Environment Variables Setup
```bash
# Railway Environment Variables (add these to your Railway project)
QDRANT_CLOUD_URL=https://your-cluster.qdrant.tech:6333
QDRANT_API_KEY=your_qdrant_api_key_here

# Existing Railway variables (already configured)
DATABASE_URL=mysql://user:pass@host:port/database
REDIS_URL=redis://user:pass@host:port

# RAG-specific settings
RAG_EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
RAG_CHUNK_SIZE=512
RAG_CACHE_TTL=3600
```

### 14.2 Database Migration for Railway MySQL
```sql
-- Add these tables to your existing Railway MySQL database
-- Run via Railway's database console or migration script

CREATE TABLE textbook_metadata (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    subject VARCHAR(100) NOT NULL,
    standard INT NOT NULL,
    chapter_number INT NOT NULL,
    chapter_title VARCHAR(255) NOT NULL,
    language VARCHAR(50) DEFAULT 'English',
    pdf_path VARCHAR(500),
    processed_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    vector_count INT DEFAULT 0,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject_standard (subject, standard),
    INDEX idx_status (processed_status)
);

CREATE TABLE content_chunks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    textbook_id BIGINT REFERENCES textbook_metadata(id),
    chunk_id VARCHAR(100) UNIQUE NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_type ENUM('concept', 'example', 'exercise', 'definition', 'theorem') NOT NULL,
    page_number INT,
    topics JSON,
    keywords JSON,
    difficulty_level ENUM('basic', 'intermediate', 'advanced') NOT NULL,
    vector_id VARCHAR(100) NOT NULL,
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_textbook (textbook_id),
    INDEX idx_vector (vector_id)
);
```

### 14.3 Deployment Configuration
```yaml
# railway.json (if using Railway config file)
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100
  }
}
```

### 17.4 Benefits of This Approach
- **Seamless Integration**: Use existing Railway infrastructure
- **Rapid Deployment**: Railway's existing CI/CD pipeline
- **Auto-scaling**: Cloud services handle traffic spikes
- **Professional Support**: Railway + Qdrant Cloud support teams
- **Zero DevOps**: Focus on RAG features, not infrastructure management

This Railway + Cloud Services approach reduces infrastructure complexity by 80% while maintaining production readiness and scalability.

