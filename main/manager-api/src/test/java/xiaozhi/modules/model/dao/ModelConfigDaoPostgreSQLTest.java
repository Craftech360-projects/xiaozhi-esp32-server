package xiaozhi.modules.model.dao;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * PostgreSQL-specific tests for ModelConfigDao
 * Tests data type compatibility and query execution
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
public class ModelConfigDaoPostgreSQLTest {

    @Autowired
    private ModelConfigDao modelConfigDao;

    @Test
    public void testGetModelCodeList() {
        // Test basic query execution with PostgreSQL
        String testModelType = "LLM";
        
        assertDoesNotThrow(() -> {
            List<String> modelCodes = modelConfigDao.getModelCodeList(testModelType, null);
            assertNotNull(modelCodes);
        });
    }

    @Test
    public void testGetModelCodeListWithFilter() {
        // Test conditional query with PostgreSQL
        String testModelType = "LLM";
        String testModelName = "openai";
        
        assertDoesNotThrow(() -> {
            List<String> modelCodes = modelConfigDao.getModelCodeList(testModelType, testModelName);
            assertNotNull(modelCodes);
        });
    }

    @Test
    public void testPostgreSQLDataTypes() {
        // Test that PostgreSQL data types work correctly
        assertDoesNotThrow(() -> {
            // This tests that the query executes without data type errors
            List<String> result = modelConfigDao.getModelCodeList("TEST_TYPE", "TEST_NAME");
            assertNotNull(result);
        });
    }
}