-- Migration script for creating music_playlist and story_playlist tables
-- These tables store playlists for each device (MAC address)

-- Create music_playlist table
CREATE TABLE IF NOT EXISTS music_playlist (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    device_id VARCHAR(32) NOT NULL COMMENT 'Device ID (references ai_device.id)',
    content_id CHAR(36) NOT NULL COMMENT 'Content ID (references content_items.id)',
    position INT NOT NULL COMMENT 'Position in playlist (0-based ordering)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update timestamp',
    INDEX idx_device_position (device_id, position),
    INDEX idx_device_content (device_id, content_id),
    UNIQUE KEY unique_device_position (device_id, position),
    CONSTRAINT fk_music_device FOREIGN KEY (device_id) REFERENCES ai_device(id) ON DELETE CASCADE,
    CONSTRAINT fk_music_content FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Music playlists for devices';

-- Create story_playlist table
CREATE TABLE IF NOT EXISTS story_playlist (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
    device_id VARCHAR(32) NOT NULL COMMENT 'Device ID (references ai_device.id)',
    content_id CHAR(36) NOT NULL COMMENT 'Content ID (references content_items.id)',
    position INT NOT NULL COMMENT 'Position in playlist (0-based ordering)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation timestamp',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update timestamp',
    INDEX idx_device_position (device_id, position),
    INDEX idx_device_content (device_id, content_id),
    UNIQUE KEY unique_device_position (device_id, position),
    CONSTRAINT fk_story_device FOREIGN KEY (device_id) REFERENCES ai_device(id) ON DELETE CASCADE,
    CONSTRAINT fk_story_content FOREIGN KEY (content_id) REFERENCES content_items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Story playlists for devices';
