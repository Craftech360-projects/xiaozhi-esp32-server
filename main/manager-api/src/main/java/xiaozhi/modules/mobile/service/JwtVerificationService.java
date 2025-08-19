package xiaozhi.modules.mobile.service;

import io.jsonwebtoken.*;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import xiaozhi.modules.mobile.config.SupabaseJwtConfig;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.Map;

/**
 * JWT Verification Service
 * Handles verification of Supabase JWT tokens
 */
@Service
@Slf4j
public class JwtVerificationService {
    
    @Autowired
    private SupabaseJwtConfig supabaseConfig;
    
    private SecretKey getSigningKey() {
        // Use the JWT secret from Supabase dashboard
        String secret = supabaseConfig.getJwt().getSecret();
        if (secret == null || secret.isEmpty() || secret.equals("your-supabase-jwt-secret")) {
            // Default secret for development - MUST be changed in production
            log.warn("Using default JWT secret - this is not secure for production!");
            secret = "your-super-secret-jwt-key-from-supabase-dashboard";
        }
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }
    
    /**
     * Verify and parse JWT token
     * @param token JWT token string
     * @return Claims if valid, null if invalid
     */
    public Claims verifyToken(String token) {
        if (!supabaseConfig.isJwtVerificationEnabled()) {
            log.warn("JWT verification is disabled - accepting all tokens");
            return Jwts.claims().build();
        }
        
        try {
            // Remove "Bearer " prefix if present
            if (token.startsWith("Bearer ")) {
                token = token.substring(7);
            }
            
            JwtParser parser = Jwts.parser()
                .verifyWith(getSigningKey())
                .build();
            
            Jws<Claims> claimsJws = parser.parseSignedClaims(token);
            Claims claims = claimsJws.getPayload();
            
            // Verify token is not expired
            Date expiration = claims.getExpiration();
            if (expiration != null && expiration.before(new Date())) {
                log.error("Token has expired");
                return null;
            }
            
            log.debug("Token verified successfully for user: {}", claims.getSubject());
            return claims;
            
        } catch (ExpiredJwtException e) {
            log.error("JWT token has expired: {}", e.getMessage());
        } catch (UnsupportedJwtException e) {
            log.error("Unsupported JWT token: {}", e.getMessage());
        } catch (MalformedJwtException e) {
            log.error("Malformed JWT token: {}", e.getMessage());
        } catch (SecurityException e) {
            log.error("Invalid JWT signature: {}", e.getMessage());
        } catch (IllegalArgumentException e) {
            log.error("JWT token is invalid: {}", e.getMessage());
        } catch (Exception e) {
            log.error("Error verifying JWT token: {}", e.getMessage());
        }
        
        return null;
    }
    
    /**
     * Extract user ID from JWT claims
     * @param claims JWT claims
     * @return Supabase user ID
     */
    public String getUserId(Claims claims) {
        if (claims == null) {
            return null;
        }
        // Supabase stores user ID in 'sub' claim
        return claims.getSubject();
    }
    
    /**
     * Extract email from JWT claims
     * @param claims JWT claims
     * @return User email
     */
    public String getEmail(Claims claims) {
        if (claims == null) {
            return null;
        }
        return claims.get("email", String.class);
    }
    
    /**
     * Extract user role from JWT claims
     * @param claims JWT claims
     * @return User role
     */
    public String getRole(Claims claims) {
        if (claims == null) {
            return null;
        }
        return claims.get("role", String.class);
    }
    
    /**
     * Extract user metadata from JWT claims
     * @param claims JWT claims
     * @return User metadata map
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getUserMetadata(Claims claims) {
        if (claims == null) {
            return null;
        }
        return (Map<String, Object>) claims.get("user_metadata");
    }
    
    /**
     * Check if token is valid
     * @param token JWT token string
     * @return true if valid, false otherwise
     */
    public boolean isTokenValid(String token) {
        return verifyToken(token) != null;
    }
    
    /**
     * Get user ID directly from token
     * @param token JWT token string
     * @return User ID or null if invalid
     */
    public String getUserIdFromToken(String token) {
        Claims claims = verifyToken(token);
        return getUserId(claims);
    }
}