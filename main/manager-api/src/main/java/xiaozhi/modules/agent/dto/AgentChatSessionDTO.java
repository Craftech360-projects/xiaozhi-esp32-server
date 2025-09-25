package xiaozhi.modules.agent.dto;

import java.util.Date;

import lombok.Data;

/**
 * 智能体会话列表DTO
 */
@Data
public class AgentChatSessionDTO {
    /**
     * 会话ID
     */
    private String sessionId;

    /**
     * 会话时间
     */
    private Date createdAt;

    /**
     * 聊天条数
     */
    private Integer chatCount;
}