package xiaozhi.modules.mobile.controller;

import xiaozhi.common.annotation.LogOperation;
import xiaozhi.common.utils.Result;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.Operation;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.*;
import xiaozhi.modules.mobile.service.SupabaseAuthService;

import java.text.SimpleDateFormat;
import java.util.*;

@RestController
@RequestMapping("/api/mobile/dashboard")
@Tag(name = "Mobile Dashboard API")
public class MobileDashboardController {
    
    private static final Logger logger = LoggerFactory.getLogger(MobileDashboardController.class);
    
    @Autowired
    private JdbcTemplate jdbcTemplate;
    
    @Autowired
    private SupabaseAuthService supabaseAuthService;
    
    @GetMapping("/{activationId}")
    @Operation(summary = "Get dashboard summary for a device")
    @LogOperation("Get dashboard summary")
    public Result getDashboardSummary(
            @PathVariable String activationId,
            @RequestHeader("Authorization") String authHeader) {
        
        try {
            // Extract and validate JWT token
            String token = authHeader.replace("Bearer ", "");
            String supabaseUserId = supabaseAuthService.validateTokenAndGetUserId(token);
            
            logger.info("Getting dashboard summary for activation: {} by user: {}", activationId, supabaseUserId);
            
            // Call stored procedure
            List<Map<String, Object>> results = jdbcTemplate.queryForList(
                "CALL GetMobileDashboardSummary(?, CURDATE())",
                supabaseUserId
            );
            
            if (results.isEmpty()) {
                return new Result().error("No data found for this activation");
            }
            
            Map<String, Object> dashboardData = results.get(0);
            
            // Build response
            Map<String, Object> response = new HashMap<>();
            
            // Child info
            Map<String, Object> childInfo = new HashMap<>();
            childInfo.put("name", dashboardData.get("child_name"));
            childInfo.put("age", dashboardData.get("child_age"));
            childInfo.put("device_online", dashboardData.get("is_online"));
            childInfo.put("last_activity", dashboardData.get("last_seen"));
            response.put("child_info", childInfo);
            
            // Today's summary
            Map<String, Object> todaySummary = new HashMap<>();
            todaySummary.put("conversations", dashboardData.get("today_conversations"));
            todaySummary.put("duration_minutes", dashboardData.get("today_duration"));
            todaySummary.put("mood", calculateMoodLabel(dashboardData.get("today_mood")));
            todaySummary.put("mood_score", dashboardData.get("today_mood"));
            todaySummary.put("engagement_level", dashboardData.get("engagement_level"));
            response.put("today_summary", todaySummary);
            
            // Week summary
            Map<String, Object> weekSummary = getWeekSummary(activationId, supabaseUserId);
            response.put("week_summary", weekSummary);
            
            // Recent achievement
            if (dashboardData.get("recent_achievement") != null) {
                Map<String, Object> achievement = new HashMap<>();
                achievement.put("milestone_name", dashboardData.get("recent_achievement"));
                achievement.put("achieved_at", new Date());
                achievement.put("description", "Great progress!");
                response.put("recent_achievement", achievement);
            }
            
            // Highlights and recommendations
            response.put("highlights", getHighlights(activationId));
            response.put("concerns", new ArrayList<>());
            response.put("recommendations", getRecommendations());
            
            return new Result().ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting dashboard summary", e);
            return new Result().error("Failed to get dashboard summary");
        }
    }
    
    @GetMapping("/{activationId}/weekly")
    @Operation(summary = "Get weekly analytics")
    @LogOperation("Get weekly analytics")
    public Result getWeeklyAnalytics(
            @PathVariable String activationId,
            @RequestHeader("Authorization") String authHeader,
            @RequestParam(required = false) String weekStart) {
        
        try {
            String token = authHeader.replace("Bearer ", "");
            String supabaseUserId = supabaseAuthService.validateTokenAndGetUserId(token);
            
            logger.info("Getting weekly analytics for activation: {}", activationId);
            
            // Get analytics from stored procedure
            List<Map<String, Object>> results = jdbcTemplate.queryForList(
                "CALL GetMobileAnalyticsSummary(?, 'weekly', DATE_SUB(CURDATE(), INTERVAL WEEKDAY(CURDATE()) DAY), CURDATE())",
                supabaseUserId
            );
            
            Map<String, Object> response = new HashMap<>();
            
            if (!results.isEmpty()) {
                Map<String, Object> weekData = results.get(0);
                response.put("week_start_date", weekData.get("week_start_date"));
                response.put("week_end_date", weekData.get("week_end_date"));
                
                Map<String, Object> summary = new HashMap<>();
                summary.put("total_conversations", weekData.get("total_conversations"));
                summary.put("total_duration_minutes", weekData.get("total_duration_minutes"));
                summary.put("average_daily_engagement", weekData.get("average_daily_engagement"));
                summary.put("engagement_trend", weekData.get("engagement_trend"));
                response.put("summary", summary);
                
                response.put("weekly_insights", weekData.get("weekly_summary"));
                response.put("achievements", weekData.get("achievements"));
            }
            
            return new Result().ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting weekly analytics", e);
            return new Result().error("Failed to get weekly analytics");
        }
    }
    
    @GetMapping("/{activationId}/daily")
    @Operation(summary = "Get daily analytics")
    @LogOperation("Get daily analytics")
    public Result getDailyAnalytics(
            @PathVariable String activationId,
            @RequestHeader("Authorization") String authHeader,
            @RequestParam(required = false) String date) {
        
        try {
            String token = authHeader.replace("Bearer ", "");
            String supabaseUserId = supabaseAuthService.validateTokenAndGetUserId(token);
            
            logger.info("Getting daily analytics for activation: {} on date: {}", activationId, date);
            
            String targetDate = date != null ? date : new SimpleDateFormat("yyyy-MM-dd").format(new Date());
            
            // Get analytics from stored procedure
            List<Map<String, Object>> results = jdbcTemplate.queryForList(
                "CALL GetMobileAnalyticsSummary(?, 'daily', ?, ?)",
                supabaseUserId, targetDate, targetDate
            );
            
            Map<String, Object> response = new HashMap<>();
            
            if (!results.isEmpty()) {
                Map<String, Object> dayData = results.get(0);
                response.put("date", dayData.get("date"));
                
                Map<String, Object> summary = new HashMap<>();
                summary.put("total_conversations", dayData.get("total_conversations"));
                summary.put("duration_minutes", dayData.get("total_duration_minutes"));
                summary.put("overall_sentiment", dayData.get("overall_sentiment"));
                summary.put("topics_discussed", dayData.get("topics_discussed"));
                summary.put("new_words_learned", dayData.get("new_words_count"));
                summary.put("engagement_level", dayData.get("engagement_level"));
                response.put("summary", summary);
                
                response.put("ai_insights", dayData.get("ai_summary"));
                response.put("key_highlights", dayData.get("key_highlights"));
                response.put("parent_recommendations", dayData.get("parent_recommendations"));
            }
            
            return new Result().ok(response);
            
        } catch (Exception e) {
            logger.error("Error getting daily analytics", e);
            return new Result().error("Failed to get daily analytics");
        }
    }
    
    private Map<String, Object> getWeekSummary(String activationId, String supabaseUserId) {
        Map<String, Object> weekSummary = new HashMap<>();
        
        try {
            // Get week totals
            String sql = "SELECT COUNT(*) as total_conversations, " +
                        "COALESCE(SUM(total_duration_minutes), 0) as total_minutes " +
                        "FROM analytics_summary_daily asd " +
                        "JOIN parent_child_mapping pcm ON asd.parent_child_mapping_id = pcm.id " +
                        "WHERE pcm.supabase_user_id = ? " +
                        "AND asd.summary_date >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)";
            
            Map<String, Object> weekData = jdbcTemplate.queryForMap(sql, supabaseUserId);
            
            weekSummary.put("total_conversations", weekData.get("total_conversations"));
            weekSummary.put("average_daily_minutes", 
                ((Number) weekData.get("total_minutes")).intValue() / 7);
            weekSummary.put("consistency_score", 0.85);
            weekSummary.put("trend", "stable");
            
        } catch (Exception e) {
            logger.warn("Could not get week summary", e);
            weekSummary.put("total_conversations", 0);
            weekSummary.put("average_daily_minutes", 0);
            weekSummary.put("consistency_score", 0);
            weekSummary.put("trend", "unknown");
        }
        
        return weekSummary;
    }
    
    private String calculateMoodLabel(Object moodScore) {
        if (moodScore == null) return "neutral";
        
        double score = ((Number) moodScore).doubleValue();
        if (score >= 0.5) return "happy";
        if (score >= 0) return "neutral";
        return "sad";
    }
    
    private List<String> getHighlights(String activationId) {
        List<String> highlights = new ArrayList<>();
        highlights.add("Great engagement with educational content today");
        highlights.add("Showed curiosity about new topics");
        return highlights;
    }
    
    private List<String> getRecommendations() {
        List<String> recommendations = new ArrayList<>();
        recommendations.add("Try exploring more math concepts");
        recommendations.add("Continue with animal-themed conversations");
        return recommendations;
    }
}