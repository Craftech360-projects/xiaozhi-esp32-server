package xiaozhi.modules.favorites.dao;

import java.util.List;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;

import xiaozhi.modules.favorites.entity.UserFavoriteEntity;

/**
 * User Favorite Data Access Object
 * Handles database operations for user favorites
 */
@Mapper
public interface UserFavoriteDao extends BaseMapper<UserFavoriteEntity> {

    /**
     * Get user's favorites by content type
     * @param userId User ID
     * @param contentType Content type (music or story)
     * @return List of favorite entities
     */
    List<UserFavoriteEntity> getFavoritesByUserAndType(
        @Param("userId") String userId,
        @Param("contentType") String contentType
    );

    /**
     * Check if content is favorited by user
     * @param userId User ID
     * @param contentId Content ID
     * @return Favorite entity if exists, null otherwise
     */
    UserFavoriteEntity findByUserAndContent(
        @Param("userId") String userId,
        @Param("contentId") String contentId
    );

    /**
     * Batch check if multiple content items are favorited
     * @param userId User ID
     * @param contentIds List of content IDs
     * @return List of favorited content IDs
     */
    List<String> checkBatchFavorites(
        @Param("userId") String userId,
        @Param("contentIds") List<String> contentIds
    );

    /**
     * Get user's favorites count by type
     * @param userId User ID
     * @param contentType Content type (music or story), null for all
     * @return Count of favorites
     */
    int getFavoritesCount(
        @Param("userId") String userId,
        @Param("contentType") String contentType
    );

    /**
     * Delete favorite by user and content
     * @param userId User ID
     * @param contentId Content ID
     * @return Number of deleted records
     */
    int deleteByUserAndContent(
        @Param("userId") String userId,
        @Param("contentId") String contentId
    );
}
