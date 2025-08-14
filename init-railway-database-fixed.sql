-- ============================================
-- Xiaozhi AI Toy Database Schema (FIXED)
-- For Railway MySQL Database
-- Project: vibrant-vitality
-- ============================================

-- Ensure proper character set
ALTER DATABASE railway CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;

-- ============================================
-- Drop existing tables (for clean install)
-- ============================================
DROP TABLE IF EXISTS learning_milestones;
DROP TABLE IF EXISTS interaction_categories;
DROP TABLE IF EXISTS daily_analytics;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_sessions;
DROP TABLE IF EXISTS parental_settings;
DROP TABLE IF EXISTS child_profile;
DROP TABLE IF EXISTS ai_device;
DROP TABLE IF EXISTS sys_user_token;
DROP TABLE IF EXISTS sys_user;

-- ============================================
-- Core System Tables
-- ============================================

-- System users table (for parents)
CREATE TABLE sys_user (
    id BIGINT NOT NULL AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(100) COMMENT 'BCrypt encrypted password',
    email VARCHAR(100),
    phone VARCHAR(20),
    full_name VARCHAR(100),
    super_admin TINYINT UNSIGNED DEFAULT 0 COMMENT '0=Regular user, 1=Admin',
    status TINYINT DEFAULT 1 COMMENT '0=Inactive, 1=Active',
    last_login DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Parent/Admin users';

-- Authentication tokens
CREATE TABLE sys_user_token (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    token VARCHAR(100) NOT NULL,
    token_type VARCHAR(20) DEFAULT 'Bearer',
    expire_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_id (user_id),
    UNIQUE KEY uk_token (token),
    FOREIGN KEY (user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    INDEX idx_expire (expire_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Authentication tokens';

-- ============================================
-- Device Management
-- ============================================

-- IoT devices (ESP32 toys) - FIXED: Removed DEFAULT UUID()
CREATE TABLE ai_device (
    id VARCHAR(32) NOT NULL,
    mac_address VARCHAR(50) NOT NULL,
    device_name VARCHAR(100),
    device_type VARCHAR(50) DEFAULT 'esp32',
    board_model VARCHAR(50) COMMENT 'e.g., ESP32-S3, ESP32-C3',
    firmware_version VARCHAR(20),
    last_connected_at DATETIME,
    last_ip_address VARCHAR(45),
    is_online BOOLEAN DEFAULT FALSE,
    total_usage_minutes INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_mac (mac_address),
    INDEX idx_online (is_online),
    INDEX idx_last_connected (last_connected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI Toy devices';

-- ============================================
-- Child Management
-- ============================================

-- Child profiles - FIXED: Removed DEFAULT UUID() and GENERATED column
CREATE TABLE child_profile (
    id VARCHAR(32) NOT NULL,
    parent_user_id BIGINT NOT NULL,
    child_name VARCHAR(100) NOT NULL,
    nickname VARCHAR(50),
    birth_date DATE,
    age INT AS (TIMESTAMPDIFF(YEAR, birth_date, CURDATE())) STORED,
    gender ENUM('male', 'female', 'other', 'prefer_not_to_say'),
    device_id VARCHAR(32),
    avatar_url VARCHAR(255),
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    interests JSON COMMENT 'Array of interests',
    learning_level VARCHAR(20) COMMENT 'beginner, intermediate, advanced',
    preferences JSON COMMENT 'User preferences and settings',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (parent_user_id) REFERENCES sys_user(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES ai_device(id) ON DELETE SET NULL,
    INDEX idx_parent (parent_user_id),
    INDEX idx_device (device_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Child user profiles';

-- ============================================
-- Conversation Storage
-- ============================================

-- Chat sessions - FIXED: Removed DEFAULT UUID() and changed GENERATED column
CREATE TABLE chat_sessions (
    id VARCHAR(32) NOT NULL,
    child_profile_id VARCHAR(32) NOT NULL,
    device_id VARCHAR(32),
    session_start DATETIME NOT NULL,
    session_end DATETIME,
    duration_seconds INT AS (TIMESTAMPDIFF(SECOND, session_start, IFNULL(session_end, NOW()))) STORED,
    interaction_count INT DEFAULT 0,
    ai_model_used VARCHAR(50),
    session_quality_score DECIMAL(3,2) COMMENT 'Quality score 0-1',
    is_complete BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (id),
    FOREIGN KEY (child_profile_id) REFERENCES child_profile(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES ai_device(id) ON DELETE SET NULL,
    INDEX idx_child (child_profile_id),
    INDEX idx_start_time (session_start),
    INDEX idx_child_date (child_profile_id, session_start DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Conversation sessions';

-- Individual messages
CREATE TABLE chat_messages (
    id BIGINT NOT NULL AUTO_INCREMENT,
    session_id VARCHAR(32) NOT NULL,
    message_order INT NOT NULL DEFAULT 0,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    content_type ENUM('text', 'audio', 'mixed') DEFAULT 'text',
    audio_url VARCHAR(255) COMMENT 'URL to audio file if stored externally',
    audio_duration_ms INT COMMENT 'Audio duration in milliseconds',
    language_code VARCHAR(10),
    timestamp DATETIME(3) DEFAULT CURRENT_TIMESTAMP(3),
    processing_time_ms INT,
    tokens_used INT,
    confidence_score DECIMAL(3,2) COMMENT 'ASR confidence 0-1',
    PRIMARY KEY (id),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
    INDEX idx_session (session_id),
    INDEX idx_timestamp (timestamp),
    INDEX idx_session_order (session_id, message_order),
    FULLTEXT idx_content (content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Chat messages';

-- ============================================
-- Analytics Tables
-- ============================================

-- Daily analytics summary
CREATE TABLE daily_analytics (
    id BIGINT NOT NULL AUTO_INCREMENT,
    child_profile_id VARCHAR(32) NOT NULL,
    analytics_date DATE NOT NULL,
    
    -- Basic metrics
    total_sessions INT DEFAULT 0,
    total_minutes INT DEFAULT 0,
    total_interactions INT DEFAULT 0,
    
    -- Engagement metrics
    avg_session_duration_minutes DECIMAL(5,2),
    longest_session_minutes INT,
    most_active_hour TINYINT COMMENT 'Hour of day (0-23)',
    
    -- Content metrics
    unique_topics JSON COMMENT 'Array of topics discussed',
    top_keywords JSON COMMENT 'Most frequent keywords',
    questions_asked INT DEFAULT 0,
    stories_created INT DEFAULT 0,
    
    -- Learning metrics
    new_words_learned JSON COMMENT 'Array of new vocabulary',
    vocabulary_complexity_score DECIMAL(3,2),
    educational_content_percentage DECIMAL(5,2),
    learning_objectives_met JSON,
    
    -- Emotional metrics
    sentiment_summary JSON COMMENT 'Sentiment analysis results',
    avg_sentiment_score DECIMAL(3,2) COMMENT 'Average sentiment -1 to 1',
    emotional_expressions JSON COMMENT 'Count of different emotions',
    
    -- AI-generated insights
    ai_summary TEXT COMMENT 'AI-generated daily summary for parents',
    recommendations JSON COMMENT 'AI recommendations for tomorrow',
    concerns JSON COMMENT 'Any concerns flagged by AI',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id),
    UNIQUE KEY uk_child_date (child_profile_id, analytics_date),
    FOREIGN KEY (child_profile_id) REFERENCES child_profile(id) ON DELETE CASCADE,
    INDEX idx_date (analytics_date),
    INDEX idx_child_date_desc (child_profile_id, analytics_date DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Daily analytics summary';

-- Message categorization and analysis
CREATE TABLE interaction_categories (
    id BIGINT NOT NULL AUTO_INCREMENT,
    message_id BIGINT NOT NULL,
    category VARCHAR(50) COMMENT 'education, storytelling, game, conversation, etc',
    sub_category VARCHAR(50) COMMENT 'math, science, language, etc',
    educational_value TINYINT COMMENT 'Educational value score 0-10',
    creativity_score TINYINT COMMENT 'Creativity score 0-10',
    complexity_level TINYINT COMMENT 'Complexity level 1-5',
    keywords JSON COMMENT 'Extracted keywords',
    topics JSON COMMENT 'Identified topics',
    sentiment_score DECIMAL(3,2) COMMENT 'Sentiment -1 to 1',
    confidence DECIMAL(3,2) COMMENT 'Categorization confidence 0-1',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
    UNIQUE KEY uk_message (message_id),
    INDEX idx_category (category),
    INDEX idx_educational (educational_value)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Message categorization';

-- Learning milestones and achievements
CREATE TABLE learning_milestones (
    id BIGINT NOT NULL AUTO_INCREMENT,
    child_profile_id VARCHAR(32) NOT NULL,
    milestone_type VARCHAR(50) COMMENT 'vocabulary, math, reading, social, creative',
    milestone_name VARCHAR(100),
    milestone_description TEXT,
    milestone_level TINYINT COMMENT 'Level 1-10',
    achieved_at DATETIME,
    evidence JSON COMMENT 'Evidence/context of achievement',
    points_earned INT DEFAULT 0,
    PRIMARY KEY (id),
    FOREIGN KEY (child_profile_id) REFERENCES child_profile(id) ON DELETE CASCADE,
    INDEX idx_child (child_profile_id),
    INDEX idx_achieved (achieved_at),
    INDEX idx_type (milestone_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Learning achievements';

-- ============================================
-- Parental Controls
-- ============================================

-- Parent control settings
CREATE TABLE parental_settings (
    id BIGINT NOT NULL AUTO_INCREMENT,
    child_profile_id VARCHAR(32) NOT NULL,
    
    -- Time controls
    daily_time_limit_minutes INT DEFAULT 60,
    session_time_limit_minutes INT DEFAULT 30,
    allowed_hours_start TIME DEFAULT '07:00:00',
    allowed_hours_end TIME DEFAULT '21:00:00',
    weekend_extra_minutes INT DEFAULT 30,
    
    -- Content controls
    content_filter_level ENUM('low', 'medium', 'high', 'custom') DEFAULT 'medium',
    blocked_topics JSON COMMENT 'Array of blocked topics',
    allowed_topics JSON COMMENT 'Array of explicitly allowed topics',
    
    -- Privacy settings
    audio_recording_enabled BOOLEAN DEFAULT TRUE,
    data_retention_days INT DEFAULT 90,
    analytics_enabled BOOLEAN DEFAULT TRUE,
    
    -- Notifications
    notification_preferences JSON COMMENT 'Notification settings',
    alert_on_concerning_content BOOLEAN DEFAULT TRUE,
    daily_summary_enabled BOOLEAN DEFAULT TRUE,
    weekly_report_enabled BOOLEAN DEFAULT TRUE,
    
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_child (child_profile_id),
    FOREIGN KEY (child_profile_id) REFERENCES child_profile(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Parental control settings';

-- ============================================
-- Helper Function for UUID Generation
-- ============================================

-- Create a function to generate UUIDs (if needed)
DELIMITER //
CREATE FUNCTION IF NOT EXISTS generate_uuid() 
RETURNS VARCHAR(36)
DETERMINISTIC
BEGIN
    RETURN LOWER(CONCAT(
        HEX(RANDOM_BYTES(4)),
        '-', HEX(RANDOM_BYTES(2)),
        '-', HEX(RANDOM_BYTES(2)),
        '-', HEX(RANDOM_BYTES(2)),
        '-', HEX(RANDOM_BYTES(6))
    ));
END//
DELIMITER ;

-- ============================================
-- Views for Easy Querying
-- ============================================

-- Child activity overview
CREATE OR REPLACE VIEW v_child_activity AS
SELECT 
    cp.id as child_id,
    cp.child_name,
    cp.age,
    cp.parent_user_id,
    su.username as parent_username,
    COUNT(DISTINCT cs.id) as total_sessions,
    COUNT(DISTINCT DATE(cs.session_start)) as active_days,
    COUNT(cm.id) as total_messages,
    IFNULL(SUM(cs.duration_seconds) / 60, 0) as total_minutes,
    MAX(cs.session_start) as last_activity,
    ad.device_name,
    ad.is_online as device_online
FROM child_profile cp
LEFT JOIN sys_user su ON cp.parent_user_id = su.id
LEFT JOIN chat_sessions cs ON cp.id = cs.child_profile_id
LEFT JOIN chat_messages cm ON cs.id = cm.session_id
LEFT JOIN ai_device ad ON cp.device_id = ad.id
GROUP BY cp.id, cp.child_name, cp.age, cp.parent_user_id, su.username, ad.device_name, ad.is_online;

-- Daily summary view
CREATE OR REPLACE VIEW v_daily_summary AS
SELECT 
    da.*,
    cp.child_name,
    cp.age,
    cp.parent_user_id,
    su.username as parent_username,
    su.email as parent_email
FROM daily_analytics da
JOIN child_profile cp ON da.child_profile_id = cp.id
JOIN sys_user su ON cp.parent_user_id = su.id;

-- Recent conversations view
CREATE OR REPLACE VIEW v_recent_conversations AS
SELECT 
    cm.id,
    cm.session_id,
    cs.child_profile_id,
    cp.child_name,
    cm.role,
    cm.content,
    cm.timestamp,
    ic.category,
    ic.sentiment_score
FROM chat_messages cm
JOIN chat_sessions cs ON cm.session_id = cs.id
JOIN child_profile cp ON cs.child_profile_id = cp.id
LEFT JOIN interaction_categories ic ON cm.id = ic.message_id
ORDER BY cm.timestamp DESC;

-- ============================================
-- Stored Procedures
-- ============================================

DELIMITER //

-- Get child's daily summary
CREATE PROCEDURE sp_get_child_daily_summary(
    IN p_child_id VARCHAR(32),
    IN p_date DATE
)
BEGIN
    SELECT * FROM daily_analytics
    WHERE child_profile_id = p_child_id 
    AND analytics_date = p_date;
END //

-- Generate daily analytics
CREATE PROCEDURE sp_generate_daily_analytics(
    IN p_date DATE
)
BEGIN
    -- Insert or update daily analytics for all active children
    INSERT INTO daily_analytics (
        child_profile_id,
        analytics_date,
        total_sessions,
        total_minutes,
        total_interactions,
        avg_session_duration_minutes,
        questions_asked
    )
    SELECT 
        cs.child_profile_id,
        p_date,
        COUNT(DISTINCT cs.id) as total_sessions,
        IFNULL(SUM(cs.duration_seconds) / 60, 0) as total_minutes,
        COUNT(cm.id) as total_interactions,
        AVG(cs.duration_seconds / 60) as avg_session_duration,
        SUM(CASE WHEN cm.content LIKE '%?%' AND cm.role = 'user' THEN 1 ELSE 0 END) as questions
    FROM chat_sessions cs
    LEFT JOIN chat_messages cm ON cs.id = cm.session_id
    WHERE DATE(cs.session_start) = p_date
    GROUP BY cs.child_profile_id
    ON DUPLICATE KEY UPDATE
        total_sessions = VALUES(total_sessions),
        total_minutes = VALUES(total_minutes),
        total_interactions = VALUES(total_interactions),
        avg_session_duration_minutes = VALUES(avg_session_duration_minutes),
        questions_asked = VALUES(questions_asked),
        updated_at = NOW();
END //

-- Clean old data
CREATE PROCEDURE sp_clean_old_data()
BEGIN
    DECLARE v_retention_days INT DEFAULT 90;
    
    -- Delete old messages based on retention settings
    DELETE cm FROM chat_messages cm
    JOIN chat_sessions cs ON cm.session_id = cs.id
    JOIN child_profile cp ON cs.child_profile_id = cp.id
    JOIN parental_settings ps ON cp.id = ps.child_profile_id
    WHERE cm.timestamp < DATE_SUB(NOW(), INTERVAL ps.data_retention_days DAY);
    
    -- Delete orphaned sessions
    DELETE FROM chat_sessions 
    WHERE session_start < DATE_SUB(NOW(), INTERVAL 365 DAY)
    AND id NOT IN (SELECT DISTINCT session_id FROM chat_messages);
END //

DELIMITER ;

-- ============================================
-- Triggers
-- ============================================

DELIMITER //

-- Update session interaction count
CREATE TRIGGER tr_update_interaction_count
AFTER INSERT ON chat_messages
FOR EACH ROW
BEGIN
    UPDATE chat_sessions 
    SET interaction_count = interaction_count + 1
    WHERE id = NEW.session_id;
END //

-- Auto-close incomplete sessions
CREATE TRIGGER tr_close_session
BEFORE INSERT ON chat_sessions
FOR EACH ROW
BEGIN
    -- Close any open sessions for this child
    UPDATE chat_sessions 
    SET session_end = NOW(), is_complete = TRUE
    WHERE child_profile_id = NEW.child_profile_id
    AND is_complete = FALSE;
END //

DELIMITER ;

-- ============================================
-- Initial Data
-- ============================================

-- Create admin user (password: admin123 - CHANGE IMMEDIATELY!)
INSERT INTO sys_user (username, password, email, full_name, super_admin) 
VALUES (
    'admin', 
    '$2a$10$YKo8h2W8GlCmPlOj6JOAp.Y7eW1Z0YQVVqPcD8LXnqFR9mFvDpGWm', 
    'admin@xiaozhi.ai',
    'System Administrator',
    1
);

-- Create demo parent account (password: parent123)
INSERT INTO sys_user (username, password, email, full_name) 
VALUES (
    'demo_parent', 
    '$2a$10$Q8zA3xrNUK1cwmH6wGDJxuZH8FQ8pVnwVYvWZR9bYGyQbKwI9Tcbm', 
    'parent@demo.com',
    'Demo Parent'
);

-- Create demo device (using function for UUID)
INSERT INTO ai_device (id, mac_address, device_name, firmware_version)
VALUES (generate_uuid(), 'AA:BB:CC:DD:EE:FF', 'Demo AI Toy', '1.0.0');

-- Get the device ID for the child profile
SET @device_id = (SELECT id FROM ai_device WHERE mac_address = 'AA:BB:CC:DD:EE:FF');

-- Create demo child profile
INSERT INTO child_profile (
    id, 
    parent_user_id, 
    child_name, 
    birth_date, 
    gender, 
    device_id,
    interests
)
VALUES (
    generate_uuid(),
    2,  -- demo_parent id
    'Little Star',
    '2018-06-15',
    'female',
    @device_id,
    '["animals", "stories", "music", "science"]'
);

-- Get the child profile ID for parental settings
SET @child_id = (SELECT id FROM child_profile WHERE child_name = 'Little Star');

-- Create demo parental settings
INSERT INTO parental_settings (child_profile_id)
VALUES (@child_id);

-- ============================================
-- Verification Queries
-- ============================================

-- Check tables created
SELECT '✅ Database initialized successfully!' as Status;
SELECT COUNT(*) as Tables FROM information_schema.tables WHERE table_schema = 'railway';
SELECT 'Admin username: admin' as Info1, 'Default password: admin123 (CHANGE THIS!)' as Info2;
SELECT 'Demo parent: demo_parent / parent123' as Demo_Account;

-- Show created tables
SELECT TABLE_NAME, TABLE_COMMENT 
FROM information_schema.tables 
WHERE table_schema = 'railway' 
ORDER BY TABLE_NAME;