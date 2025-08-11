# Requirements Document

## Introduction

This feature involves migrating the xiaozhi-esp32-server application from MySQL database to Azure PostgreSQL. The migration includes updating database drivers, modifying SQL syntax for PostgreSQL compatibility, updating configuration files, and ensuring all existing functionality continues to work seamlessly with the new database system.

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want to migrate from MySQL to Azure PostgreSQL, so that I can leverage Azure's managed PostgreSQL service with better scalability, security, and cloud integration.

#### Acceptance Criteria

1. WHEN the application starts THEN it SHALL connect to Azure PostgreSQL instead of MySQL
2. WHEN database operations are performed THEN they SHALL execute successfully on PostgreSQL
3. WHEN existing data needs to be preserved THEN the migration SHALL maintain data integrity
4. WHEN SQL queries are executed THEN they SHALL be compatible with PostgreSQL syntax

### Requirement 2

**User Story:** As a developer, I want all MyBatis XML mappers to work with PostgreSQL, so that existing database queries continue to function without breaking the application.

#### Acceptance Criteria

1. WHEN MyBatis queries are executed THEN they SHALL use PostgreSQL-compatible SQL syntax
2. WHEN JSON operations are performed THEN they SHALL use PostgreSQL JSON functions instead of MySQL JSON functions
3. WHEN date/time operations are used THEN they SHALL use PostgreSQL date/time functions
4. WHEN auto-increment fields are used THEN they SHALL use PostgreSQL SERIAL or IDENTITY columns

### Requirement 3

**User Story:** As a DevOps engineer, I want updated configuration files and Docker setup, so that the application can be deployed with Azure PostgreSQL in both development and production environments.

#### Acceptance Criteria

1. WHEN the application is configured THEN it SHALL use PostgreSQL JDBC driver and connection settings
2. WHEN Docker containers are deployed THEN they SHALL use PostgreSQL instead of MySQL
3. WHEN environment variables are set THEN they SHALL reflect PostgreSQL connection parameters
4. WHEN connection pooling is configured THEN it SHALL work optimally with PostgreSQL

### Requirement 4

**User Story:** As a database administrator, I want Liquibase migrations to be PostgreSQL-compatible, so that database schema changes can be applied successfully to Azure PostgreSQL.

#### Acceptance Criteria

1. WHEN Liquibase migrations run THEN they SHALL execute successfully on PostgreSQL
2. WHEN data types are defined THEN they SHALL use PostgreSQL-compatible data types
3. WHEN constraints are created THEN they SHALL follow PostgreSQL syntax
4. WHEN indexes are created THEN they SHALL use PostgreSQL index syntax

### Requirement 5

**User Story:** As a system user, I want all existing application features to work identically, so that the database migration is transparent to end users.

#### Acceptance Criteria

1. WHEN users interact with the application THEN all features SHALL work exactly as before
2. WHEN data is queried THEN results SHALL be identical to the MySQL implementation
3. WHEN data is inserted or updated THEN it SHALL be stored correctly in PostgreSQL
4. WHEN application performance is measured THEN it SHALL meet or exceed current performance levels