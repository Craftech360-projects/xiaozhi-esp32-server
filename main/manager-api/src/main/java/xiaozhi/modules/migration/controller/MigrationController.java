package xiaozhi.modules.migration.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.migration.service.MigrationService;

import java.io.File;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Database Migration Controller
 * Provides endpoints for MySQL to PostgreSQL migration
 */
@Slf4j
@RestController
@RequestMapping("/migration")
@Tag(name = "Database Migration", description = "MySQL to PostgreSQL migration operations")
public class MigrationController {

    @Autowired
    private MigrationService migrationService;

    @PostMapping("/export-mysql")
    @Operation(summary = "Export data from MySQL database")
    public Result<String> exportMySQL(@RequestParam(defaultValue = "127.0.0.1") String host,
                                     @RequestParam(defaultValue = "3306") int port,
                                     @RequestParam(defaultValue = "xiaozhi_esp32_server") String database,
                                     @RequestParam(defaultValue = "root") String username,
                                     @RequestParam(defaultValue = "123456") String password,
                                     @RequestParam(required = false) String outputDir) {
        try {
            if (outputDir == null) {
                outputDir = generateOutputDir("mysql_export");
            }
            
            migrationService.exportFromMySQL(host, port, database, username, password, outputDir);
            
            return Result.ok("MySQL data exported successfully to: " + outputDir);
        } catch (Exception e) {
            log.error("Failed to export MySQL data", e);
            return Result.error("Export failed: " + e.getMessage());
        }
    }

    @PostMapping("/import-postgresql")
    @Operation(summary = "Import data to PostgreSQL database")
    public Result<String> importPostgreSQL(@RequestParam(defaultValue = "127.0.0.1") String host,
                                          @RequestParam(defaultValue = "5432") int port,
                                          @RequestParam(defaultValue = "xiaozhi_esp32_server") String database,
                                          @RequestParam(defaultValue = "postgres") String username,
                                          @RequestParam(defaultValue = "123456") String password,
                                          @RequestParam String inputDir) {
        try {
            migrationService.importToPostgreSQL(host, port, database, username, password, inputDir);
            
            return Result.ok("PostgreSQL data imported successfully from: " + inputDir);
        } catch (Exception e) {
            log.error("Failed to import PostgreSQL data", e);
            return Result.error("Import failed: " + e.getMessage());
        }
    }

    @PostMapping("/migrate-full")
    @Operation(summary = "Full migration from MySQL to PostgreSQL")
    public Result<String> migrateDatabase(@RequestParam(defaultValue = "127.0.0.1") String mysqlHost,
                                         @RequestParam(defaultValue = "3306") int mysqlPort,
                                         @RequestParam(defaultValue = "xiaozhi_esp32_server") String mysqlDatabase,
                                         @RequestParam(defaultValue = "root") String mysqlUsername,
                                         @RequestParam(defaultValue = "123456") String mysqlPassword,
                                         @RequestParam(defaultValue = "127.0.0.1") String postgresHost,
                                         @RequestParam(defaultValue = "5432") int postgresPort,
                                         @RequestParam(defaultValue = "xiaozhi_esp32_server") String postgresDatabase,
                                         @RequestParam(defaultValue = "postgres") String postgresUsername,
                                         @RequestParam(defaultValue = "123456") String postgresPassword,
                                         @RequestParam(required = false) String tempDir) {
        try {
            if (tempDir == null) {
                tempDir = generateOutputDir("migration_temp");
            }
            
            migrationService.migrateDatabase(mysqlHost, mysqlPort, mysqlDatabase, mysqlUsername, mysqlPassword,
                                           postgresHost, postgresPort, postgresDatabase, postgresUsername, postgresPassword,
                                           tempDir);
            
            return Result.ok("Database migration completed successfully. Temp files in: " + tempDir);
        } catch (Exception e) {
            log.error("Failed to migrate database", e);
            return Result.error("Migration failed: " + e.getMessage());
        }
    }

    @PostMapping("/validate")
    @Operation(summary = "Validate migration between MySQL and PostgreSQL")
    public Result<String> validateMigration(@RequestParam(defaultValue = "127.0.0.1") String mysqlHost,
                                           @RequestParam(defaultValue = "3306") int mysqlPort,
                                           @RequestParam(defaultValue = "xiaozhi_esp32_server") String mysqlDatabase,
                                           @RequestParam(defaultValue = "root") String mysqlUsername,
                                           @RequestParam(defaultValue = "123456") String mysqlPassword,
                                           @RequestParam(defaultValue = "127.0.0.1") String postgresHost,
                                           @RequestParam(defaultValue = "5432") int postgresPort,
                                           @RequestParam(defaultValue = "xiaozhi_esp32_server") String postgresDatabase,
                                           @RequestParam(defaultValue = "postgres") String postgresUsername,
                                           @RequestParam(defaultValue = "123456") String postgresPassword) {
        try {
            migrationService.validateMigration(mysqlHost, mysqlPort, mysqlDatabase, mysqlUsername, mysqlPassword,
                                             postgresHost, postgresPort, postgresDatabase, postgresUsername, postgresPassword);
            
            return Result.ok("Migration validation completed successfully");
        } catch (Exception e) {
            log.error("Failed to validate migration", e);
            return Result.error("Validation failed: " + e.getMessage());
        }
    }

    @PostMapping("/quick-export")
    @Operation(summary = "Quick export from local MySQL (default settings)")
    public Result<String> quickExportMySQL(@RequestParam(required = false) String outputDir) {
        try {
            if (outputDir == null) {
                outputDir = generateOutputDir("mysql_export");
            }
            
            migrationService.exportCurrentMySQLData(outputDir);
            
            return Result.ok("MySQL data exported successfully to: " + outputDir);
        } catch (Exception e) {
            log.error("Failed to export MySQL data", e);
            return Result.error("Export failed: " + e.getMessage());
        }
    }

    @PostMapping("/quick-import")
    @Operation(summary = "Quick import to Azure PostgreSQL (using environment variables)")
    public Result<String> quickImportPostgreSQL(@RequestParam String inputDir) {
        try {
            migrationService.importToAzurePostgreSQL(inputDir);
            
            return Result.ok("Azure PostgreSQL data imported successfully from: " + inputDir);
        } catch (Exception e) {
            log.error("Failed to import Azure PostgreSQL data", e);
            return Result.error("Import failed: " + e.getMessage());
        }
    }

    @PostMapping("/quick-migrate")
    @Operation(summary = "Quick migration from local MySQL to Azure PostgreSQL")
    public Result<String> quickMigrate(@RequestParam(required = false) String tempDir) {
        try {
            if (tempDir == null) {
                tempDir = generateOutputDir("migration_temp");
            }
            
            migrationService.migrateToAzureDatabase(tempDir);
            
            return Result.ok("Database migration to Azure PostgreSQL completed successfully. Temp files in: " + tempDir);
        } catch (Exception e) {
            log.error("Failed to migrate database to Azure", e);
            return Result.error("Migration failed: " + e.getMessage());
        }
    }

    /**
     * Generate output directory with timestamp
     */
    private String generateOutputDir(String prefix) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        String dirName = prefix + "_" + timestamp;
        
        // Create directory in system temp folder
        String tempDir = System.getProperty("java.io.tmpdir");
        File outputDir = new File(tempDir, dirName);
        outputDir.mkdirs();
        
        return outputDir.getAbsolutePath();
    }
}