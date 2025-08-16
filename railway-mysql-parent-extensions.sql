-- Railway MySQL Extensions for Parental App Integration
-- This extends the existing Xiaozhi database to support parent-child analytics

-- ===========================================
-- 1. PARENT-CHILD MAPPING TABLES
-- ===========================================

-- Link Supabase parents to Railway devices
CREATE TABLE parent_child_mapping (
    id VARCHAR(32) PRIMARY KEY,
    supabase_user_id VARCHAR(36) NOT NULL, -- UUID from Supabase auth.users
    supabase_activation_id VARCHAR(36) NOT NULL, -- UUID from Supabase device_activations
    device_mac_address VARCHAR(50) NOT NULL,
    child_name VARCHAR(100) NOT NULL,
    child_age INT,
    child_interests JSON,
    relationship_type VARCHAR(20) DEFAULT 'parent', -- 'parent', 'guardian'
    activation_status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'suspended'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key to existing device table
    FOREIGN KEY (device_mac_address) REFERENCES ai_device(mac_address),
    
    -- Indexes for fast lookups
    INDEX idx_supabase_user (supabase_user_id),
    INDEX idx_device_mac (device_mac_address),
    INDEX idx_activation_id (supabase_activation_id),
    
    -- Ensure one active mapping per device
    UNIQUE KEY uk_device_active (device_mac_address, activation_status)
);

-- Child profile extended information
CREATE TABLE child_profile_extended (
    id VARCHAR(32) PRIMARY KEY,
    parent_child_mapping_id VARCHAR(32) NOT NULL,
    learning_level VARCHAR(20), -- 'beginner', 'intermediate', 'advanced'
    preferred_topics JSON, -- ['animals', 'numbers', 'stories', 'music']
    learning_goals JSON, -- Parent-set goals
    language_preference VARCHAR(10) DEFAULT 'en',
    content_restrictions JSON, -- Age-appropriate content filters
    daily_time_limit_minutes INT DEFAULT 60,
    bedtime_cutoff TIME DEFAULT '20:00:00',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_child_mapping_id) REFERENCES parent_child_mapping(id) ON DELETE CASCADE,
    INDEX idx_mapping_id (parent_child_mapping_id)
);

-- ===========================================
-- 2. ANALYTICS SUMMARY TABLES
-- ===========================================

-- Pre-computed daily analytics for mobile app consumption
CREATE TABLE analytics_summary_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_child_mapping_id VARCHAR(32) NOT NULL,
    summary_date DATE NOT NULL,
    
    -- Engagement metrics
    total_conversations INT DEFAULT 0,
    total_duration_minutes INT DEFAULT 0,
    average_session_duration DECIMAL(5,2) DEFAULT 0,
    longest_session_minutes INT DEFAULT 0,
    
    -- Learning metrics
    topics_discussed JSON, -- ['animals', 'counting', 'colors']
    new_words_count INT DEFAULT 0,
    questions_asked INT DEFAULT 0,
    creative_responses INT DEFAULT 0,
    
    -- Emotional metrics
    overall_sentiment DECIMAL(3,2) DEFAULT 0, -- -1 to 1
    mood_indicators JSON, -- ['happy', 'curious', 'frustrated']
    emotional_expressions JSON,
    
    -- Behavioral metrics
    politeness_score DECIMAL(3,2) DEFAULT 0,
    attention_span_minutes DECIMAL(5,2) DEFAULT 0,
    engagement_level VARCHAR(20), -- 'low', 'medium', 'high'
    
    -- AI-generated insights
    ai_summary TEXT,
    key_highlights JSON,
    parent_recommendations JSON,
    concerns_flagged JSON,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_child_mapping_id) REFERENCES parent_child_mapping(id) ON DELETE CASCADE,
    UNIQUE KEY uk_mapping_date (parent_child_mapping_id, summary_date),
    INDEX idx_summary_date (summary_date),
    INDEX idx_mapping_date (parent_child_mapping_id, summary_date DESC)
);

-- Weekly analytics summary
CREATE TABLE analytics_summary_weekly (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_child_mapping_id VARCHAR(32) NOT NULL,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    
    -- Aggregated metrics
    total_conversations INT DEFAULT 0,
    total_duration_minutes INT DEFAULT 0,
    average_daily_engagement DECIMAL(5,2) DEFAULT 0,
    consistency_score DECIMAL(3,2) DEFAULT 0, -- How consistent daily usage is
    
    -- Learning progress
    vocabulary_growth_rate DECIMAL(5,2) DEFAULT 0,
    topic_diversity_score DECIMAL(3,2) DEFAULT 0,
    learning_milestones_achieved JSON,
    skill_improvements JSON,
    
    -- Trends
    engagement_trend VARCHAR(20), -- 'increasing', 'decreasing', 'stable'
    mood_trend VARCHAR(20),
    preferred_activity_times JSON, -- ['morning', 'afternoon', 'evening']
    
    -- Parent insights
    weekly_summary TEXT,
    achievements JSON,
    areas_for_improvement JSON,
    next_week_suggestions JSON,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_child_mapping_id) REFERENCES parent_child_mapping(id) ON DELETE CASCADE,
    UNIQUE KEY uk_mapping_week (parent_child_mapping_id, week_start_date),
    INDEX idx_week_start (week_start_date DESC)
);

-- ===========================================
-- 3. INTERACTION CATEGORIZATION
-- ===========================================

-- Categorize conversations for better analytics
CREATE TABLE interaction_categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    chat_history_id BIGINT NOT NULL,
    parent_child_mapping_id VARCHAR(32) NOT NULL,
    
    -- Category classification
    primary_category VARCHAR(50), -- 'education', 'entertainment', 'social', 'creative'
    sub_category VARCHAR(50), -- 'math', 'reading', 'storytelling', 'game'
    educational_value DECIMAL(3,2) DEFAULT 0, -- 0 to 1 score
    
    -- Content analysis
    keywords_extracted JSON,
    sentiment_score DECIMAL(3,2) DEFAULT 0, -- -1 to 1
    complexity_level VARCHAR(20), -- 'simple', 'medium', 'complex'
    child_initiated BOOLEAN DEFAULT false, -- Did child start the conversation?
    
    -- Learning indicators
    vocabulary_used JSON, -- New/advanced words used
    concepts_discussed JSON, -- ['counting', 'colors', 'animals']
    problem_solving_involved BOOLEAN DEFAULT false,
    creativity_demonstrated BOOLEAN DEFAULT false,
    
    -- Quality metrics
    engagement_quality VARCHAR(20), -- 'low', 'medium', 'high'
    response_appropriateness DECIMAL(3,2) DEFAULT 1, -- How appropriate were responses
    educational_alignment DECIMAL(3,2) DEFAULT 0, -- Alignment with learning goals
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (chat_history_id) REFERENCES ai_agent_chat_history(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_child_mapping_id) REFERENCES parent_child_mapping(id) ON DELETE CASCADE,
    INDEX idx_chat_history (chat_history_id),
    INDEX idx_parent_mapping (parent_child_mapping_id),
    INDEX idx_category (primary_category, sub_category),
    INDEX idx_created_date (created_at DESC)
);

-- ===========================================
-- 4. MILESTONES AND ACHIEVEMENTS
-- ===========================================

-- Track child's learning milestones
CREATE TABLE child_milestones (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_child_mapping_id VARCHAR(32) NOT NULL,
    
    -- Milestone details
    milestone_type VARCHAR(50), -- 'vocabulary', 'social', 'cognitive', 'creative'
    milestone_name VARCHAR(100), -- 'First 100 words', 'Polite conversation', etc.
    milestone_description TEXT,
    
    -- Achievement tracking
    target_value DECIMAL(10,2), -- Target number (e.g., 100 words)
    current_value DECIMAL(10,2), -- Current progress
    unit_of_measure VARCHAR(20), -- 'words', 'minutes', 'conversations'
    
    -- Status and timing
    achievement_status VARCHAR(20) DEFAULT 'in_progress', -- 'not_started', 'in_progress', 'achieved'
    achieved_at DATETIME,
    target_date DATE,
    
    -- Context
    age_group VARCHAR(20), -- '3-4', '4-5', '5-6', etc.
    difficulty_level VARCHAR(20), -- 'easy', 'medium', 'hard'
    related_interactions JSON, -- IDs of conversations that contributed
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_child_mapping_id) REFERENCES parent_child_mapping(id) ON DELETE CASCADE,
    INDEX idx_parent_mapping_milestones (parent_child_mapping_id),
    INDEX idx_milestone_type (milestone_type),
    INDEX idx_achievement_status (achievement_status),
    INDEX idx_achieved_date (achieved_at DESC)
);

-- ===========================================
-- 5. PARENTAL SETTINGS AND PREFERENCES
-- ===========================================

-- Store parent preferences synced from Supabase
CREATE TABLE parental_settings_sync (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_child_mapping_id VARCHAR(32) NOT NULL,
    
    -- Data preferences (synced from Supabase)
    analytics_enabled BOOLEAN DEFAULT true,
    detailed_analytics BOOLEAN DEFAULT true,
    audio_storage_enabled BOOLEAN DEFAULT true,
    data_retention_days INT DEFAULT 90,
    
    -- Content preferences
    content_filters JSON, -- Synced from Supabase app_settings
    educational_focus JSON, -- ['creativity', 'learning', 'social_skills']
    time_restrictions JSON, -- Daily time limits, bedtime cutoffs
    
    -- Notification preferences (for backend processing)
    daily_summary_enabled BOOLEAN DEFAULT true,
    weekly_report_enabled BOOLEAN DEFAULT true,
    achievement_notifications BOOLEAN DEFAULT true,
    concern_alerts BOOLEAN DEFAULT true,
    
    -- Sync tracking
    last_synced_from_supabase DATETIME,
    supabase_settings_version INT DEFAULT 1,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_child_mapping_id) REFERENCES parent_child_mapping(id) ON DELETE CASCADE,
    UNIQUE KEY uk_mapping_settings (parent_child_mapping_id),
    INDEX idx_last_synced (last_synced_from_supabase)
);

-- ===========================================
-- 6. NOTIFICATION QUEUE FOR MOBILE APP
-- ===========================================

-- Queue notifications to be sent to mobile app
CREATE TABLE mobile_notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_child_mapping_id VARCHAR(32) NOT NULL,
    supabase_user_id VARCHAR(36) NOT NULL,
    
    -- Notification details
    notification_type VARCHAR(50), -- 'daily_summary', 'achievement', 'concern', 'milestone'
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    data_payload JSON, -- Additional data for the mobile app
    
    -- Delivery tracking
    delivery_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
    scheduled_for DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent_at DATETIME,
    delivered_at DATETIME,
    
    -- Mobile app targeting
    platform VARCHAR(20), -- 'android', 'ios', 'both'
    priority VARCHAR(10) DEFAULT 'normal', -- 'low', 'normal', 'high'
    push_token VARCHAR(500), -- FCM/APNS token
    
    -- Error tracking
    error_message TEXT,
    retry_count INT DEFAULT 0,
    max_retries INT DEFAULT 3,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_child_mapping_id) REFERENCES parent_child_mapping(id) ON DELETE CASCADE,
    INDEX idx_parent_mapping_notifications (parent_child_mapping_id),
    INDEX idx_supabase_user (supabase_user_id),
    INDEX idx_delivery_status (delivery_status),
    INDEX idx_scheduled_for (scheduled_for),
    INDEX idx_notification_type (notification_type)
);

-- ===========================================
-- 7. MOBILE APP ANALYTICS CACHE
-- ===========================================

-- Cache frequently requested data for mobile app performance
CREATE TABLE mobile_analytics_cache (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    parent_child_mapping_id VARCHAR(32) NOT NULL,
    cache_key VARCHAR(100) NOT NULL, -- 'dashboard_summary', 'weekly_stats', etc.
    cache_period VARCHAR(20), -- 'today', 'this_week', 'this_month'
    
    -- Cached data
    data_json JSON NOT NULL,
    
    -- Cache management
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_child_mapping_id) REFERENCES parent_child_mapping(id) ON DELETE CASCADE,
    UNIQUE KEY uk_cache_key (parent_child_mapping_id, cache_key, cache_period),
    INDEX idx_expires_at (expires_at),
    INDEX idx_cache_key (cache_key)
);

-- ===========================================
-- 8. STORED PROCEDURES FOR MOBILE API
-- ===========================================

DELIMITER //

-- Get dashboard summary for mobile app
CREATE PROCEDURE GetMobileDashboardSummary(
    IN p_supabase_user_id VARCHAR(36),
    IN p_date DATE
)
BEGIN
    SELECT 
        pcm.id as mapping_id,
        pcm.child_name,
        pcm.child_age,
        pcm.device_mac_address,
        
        -- Today's stats
        COALESCE(asd.total_conversations, 0) as today_conversations,
        COALESCE(asd.total_duration_minutes, 0) as today_duration,
        COALESCE(asd.overall_sentiment, 0) as today_mood,
        asd.engagement_level,
        
        -- Device status
        ad.is_online,
        ad.last_seen,
        
        -- Recent achievement
        (SELECT milestone_name 
         FROM child_milestones 
         WHERE parent_child_mapping_id = pcm.id 
         AND achievement_status = 'achieved'
         AND achieved_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
         ORDER BY achieved_at DESC 
         LIMIT 1) as recent_achievement,
         
        -- Concerns
        CASE 
            WHEN asd.concerns_flagged IS NOT NULL AND JSON_LENGTH(asd.concerns_flagged) > 0 
            THEN true 
            ELSE false 
        END as has_concerns
        
    FROM parent_child_mapping pcm
    LEFT JOIN analytics_summary_daily asd ON pcm.id = asd.parent_child_mapping_id AND asd.summary_date = p_date
    LEFT JOIN ai_device ad ON pcm.device_mac_address = ad.mac_address
    WHERE pcm.supabase_user_id = p_supabase_user_id
    AND pcm.activation_status = 'active';
END //

-- Get conversation history for mobile app
CREATE PROCEDURE GetMobileConversationHistory(
    IN p_supabase_user_id VARCHAR(36),
    IN p_start_date DATE,
    IN p_end_date DATE,
    IN p_limit INT
)
BEGIN
    SELECT 
        ch.id,
        ch.session_id,
        ch.chat_type, -- 1=child, 2=ai
        ch.content,
        ch.created_at,
        
        -- Categorization
        ic.primary_category,
        ic.sub_category,
        ic.sentiment_score,
        ic.educational_value,
        
        -- Child info
        pcm.child_name
        
    FROM ai_agent_chat_history ch
    JOIN parent_child_mapping pcm ON ch.mac_address = pcm.device_mac_address
    LEFT JOIN interaction_categories ic ON ch.id = ic.chat_history_id
    
    WHERE pcm.supabase_user_id = p_supabase_user_id
    AND pcm.activation_status = 'active'
    AND DATE(ch.created_at) BETWEEN p_start_date AND p_end_date
    
    ORDER BY ch.created_at DESC
    LIMIT p_limit;
END //

-- Get analytics summary for mobile app
CREATE PROCEDURE GetMobileAnalyticsSummary(
    IN p_supabase_user_id VARCHAR(36),
    IN p_period VARCHAR(20), -- 'daily', 'weekly', 'monthly'
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    IF p_period = 'daily' THEN
        SELECT 
            summary_date as date,
            total_conversations,
            total_duration_minutes,
            overall_sentiment,
            topics_discussed,
            new_words_count,
            engagement_level,
            ai_summary,
            key_highlights,
            parent_recommendations
        FROM analytics_summary_daily asd
        JOIN parent_child_mapping pcm ON asd.parent_child_mapping_id = pcm.id
        WHERE pcm.supabase_user_id = p_supabase_user_id
        AND pcm.activation_status = 'active'
        AND asd.summary_date BETWEEN p_start_date AND p_end_date
        ORDER BY asd.summary_date DESC;
        
    ELSEIF p_period = 'weekly' THEN
        SELECT 
            week_start_date,
            week_end_date,
            total_conversations,
            total_duration_minutes,
            average_daily_engagement,
            learning_milestones_achieved,
            engagement_trend,
            weekly_summary,
            achievements,
            next_week_suggestions
        FROM analytics_summary_weekly asw
        JOIN parent_child_mapping pcm ON asw.parent_child_mapping_id = pcm.id
        WHERE pcm.supabase_user_id = p_supabase_user_id
        AND pcm.activation_status = 'active'
        AND asw.week_start_date BETWEEN p_start_date AND p_end_date
        ORDER BY asw.week_start_date DESC;
    END IF;
END //

DELIMITER ;

-- ===========================================
-- 9. INDEXES FOR MOBILE APP PERFORMANCE
-- ===========================================

-- Optimize common mobile app queries
CREATE INDEX idx_chat_history_mac_date ON ai_agent_chat_history(mac_address, created_at DESC);
CREATE INDEX idx_analytics_mapping_date ON analytics_summary_daily(parent_child_mapping_id, summary_date DESC);
CREATE INDEX idx_milestones_mapping_status ON child_milestones(parent_child_mapping_id, achievement_status, achieved_at DESC);
CREATE INDEX idx_notifications_user_status ON mobile_notifications(supabase_user_id, delivery_status, scheduled_for);

-- ===========================================
-- 10. SAMPLE DATA GENERATION
-- ===========================================

-- Function to generate sample activation for testing
DELIMITER //

CREATE PROCEDURE CreateSampleParentChildMapping(
    IN p_supabase_user_id VARCHAR(36),
    IN p_device_mac VARCHAR(50),
    IN p_child_name VARCHAR(100),
    IN p_child_age INT
)
BEGIN
    DECLARE v_mapping_id VARCHAR(32);
    
    -- Generate mapping ID
    SET v_mapping_id = CONCAT('pcm_', SUBSTRING(MD5(RAND()), 1, 28));
    
    -- Insert parent-child mapping
    INSERT INTO parent_child_mapping (
        id,
        supabase_user_id,
        supabase_activation_id,
        device_mac_address,
        child_name,
        child_age,
        child_interests,
        activation_status
    ) VALUES (
        v_mapping_id,
        p_supabase_user_id,
        UUID(),
        p_device_mac,
        p_child_name,
        p_child_age,
        JSON_ARRAY('animals', 'counting', 'stories'),
        'active'
    );
    
    -- Create child profile
    INSERT INTO child_profile_extended (
        id,
        parent_child_mapping_id,
        learning_level,
        preferred_topics,
        language_preference
    ) VALUES (
        CONCAT('cp_', SUBSTRING(MD5(RAND()), 1, 28)),
        v_mapping_id,
        'beginner',
        JSON_ARRAY('animals', 'numbers', 'colors'),
        'en'
    );
    
    -- Create default settings
    INSERT INTO parental_settings_sync (
        parent_child_mapping_id,
        analytics_enabled,
        audio_storage_enabled
    ) VALUES (
        v_mapping_id,
        true,
        true
    );
    
    SELECT v_mapping_id as mapping_id, 'Sample parent-child mapping created successfully' as message;
END //

DELIMITER ;

-- Add triggers for automatic analytics processing
DELIMITER //

-- Trigger to update analytics when new chat is added
CREATE TRIGGER tr_chat_history_analytics AFTER INSERT ON ai_agent_chat_history
FOR EACH ROW
BEGIN
    -- Check if this device has a parent mapping
    IF EXISTS (SELECT 1 FROM parent_child_mapping WHERE device_mac_address = NEW.mac_address AND activation_status = 'active') THEN
        -- Insert into a processing queue or call analytics processing
        INSERT IGNORE INTO mobile_analytics_cache (
            parent_child_mapping_id,
            cache_key,
            cache_period,
            data_json,
            expires_at
        ) 
        SELECT 
            pcm.id,
            'needs_processing',
            'realtime',
            JSON_OBJECT('chat_id', NEW.id, 'timestamp', NEW.created_at),
            DATE_ADD(NOW(), INTERVAL 1 HOUR)
        FROM parent_child_mapping pcm 
        WHERE pcm.device_mac_address = NEW.mac_address 
        AND pcm.activation_status = 'active';
    END IF;
END //

DELIMITER ;

-- Views for mobile API consumption
CREATE VIEW mobile_child_summary AS
SELECT 
    pcm.id as mapping_id,
    pcm.supabase_user_id,
    pcm.child_name,
    pcm.child_age,
    pcm.device_mac_address,
    pcm.activation_status,
    pcm.created_at as activation_date,
    
    -- Device status
    ad.is_online as device_online,
    ad.last_seen as device_last_seen,
    
    -- Today's activity
    COALESCE(asd_today.total_conversations, 0) as today_conversations,
    COALESCE(asd_today.total_duration_minutes, 0) as today_minutes,
    asd_today.overall_sentiment as today_mood,
    
    -- This week's activity
    COALESCE(
        (SELECT SUM(total_conversations) 
         FROM analytics_summary_daily 
         WHERE parent_child_mapping_id = pcm.id 
         AND summary_date >= DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY)), 
        0
    ) as week_conversations,
    
    -- Recent achievement
    (SELECT milestone_name 
     FROM child_milestones 
     WHERE parent_child_mapping_id = pcm.id 
     AND achievement_status = 'achieved'
     ORDER BY achieved_at DESC 
     LIMIT 1) as latest_achievement
     
FROM parent_child_mapping pcm
LEFT JOIN ai_device ad ON pcm.device_mac_address = ad.mac_address
LEFT JOIN analytics_summary_daily asd_today ON pcm.id = asd_today.parent_child_mapping_id 
    AND asd_today.summary_date = CURDATE()
WHERE pcm.activation_status = 'active';

-- Grant permissions (adjust as needed for your user)
-- GRANT SELECT, INSERT, UPDATE ON cheeko_database.parent_child_mapping TO 'your_api_user'@'%';
-- GRANT SELECT, INSERT, UPDATE ON cheeko_database.analytics_summary_daily TO 'your_api_user'@'%';
-- GRANT EXECUTE ON PROCEDURE cheeko_database.GetMobileDashboardSummary TO 'your_api_user'@'%';