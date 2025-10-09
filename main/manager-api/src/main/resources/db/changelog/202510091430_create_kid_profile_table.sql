-- Create kid_profile table for storing children profiles linked to devices
-- Each user (parent) can have multiple kids, and each device can be assigned to one kid

CREATE TABLE IF NOT EXISTS `kid_profile` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT 'Primary key',
  `user_id` bigint NOT NULL COMMENT 'FK to sys_user table (parent)',
  `name` varchar(100) NOT NULL COMMENT 'Child name',
  `date_of_birth` date NOT NULL COMMENT 'Child date of birth',
  `gender` varchar(20) DEFAULT NULL COMMENT 'Child gender (male/female/other)',
  `interests` text COMMENT 'JSON array of child interests',
  `avatar_url` varchar(500) DEFAULT NULL COMMENT 'Avatar URL',
  `creator` bigint DEFAULT NULL COMMENT 'Creator user ID',
  `create_date` datetime DEFAULT NULL COMMENT 'Creation date',
  `updater` bigint DEFAULT NULL COMMENT 'Last updater user ID',
  `update_date` datetime DEFAULT NULL COMMENT 'Last update date',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_kid_profile_user` FOREIGN KEY (`user_id`) REFERENCES `sys_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Kid profiles table';
