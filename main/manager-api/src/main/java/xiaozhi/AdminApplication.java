package xiaozhi;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication(exclude = {
     org.springframework.boot.autoconfigure.http.client.HttpClientAutoConfiguration.class,
     org.springframework.boot.autoconfigure.web.client.RestClientAutoConfiguration.class
})
public class AdminApplication {

    public static void main(String[] args) {
        SpringApplication.run(AdminApplication.class, args);
        System.out.println("http://localhost:8002/xiaozhi/doc.html");
    }
}