package xiaozhi.modules.favorites.controller;

import java.util.List;
import java.util.Set;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.content.dto.ContentLibraryDTO;
import xiaozhi.modules.favorites.service.UserFavoriteService;

/**
 * User Favorites REST API Controller
 * Handles user favorites operations for music and stories
 */
@RestController
@RequestMapping("/favorites")
@AllArgsConstructor
@Slf4j
@Tag(name = "User Favorites", description = "User Favorites Management for Music and Stories")
public class UserFavoriteController {

    private final UserFavoriteService userFavoriteService;

    @GetMapping
    @Operation(summary = "Get user's favorites", description = "Retrieves user's favorited content with optional type filter")
    public Result<List<ContentLibraryDTO>> getFavorites(
            @Parameter(description = "User ID", required = true) @RequestParam String userId,
            @Parameter(description = "Content type filter (music or story)") @RequestParam(required = false) String contentType) {

        try {
            List<ContentLibraryDTO> favorites = userFavoriteService.getFavoritesWithContent(userId, contentType);
            return new Result<List<ContentLibraryDTO>>().ok(favorites);
        } catch (Exception e) {
            log.error("Error getting favorites for user {}: {}", userId, e.getMessage(), e);
            return new Result<List<ContentLibraryDTO>>().error(e.getMessage());
        }
    }

    @PostMapping
    @Operation(summary = "Add content to favorites", description = "Adds a content item to user's favorites")
    public Result<String> addFavorite(@RequestBody AddFavoriteRequest request) {
        try {
            String favoriteId = userFavoriteService.addFavorite(
                request.getUserId(),
                request.getContentId(),
                request.getContentType()
            );
            return new Result<String>().ok(favoriteId);
        } catch (Exception e) {
            log.error("Error adding favorite for user {}: {}", request.getUserId(), e.getMessage(), e);
            return new Result<String>().error(e.getMessage());
        }
    }

    @DeleteMapping("/{contentId}")
    @Operation(summary = "Remove content from favorites", description = "Removes a content item from user's favorites")
    public Result<Boolean> removeFavorite(
            @Parameter(description = "Content ID to remove", required = true) @PathVariable String contentId,
            @Parameter(description = "User ID", required = true) @RequestParam String userId) {

        try {
            boolean removed = userFavoriteService.removeFavorite(userId, contentId);
            if (removed) {
                return new Result<Boolean>().ok(true);
            } else {
                return new Result<Boolean>().error("Favorite not found");
            }
        } catch (Exception e) {
            log.error("Error removing favorite for user {}: {}", userId, e.getMessage(), e);
            return new Result<Boolean>().error(e.getMessage());
        }
    }

    @GetMapping("/check")
    @Operation(summary = "Check if content is favorited", description = "Checks if a content item is in user's favorites")
    public Result<Boolean> checkFavorite(
            @Parameter(description = "User ID", required = true) @RequestParam String userId,
            @Parameter(description = "Content ID", required = true) @RequestParam String contentId) {

        try {
            boolean isFavorited = userFavoriteService.isFavorited(userId, contentId);
            return new Result<Boolean>().ok(isFavorited);
        } catch (Exception e) {
            log.error("Error checking favorite for user {}: {}", userId, e.getMessage(), e);
            return new Result<Boolean>().error(e.getMessage());
        }
    }

    @PostMapping("/check-batch")
    @Operation(summary = "Batch check favorites", description = "Checks which content items are favorited by user")
    public Result<Set<String>> checkBatchFavorites(@RequestBody CheckBatchRequest request) {
        try {
            Set<String> favoritedIds = userFavoriteService.checkBatchFavorites(
                request.getUserId(),
                request.getContentIds()
            );
            return new Result<Set<String>>().ok(favoritedIds);
        } catch (Exception e) {
            log.error("Error batch checking favorites for user {}: {}", request.getUserId(), e.getMessage(), e);
            return new Result<Set<String>>().error(e.getMessage());
        }
    }

    @GetMapping("/count")
    @Operation(summary = "Get favorites count", description = "Returns the number of favorites for a user")
    public Result<Integer> getFavoritesCount(
            @Parameter(description = "User ID", required = true) @RequestParam String userId,
            @Parameter(description = "Content type filter (music or story)") @RequestParam(required = false) String contentType) {

        try {
            int count = userFavoriteService.getFavoritesCount(userId, contentType);
            return new Result<Integer>().ok(count);
        } catch (Exception e) {
            log.error("Error getting favorites count for user {}: {}", userId, e.getMessage(), e);
            return new Result<Integer>().error(e.getMessage());
        }
    }

    /**
     * Request DTO for adding a favorite
     */
    @Data
    public static class AddFavoriteRequest {
        @Parameter(description = "User ID", required = true)
        private String userId;

        @Parameter(description = "Content ID", required = true)
        private String contentId;

        @Parameter(description = "Content type (music or story)", required = true)
        private String contentType;
    }

    /**
     * Request DTO for batch checking favorites
     */
    @Data
    public static class CheckBatchRequest {
        @Parameter(description = "User ID", required = true)
        private String userId;

        @Parameter(description = "List of content IDs to check", required = true)
        private List<String> contentIds;
    }
}
