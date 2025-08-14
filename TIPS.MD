
  CREATE TABLE child_profile (
      id VARCHAR(32) NOT NULL,
      parent_user_id BIGINT NOT NULL,
      child_name VARCHAR(100) NOT NULL,
      nickname VARCHAR(50),
      birth_date DATE,
      -- Removed the generated age column
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
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

  📊 To Get Age When Needed:

  Create a view that calculates age dynamically:

  -- After creating the table, create this view
  CREATE VIEW v_child_profile_with_age AS
  SELECT
      *,
      TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) as age
  FROM child_profile;

  -- Then query like this:
  SELECT * FROM v_child_profile_with_age WHERE child_name = 'Little Star';

  🚀 Alternative: Use a Stored Function

  -- Create a function to calculate age
  DELIMITER //
  CREATE FUNCTION calculate_age(birth_date DATE)
  RETURNS INT
  DETERMINISTIC
  BEGIN
      RETURN TIMESTAMPDIFF(YEAR, birth_date, CURRENT_DATE);
  END//
  DELIMITER ;

  -- Use in queries:
  SELECT *, calculate_age(birth_date) as age FROM child_profile;

  This approach avoids the restriction while still giving you age calculation functionality!
