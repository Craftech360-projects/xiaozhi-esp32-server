package xiaozhi.modules.content.service.impl;

import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.config.SupabaseConfig;
import xiaozhi.modules.content.dao.ContentLibraryDao;
import xiaozhi.modules.content.entity.ContentLibraryEntity;
import xiaozhi.modules.content.service.SupabaseContentService;

/**
 * Supabase Content Service Implementation
 */
@Service
@AllArgsConstructor
@Slf4j
public class SupabaseContentServiceImpl implements SupabaseContentService {

    private final RestTemplate restTemplate;
    private final SupabaseConfig supabaseConfig;
    private final ContentLibraryDao contentLibraryDao;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public Map<String, Object> fetchContentById(String contentId) {
        try {
            String url = supabaseConfig.getRestApiUrl() + "/content_items?id=eq." + contentId;

            HttpHeaders headers = createHeaders();
            HttpEntity<String> entity = new HttpEntity<>(headers);

            ResponseEntity<List<Map<String, Object>>> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                entity,
                new ParameterizedTypeReference<List<Map<String, Object>>>() {}
            );

            List<Map<String, Object>> items = response.getBody();
            if (items != null && !items.isEmpty()) {
                return items.get(0);
            }

            log.warn("No content found in Supabase for ID: {}", contentId);
            return null;
        } catch (Exception e) {
            log.error("Error fetching content from Supabase for ID: {}", contentId, e);
            return null;
        }
    }

    @Override
    public List<Map<String, Object>> fetchAllContent() {
        try {
            String url = supabaseConfig.getRestApiUrl() + "/content_items?order=created_at.desc";

            HttpHeaders headers = createHeaders();
            HttpEntity<String> entity = new HttpEntity<>(headers);

            ResponseEntity<List<Map<String, Object>>> response = restTemplate.exchange(
                url,
                HttpMethod.GET,
                entity,
                new ParameterizedTypeReference<List<Map<String, Object>>>() {}
            );

            List<Map<String, Object>> items = response.getBody();
            log.info("Fetched {} content items from Supabase", items != null ? items.size() : 0);
            return items;
        } catch (Exception e) {
            log.error("Error fetching all content from Supabase", e);
            return List.of();
        }
    }

    @Override
    @Transactional
    public void syncContentToLocal(String contentId) {
        Map<String, Object> content = fetchContentById(contentId);
        if (content != null) {
            saveContentToLocal(content);
        }
    }

    @Override
    @Transactional
    public void syncAllContentToLocal() {
        List<Map<String, Object>> allContent = fetchAllContent();
        log.info("Starting sync of {} content items to local database", allContent.size());

        int synced = 0;
        for (Map<String, Object> content : allContent) {
            try {
                saveContentToLocal(content);
                synced++;
            } catch (Exception e) {
                log.error("Error syncing content item: {}", content.get("id"), e);
            }
        }

        log.info("Successfully synced {} out of {} content items", synced, allContent.size());
    }

    private void saveContentToLocal(Map<String, Object> content) {
        String id = (String) content.get("id");

        // Check if content already exists
        ContentLibraryEntity existing = contentLibraryDao.selectById(id);
        if (existing != null) {
            // Update existing content
            updateContentEntity(existing, content);
            contentLibraryDao.updateById(existing);
            log.debug("Updated content in local database: {}", id);
        } else {
            // Create new content
            ContentLibraryEntity newEntity = createContentEntity(content);
            contentLibraryDao.insert(newEntity);
            log.debug("Added new content to local database: {}", id);
        }
    }

    private ContentLibraryEntity createContentEntity(Map<String, Object> content) {
        ContentLibraryEntity entity = new ContentLibraryEntity();
        entity.setId((String) content.get("id"));
        entity.setTitle((String) content.get("title"));
        entity.setRomanized((String) content.get("romanized"));
        entity.setFilename((String) content.get("filename"));
        entity.setContentType((String) content.get("content_type"));
        entity.setCategory((String) content.get("category"));

        // Convert alternatives array to JSON string
        List<String> alternatives = (List<String>) content.get("alternatives");
        if (alternatives != null) {
            try {
                entity.setAlternatives(objectMapper.writeValueAsString(alternatives));
            } catch (Exception e) {
                log.warn("Error converting alternatives to JSON", e);
                entity.setAlternatives("[]");
            }
        } else {
            entity.setAlternatives("[]");
        }

        entity.setAwsS3Url((String) content.get("file_url"));

        // Handle duration_seconds which might be Integer
        Object duration = content.get("duration_seconds");
        if (duration != null) {
            entity.setDurationSeconds(duration instanceof Integer ? (Integer) duration : Integer.parseInt(duration.toString()));
        }

        entity.setIsActive(1); // Default to active
        entity.setCreatedAt(new Date());
        entity.setUpdatedAt(new Date());

        return entity;
    }

    private void updateContentEntity(ContentLibraryEntity entity, Map<String, Object> content) {
        entity.setTitle((String) content.get("title"));
        entity.setRomanized((String) content.get("romanized"));
        entity.setFilename((String) content.get("filename"));
        entity.setContentType((String) content.get("content_type"));
        entity.setCategory((String) content.get("category"));

        // Convert alternatives array to JSON string
        List<String> alternatives = (List<String>) content.get("alternatives");
        if (alternatives != null) {
            try {
                entity.setAlternatives(objectMapper.writeValueAsString(alternatives));
            } catch (Exception e) {
                log.warn("Error converting alternatives to JSON", e);
            }
        }

        entity.setAwsS3Url((String) content.get("file_url"));

        // Handle duration_seconds
        Object duration = content.get("duration_seconds");
        if (duration != null) {
            entity.setDurationSeconds(duration instanceof Integer ? (Integer) duration : Integer.parseInt(duration.toString()));
        }

        entity.setUpdatedAt(new Date());
    }

    private HttpHeaders createHeaders() {
        HttpHeaders headers = new HttpHeaders();
        headers.set("apikey", supabaseConfig.getServiceKey());
        headers.set("Authorization", "Bearer " + supabaseConfig.getServiceKey());
        headers.set("Content-Type", "application/json");
        return headers;
    }
}