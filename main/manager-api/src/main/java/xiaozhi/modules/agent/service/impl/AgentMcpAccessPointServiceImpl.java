package xiaozhi.modules.agent.service.impl;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.jetbrains.annotations.NotNull;
import org.springframework.stereotype.Service;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.utils.AESUtils;
import xiaozhi.common.utils.HashEncryptionUtil;
import xiaozhi.modules.agent.service.AgentMcpAccessPointService;
import xiaozhi.modules.sys.service.SysParamsService;

import java.net.URI;
import java.net.URISyntaxException;
import java.util.List;

@AllArgsConstructor
@Service
@Slf4j
public class AgentMcpAccessPointServiceImpl implements AgentMcpAccessPointService {
    private SysParamsService sysParamsService;

    @Override
    public String getAgentMcpAccessAddress(String id) {
        // 获取到mcp的地址
        String url = sysParamsService.getValue(Constant.SERVER_MCP_ENDPOINT, true);
        if (StringUtils.isBlank(url)) {
            return null;
        }
        try {
            URI uri = new URI(url);
            // 获取智能体mcp的url前缀
            String agentMcpUrl = getAgentMcpUrl(uri);
            // 获取密钥
            String key = getSecretKey(uri);
            // 获取加密的token
            String encryptToken = encryptToken(id, key);
            // 返回智能体Mcp路径的格式
            String AgentMcpUrl = "%s/mcp?token=%s";
            return AgentMcpUrl.formatted(agentMcpUrl,encryptToken);
        } catch (URISyntaxException e) {
            log.error("路径格式不正确路径：{}，\n错误信息:{}",url,e.getMessage());
            throw new RuntimeException("mcp的地址存在错误，请进入参数管理修改mcp接入点地址");
        }
    }
    @Override
    public List<String> getAgentMcpToolsList(String id) {
        List<String> list = List.of();
        String url = sysParamsService.getValue(Constant.SERVER_MCP_ENDPOINT, true);
        if (StringUtils.isBlank(url)) {
            return list;
        }

        return list;
    }

    /**
     * 获取密钥
     * @param uri mcp地址
     * @return 密钥
     */
    private static String getSecretKey(URI uri) {
        // 获取参数
        String query = uri.getQuery();
        // 获取aes加密密钥
        String str = "key=";
        return query.substring(query.indexOf(str) + str.length());
    }

    /**
     * 获取智能体mcp接入点url
     * @param uri mcp地址
     * @return 智能体mcp接入点url
     */
    private String getAgentMcpUrl(URI uri) {
        // 获取协议
        String wsScheme = (uri.getScheme().equals("https")) ? "wss" : "ws" ;
        // 获取主机，端口，路径
        String path = uri.getSchemeSpecificPart();
        // 获取到最后一个/前的path
        path = path.substring(0,path.lastIndexOf("/"));
        return wsScheme+":"+path;
    }




    /**
     * 获取对智能体id加密的token
     * @param agentId 智能体id
     * @param key 加密密钥
     * @return 加密后token
     */
    private static String encryptToken(String agentId, String key) {
        // 使用md5对智能体id进行加密
        String md5 = HashEncryptionUtil.Md5hexDigest(agentId);
        // aes需要加密文本
        String json = "{\"agentId\": %s}".formatted(md5);
        // 加密后成token值
        return AESUtils.encrypt(key, json);
    }
}
