package xiaozhi.modules.favorites.service;

import java.util.List;
import java.util.Set;

import xiaozhi.modules.content.dto.ContentLibraryDTO;
import xiaozhi.modules.favorites.dto.UserFavoriteDTO;

/**
 * User Favorite Service Interface
 * Handles business logic for user favorites operations
 */
public interface UserFavoriteService {

    /**
     * Get user's favorites with full content details
     * @param userId User ID
     * @param contentType Content type (music or story), null for all
     * @return List of favorites with content details
     */
    List<ContentLibraryDTO> getFavoritesWithContent(String userId, String contentType);

    /**
     * Add content to favorites
     * @param userId User ID
     * @param contentId Content ID
     * @param contentType Content type (music or story)
     * @return Created favorite ID
     */
    String addFavorite(String userId, String contentId, String contentType);

    /**
     * Remove content from favorites
     * @param userId User ID
     * @param contentId Content ID
     * @return Success status
     */
    boolean removeFavorite(String userId, String contentId);

    /**
     * Check if content is favorited by user
     * @param userId User ID
     * @param contentId Content ID
     * @return True if favorited, false otherwise
     */
    boolean isFavorited(String userId, String contentId);

    /**
     * Batch check if multiple contents are favorited
     * @param userId User ID
     * @param contentIds List of content IDs to check
     * @return Set of favorited content IDs
     */
    Set<String> checkBatchFavorites(String userId, List<String> contentIds);

    /**
     * Get user's favorites count
     * @param userId User ID
     * @param contentType Content type filter (music or story), null for all
     * @return Number of favorites
     */
    int getFavoritesCount(String userId, String contentType);
}
