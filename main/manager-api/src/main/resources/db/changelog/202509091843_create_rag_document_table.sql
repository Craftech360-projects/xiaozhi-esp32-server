-- liquibase formatted sql

-- changeset xiaozhi:202509091843
-- comment: Create rag_document table for RAG document management
CREATE TABLE IF NOT EXISTS rag_document (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    document_name VARCHAR(500) COMMENT '文档名称',
    file_name VARCHAR(500) NOT NULL COMMENT '文件名',
    grade VARCHAR(100) COMMENT '年级',
    subject VARCHAR(100) COMMENT '学科',
    file_size BIGINT COMMENT '文件大小(字节)',
    file_path VARCHAR(1000) COMMENT '文件路径',
    status VARCHAR(50) DEFAULT 'UPLOADED' COMMENT '状态: UPLOADED, PROCESSING, PROCESSED, FAILED',
    total_chunks INT DEFAULT 0 COMMENT '总块数',
    processed_chunks INT DEFAULT 0 COMMENT '已处理块数',
    processing_error TEXT COMMENT '处理错误信息',
    processing_stats TEXT COMMENT '处理统计信息',
    upload_time DATETIME COMMENT '上传时间',
    processed_time DATETIME COMMENT '处理完成时间',
    description TEXT COMMENT '描述',
    tags VARCHAR(1000) COMMENT '标签',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted TINYINT DEFAULT 0 COMMENT '删除标记: 0-未删除, 1-已删除'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='RAG文档管理表';

-- Create indexes for better performance
CREATE INDEX idx_rag_document_grade_subject ON rag_document(grade, subject);
CREATE INDEX idx_rag_document_status ON rag_document(status);
CREATE INDEX idx_rag_document_deleted ON rag_document(deleted);
CREATE INDEX idx_rag_document_upload_time ON rag_document(upload_time);