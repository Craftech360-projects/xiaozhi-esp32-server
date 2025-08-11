package xiaozhi.modules.agent.dao;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.transaction.annotation.Transactional;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PostgreSQL-specific tests for AiAgentChatHistoryDao
 * Tests JDBC type mappings and delete operations
 */
@SpringBootTest
@ActiveProfiles("test")
@TestPropertySource(properties = {
    "spring.datasource.driver-class-name=org.postgresql.Driver",
    "spring.datasource.url=jdbc:postgresql://localhost:5432/xiaozhi_esp32_server_test?sslmode=disable",
    "spring.datasource.username=postgres",
    "spring.datasource.password=123456"
})
@Transactional
public class AiAgentChatHistoryDaoPostgreSQLTest {

    @Autowired
    private AiAgentChatHistoryDao aiAgentChatHistoryDao;

    @Test
    public void testDeleteAudioByAgentId() {
        // Test DELETE operation with subquery
        String testAgentId = "test-agent-id";
        
        assertDoesNotThrow(() -> {
            aiAgentChatHistoryDao.deleteAudioByAgentId(testAgentId);
        });
    }

    @Test
    public void testDeleteAudioIdByAgentId() {
        // Test UPDATE operation setting NULL values
        String testAgentId = "test-agent-id";
        
        assertDoesNotThrow(() -> {
            aiAgentChatHistoryDao.deleteAudioIdByAgentId(testAgentId);
        });
    }

    @Test
    public void testDeleteHistoryByAgentId() {
        // Test simple DELETE operation
        String testAgentId = "test-agent-id";
        
        assertDoesNotThrow(() -> {
            aiAgentChatHistoryDao.deleteHistoryByAgentId(testAgentId);
        });
    }

    @Test
    public void testPostgreSQLJdbcTypes() {
        // Test that PostgreSQL JDBC types work correctly
        // This tests the SMALLINT and VARCHAR type mappings
        
        assertDoesNotThrow(() -> {
            // All delete operations should execute without JDBC type errors
            String testId = "test-id";
            aiAgentChatHistoryDao.deleteAudioByAgentId(testId);
            aiAgentChatHistoryDao.deleteAudioIdByAgentId(testId);
            aiAgentChatHistoryDao.deleteHistoryByAgentId(testId);
        });
    }

    @Test
    public void testCascadeOperations() {
        // Test that cascade delete operations work with PostgreSQL
        String testAgentId = "test-agent-id";
        
        assertDoesNotThrow(() -> {
            // Execute all delete operations in sequence
            aiAgentChatHistoryDao.deleteAudioByAgentId(testAgentId);
            aiAgentChatHistoryDao.deleteAudioIdByAgentId(testAgentId);
            aiAgentChatHistoryDao.deleteHistoryByAgentId(testAgentId);
        });
    }
}