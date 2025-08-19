package xiaozhi.modules.mobile.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import lombok.Data;

/**
 * Supabase JWT Configuration
 * Holds the configuration for verifying Supabase JWT tokens
 */
@Configuration
@ConfigurationProperties(prefix = "supabase")
@Data
public class SupabaseJwtConfig {
    
    /**
     * Supabase project URL
     */
    private String url;
    
    /**
     * Anon configuration
     */
    private Anon anon = new Anon();
    
    /**
     * JWT configuration
     */
    private Jwt jwt = new Jwt();
    
    @Data
    public static class Anon {
        private String key;
    }
    
    @Data
    public static class Jwt {
        private String secret;
    }
    
    /**
     * JWT issuer
     */
    private String issuer = "https://nstiqzvkvshqglfqmlxs.supabase.co/auth/v1";
    
    /**
     * Enable/disable JWT verification
     */
    private boolean jwtVerificationEnabled = true;
    
    /**
     * Token expiration tolerance in seconds
     */
    private long expirationTolerance = 60;
}