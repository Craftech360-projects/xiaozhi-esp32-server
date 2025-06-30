-- 更新 get_news_from_newsnow 插件配置，添加新闻源配置字段
-- 执行时间：2025-06-25

-- 更新现有的 get_news_from_newsnow 插件配置
UPDATE ai_model_provider 
SET fields = JSON_ARRAY(
    JSON_OBJECT(
        'key', 'url',
        'type', 'string',
        'label', '接口地址',
        'default', 'https://newsnow.busiyi.world/api/s?id='
    ),
    JSON_OBJECT(
        'key', 'news_sources',
        'type', 'json',
        'label', '新闻源配置',
        'default', '{"thepaper":"澎湃新闻","baidu":"百度热搜","cls-depth":"财联社"}'
    )
)
WHERE provider_code = 'get_news_from_newsnow' 
AND model_type = 'Plugin';