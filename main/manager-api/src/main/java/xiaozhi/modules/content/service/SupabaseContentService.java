package xiaozhi.modules.content.service;

import java.util.List;
import java.util.Map;

/**
 * Supabase Content Service Interface
 * Fetches content from Supabase and syncs to local database
 */
public interface SupabaseContentService {

    /**
     * Fetch content item by ID from Supabase
     */
    Map<String, Object> fetchContentById(String contentId);

    /**
     * Fetch all content items from Supabase
     */
    List<Map<String, Object>> fetchAllContent();

    /**
     * Sync content from Supabase to local MySQL database
     */
    void syncContentToLocal(String contentId);

    /**
     * Sync all content from Supabase to local MySQL database
     */
    void syncAllContentToLocal();
}