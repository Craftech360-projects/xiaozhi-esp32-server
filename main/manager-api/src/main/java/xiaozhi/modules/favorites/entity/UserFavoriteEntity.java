package xiaozhi.modules.favorites.entity;

import java.io.Serializable;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

/**
 * User Favorite Entity
 * Represents user's favorited music and story content
 *
 * @TableName user_favorites
 */
@TableName(value = "user_favorites")
@Data
public class UserFavoriteEntity implements Serializable {
    /**
     * Favorite unique identifier
     */
    @TableId(type = IdType.ASSIGN_UUID)
    private String id;

    /**
     * User ID from Supabase Auth
     */
    private String userId;

    /**
     * Foreign key to content_library.id
     */
    private String contentId;

    /**
     * Type of content: music or story
     */
    private String contentType;

    /**
     * When the favorite was added
     */
    private Date createdAt;

    @TableField(exist = false)
    private static final long serialVersionUID = 1L;

    /**
     * Content Type Enum
     */
    public enum ContentType {
        MUSIC("music"),
        STORY("story");

        private final String value;

        ContentType(String value) {
            this.value = value;
        }

        public String getValue() {
            return value;
        }

        public static ContentType fromValue(String value) {
            for (ContentType type : ContentType.values()) {
                if (type.value.equalsIgnoreCase(value)) {
                    return type;
                }
            }
            throw new IllegalArgumentException("Invalid ContentType value: " + value);
        }
    }
}
