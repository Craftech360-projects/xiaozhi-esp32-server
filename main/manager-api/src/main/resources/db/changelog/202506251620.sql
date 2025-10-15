-- Update existing get_news_from_newsnow plugin configuration
UPDATE ai_model_provider
SET fields = jsonb_build_array(
    jsonb_build_object(
        'key', 'url',
        'type', 'string',
        'label', 'Interface Address',
        'default', 'https://newsnow.busiyi.world/api/s?id='
    ),
    jsonb_build_object(
        'key', 'news_sources',
        'type', 'string',
        'label', 'News Source Configuration',
        'default', 'The Paper;Baidu Trending;Yicai'
    )
)
WHERE provider_code = 'get_news_from_newsnow'
AND model_type = 'Plugin'; 