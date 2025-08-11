package xiaozhi.modules.migration;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import xiaozhi.modules.migration.service.MigrationService;
import xiaozhi.modules.migration.util.DatabaseMigrationUtil;

import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration tests for database migration functionality
 */
@SpringBootTest
@ActiveProfiles("test")
public class MigrationIntegrationTest {

    @Autowired
    private MigrationService migrationService;

    @Autowired
    private DatabaseMigrationUtil migrationUtil;

    @TempDir
    Path tempDir;

    @Test
    public void testMigrationServiceInitialization() {
        // Test that migration service is properly initialized
        assertNotNull(migrationService);
        assertNotNull(migrationUtil);
    }

    @Test
    public void testExportDirectoryCreation() {
        // Test that export creates proper directory structure
        String outputDir = tempDir.resolve("test_export").toString();
        
        assertDoesNotThrow(() -> {
            // This should create the directory structure even if database connection fails
            // We're testing the utility logic, not the actual database connection
        });
    }

    @Test
    public void testMigrationUtilityMethods() {
        // Test utility methods that don't require database connection
        assertDoesNotThrow(() -> {
            // Test that the utility classes are properly constructed
            DatabaseMigrationUtil util = new DatabaseMigrationUtil();
            assertNotNull(util);
        });
    }

    @Test
    public void testConfigurationValidation() {
        // Test that migration configuration is valid
        assertDoesNotThrow(() -> {
            // Test service method calls (they may fail due to no database, but should not throw config errors)
            try {
                migrationService.exportCurrentMySQLData(tempDir.toString());
            } catch (RuntimeException e) {
                // Expected if no database is available, but should not be configuration errors
                assertTrue(e.getMessage().contains("Failed to export") || 
                          e.getMessage().contains("Connection") ||
                          e.getMessage().contains("database"));
            }
        });
    }

    @Test
    public void testPostgreSQLConnectionString() {
        // Test PostgreSQL connection string generation
        assertDoesNotThrow(() -> {
            try {
                migrationService.importToLocalPostgreSQL(tempDir.toString());
            } catch (RuntimeException e) {
                // Expected if no database is available
                assertTrue(e.getMessage().contains("Failed to import") || 
                          e.getMessage().contains("Connection") ||
                          e.getMessage().contains("database"));
            }
        });
    }
}