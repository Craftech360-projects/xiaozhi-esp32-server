package xiaozhi.modules.mobile.service;

/**
 * Supabase authentication service
 */
public interface SupabaseAuthService {

    /**
     * Verify Supabase JWT token and return user ID
     */
    String verifyToken(String token) throws SecurityException;

    /**
     * Check if user has admin privileges
     */
    boolean isAdminUser(String token);

    /**
     * Get user information from token
     */
    SupabaseUser getUserFromToken(String token);

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