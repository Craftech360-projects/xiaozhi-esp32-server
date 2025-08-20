package xiaozhi.modules.mobile.service.impl;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import xiaozhi.modules.mobile.service.SupabaseAuthService;

import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

@Service
public class SupabaseAuthServiceImpl implements SupabaseAuthService {

    private static final Logger logger = LoggerFactory.getLogger(SupabaseAuthServiceImpl.class);

    @Value("${supabase.jwt.secret:your-supabase-jwt-secret}")
    private String supabaseJwtSecret;

    @Value("${supabase.url:https://popppjirsdedxhetcphs.supabase.co}")
    private String supabaseUrl;

    @Value("${supabase.anon.key:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBvcHBwamlyc2RlZHhoZXRjcGhzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDM3NjMxMDAsImV4cCI6MjA1OTMzOTEwMH0.Ihv60cbfUSeDN5dPDsOZRz4y79ek3D5YZZgKwBsMkSc}")
    private String supabaseAnonKey;

    @Override
    public boolean validateSupabaseToken(String token) {
        try {
            // For development, we'll do basic validation
            // In production, you should verify against Supabase's public key

            // Basic JWT structure check
            String[] parts = token.split("\\.");
            if (parts.length != 3) {
                logger.warn("Invalid JWT structure");
                return false;
            }

            // Decode payload
            String payload = new String(Base64.getUrlDecoder().decode(parts[1]));

            // Check if token contains supabase issuer
            if (!payload.contains("supabase")) {
                logger.warn("Token is not from Supabase");
                return false;
            }

            // For testing, accept any properly structured token
            // In production, verify signature with Supabase JWT secret
            return true;

        } catch (Exception e) {
            logger.error("Error validating Supabase token", e);
            return false;
        }
    }

    @Override
    public String validateTokenAndGetUserId(String token) throws SecurityException {
        try {
            if (!validateSupabaseToken(token)) {
                throw new SecurityException("Invalid or expired token");
            }

            // Parse JWT payload to get user ID
            String[] parts = token.split("\\.");
            String payload = new String(Base64.getUrlDecoder().decode(parts[1]));

            // Simple JSON parsing for sub claim
            // In production, use a proper JSON parser
            int subIndex = payload.indexOf("\"sub\":\"");
            if (subIndex == -1) {
                // For testing, return a test user ID
                logger.debug("No sub claim found, using test user ID");
                return "test-supabase-user-001";
            }

            subIndex += 7; // Length of "sub":"
            int endIndex = payload.indexOf("\"", subIndex);
            String userId = payload.substring(subIndex, endIndex);

            logger.debug("Token validated for user: {}", userId);
            return userId;

        } catch (Exception e) {
            logger.error("Error extracting user ID from token", e);
            throw new SecurityException("Failed to validate token", e);
        }
    }

    @Override
    public Map<String, Object> getTokenClaims(String token) {
        try {
            Map<String, Object> claims = new HashMap<>();

            String[] parts = token.split("\\.");
            if (parts.length != 3) {
                return claims;
            }

            String payload = new String(Base64.getUrlDecoder().decode(parts[1]));

            // Simple parsing for common claims
            claims.put("payload", payload);

            return claims;

        } catch (Exception e) {
            logger.error("Error getting token claims", e);
            return new HashMap<>();
        }
    }

    @Override
    public boolean verifyUserAccess(String token, String resourceId) {
        try {
            String userId = validateTokenAndGetUserId(token);

            // Here you would check if the user has access to the specific resource
            // For now, we'll return true if the token is valid
            return userId != null && !userId.isEmpty();

        } catch (Exception e) {
            logger.error("Error verifying user access", e);
            return false;
        }
    }
}