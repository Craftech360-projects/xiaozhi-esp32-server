package xiaozhi.common.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.DefaultResponseErrorHandler;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;

/**
 * RestTemplate配置
 */
@Configuration
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate() {
        RestTemplate restTemplate = new RestTemplate();

        // 配置连接和读取超时
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000); // 5秒连接超时
        factory.setReadTimeout(30000);   // 30秒读取超时
        restTemplate.setRequestFactory(factory);

        // 配置错误处理器，避免抛出异常
        restTemplate.setErrorHandler(new DefaultResponseErrorHandler() {
            @Override
            public void handleError(org.springframework.http.client.ClientHttpResponse response) throws IOException {
                // 不抛出异常，让调用方处理错误响应
                // 这样可以避免RestTemplate在遇到4xx/5xx状态码时抛出异常
            }
        });

        return restTemplate;
    }
}