package xiaozhi.modules.agent.dao;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.transaction.annotation.Transactional;
import xiaozhi.modules.agent.vo.AgentInfoVO;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PostgreSQL-specific tests for AgentDao
 * Tests JSON functions and PostgreSQL compatibility
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
public class AgentDaoPostgreSQLTest {

    @Autowired
    private AgentDao agentDao;

    @Test
    public void testGetDeviceCountByAgentId() {
        // Test basic count query
        String testAgentId = "test-agent-id";
        Integer count = agentDao.getDeviceCountByAgentId(testAgentId);
        
        assertNotNull(count);
        assertTrue(count >= 0);
    }

    @Test
    public void testSelectAgentInfoById() {
        // Test complex JSON aggregation query with PostgreSQL functions
        String testAgentId = "test-agent-id";
        AgentInfoVO agentInfo = agentDao.selectAgentInfoById(testAgentId);
        
        // The query should execute without errors even if no data is found
        // This tests PostgreSQL JSON function compatibility
        if (agentInfo != null) {
            // Verify JSON functions work correctly
            assertNotNull(agentInfo.getFunctions());
            // Functions should be a valid JSON array (empty or with data)
            assertTrue(agentInfo.getFunctions() instanceof java.util.List || 
                      agentInfo.getFunctions() == null);
        }
    }

    @Test
    public void testGetDefaultAgentByMacAddress() {
        // Test JOIN query with PostgreSQL
        String testMacAddress = "test-mac-address";
        var agent = agentDao.getDefaultAgentByMacAddress(testMacAddress);
        
        // Query should execute without errors
        // This tests PostgreSQL LIMIT/OFFSET syntax
        assertDoesNotThrow(() -> {
            agentDao.getDefaultAgentByMacAddress(testMacAddress);
        });
    }

    @Test
    public void testPostgreSQLJsonFunctions() {
        // Test that PostgreSQL JSON functions work correctly
        // This is an integration test for the converted JSON functions
        
        assertDoesNotThrow(() -> {
            // This should not throw any SQL syntax errors
            AgentInfoVO result = agentDao.selectAgentInfoById("non-existent-id");
            // Result can be null, but query should execute successfully
        });
    }
}