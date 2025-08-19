package xiaozhi.modules.mobile.config;

import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import xiaozhi.modules.mobile.filter.MobileAuthFilter;

/**
 * Mobile API Configuration
 * Configures filters and other settings for mobile API endpoints
 */
@Configuration
public class MobileApiConfig {
    
    /**
     * Register the mobile auth filter for mobile API endpoints
     */
    @Bean
    public FilterRegistrationBean<MobileAuthFilter> mobileAuthFilterRegistration(MobileAuthFilter filter) {
        FilterRegistrationBean<MobileAuthFilter> registration = new FilterRegistrationBean<>();
        registration.setFilter(filter);
        registration.addUrlPatterns("/api/mobile/*");
        registration.setOrder(1);
        registration.setName("mobileAuthFilter");
        return registration;
    }
}