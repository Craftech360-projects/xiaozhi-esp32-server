package xiaozhi.modules.mobile.service;

import java.util.Map;

/**
 * Supabase authentication service
 */
public interface SupabaseAuthService {

    /**
     * Validate Supabase JWT token
     */
    boolean validateSupabaseToken(String token);

    /**
     * Verify Supabase JWT token and return user ID
     */
    String validateTokenAndGetUserId(String token) throws SecurityException;

    /**
     * Verify Supabase JWT token and return user ID (legacy method name)
     */
    default String verifyToken(String token) throws SecurityException {
        return validateTokenAndGetUserId(token);
    }

    /**
     * Get token claims
     */
    Map<String, Object> getTokenClaims(String token);

    /**
     * Verify user has access to resource
     */
    boolean verifyUserAccess(String token, String resourceId);

    /**
     * Check if user has admin privileges
     */
    default boolean isAdminUser(String token) {
        // For now, no admin check
        return false;
    }

    /**
     * Get user information from token
     */
    default SupabaseUser getUserFromToken(String token) {
        try {
            String userId = validateTokenAndGetUserId(token);
            return new SupabaseUser(userId, null, null);
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * Supabase user information
     */
    class SupabaseUser {
        private String id;
        private String email;
        private String fullName;

        // Constructors
        public SupabaseUser() {}

        public SupabaseUser(String id, String email, String fullName) {
            this.id = id;
            this.email = email;
            this.fullName = fullName;
        }

        // Getters and setters
        public String getId() { return id; }
        public void setId(String id) { this.id = id; }

        public String getEmail() { return email; }
        public void setEmail(String email) { this.email = email; }

        public String getFullName() { return fullName; }
        public void setFullName(String fullName) { this.fullName = fullName; }
    }
}