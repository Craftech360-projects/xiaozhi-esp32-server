package xiaozhi.modules.config.service;

import xiaozhi.modules.config.dto.LiveKitChatDataDTO;
import java.util.List;
import java.util.Map;

/**
 * LiveKit Chat Service Interface
 * Service for fetching chat data from LiveKit server and storing to MySQL
 *
 * @author Claude Code
 * @version 1.0
 * @since 1.0.0
 */
public interface LiveKitChatService {

    /**
     * Fetch chat data from LiveKit server for a specific agent
     *
     * @param agentId The agent ID to fetch chat data for
     * @param sessionId The session ID (optional)
     * @return List of chat data from LiveKit
     */
    List<LiveKitChatDataDTO> fetchChatDataFromLiveKit(String agentId, String sessionId);

    /**
     * Store LiveKit chat data to MySQL with agent binding
     *
     * @param chatDataList List of chat data to store
     * @param agentId The agent ID to bind the chat data to
     * @return Success status
     */
    boolean storeChatDataToMySQL(List<LiveKitChatDataDTO> chatDataList, String agentId);

    /**
     * Fetch and store chat data in one operation
     *
     * @param agentId The agent ID
     * @param sessionId The session ID (optional)
     * @return Success status
     */
    boolean syncChatDataFromLiveKit(String agentId, String sessionId);

    /**
     * Get chat history from MySQL for specific agent
     *
     * @param agentId The agent ID
     * @param sessionId The session ID (optional)
     * @return Chat history data including sessions and messages
     */
    Map<String, Object> getChatHistoryFromMySQL(String agentId, String sessionId);
}