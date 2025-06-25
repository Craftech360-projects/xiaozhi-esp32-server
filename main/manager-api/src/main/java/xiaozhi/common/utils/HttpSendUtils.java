package xiaozhi.common.utils;

import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.jetbrains.annotations.Nullable;
import org.springframework.stereotype.Component;
import xiaozhi.common.exception.RenException;

import java.io.IOException;

@Slf4j
@Component
public class HttpSendUtils {
    private OkHttpClient client = new OkHttpClient();

    /**
     * 发送get请求，获取返回的body转换成字符串
     * @param url get请求地址
     * @return body内容
     */
    public String fetchGetBodyAsString(String url) {
        Request request = new Request.Builder()
                .url(url)
                .build();
        return getString(url, request);
    }

    /**
     * 发送post请求，参数为json格式。取返回的body转换成字符串
     * @param url post请求地址
     * @param json json参数
     * @return body内容
     */
    public String fetchJsonPostBodyAsString(String url,String json) {
        // 创建请求体
        MediaType JSON = MediaType.get("application/json; charset=utf-8");
        RequestBody body = RequestBody.create(json, JSON);

        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();

        return getString(url, request);
    }

    private String getString(String url, Request request) {
        String body = null;
        try (Response response = client.newCall(request).execute()) {
            if (response.isSuccessful()) {
                if (response.body() != null){
                    body = response.body().string();
                }
            } else {
                throw new RenException("请求失败，错误码："+response.code());
            }
        } catch (Exception e) {
            String method = request.method();
            log.error("{}请求发送错误地址：{} \n 发送错误信息:{}",method, url,e.getMessage());
            throw new RenException("请求发送失败");
        }
        return body;
    }
}
