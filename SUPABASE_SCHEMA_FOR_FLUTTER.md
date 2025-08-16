# Supabase Database Schema for Flutter Parental App

## Overview
This document outlines the Supabase database schema needed for the Flutter parental app, which integrates with the existing Railway MySQL Xiaozhi backend.

## Database Tables

### 1. Parent Users (Extended from Supabase Auth)
```sql
-- Table: parent_profiles
-- Purpose: Store additional parent information beyond basic auth
CREATE TABLE parent_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(255),
    phone_number VARCHAR(20),
    preferred_language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_preferences JSONB DEFAULT '{"email": true, "push": true, "daily_summary": true}',
    onboarding_completed BOOLEAN DEFAULT false,
    terms_accepted_at TIMESTAMP WITH TIME ZONE,
    privacy_policy_accepted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS (Row Level Security)
ALTER TABLE parent_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only access their own profile
CREATE POLICY "Users can view own profile" ON parent_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON parent_profiles
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON parent_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);
```

### 2. Activation Codes
```sql
-- Table: activation_codes
-- Purpose: Store 6-digit codes for toy activation
CREATE TABLE activation_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activation_code VARCHAR(6) NOT NULL UNIQUE,
    toy_serial_number VARCHAR(100) NOT NULL UNIQUE,
    toy_model VARCHAR(50) NOT NULL,
    is_used BOOLEAN DEFAULT false,
    used_by_user_id UUID REFERENCES auth.users(id),
    used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    batch_id VARCHAR(50), -- For tracking code generation batches
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure code is exactly 6 digits
    CONSTRAINT activation_code_format CHECK (activation_code ~ '^[0-9]{6}$')
);

-- Enable RLS
ALTER TABLE activation_codes ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see codes they've used
CREATE POLICY "Users can view own activated codes" ON activation_codes
    FOR SELECT USING (used_by_user_id = auth.uid());

-- Index for fast code lookup
CREATE INDEX idx_activation_codes_code ON activation_codes(activation_code);
CREATE INDEX idx_activation_codes_serial ON activation_codes(toy_serial_number);
```

### 3. Device Activations (Bridge Table)
```sql
-- Table: device_activations
-- Purpose: Link Supabase parents to Railway MySQL devices
CREATE TABLE device_activations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    activation_code_id UUID NOT NULL REFERENCES activation_codes(id),
    toy_serial_number VARCHAR(100) NOT NULL,
    railway_device_mac VARCHAR(50) NOT NULL, -- MAC address from Railway DB
    railway_device_id VARCHAR(32), -- Device ID from Railway ai_device table
    child_name VARCHAR(100),
    child_age INTEGER CHECK (child_age >= 3 AND child_age <= 12),
    child_interests JSONB DEFAULT '[]',
    activation_status VARCHAR(20) DEFAULT 'pending' CHECK (activation_status IN ('pending', 'active', 'inactive', 'error')),
    last_sync_at TIMESTAMP WITH TIME ZONE,
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE device_activations ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own activations" ON device_activations
    FOR SELECT USING (parent_user_id = auth.uid());

CREATE POLICY "Users can update own activations" ON device_activations
    FOR UPDATE USING (parent_user_id = auth.uid());

CREATE POLICY "Users can insert own activations" ON device_activations
    FOR INSERT WITH CHECK (parent_user_id = auth.uid());

-- Indexes
CREATE INDEX idx_device_activations_parent ON device_activations(parent_user_id);
CREATE INDEX idx_device_activations_mac ON device_activations(railway_device_mac);
CREATE UNIQUE INDEX idx_device_activations_unique_device ON device_activations(railway_device_mac) WHERE activation_status = 'active';
```

### 4. App Settings & Preferences
```sql
-- Table: app_settings
-- Purpose: Store parent app preferences and settings
CREATE TABLE app_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device_activation_id UUID NOT NULL REFERENCES device_activations(id) ON DELETE CASCADE,
    
    -- Analytics preferences
    analytics_enabled BOOLEAN DEFAULT true,
    detailed_analytics BOOLEAN DEFAULT true,
    audio_storage_enabled BOOLEAN DEFAULT true,
    data_retention_days INTEGER DEFAULT 90 CHECK (data_retention_days >= 30),
    
    -- Notification settings
    daily_summary_enabled BOOLEAN DEFAULT true,
    daily_summary_time TIME DEFAULT '19:00:00',
    weekly_report_enabled BOOLEAN DEFAULT true,
    achievement_notifications BOOLEAN DEFAULT true,
    concern_alerts BOOLEAN DEFAULT true,
    
    -- Content filters
    content_filters JSONB DEFAULT '{"inappropriate_content": true, "violence": true, "adult_themes": true}',
    educational_focus JSONB DEFAULT '["creativity", "learning", "social_skills"]',
    
    -- Privacy settings
    data_sharing_analytics BOOLEAN DEFAULT false,
    data_sharing_research BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one setting per parent-device combination
    UNIQUE(parent_user_id, device_activation_id)
);

-- Enable RLS
ALTER TABLE app_settings ENABLE ROW LEVEL SECURITY;

-- RLS Policy
CREATE POLICY "Users can manage own app settings" ON app_settings
    FOR ALL USING (parent_user_id = auth.uid());
```

### 5. Sync Status (For Railway Integration)
```sql
-- Table: railway_sync_status
-- Purpose: Track synchronization with Railway MySQL database
CREATE TABLE railway_sync_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_activation_id UUID NOT NULL REFERENCES device_activations(id) ON DELETE CASCADE,
    
    -- Sync tracking
    last_chat_sync_at TIMESTAMP WITH TIME ZONE,
    last_analytics_sync_at TIMESTAMP WITH TIME ZONE,
    last_successful_sync_at TIMESTAMP WITH TIME ZONE,
    sync_errors JSONB DEFAULT '[]',
    
    -- Data freshness indicators
    total_conversations_synced INTEGER DEFAULT 0,
    last_conversation_timestamp TIMESTAMP WITH TIME ZONE,
    analytics_last_updated TIMESTAMP WITH TIME ZONE,
    
    -- Connection status
    railway_api_status VARCHAR(20) DEFAULT 'unknown' CHECK (railway_api_status IN ('connected', 'disconnected', 'error', 'unknown')),
    device_online_status BOOLEAN DEFAULT false,
    device_last_seen TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(device_activation_id)
);

-- Enable RLS
ALTER TABLE railway_sync_status ENABLE ROW LEVEL SECURITY;

-- RLS Policy
CREATE POLICY "Users can view own sync status" ON railway_sync_status
    FOR SELECT USING (
        device_activation_id IN (
            SELECT id FROM device_activations WHERE parent_user_id = auth.uid()
        )
    );
```

## Database Functions

### 1. Activation Code Validation Function
```sql
-- Function: validate_and_use_activation_code
-- Purpose: Atomically validate and mark activation code as used
CREATE OR REPLACE FUNCTION validate_and_use_activation_code(
    p_activation_code VARCHAR(6),
    p_user_id UUID,
    p_child_name VARCHAR(100),
    p_child_age INTEGER,
    p_railway_device_mac VARCHAR(50)
)
RETURNS TABLE(
    success BOOLEAN,
    message TEXT,
    activation_id UUID,
    toy_serial_number VARCHAR(100)
) 
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_code_record activation_codes%ROWTYPE;
    v_activation_id UUID;
BEGIN
    -- Check if code exists and is not used
    SELECT * INTO v_code_record
    FROM activation_codes
    WHERE activation_code = p_activation_code
    AND is_used = false
    AND (expires_at IS NULL OR expires_at > NOW());
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT false, 'Invalid or expired activation code', NULL::UUID, NULL::VARCHAR(100);
        RETURN;
    END IF;
    
    -- Check if device is already activated
    IF EXISTS (SELECT 1 FROM device_activations WHERE railway_device_mac = p_railway_device_mac AND activation_status = 'active') THEN
        RETURN QUERY SELECT false, 'Device is already activated', NULL::UUID, NULL::VARCHAR(100);
        RETURN;
    END IF;
    
    -- Mark code as used
    UPDATE activation_codes
    SET is_used = true,
        used_by_user_id = p_user_id,
        used_at = NOW()
    WHERE id = v_code_record.id;
    
    -- Create device activation record
    INSERT INTO device_activations (
        parent_user_id,
        activation_code_id,
        toy_serial_number,
        railway_device_mac,
        child_name,
        child_age,
        activation_status
    ) VALUES (
        p_user_id,
        v_code_record.id,
        v_code_record.toy_serial_number,
        p_railway_device_mac,
        p_child_name,
        p_child_age,
        'pending'
    ) RETURNING id INTO v_activation_id;
    
    -- Create default app settings
    INSERT INTO app_settings (parent_user_id, device_activation_id)
    VALUES (p_user_id, v_activation_id);
    
    -- Create sync status record
    INSERT INTO railway_sync_status (device_activation_id)
    VALUES (v_activation_id);
    
    RETURN QUERY SELECT true, 'Activation successful', v_activation_id, v_code_record.toy_serial_number;
END;
$$;
```

### 2. Generate Activation Codes Function
```sql
-- Function: generate_activation_codes
-- Purpose: Generate batch of activation codes for toy manufacturing
CREATE OR REPLACE FUNCTION generate_activation_codes(
    p_batch_size INTEGER,
    p_toy_model VARCHAR(50),
    p_batch_id VARCHAR(50),
    p_expires_at TIMESTAMP WITH TIME ZONE DEFAULT NULL
)
RETURNS TABLE(
    activation_code VARCHAR(6),
    toy_serial_number VARCHAR(100)
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    i INTEGER;
    v_code VARCHAR(6);
    v_serial VARCHAR(100);
    v_unique_found BOOLEAN;
BEGIN
    FOR i IN 1..p_batch_size LOOP
        v_unique_found := false;
        
        -- Generate unique 6-digit code
        WHILE NOT v_unique_found LOOP
            v_code := LPAD((RANDOM() * 999999)::INTEGER::TEXT, 6, '0');
            
            -- Check if code already exists
            IF NOT EXISTS (SELECT 1 FROM activation_codes WHERE activation_code = v_code) THEN
                v_unique_found := true;
            END IF;
        END LOOP;
        
        -- Generate serial number
        v_serial := p_toy_model || '-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(i::TEXT, 6, '0');
        
        -- Insert activation code
        INSERT INTO activation_codes (
            activation_code,
            toy_serial_number,
            toy_model,
            batch_id,
            expires_at
        ) VALUES (
            v_code,
            v_serial,
            p_toy_model,
            p_batch_id,
            p_expires_at
        );
        
        RETURN QUERY SELECT v_code, v_serial;
    END LOOP;
END;
$$;
```

## Views for Flutter App

### 1. Parent Dashboard View
```sql
-- View: parent_dashboard_summary
-- Purpose: Provide dashboard data for Flutter app
CREATE VIEW parent_dashboard_summary AS
SELECT 
    da.id as activation_id,
    da.child_name,
    da.child_age,
    da.toy_serial_number,
    da.activation_status,
    da.activated_at,
    rss.device_online_status,
    rss.device_last_seen,
    rss.total_conversations_synced,
    rss.last_conversation_timestamp,
    rss.railway_api_status,
    ac.toy_model,
    pp.preferred_language,
    pp.timezone,
    as_table.daily_summary_enabled,
    as_table.analytics_enabled
FROM device_activations da
JOIN activation_codes ac ON da.activation_code_id = ac.id
JOIN parent_profiles pp ON da.parent_user_id = pp.user_id
LEFT JOIN railway_sync_status rss ON da.id = rss.device_activation_id
LEFT JOIN app_settings as_table ON da.id = as_table.device_activation_id
WHERE da.parent_user_id = auth.uid()
AND da.activation_status = 'active';
```

## Flutter Integration Guidelines

### 1. Authentication Flow
```dart
// Your Flutter app should implement this flow:
// 1. Supabase Auth sign-in (Google/Apple)
// 2. Check if parent_profile exists, create if not
// 3. Check for existing device activations
// 4. If no activations, show activation code input
// 5. After activation, sync with Railway backend
```

### 2. API Endpoints Needed
Your existing Java API should implement these endpoints for Flutter:

```yaml
# Authentication
POST /api/mobile/auth/verify-token
POST /api/mobile/auth/link-supabase-user

# Activation
POST /api/mobile/activate-device
GET /api/mobile/activation-status/{activationId}

# Analytics (consumed by Flutter)
GET /api/mobile/dashboard-summary/{activationId}
GET /api/mobile/analytics/daily/{activationId}
GET /api/mobile/analytics/weekly/{activationId}
GET /api/mobile/conversations/{activationId}

# Real-time
WS /api/mobile/realtime/{activationId}
```

### 3. Data Sync Strategy
```dart
// Flutter app should:
// 1. Store critical data locally (SQLite/Hive)
// 2. Sync periodically with Railway backend
// 3. Handle offline scenarios gracefully
// 4. Use WebSocket for real-time updates
```

## Security Considerations

### 1. Row Level Security (RLS)
- All tables have RLS enabled
- Parents can only access their own data
- Activation codes are protected

### 2. API Security
- JWT tokens from Supabase validated on Railway backend
- Rate limiting on activation endpoints
- Encryption for sensitive data

### 3. Privacy Compliance
- COPPA compliance for children's data
- GDPR compliance for EU users
- Clear consent flows in Flutter app

## Next Steps for Implementation

1. **Create these Supabase tables** in your Flutter project's Supabase instance
2. **Extend your Java API** with mobile endpoints
3. **Implement bridge service** to sync Supabase ↔ Railway data
4. **Add WebSocket support** for real-time updates
5. **Create analytics pipeline** that works with both systems

This schema provides the foundation for your Flutter app to authenticate parents and link them to their children's toy data stored in Railway MySQL.