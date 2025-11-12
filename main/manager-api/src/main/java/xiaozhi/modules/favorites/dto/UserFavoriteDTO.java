package xiaozhi.modules.favorites.dto;

import java.io.Serializable;
import java.util.Date;

import com.fasterxml.jackson.annotation.JsonFormat;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * User Favorite Data Transfer Object
 */
@Data
@Schema(description = "User Favorite")
public class UserFavoriteDTO implements Serializable {

    @Schema(description = "Favorite ID")
    private String id;

    @Schema(description = "User ID")
    private String userId;

    @Schema(description = "Content ID")
    private String contentId;

    @Schema(description = "Content Type (music/story)")
    private String contentType;

    @Schema(description = "Created timestamp")
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+5:30")
    private Date createdAt;

    private static final long serialVersionUID = 1L;
}
