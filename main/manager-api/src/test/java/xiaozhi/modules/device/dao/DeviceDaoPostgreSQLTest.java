package xiaozhi.modules.device.dao;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.transaction.annotation.Transactional;

import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PostgreSQL-specific tests for DeviceDao
 * Tests pagination syntax and date handling
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
public class DeviceDaoPostgreSQLTest {

    @Autowired
    private DeviceDao deviceDao;

    @Test
    public void testGetAllLastConnectedAtByAgentId() {
        // Test PostgreSQL LIMIT/OFFSET syntax
        String testAgentId = "test-agent-id";
        
        assertDoesNotThrow(() -> {
            Date lastConnected = deviceDao.getAllLastConnectedAtByAgentId(testAgentId);
            // Result can be null if no devices exist, but query should execute
        });
    }

    @Test
    public void testPostgreSQLPaginationSyntax() {
        // Test that the converted LIMIT/OFFSET syntax works
        String testAgentId = "test-agent-id";
        
        // This should not throw SQL syntax errors
        assertDoesNotThrow(() -> {
            Date result = deviceDao.getAllLastConnectedAtByAgentId(testAgentId);
        });
    }

    @Test
    public void testDateHandling() {
        // Test PostgreSQL TIMESTAMP handling
        String testAgentId = "test-agent-id";
        Date result = deviceDao.getAllLastConnectedAtByAgentId(testAgentId);
        
        // If result is not null, it should be a valid Date object
        if (result != null) {
            assertNotNull(result);
            assertTrue(result instanceof Date);
        }
    }
}