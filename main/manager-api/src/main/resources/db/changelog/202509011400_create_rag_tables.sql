-- RAG System Tables for Educational AI Assistant
-- Standard 6 Mathematics Implementation with Full Extensibility

-- Textbook metadata table (ready for all subjects and standards)
CREATE TABLE IF NOT EXISTS `rag_textbook_metadata` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `subject` VARCHAR(100) NOT NULL COMMENT 'Subject name: mathematics, science, english, etc.',
  `standard` INT NOT NULL COMMENT 'Class standard: 1-12',
  `chapter_number` INT NOT NULL COMMENT 'Chapter number within textbook',
  `chapter_title` VARCHAR(255) NOT NULL COMMENT 'Chapter title',
  `textbook_title` VARCHAR(255) NOT NULL COMMENT 'Complete textbook title',
  `language` VARCHAR(50) NOT NULL DEFAULT 'English' COMMENT 'Content language',
  `pdf_path` VARCHAR(500) COMMENT 'Path to original PDF file',
  `total_pages` INT COMMENT 'Total pages in textbook',
  `curriculum_year` VARCHAR(20) COMMENT 'Academic year/curriculum version',
  `processed_status` ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending',
  `vector_count` INT DEFAULT 0 COMMENT 'Total vectors stored in Qdrant',
  `chunk_count` INT DEFAULT 0 COMMENT 'Total chunks processed',
  `processing_started_at` DATETIME NULL,
  `processing_completed_at` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `created_by` BIGINT COMMENT 'User who initiated processing',
  
  -- Indexes for performance
  INDEX `idx_subject_standard` (`subject`, `standard`),
  INDEX `idx_status` (`processed_status`),
  INDEX `idx_language` (`language`),
  INDEX `idx_created_at` (`created_at`),
  
  -- Unique constraint to prevent duplicate textbooks
  UNIQUE KEY `uk_textbook` (`subject`, `standard`, `chapter_number`, `language`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Textbook metadata for RAG system';

-- Content chunks table with rich educational metadata
CREATE TABLE IF NOT EXISTS `rag_content_chunks` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `textbook_id` BIGINT NOT NULL COMMENT 'Reference to textbook metadata',
  `chunk_id` VARCHAR(100) NOT NULL COMMENT 'Unique chunk identifier for Qdrant',
  `chunk_text` TEXT NOT NULL COMMENT 'Actual text content of the chunk',
  `chunk_type` ENUM('concept', 'example', 'exercise', 'definition', 'theorem', 'formula', 'diagram_description') NOT NULL,
  `content_type` ENUM('text', 'formula', 'diagram_description', 'mixed') NOT NULL DEFAULT 'text',
  
  -- Document structure
  `page_number` INT COMMENT 'Page number in original textbook',
  `section_title` VARCHAR(255) COMMENT 'Section/subsection title',
  `paragraph_index` INT COMMENT 'Paragraph position within section',
  
  -- Educational metadata (JSON for flexibility)
  `topics` JSON COMMENT 'Array of main topics covered',
  `subtopics` JSON COMMENT 'Array of detailed subtopics',
  `keywords` JSON COMMENT 'Array of educational keywords',
  `learning_objectives` JSON COMMENT 'Array of learning objectives addressed',
  `prerequisites` JSON COMMENT 'Array of prerequisite concepts',
  `related_concepts` JSON COMMENT 'Array of related topics for cross-referencing',
  
  -- Content classification
  `difficulty_level` ENUM('basic', 'intermediate', 'advanced') NOT NULL DEFAULT 'basic',
  `importance_score` DECIMAL(3,2) DEFAULT 0.50 COMMENT 'Curriculum importance (0.0-1.0)',
  `cognitive_level` ENUM('remember', 'understand', 'apply', 'analyze', 'evaluate', 'create') COMMENT 'Bloom\'s taxonomy level',
  
  -- Technical metadata
  `chunk_tokens` INT COMMENT 'Token count for the chunk',
  `chunk_level` ENUM('primary', 'secondary', 'micro') NOT NULL DEFAULT 'primary' COMMENT 'Hierarchical chunk level',
  `parent_chunk_id` VARCHAR(100) COMMENT 'Parent chunk for hierarchical structure',
  `child_chunk_ids` JSON COMMENT 'Array of child chunk IDs',
  
  -- Vector database metadata
  `vector_id` VARCHAR(100) NOT NULL COMMENT 'Vector ID in Qdrant collection',
  `embedding_model` VARCHAR(100) NOT NULL DEFAULT 'BAAI/bge-large-en-v1.5',
  `embedding_dimension` INT NOT NULL DEFAULT 768,
  `collection_name` VARCHAR(100) NOT NULL COMMENT 'Qdrant collection name',
  
  -- Processing metadata
  `processing_metadata` JSON COMMENT 'Additional processing information',
  `quality_score` DECIMAL(3,2) COMMENT 'Content quality assessment (0.0-1.0)',
  `extraction_method` VARCHAR(50) COMMENT 'How content was extracted (pdf, ocr, manual)',
  
  -- Timestamps
  `processed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  -- Foreign key constraint
  CONSTRAINT `fk_chunks_textbook` FOREIGN KEY (`textbook_id`) REFERENCES `rag_textbook_metadata`(`id`) ON DELETE CASCADE,
  
  -- Indexes for performance
  INDEX `idx_textbook_id` (`textbook_id`),
  INDEX `idx_chunk_id` (`chunk_id`),
  INDEX `idx_vector_id` (`vector_id`),
  INDEX `idx_content_type` (`content_type`),
  INDEX `idx_chunk_type` (`chunk_type`),
  INDEX `idx_difficulty_level` (`difficulty_level`),
  INDEX `idx_collection_name` (`collection_name`),
  INDEX `idx_page_number` (`page_number`),
  INDEX `idx_importance_score` (`importance_score`),
  INDEX `idx_processed_at` (`processed_at`),
  
  -- Unique constraint for chunk IDs
  UNIQUE KEY `uk_chunk_id` (`chunk_id`),
  
  -- Full-text search index
  FULLTEXT KEY `ft_chunk_text` (`chunk_text`),
  FULLTEXT KEY `ft_section_title` (`section_title`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Content chunks with educational metadata';

-- Query analytics table (privacy-focused, no personal data)
CREATE TABLE IF NOT EXISTS `rag_query_analytics` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `query_hash` VARCHAR(64) NOT NULL COMMENT 'SHA-256 hash of query for privacy',
  `detected_subject` VARCHAR(100) COMMENT 'AI-detected subject',
  `detected_standard` INT COMMENT 'AI-inferred standard level',
  `query_type` VARCHAR(50) COMMENT 'Type of educational query',
  `query_complexity` ENUM('low', 'medium', 'high') COMMENT 'Query complexity level',
  `intent_confidence` DECIMAL(3,2) COMMENT 'Intent detection confidence',
  
  -- Performance metrics
  `response_time_ms` INT COMMENT 'Total response time in milliseconds',
  `retrieval_time_ms` INT COMMENT 'Vector retrieval time',
  `llm_time_ms` INT COMMENT 'LLM generation time',
  `vectors_retrieved` INT COMMENT 'Number of vectors retrieved',
  `cache_hit` BOOLEAN DEFAULT FALSE COMMENT 'Whether result was cached',
  
  -- Quality metrics
  `relevance_score` DECIMAL(3,2) COMMENT 'Average relevance score of results',
  `user_satisfaction` ENUM('positive', 'neutral', 'negative') COMMENT 'User feedback if provided',
  `response_used` BOOLEAN DEFAULT TRUE COMMENT 'Whether response was accepted',
  
  -- Context
  `session_id` VARCHAR(100) COMMENT 'Anonymous session identifier',
  `device_type` VARCHAR(50) COMMENT 'ESP32 or other device type',
  `query_timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  
  -- Indexes for analytics
  INDEX `idx_detected_subject_standard` (`detected_subject`, `detected_standard`),
  INDEX `idx_query_timestamp` (`query_timestamp`),
  INDEX `idx_query_type` (`query_type`),
  INDEX `idx_response_time` (`response_time_ms`),
  INDEX `idx_cache_hit` (`cache_hit`),
  INDEX `idx_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Anonymous query analytics for system optimization';

-- Processing jobs table for async processing
CREATE TABLE IF NOT EXISTS `rag_processing_jobs` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `textbook_id` BIGINT NOT NULL,
  `job_type` ENUM('pdf_processing', 'embedding_generation', 'vector_storage', 'metadata_extraction') NOT NULL,
  `job_status` ENUM('pending', 'running', 'completed', 'failed', 'cancelled') NOT NULL DEFAULT 'pending',
  `progress_percentage` DECIMAL(5,2) DEFAULT 0.00 COMMENT 'Job completion percentage',
  `current_step` VARCHAR(255) COMMENT 'Current processing step description',
  `total_steps` INT COMMENT 'Total number of processing steps',
  `completed_steps` INT DEFAULT 0,
  
  -- Job details
  `job_config` JSON COMMENT 'Job configuration parameters',
  `error_message` TEXT COMMENT 'Error details if job failed',
  `result_summary` JSON COMMENT 'Job result summary',
  
  -- Timing
  `started_at` DATETIME NULL,
  `completed_at` DATETIME NULL,
  `estimated_completion` DATETIME NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  -- Worker information
  `worker_id` VARCHAR(100) COMMENT 'Processing worker identifier',
  `retry_count` INT DEFAULT 0 COMMENT 'Number of retry attempts',
  `max_retries` INT DEFAULT 3 COMMENT 'Maximum allowed retries',
  
  CONSTRAINT `fk_jobs_textbook` FOREIGN KEY (`textbook_id`) REFERENCES `rag_textbook_metadata`(`id`) ON DELETE CASCADE,
  
  INDEX `idx_textbook_id` (`textbook_id`),
  INDEX `idx_job_status` (`job_status`),
  INDEX `idx_job_type` (`job_type`),
  INDEX `idx_created_at` (`created_at`),
  INDEX `idx_started_at` (`started_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Async processing jobs for RAG content';

-- Qdrant collection management table
CREATE TABLE IF NOT EXISTS `rag_qdrant_collections` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
  `collection_name` VARCHAR(100) NOT NULL COMMENT 'Qdrant collection name',
  `subject` VARCHAR(100) NOT NULL COMMENT 'Subject this collection handles',
  `standards` JSON NOT NULL COMMENT 'Array of standards covered (e.g., [1,2,3,4,5,6,7,8,9,10,11,12])',
  `vector_dimension` INT NOT NULL DEFAULT 768,
  `distance_metric` VARCHAR(20) NOT NULL DEFAULT 'Cosine',
  `total_vectors` BIGINT DEFAULT 0,
  `collection_config` JSON COMMENT 'Qdrant collection configuration',
  `optimization_config` JSON COMMENT 'Performance optimization settings',
  
  -- Status
  `status` ENUM('active', 'inactive', 'optimizing', 'error') NOT NULL DEFAULT 'active',
  `last_optimized` DATETIME NULL,
  `health_score` DECIMAL(3,2) COMMENT 'Collection health score (0.0-1.0)',
  
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  
  UNIQUE KEY `uk_collection_name` (`collection_name`),
  INDEX `idx_subject` (`subject`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Qdrant collections management';

-- Insert initial collection for Standard 6 Mathematics
INSERT INTO `rag_qdrant_collections` (
  `collection_name`, 
  `subject`, 
  `standards`, 
  `vector_dimension`, 
  `distance_metric`,
  `collection_config`,
  `optimization_config`
) VALUES (
  'mathematics_std6',
  'mathematics', 
  '[6]',
  768,
  'Cosine',
  JSON_OBJECT(
    'hnsw_config', JSON_OBJECT('m', 32, 'ef_construct', 128),
    'quantization_config', JSON_OBJECT('type', 'scalar', 'scalar_type', 'int8'),
    'optimizers_config', JSON_OBJECT('default_segment_number', 2, 'max_segment_size', 1000000)
  ),
  JSON_OBJECT(
    'indexing_threshold', 20000,
    'payload_on_disk', false,
    'vectors_on_disk', true
  )
) ON DUPLICATE KEY UPDATE
  `updated_at` = CURRENT_TIMESTAMP,
  `collection_config` = VALUES(`collection_config`),
  `optimization_config` = VALUES(`optimization_config`);

-- Create indexes on JSON columns for better performance (MySQL 8.0+)
-- These are optional but recommended for production
-- ALTER TABLE rag_content_chunks ADD INDEX idx_topics ((CAST(topics AS CHAR(255) ARRAY)));
-- ALTER TABLE rag_content_chunks ADD INDEX idx_keywords ((CAST(keywords AS CHAR(255) ARRAY)));
-- ALTER TABLE rag_content_chunks ADD INDEX idx_difficulty_topics (difficulty_level, (CAST(topics AS CHAR(255) ARRAY)));