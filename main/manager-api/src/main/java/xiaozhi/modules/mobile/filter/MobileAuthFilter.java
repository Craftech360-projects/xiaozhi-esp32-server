package xiaozhi.modules.mobile.filter;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Claims;
import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.mobile.service.JwtVerificationService;

import java.io.IOException;
import java.io.PrintWriter;
import java.util.Arrays;
import java.util.List;

/**
 * Mobile API Authentication Filter
 * Verifies Supabase JWT tokens for mobile API endpoints
 */
@Component
@Slf4j
public class MobileAuthFilter implements Filter {
    
    @Autowired
    private JwtVerificationService jwtVerificationService;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    // Endpoints that don't require authentication
    private static final List<String> EXCLUDED_PATHS = Arrays.asList(
        "/xiaozhi/api/mobile/health",
        "/xiaozhi/api/mobile/activation/check-code",
        "/xiaozhi/api/mobile/test"
    );
    
    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) 
            throws IOException, ServletException {
        
        HttpServletRequest httpRequest = (HttpServletRequest) request;
        HttpServletResponse httpResponse = (HttpServletResponse) response;
        
        String requestPath = httpRequest.getRequestURI();
        String contextPath = httpRequest.getContextPath();
        String pathWithoutContext = requestPath.substring(contextPath.length());
        
        log.debug("Request path: {}, Context path: {}, Path without context: {}", 
            requestPath, contextPath, pathWithoutContext);
        
        // Skip authentication for excluded paths
        if (isExcludedPath(requestPath)) {
            chain.doFilter(request, response);
            return;
        }
        
        // Only apply to mobile API endpoints (check path without context)
        if (!pathWithoutContext.startsWith("/api/mobile/")) {
            chain.doFilter(request, response);
            return;
        }
        
        // Get Authorization header
        String authHeader = httpRequest.getHeader("Authorization");
        
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            sendErrorResponse(httpResponse, HttpServletResponse.SC_UNAUTHORIZED, 
                "Missing or invalid Authorization header");
            return;
        }
        
        String token = authHeader.substring(7);
        
        // Verify token
        Claims claims = jwtVerificationService.verifyToken(token);
        
        if (claims == null) {
            sendErrorResponse(httpResponse, HttpServletResponse.SC_UNAUTHORIZED, 
                "Invalid or expired token");
            return;
        }
        
        // Extract user information
        String userId = jwtVerificationService.getUserId(claims);
        String email = jwtVerificationService.getEmail(claims);
        
        if (userId == null) {
            sendErrorResponse(httpResponse, HttpServletResponse.SC_UNAUTHORIZED, 
                "Invalid token: missing user information");
            return;
        }
        
        // Store user info in request attributes for use in controllers
        httpRequest.setAttribute("supabaseUserId", userId);
        httpRequest.setAttribute("userEmail", email);
        httpRequest.setAttribute("userClaims", claims);
        
        log.debug("Authenticated request from user: {} for path: {}", userId, requestPath);
        
        // Continue with the request
        chain.doFilter(request, response);
    }
    
    private boolean isExcludedPath(String path) {
        return EXCLUDED_PATHS.stream().anyMatch(path::startsWith);
    }
    
    private void sendErrorResponse(HttpServletResponse response, int status, String message) 
            throws IOException {
        response.setStatus(status);
        response.setContentType("application/json;charset=UTF-8");
        
        Result<Object> errorResponse = new Result<>().error(status, message);
        
        try (PrintWriter writer = response.getWriter()) {
            writer.write(objectMapper.writeValueAsString(errorResponse));
            writer.flush();
        }
    }
}