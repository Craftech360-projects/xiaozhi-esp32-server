package xiaozhi.modules.favorites.service.impl;

import java.util.Arrays;
import java.util.Collections;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.exception.RenException;
import xiaozhi.modules.content.dao.ContentLibraryDao;
import xiaozhi.modules.content.dto.ContentLibraryDTO;
import xiaozhi.modules.content.entity.ContentLibraryEntity;
import xiaozhi.modules.content.service.SupabaseContentService;
import xiaozhi.modules.favorites.dao.UserFavoriteDao;
import xiaozhi.modules.favorites.entity.UserFavoriteEntity;
import xiaozhi.modules.favorites.service.UserFavoriteService;

/**
 * User Favorite Service Implementation
 */
@Service
@AllArgsConstructor
@Slf4j
public class UserFavoriteServiceImpl implements UserFavoriteService {

    private final UserFavoriteDao userFavoriteDao;
    private final ContentLibraryDao contentLibraryDao;
    private final SupabaseContentService supabaseContentService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public List<ContentLibraryDTO> getFavoritesWithContent(String userId, String contentType) {
        if (userId == null || userId.trim().isEmpty()) {
            throw new RenException("User ID cannot be empty");
        }

        // Get user's favorites
        List<UserFavoriteEntity> favorites = userFavoriteDao.getFavoritesByUserAndType(userId, contentType);

        if (favorites.isEmpty()) {
            return List.of();
        }

        // Extract content IDs
        List<String> contentIds = favorites.stream()
                .map(UserFavoriteEntity::getContentId)
                .collect(Collectors.toList());

        // Fetch content details
        List<ContentLibraryEntity> contentEntities = contentLibraryDao.selectBatchIds(contentIds);

        // Convert to DTOs and maintain the order of favorites
        return favorites.stream()
                .map(favorite -> {
                    ContentLibraryEntity content = contentEntities.stream()
                            .filter(c -> c.getId().equals(favorite.getContentId()))
                            .findFirst()
                            .orElse(null);

                    if (content == null) {
                        log.warn("Content not found in library for favorite: {}, attempting to sync from Supabase", favorite.getContentId());
                        // Try to sync from Supabase
                        try {
                            supabaseContentService.syncContentToLocal(favorite.getContentId());
                            // Try to fetch again after sync
                            content = contentLibraryDao.selectById(favorite.getContentId());
                        } catch (Exception e) {
                            log.error("Error syncing content from Supabase: {}", favorite.getContentId(), e);
                        }

                        if (content == null) {
                            // If still not found, create a placeholder
                            log.warn("Content still not found after sync attempt, creating placeholder");
                            ContentLibraryDTO placeholder = new ContentLibraryDTO();
                            placeholder.setId(favorite.getContentId());
                            placeholder.setTitle("Content " + favorite.getContentId().substring(0, 8));
                            placeholder.setContentType(favorite.getContentType());
                            placeholder.setCategory("Unknown");
                            placeholder.setIsActive(true);
                            return placeholder;
                        }
                    }

                    return convertToDTO(content);
                })
                .collect(Collectors.toList());
    }

    @Override
    @Transactional
    public String addFavorite(String userId, String contentId, String contentType) {
        if (userId == null || userId.trim().isEmpty()) {
            throw new RenException("User ID cannot be empty");
        }
        if (contentId == null || contentId.trim().isEmpty()) {
            throw new RenException("Content ID cannot be empty");
        }
        if (contentType == null || contentType.trim().isEmpty()) {
            throw new RenException("Content type cannot be empty");
        }

        // Validate content type
        try {
            UserFavoriteEntity.ContentType.fromValue(contentType);
        } catch (IllegalArgumentException e) {
            throw new RenException("Invalid content type: " + contentType);
        }

        // Check if already favorited
        UserFavoriteEntity existing = userFavoriteDao.findByUserAndContent(userId, contentId);
        if (existing != null) {
            log.info("Content already favorited by user: userId={}, contentId={}", userId, contentId);
            return existing.getId();
        }

        // Verify content exists (skip if content_library is not populated)
        try {
            ContentLibraryEntity content = contentLibraryDao.selectById(contentId);
            if (content == null) {
                log.warn("Content not found in library, but allowing favorite: " + contentId);
                // Continue without verification in dev mode
            }
        } catch (Exception e) {
            log.warn("Could not verify content existence, continuing: " + e.getMessage());
            // Continue without verification if content_library table issues
        }

        // Create favorite
        UserFavoriteEntity favorite = new UserFavoriteEntity();
        favorite.setId(UUID.randomUUID().toString());
        favorite.setUserId(userId);
        favorite.setContentId(contentId);
        favorite.setContentType(contentType);
        favorite.setCreatedAt(new Date());

        int result = userFavoriteDao.insert(favorite);
        if (result > 0) {
            log.info("Favorite added: userId={}, contentId={}, type={}", userId, contentId, contentType);
            return favorite.getId();
        } else {
            throw new RenException("Failed to add favorite");
        }
    }

    @Override
    @Transactional
    public boolean removeFavorite(String userId, String contentId) {
        if (userId == null || userId.trim().isEmpty()) {
            throw new RenException("User ID cannot be empty");
        }
        if (contentId == null || contentId.trim().isEmpty()) {
            throw new RenException("Content ID cannot be empty");
        }

        int result = userFavoriteDao.deleteByUserAndContent(userId, contentId);
        if (result > 0) {
            log.info("Favorite removed: userId={}, contentId={}", userId, contentId);
            return true;
        } else {
            log.warn("Favorite not found: userId={}, contentId={}", userId, contentId);
            return false;
        }
    }

    @Override
    public boolean isFavorited(String userId, String contentId) {
        if (userId == null || userId.trim().isEmpty() || contentId == null || contentId.trim().isEmpty()) {
            return false;
        }

        UserFavoriteEntity favorite = userFavoriteDao.findByUserAndContent(userId, contentId);
        return favorite != null;
    }

    @Override
    public Set<String> checkBatchFavorites(String userId, List<String> contentIds) {
        if (userId == null || userId.trim().isEmpty() || contentIds == null || contentIds.isEmpty()) {
            return new HashSet<>();
        }

        List<String> favoritedIds = userFavoriteDao.checkBatchFavorites(userId, contentIds);
        return new HashSet<>(favoritedIds);
    }

    @Override
    public int getFavoritesCount(String userId, String contentType) {
        if (userId == null || userId.trim().isEmpty()) {
            return 0;
        }

        return userFavoriteDao.getFavoritesCount(userId, contentType);
    }

    /**
     * Convert ContentLibraryEntity to DTO
     */
    private ContentLibraryDTO convertToDTO(ContentLibraryEntity entity) {
        if (entity == null) {
            return null;
        }

        ContentLibraryDTO dto = new ContentLibraryDTO();
        dto.setId(entity.getId());
        dto.setTitle(entity.getTitle());
        dto.setRomanized(entity.getRomanized());
        dto.setFilename(entity.getFilename());
        dto.setContentType(entity.getContentType());
        dto.setCategory(entity.getCategory());

        // Parse alternatives JSON string to List<String>
        dto.setAlternatives(parseAlternatives(entity.getAlternatives()));

        dto.setAwsS3Url(entity.getAwsS3Url());
        dto.setDurationSeconds(entity.getDurationSeconds());
        dto.setFileSizeBytes(entity.getFileSizeBytes());

        // Convert Integer (0/1) to Boolean
        dto.setIsActive(entity.getIsActive() != null && entity.getIsActive() == 1);

        return dto;
    }

    /**
     * Parse alternatives JSON string to List
     */
    private List<String> parseAlternatives(String alternativesJson) {
        if (alternativesJson == null || alternativesJson.trim().isEmpty()) {
            return Collections.emptyList();
        }

        try {
            return objectMapper.readValue(alternativesJson, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            log.warn("Failed to parse alternatives JSON: {}", alternativesJson, e);
            return Collections.emptyList();
        }
    }
}
