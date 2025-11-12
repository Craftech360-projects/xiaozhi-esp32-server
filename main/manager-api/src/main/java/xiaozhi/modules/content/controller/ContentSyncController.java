package xiaozhi.modules.content.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.content.service.SupabaseContentService;

/**
 * Content Sync Controller
 * Provides endpoints to sync content from Supabase to local MySQL database
 */
@RestController
@RequestMapping("/api/content/sync")
@AllArgsConstructor
@Tag(name = "Content Sync")
@Slf4j
public class ContentSyncController {

    private final SupabaseContentService supabaseContentService;

    @PostMapping("/all")
    @Operation(summary = "Sync all content from Supabase to local database")
    public Result<?> syncAllContent() {
        try {
            log.info("Starting full content sync from Supabase");
            supabaseContentService.syncAllContentToLocal();
            return new Result<>().ok("Content sync completed successfully");
        } catch (Exception e) {
            log.error("Error during content sync", e);
            return new Result<>().error("Content sync failed: " + e.getMessage());
        }
    }

    @PostMapping("/{contentId}")
    @Operation(summary = "Sync specific content item from Supabase to local database")
    public Result<?> syncContent(@PathVariable String contentId) {
        try {
            log.info("Syncing content item: {}", contentId);
            supabaseContentService.syncContentToLocal(contentId);
            return new Result<>().ok("Content item synced successfully");
        } catch (Exception e) {
            log.error("Error syncing content item: {}", contentId, e);
            return new Result<>().error("Content sync failed: " + e.getMessage());
        }
    }
}