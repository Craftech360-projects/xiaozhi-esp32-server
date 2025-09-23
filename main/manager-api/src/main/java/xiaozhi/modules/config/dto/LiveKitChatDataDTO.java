package xiaozhi.modules.config.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * LiveKit Chat Data Transfer Object
 * Represents chat data received from LiveKit server
 *
 * @author Claude Code
 * @version 1.0
 * @since 1.0.0
 */
@Data
@Schema(description = "LiveKit Chat Data Transfer Object")
public class LiveKitChatDataDTO {

    @Schema(description = "Session ID from LiveKit")
    @JsonProperty("session_id")
    private String sessionId;

    @Schema(description = "Message type: user_input_transcribed, speech_created, agent_state_changed")
    @JsonProperty("type")
    private String type;

    @Schema(description = "Message content/transcript")
    @JsonProperty("content")
    private String content;

    @Schema(description = "Speaker/participant identity")
    @JsonProperty("speaker")
    private String speaker;

    @Schema(description = "Timestamp of the message")
    @JsonProperty("timestamp")
    private Long timestamp;

    @Schema(description = "Speech ID for audio messages")
    @JsonProperty("speech_id")
    private String speechId;

    @Schema(description = "Duration in milliseconds for speech messages")
    @JsonProperty("duration_ms")
    private Long durationMs;

    @Schema(description = "Agent ID associated with the chat")
    @JsonProperty("agent_id")
    private String agentId;

    @Schema(description = "MAC address of the device (if available)")
    @JsonProperty("mac_address")
    private String macAddress;

    @Schema(description = "Additional metadata as JSON string")
    @JsonProperty("metadata")
    private String metadata;
}