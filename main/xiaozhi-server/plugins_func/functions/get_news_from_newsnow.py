import random
import requests
import json
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from markitdown import MarkItDown

TAG = __name__
logger = setup_logging()

CHANNEL_MAP = {
    "V2EX": "v2ex-share",
    "知乎": "zhihu",
    "微博": "weibo",
    "联合早报": "zaobao",
    "酷安": "coolapk",
    "MKTNews": "mktnews-flash",
    "华尔街见闻": "wallstreetcn-quick",
    "36氪": "36kr-quick",
    "抖音": "douyin",
    "虎扑": "hupu",
    "百度贴吧": "tieba",
    "今日头条": "toutiao",
    "IT之家": "ithome",
    "澎湃新闻": "thepaper",
    "卫星通讯社": "sputniknewscn",
    "参考消息": "cankaoxiaoxi",
    "远景论坛": "pcbeta-windows11",
    "财联社": "cls-depth",
    "雪球": "xueqiu-hotstock",
    "格隆汇": "gelonghui",
    "法布财经": "fastbull-express",
    "Solidot": "solidot",
    "Hacker News": "hackernews",
    "Product Hunt": "producthunt",
    "Github": "github-trending-today",
    "哔哩哔哩": "bilibili-hot-search",
    "快手": "kuaishou",
    "靠谱新闻": "kaopu",
    "金十数据": "jin10",
    "百度热搜": "baidu",
    "牛客": "nowcoder",
    "少数派": "sspai",
    "稀土掘金": "juejin",
    "凤凰网": "ifeng",
    "虫部落": "chongbuluo-latest",
}

# Default news sources dictionary, used when not specified in config
DEFAULT_NEWS_SOURCES = "澎湃新闻;百度热搜;财联社"

def get_news_sources_from_config(conn):
    """Get news sources string from config"""
    try:
        # Try to get news sources from plugin config
        if (
            conn.config.get("plugins")
            and conn.config["plugins"].get("get_news_from_newsnow")
            and conn.config["plugins"]["get_news_from_newsnow"].get("news_sources")
        ):
            # Get configured news sources string
            news_sources_config = conn.config["plugins"]["get_news_from_newsnow"][
                "news_sources"
            ]
            if isinstance(news_sources_config, str) and news_sources_config.strip():
                logger.bind(tag=TAG).debug(f"Using configured news sources: {news_sources_config}")
                return news_sources_config
            else:
                logger.bind(tag=TAG).warning("News sources config is empty or format error, using default config")
        else:
            logger.bind(tag=TAG).debug("News sources config not found, using default config")
        return DEFAULT_NEWS_SOURCES
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to get news sources config: {e}, using default config")
        return DEFAULT_NEWS_SOURCES

# Get all available news source names from CHANNEL_MAP
available_sources = list(CHANNEL_MAP.keys())
example_sources_str = "、".join(available_sources)

GET_NEWS_FROM_NEWSNOW_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_news_from_newsnow",
        "description": (
            "Get latest news, randomly select one news item for broadcast. "
            f"Users can choose different news sources, standard names are: {example_sources_str}. "
            "For example, if user wants Baidu news, it's actually Baidu Hot Search. If not specified, defaults to Pengpai News. "
            "Users can request detailed content, in which case detailed news content will be retrieved."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": f"Standard Chinese name of news source, e.g., {example_sources_str} etc. Optional parameter, uses default news source if not provided",
                },
                "detail": {
                    "type": "boolean",
                    "description": "Whether to get detailed content, default is false. If true, gets detailed content of the previous news",
                },
                "lang": {
                    "type": "string",
                    "description": "Language code used by user, e.g., zh_CN/zh_HK/en_US/ja_JP etc., default zh_CN",
                },
            },
            "required": ["lang"],
        },
    },
}

def fetch_news_from_api(conn, source="thepaper"):
    """Fetch news list from API"""
    try:
        api_url = f"https://newsnow.busiyi.world/api/s?id={source}"
        if conn.config["plugins"].get("get_news_from_newsnow") and conn.config[
            "plugins"
        ]["get_news_from_newsnow"].get("url"):
            api_url = conn.config["plugins"]["get_news_from_newsnow"]["url"] + source
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "items" in data:
            return data["items"]
        else:
            logger.bind(tag=TAG).error(f"News API response format error: {data}")
            return []
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to get news API: {e}")
        return []

def fetch_news_detail(url):
    """Get news detail page content and clean HTML using MarkItDown"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # Use MarkItDown to clean HTML content
        md = MarkItDown(enable_plugins=False)
        result = md.convert(response)
        # Get cleaned text content
        clean_text = result.text_content
        # If cleaned content is empty, return hint message
        if not clean_text or len(clean_text.strip()) == 0:
            logger.bind(tag=TAG).warning(f"Cleaned news content is empty: {url}")
            return "Unable to parse news detail content, possibly due to special website structure or restricted content."
        return clean_text
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to get news details: {e}")
        return "Unable to get detailed content"

@register_function(
    "get_news_from_newsnow",
    GET_NEWS_FROM_NEWSNOW_FUNCTION_DESC,
    ToolType.SYSTEM_CTL,
)
def get_news_from_newsnow(
    conn, source: str = "澎湃新闻", detail: bool = False, lang: str = "zh_CN"
):
    """Get news and randomly select one for broadcast, or get detailed content of previous news"""
    try:
        # Get currently configured news sources
        news_sources = get_news_sources_from_config(conn)
        # If detail is True, get detailed content of previous news
        detail = str(detail).lower() == "true"
        if detail:
            if (
                not hasattr(conn, "last_newsnow_link")
                or not conn.last_newsnow_link
                or "url" not in conn.last_newsnow_link
            ):
                return ActionResponse(
                    Action.REQLLM,
                    "Sorry, no recently queried news found, please get a news item first.",
                    None,
                )
            
            url = conn.last_newsnow_link.get("url")
            title = conn.last_newsnow_link.get("title", "Unknown title")
            source_id = conn.last_newsnow_link.get("source_id", "thepaper")
            source_name = CHANNEL_MAP.get(source_id, "Unknown source")
            
            if not url or url == "#":
                return ActionResponse(
                    Action.REQLLM, 
                    "Sorry, this news has no available link to get detailed content.", 
                    None
                )
            
            logger.bind(tag=TAG).debug(
                f"Getting news details: {title}, source: {source_name}, URL={url}"
            )
            
            # Get news details
            detail_content = fetch_news_detail(url)
            if not detail_content or detail_content == "Unable to get detailed content":
                return ActionResponse(
                    Action.REQLLM,
                    f"Sorry, unable to get detailed content of '{title}', link may be invalid or website structure changed.",
                    None,
                )
            
            # Build detail report
            detail_report = (
                f"Based on the following data, respond to user's news detail query in {lang}:\n\n"
                f"News title: {title}\n"
                # f"News source: {source_name}\n"
                f"Detailed content: {detail_content}\n\n"
                f"(Please summarize the above news content, extract key information, and broadcast to user in a natural, fluent manner, "
                f"don't mention this is a summary, tell it like a complete news story)"
            )
            
            return ActionResponse(Action.REQLLM, detail_report, None)
        
        # Otherwise, get news list and randomly select one
        # Convert Chinese name to English ID
        english_source_id = None
        # Check if input Chinese name is in configured news sources
        news_sources_list = [
            name.strip() for name in news_sources.split(";") if name.strip()
        ]
        if source in news_sources_list:
            # If input Chinese name is in configured news sources, find corresponding English ID in CHANNEL_MAP
            english_source_id = CHANNEL_MAP.get(source)
        # If corresponding English ID not found, use default source
        if not english_source_id:
            logger.bind(tag=TAG).warning(f"Invalid news source: {source}, using default source Pengpai News")
            english_source_id = "thepaper"
            source = "澎湃新闻"
        
        logger.bind(tag=TAG).info(f"Getting news: news source={source}({english_source_id})")
        
        # Get news list
        news_items = fetch_news_from_api(conn, english_source_id)
        if not news_items:
            return ActionResponse(
                Action.REQLLM,
                f"Sorry, unable to get news from {source}, please try again later or try other news sources.",
                None,
            )
        
        # Randomly select one news item
        selected_news = random.choice(news_items)
        # Save current news link to connection object for future detail queries
        if not hasattr(conn, "last_newsnow_link"):
            conn.last_newsnow_link = {}
        conn.last_newsnow_link = {
            "url": selected_news.get("url", "#"),
            "title": selected_news.get("title", "Unknown title"),
            "source_id": english_source_id,
        }
        
        # Build news report
        news_report = (
            f"Based on the following data, respond to user's news query in {lang}:\n\n"
            f"News title: {selected_news['title']}\n"
            # f"News source: {source}\n"
            f"(Please broadcast this news title to user in a natural, fluent manner, "
            f"remind user they can request detailed content, in which case detailed news content will be retrieved.)"
        )
        
        return ActionResponse(Action.REQLLM, news_report, None)
    except Exception as e:
        logger.bind(tag=TAG).error(f"Error getting news: {e}")
        return ActionResponse(
            Action.REQLLM, 
            "Sorry, an error occurred while getting news, please try again later.", 
            None
        )
