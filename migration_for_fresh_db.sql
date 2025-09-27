-- ===================================================================
-- XIAOZHI ESP32 SERVER - FRESH DATABASE MIGRATION SCRIPT
-- ===================================================================
-- This script creates the complete database schema and data for xiaozhi_fresh
-- Modified for MySQL Workbench usage
-- Compatible with MySQL 8.0+
-- ===================================================================

-- Use the fresh database (make sure you created 'xiaozhi_fresh' first)
USE xiaozhi_fresh;

-- MySQL compatibility settings
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Clear any existing data (fresh start)
SET FOREIGN_KEY_CHECKS = 0;