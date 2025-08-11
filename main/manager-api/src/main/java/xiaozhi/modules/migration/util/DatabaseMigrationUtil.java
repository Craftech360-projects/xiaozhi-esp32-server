package xiaozhi.modules.migration.util;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.sql.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * Database Migration Utility for MySQL to PostgreSQL migration
 * This utility handles data export from MySQL and import to PostgreSQL
 */
@Slf4j
@Component
public class DatabaseMigrationUtil {

    private static final ObjectMapper objectMapper = new ObjectMapper();
    private static final DateTimeFormatter TIMESTAMP_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    /**
     * Export data from MySQL database
     */
    public void exportMySQLData(String mysqlUrl, String username, String password, String outputDir) {
        log.info("Starting MySQL data export to directory: {}", outputDir);
        
        try {
            // Create output directory
            Path outputPath = Paths.get(outputDir);
            Files.createDirectories(outputPath);
            
            // Connect to MySQL
            try (Connection connection = DriverManager.getConnection(mysqlUrl, username, password)) {
                log.info("Connected to MySQL database");
                
                // Get all tables
                List<String> tables = getAllTables(connection);
                log.info("Found {} tables to export", tables.size());
                
                // Export each table
                for (String table : tables) {
                    exportTable(connection, table, outputPath);
                }
                
                // Create metadata file
                createMetadataFile(outputPath, tables);
                
                log.info("MySQL data export completed successfully");
            }
        } catch (Exception e) {
            log.error("Error during MySQL data export", e);
            throw new RuntimeException("Failed to export MySQL data", e);
        }
    }

    /**
     * Import data to PostgreSQL database
     */
    public void importPostgreSQLData(String postgresUrl, String username, String password, String inputDir) {
        log.info("Starting PostgreSQL data import from directory: {}", inputDir);
        
        try {
            Path inputPath = Paths.get(inputDir);
            if (!Files.exists(inputPath)) {
                throw new IllegalArgumentException("Input directory does not exist: " + inputDir);
            }
            
            // Connect to PostgreSQL
            try (Connection connection = DriverManager.getConnection(postgresUrl, username, password)) {
                log.info("Connected to PostgreSQL database");
                
                // Read metadata
                Map<String, Object> metadata = readMetadataFile(inputPath);
                @SuppressWarnings("unchecked")
                List<String> tables = (List<String>) metadata.get("tables");
                
                log.info("Found {} tables to import", tables.size());
                
                // Import each table
                for (String table : tables) {
                    importTable(connection, table, inputPath);
                }
                
                log.info("PostgreSQL data import completed successfully");
            }
        } catch (Exception e) {
            log.error("Error during PostgreSQL data import", e);
            throw new RuntimeException("Failed to import PostgreSQL data", e);
        }
    }

    /**
     * Get all table names from the database
     */
    private List<String> getAllTables(Connection connection) throws SQLException {
        List<String> tables = new ArrayList<>();
        DatabaseMetaData metaData = connection.getMetaData();
        
        try (ResultSet rs = metaData.getTables(null, null, "%", new String[]{"TABLE"})) {
            while (rs.next()) {
                String tableName = rs.getString("TABLE_NAME");
                // Skip system tables and views
                if (!tableName.startsWith("information_schema") && 
                    !tableName.startsWith("performance_schema") &&
                    !tableName.startsWith("mysql") &&
                    !tableName.startsWith("sys")) {
                    tables.add(tableName);
                }
            }
        }
        
        return tables;
    }

    /**
     * Export a single table to JSON file
     */
    private void exportTable(Connection connection, String tableName, Path outputPath) {
        log.info("Exporting table: {}", tableName);
        
        try {
            String sql = "SELECT * FROM " + tableName;
            try (PreparedStatement stmt = connection.prepareStatement(sql);
                 ResultSet rs = stmt.executeQuery()) {
                
                ResultSetMetaData metaData = rs.getMetaData();
                int columnCount = metaData.getColumnCount();
                
                List<Map<String, Object>> rows = new ArrayList<>();
                
                while (rs.next()) {
                    Map<String, Object> row = new LinkedHashMap<>();
                    
                    for (int i = 1; i <= columnCount; i++) {
                        String columnName = metaData.getColumnName(i);
                        Object value = rs.getObject(i);
                        
                        // Convert MySQL-specific types
                        value = convertMySQLValue(value, metaData.getColumnType(i));
                        
                        row.put(columnName, value);
                    }
                    
                    rows.add(row);
                }
                
                // Write to JSON file
                Path tableFile = outputPath.resolve(tableName + ".json");
                objectMapper.writerWithDefaultPrettyPrinter().writeValue(tableFile.toFile(), rows);
                
                log.info("Exported {} rows from table {}", rows.size(), tableName);
            }
        } catch (Exception e) {
            log.error("Error exporting table: {}", tableName, e);
            throw new RuntimeException("Failed to export table: " + tableName, e);
        }
    }

    /**
     * Import a single table from JSON file
     */
    private void importTable(Connection connection, String tableName, Path inputPath) {
        log.info("Importing table: {}", tableName);
        
        try {
            Path tableFile = inputPath.resolve(tableName + ".json");
            if (!Files.exists(tableFile)) {
                log.warn("Table file not found: {}, skipping", tableFile);
                return;
            }
            
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> rows = objectMapper.readValue(tableFile.toFile(), List.class);
            
            if (rows.isEmpty()) {
                log.info("No data to import for table: {}", tableName);
                return;
            }
            
            // Get column names from first row
            Set<String> columns = rows.get(0).keySet();
            
            // Build INSERT statement
            String columnList = String.join(", ", columns);
            String placeholders = String.join(", ", Collections.nCopies(columns.size(), "?"));
            String sql = String.format("INSERT INTO %s (%s) VALUES (%s)", tableName, columnList, placeholders);
            
            try (PreparedStatement stmt = connection.prepareStatement(sql)) {
                connection.setAutoCommit(false);
                
                int batchSize = 1000;
                int count = 0;
                
                for (Map<String, Object> row : rows) {
                    int paramIndex = 1;
                    for (String column : columns) {
                        Object value = row.get(column);
                        
                        // Convert PostgreSQL-compatible values
                        value = convertPostgreSQLValue(value);
                        
                        stmt.setObject(paramIndex++, value);
                    }
                    
                    stmt.addBatch();
                    count++;
                    
                    if (count % batchSize == 0) {
                        stmt.executeBatch();
                        connection.commit();
                        log.debug("Imported {} rows for table {}", count, tableName);
                    }
                }
                
                // Execute remaining batch
                stmt.executeBatch();
                connection.commit();
                connection.setAutoCommit(true);
                
                log.info("Imported {} rows to table {}", count, tableName);
            }
        } catch (Exception e) {
            log.error("Error importing table: {}", tableName, e);
            try {
                connection.rollback();
            } catch (SQLException rollbackEx) {
                log.error("Error rolling back transaction", rollbackEx);
            }
            throw new RuntimeException("Failed to import table: " + tableName, e);
        }
    }

    /**
     * Convert MySQL-specific values for export
     */
    private Object convertMySQLValue(Object value, int sqlType) {
        if (value == null) {
            return null;
        }
        
        switch (sqlType) {
            case Types.TINYINT:
                // Convert TINYINT to Integer for PostgreSQL SMALLINT
                return ((Number) value).intValue();
            case Types.TIMESTAMP:
                // Convert Timestamp to String for consistent handling
                if (value instanceof Timestamp) {
                    return ((Timestamp) value).toLocalDateTime().format(TIMESTAMP_FORMATTER);
                }
                break;
            case Types.LONGVARCHAR:
            case Types.CLOB:
                // Convert LONGTEXT to String
                return value.toString();
        }
        
        return value;
    }

    /**
     * Convert values for PostgreSQL import
     */
    private Object convertPostgreSQLValue(Object value) {
        if (value == null) {
            return null;
        }
        
        // Convert string timestamps back to Timestamp objects
        if (value instanceof String) {
            String strValue = (String) value;
            if (strValue.matches("\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}")) {
                try {
                    LocalDateTime dateTime = LocalDateTime.parse(strValue, TIMESTAMP_FORMATTER);
                    return Timestamp.valueOf(dateTime);
                } catch (Exception e) {
                    // If parsing fails, return as string
                    return value;
                }
            }
        }
        
        return value;
    }

    /**
     * Create metadata file with export information
     */
    private void createMetadataFile(Path outputPath, List<String> tables) throws IOException {
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("exportDate", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        metadata.put("sourceDatabase", "MySQL");
        metadata.put("targetDatabase", "PostgreSQL");
        metadata.put("tables", tables);
        metadata.put("tableCount", tables.size());
        
        Path metadataFile = outputPath.resolve("migration_metadata.json");
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(metadataFile.toFile(), metadata);
        
        log.info("Created metadata file: {}", metadataFile);
    }

    /**
     * Read metadata file
     */
    @SuppressWarnings("unchecked")
    private Map<String, Object> readMetadataFile(Path inputPath) throws IOException {
        Path metadataFile = inputPath.resolve("migration_metadata.json");
        if (!Files.exists(metadataFile)) {
            throw new IllegalArgumentException("Metadata file not found: " + metadataFile);
        }
        
        return objectMapper.readValue(metadataFile.toFile(), Map.class);
    }

    /**
     * Validate data integrity after migration
     */
    public void validateMigration(String mysqlUrl, String mysqlUser, String mysqlPass,
                                 String postgresUrl, String postgresUser, String postgresPass) {
        log.info("Starting migration validation");
        
        try (Connection mysqlConn = DriverManager.getConnection(mysqlUrl, mysqlUser, mysqlPass);
             Connection postgresConn = DriverManager.getConnection(postgresUrl, postgresUser, postgresPass)) {
            
            List<String> tables = getAllTables(mysqlConn);
            boolean allValid = true;
            
            for (String table : tables) {
                if (!validateTableData(mysqlConn, postgresConn, table)) {
                    allValid = false;
                }
            }
            
            if (allValid) {
                log.info("Migration validation completed successfully - all tables match");
            } else {
                log.error("Migration validation failed - some tables have mismatched data");
            }
            
        } catch (Exception e) {
            log.error("Error during migration validation", e);
            throw new RuntimeException("Failed to validate migration", e);
        }
    }

    /**
     * Validate data for a single table
     */
    private boolean validateTableData(Connection mysqlConn, Connection postgresConn, String tableName) {
        try {
            // Count rows in both databases
            long mysqlCount = getRowCount(mysqlConn, tableName);
            long postgresCount = getRowCount(postgresConn, tableName);
            
            if (mysqlCount == postgresCount) {
                log.info("Table {} validation passed: {} rows", tableName, mysqlCount);
                return true;
            } else {
                log.error("Table {} validation failed: MySQL={} rows, PostgreSQL={} rows", 
                         tableName, mysqlCount, postgresCount);
                return false;
            }
        } catch (Exception e) {
            log.error("Error validating table: {}", tableName, e);
            return false;
        }
    }

    /**
     * Get row count for a table
     */
    private long getRowCount(Connection connection, String tableName) throws SQLException {
        String sql = "SELECT COUNT(*) FROM " + tableName;
        try (PreparedStatement stmt = connection.prepareStatement(sql);
             ResultSet rs = stmt.executeQuery()) {
            if (rs.next()) {
                return rs.getLong(1);
            }
            return 0;
        }
    }
}