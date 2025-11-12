package xiaozhi.common.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;
import lombok.Data;

/**
 * Supabase Configuration Properties
 */
@Configuration
@ConfigurationProperties(prefix = "supabase")
@Data
public class SupabaseConfig {
    private String url;
    private String anonKey;
    private String serviceKey;

    public String getRestApiUrl() {
        return url + "/rest/v1";
    }
}