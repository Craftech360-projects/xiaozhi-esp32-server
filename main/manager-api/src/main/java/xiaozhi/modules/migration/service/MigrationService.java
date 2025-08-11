package xiaozhi.modules.migration.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import xiaozhi.modules.migration.util.DatabaseMigrationUtil;

/**
 * Migration Service for handling database migration operations
 */
@Slf4j
@Service
public class MigrationService {

    @Autowired
    private DatabaseMigrationUtil migrationUtil;

    /**
     * Export data from MySQL database
     */
    public void exportFromMySQL(String host, int port, String database, 
                               String username, String password, String outputDir) {
        String mysqlUrl = String.format("jdbc:mysql://%s:%d/%s?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai", 
                                       host, port, database);
        
        log.info("Starting MySQL export from {}:{}/{}", host, port, database);
        migrationUtil.exportMySQLData(mysqlUrl, username, password, outputDir);
    }

    /**
     * Import data to PostgreSQL database
     */
    public void importToPostgreSQL(String host, int port, String database,
                                  String username, String password, String inputDir) {
        String postgresUrl = String.format("jdbc:postgresql://%s:%d/%s?sslmode=disable&characterEncoding=UTF-8", 
                                          host, port, database);
        
        log.info("Starting PostgreSQL import to {}:{}/{}", host, port, database);
        migrationUtil.importPostgreSQLData(postgresUrl, username, password, inputDir);
    }

    /**
     * Full migration from MySQL to PostgreSQL
     */
    public void migrateDatabase(String mysqlHost, int mysqlPort, String mysqlDatabase,
                               String mysqlUsername, String mysqlPassword,
                               String postgresHost, int postgresPort, String postgresDatabase,
                               String postgresUsername, String postgresPassword,
                               String tempDir) {
        
        log.info("Starting full database migration from MySQL to PostgreSQL");
        
        try {
            // Step 1: Export from MySQL
            log.info("Step 1: Exporting data from MySQL");
            exportFromMySQL(mysqlHost, mysqlPort, mysqlDatabase, mysqlUsername, mysqlPassword, tempDir);
            
            // Step 2: Import to PostgreSQL
            log.info("Step 2: Importing data to PostgreSQL");
            importToPostgreSQL(postgresHost, postgresPort, postgresDatabase, 
                             postgresUsername, postgresPassword, tempDir);
            
            // Step 3: Validate migration
            log.info("Step 3: Validating migration");
            validateMigration(mysqlHost, mysqlPort, mysqlDatabase, mysqlUsername, mysqlPassword,
                            postgresHost, postgresPort, postgresDatabase, postgresUsername, postgresPassword);
            
            log.info("Database migration completed successfully");
            
        } catch (Exception e) {
            log.error("Database migration failed", e);
            throw new RuntimeException("Migration failed", e);
        }
    }

    /**
     * Validate migration between MySQL and PostgreSQL
     */
    public void validateMigration(String mysqlHost, int mysqlPort, String mysqlDatabase,
                                 String mysqlUsername, String mysqlPassword,
                                 String postgresHost, int postgresPort, String postgresDatabase,
                                 String postgresUsername, String postgresPassword) {
        
        String mysqlUrl = String.format("jdbc:mysql://%s:%d/%s?useUnicode=true&characterEncoding=UTF-8&serverTimezone=Asia/Shanghai", 
                                       mysqlHost, mysqlPort, mysqlDatabase);
        String postgresUrl = String.format("jdbc:postgresql://%s:%d/%s?sslmode=disable&characterEncoding=UTF-8", 
                                          postgresHost, postgresPort, postgresDatabase);
        
        migrationUtil.validateMigration(mysqlUrl, mysqlUsername, mysqlPassword,
                                       postgresUrl, postgresUsername, postgresPassword);
    }

    /**
     * Export data from current MySQL setup (using default connection parameters)
     */
    public void exportCurrentMySQLData(String outputDir) {
        // Default MySQL connection parameters for xiaozhi-esp32-server
        exportFromMySQL("127.0.0.1", 3306, "xiaozhi_esp32_server", "root", "123456", outputDir);
    }

    /**
     * Import data to Azure PostgreSQL (using default connection parameters)
     */
    public void importToAzurePostgreSQL(String inputDir) {
        // Default Azure PostgreSQL connection parameters for xiaozhi-esp32-server
        String server = System.getenv("AZURE_POSTGRES_SERVER");
        String database = System.getenv("AZURE_POSTGRES_DATABASE");
        String username = System.getenv("AZURE_POSTGRES_USERNAME");
        String password = System.getenv("AZURE_POSTGRES_PASSWORD");
        
        if (server == null || database == null || username == null || password == null) {
            throw new RuntimeException("Azure PostgreSQL environment variables not set. Please set AZURE_POSTGRES_SERVER, AZURE_POSTGRES_DATABASE, AZURE_POSTGRES_USERNAME, and AZURE_POSTGRES_PASSWORD");
        }
        
        String host = server + ".postgres.database.azure.com";
        importToPostgreSQL(host, 5432, database, username + "@" + server, password, inputDir);
    }

    /**
     * Quick migration from local MySQL to Azure PostgreSQL
     */
    public void migrateToAzureDatabase(String tempDir) {
        String server = System.getenv("AZURE_POSTGRES_SERVER");
        String database = System.getenv("AZURE_POSTGRES_DATABASE");
        String username = System.getenv("AZURE_POSTGRES_USERNAME");
        String password = System.getenv("AZURE_POSTGRES_PASSWORD");
        
        if (server == null || database == null || username == null || password == null) {
            throw new RuntimeException("Azure PostgreSQL environment variables not set. Please set AZURE_POSTGRES_SERVER, AZURE_POSTGRES_DATABASE, AZURE_POSTGRES_USERNAME, and AZURE_POSTGRES_PASSWORD");
        }
        
        String host = server + ".postgres.database.azure.com";
        migrateDatabase("127.0.0.1", 3306, "xiaozhi_esp32_server", "root", "123456",
                       host, 5432, database, username + "@" + server, password,
                       tempDir);
    }
}