package xiaozhi.modules.agent.service.impl;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
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
            // 使用md5对智能体id进行加密
            String md5 = HashEncryptionUtil.Md5hexDigest(id);
            // aes需要加密文本
            String json = "{\"agentId\": %s}".formatted(md5);
            URI uri = new URI(url);
            String query = uri.getQuery();
            // 获取aes加密密钥
            String str = "key=";
            String key = query.substring(query.indexOf(str) + str.length());
            // 加密后成token值
            String encryptToken = AESUtils.encrypt(key, json);
            // 获取路径组成部分
            // 获取协议
            String wsScheme = (uri.getScheme().equals("https")) ? "wss" : "ws" ;
            // 获取主机，端口，路径
            String path = uri.getSchemeSpecificPart();
            // 获取参数
            path = path.substring(0,path.lastIndexOf("/"));
            // 返回智能体Mcp路径的格式
            String AgentMcpUrl = "%s:%s/mcp?token=%s";
            return AgentMcpUrl.formatted(wsScheme,path,encryptToken);
        } catch (URISyntaxException e) {
            log.error("路径格式不正确路径：{}，\n错误信息:{}",url,e.getMessage());
            throw new RuntimeException("mcp的地址存在错误，请进入参数管理修改mcp接入点地址");
        }
    }

    @Override
    public List<String> getAgentMcpToolsList(String id) {
        return List.of();
    }
}
