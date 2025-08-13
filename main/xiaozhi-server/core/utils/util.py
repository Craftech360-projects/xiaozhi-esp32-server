import json
import socket
import subprocess
import re
import os
import wave
from io import BytesIO
from core.utils import p3
import numpy as np
import requests
import opuslib_next
from pydub import AudioSegment
import copy

TAG = __name__
emoji_map = {
    "neutral": "😶",
    "happy": "🙂",
    "laughing": "😆",
    "funny": "😂",
    "sad": "😔",
    "angry": "😠",
    "crying": "😭",
    "loving": "😍",
    "embarrassed": "😳",
    "surprised": "😲",
    "shocked": "😱",
    "thinking": "🤔",
    "winking": "😉",
    "cool": "😎",
    "relaxed": "😌",
    "delicious": "🤤",
    "kissy": "😘",
    "confident": "😏",
    "sleepy": "😴",
    "silly": "😜",
    "confused": "🙄",
}


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Connect to Google's DNS servers
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        return "127.0.0.1"


def is_private_ip(ip_addr):
    """
    Check if an IP address is a private IP address (compatible with IPv4 and IPv6).

    @param {string} ip_addr - The IP address to check.
    @return {bool} True if the IP address is private, False otherwise.
    """
    try:
        # Validate IPv4 or IPv6 address format
        if not re.match(
            r"^(\d{1,3}\.){3}\d{1,3}$|^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$", ip_addr
        ):
            return False  # Invalid IP address format

        # IPv4 private address ranges
        if "." in ip_addr:  # IPv4 address
            ip_parts = list(map(int, ip_addr.split(".")))
            if ip_parts[0] == 10:
                return True  # 10.0.0.0/8 range
            elif ip_parts[0] == 172 and 16 <= ip_parts[1] <= 31:
                return True  # 172.16.0.0/12 range
            elif ip_parts[0] == 192 and ip_parts[1] == 168:
                return True  # 192.168.0.0/16 range
            elif ip_addr == "127.0.0.1":
                return True  # Loopback address
            elif ip_parts[0] == 169 and ip_parts[1] == 254:
                return True  # Link-local address 169.254.0.0/16
            else:
                return False  # Not a private IPv4 address
        else:  # IPv6 address
            ip_addr = ip_addr.lower()
            if ip_addr.startswith("fc00:") or ip_addr.startswith("fd00:"):
                return True  # Unique Local Addresses (FC00::/7)
            elif ip_addr == "::1":
                return True  # Loopback address
            elif ip_addr.startswith("fe80:"):
                return True  # Link-local unicast addresses (FE80::/10)
            else:
                return False  # Not a private IPv6 address

    except (ValueError, IndexError):
        return False  # IP address format error or insufficient segments


def get_ip_info(ip_addr, logger):
    try:
        if is_private_ip(ip_addr):
            ip_addr = ""
        url = f"https://whois.pconline.com.cn/ipJson.jsp?json=true&ip={ip_addr}"
        resp = requests.get(url).json()
        ip_info = {"city": resp.get("city")}
        return ip_info
    except Exception as e:
        logger.bind(tag=TAG).error(f"Error getting client ip info: {e}")
        return {}


def write_json_file(file_path, data):
    """Write data to JSON file"""
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def is_punctuation_or_emoji(char):
    """Check if character is space, specified punctuation, or emoji"""
    # Define Chinese and English punctuation marks to be removed (including full-width/half-width)
    punctuation_set = {
        "，",
        ",",  # Chinese comma + English comma
        "-",
        "－",  # English hyphen + Chinese full-width dash
        "、",  # Chinese pause mark
        """,
        """,
        '"',  # Chinese double quotes + English quotes
        "：",
        ":",  # Chinese colon + English colon
    }
    if char.isspace() or char in punctuation_set:
        return True
    # Check emoji symbols (retain original logic)
    code_point = ord(char)
    emoji_ranges = [
        (0x1F600, 0x1F64F),
        (0x1F300, 0x1F5FF),
        (0x1F680, 0x1F6FF),
        (0x1F900, 0x1F9FF),
        (0x1FA70, 0x1FAFF),
        (0x2600, 0x26FF),
        (0x2700, 0x27BF),
    ]
    return any(start <= code_point <= end for start, end in emoji_ranges)


def get_string_no_punctuation_or_emoji(s):
    """Remove spaces, punctuation marks and emoji symbols from the beginning and end of string"""
    chars = list(s)
    # Process characters at the beginning
    start = 0
    while start < len(chars) and is_punctuation_or_emoji(chars[start]):
        start += 1
    # Process characters at the end
    end = len(chars) - 1
    while end >= start and is_punctuation_or_emoji(chars[end]):
        end -= 1
    return "".join(chars[start: end + 1])


def remove_punctuation_and_length(text):
    # Unicode ranges for full-width and half-width symbols
    full_width_punctuations = (
        "！＂＃＄％＆＇（）＊＋，－。／：；＜＝＞？＠［＼］＾＿｀｛｜｝～"
    )
    half_width_punctuations = r'!"#$%&\'()*+,-./:;<=>?@[\]^_`{|}~'
    space = " "  # Half-width space
    full_width_space = "　"  # Full-width space

    # Remove full-width and half-width symbols and spaces
    result = "".join(
        [
            char
            for char in text
            if char not in full_width_punctuations
            and char not in half_width_punctuations
            and char not in space
            and char not in full_width_space
        ]
    )

    if result == "Yeah":
        return 0, ""
    return len(result), result


def check_model_key(modelType, modelKey):
    if "you" in modelKey:
        return f"Configuration error: {modelType} API key not set, current value is: {modelKey}"
    return None


def parse_string_to_list(value, separator=";"):
    """
    Convert input value to list
    Args:
        value: Input value, can be None, string, or list
        separator: Separator, default is semicolon
    Returns:
        list: Processed list
    """
    if value is None or value == "":
        return []
    elif isinstance(value, str):
        return [item.strip() for item in value.split(separator) if item.strip()]
    elif isinstance(value, list):
        return value
    return []


def check_ffmpeg_installed():
    ffmpeg_installed = False
    try:
        # Execute ffmpeg -version command and capture output
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,  # Throw exception if return code is non-zero
        )
        # Check if output contains version information (optional)
        output = result.stdout + result.stderr
        if "ffmpeg version" in output.lower():
            ffmpeg_installed = True
        return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Command execution failed or not found
        ffmpeg_installed = False
    if not ffmpeg_installed:
        error_msg = "Your computer has not correctly installed ffmpeg\n"
        error_msg += "\nWe recommend you:\n"
        error_msg += "1. Follow the project's installation documentation to correctly enter conda environment\n"
        error_msg += "2. Read the installation documentation on how to install ffmpeg in conda environment\n"
        raise ValueError(error_msg)


def extract_json_from_string(input_string):
    """Extract JSON part from string"""
    pattern = r"(\{.*\})"
    match = re.search(pattern, input_string, re.DOTALL)  # Add re.DOTALL
    if match:
        return match.group(1)  # Return extracted JSON string
    return None


def analyze_emotion(text):
    """
    Analyze text emotion and return corresponding emoji name (supports Chinese and English)
    """
    if not text or not isinstance(text, str):
        return "neutral"

    original_text = text
    text = text.lower().strip()

    # Check if contains existing emoji
    for emotion, emoji in emoji_map.items():
        if emoji in original_text:
            return emotion

    # Punctuation analysis
    has_exclamation = "!" in original_text or "！" in original_text
    has_question = "?" in original_text or "？" in original_text
    has_ellipsis = "..." in original_text or "…" in original_text

    # Define emotion keyword mapping (Chinese and English extended version)
    emotion_keywords = {
        "happy": [
            "开心",
            "高兴",
            "快乐",
            "愉快",
            "幸福",
            "满意",
            "棒",
            "好",
            "不错",
            "完美",
            "棒极了",
            "太好了",
            "好呀",
            "好的",
            "happy",
            "joy",
            "great",
            "good",
            "nice",
            "awesome",
            "fantastic",
            "wonderful",
        ],
        "laughing": [
            "哈哈",
            "哈哈哈",
            "呵呵",
            "嘿嘿",
            "嘻嘻",
            "笑死",
            "太好笑了",
            "笑死我了",
            "lol",
            "lmao",
            "haha",
            "hahaha",
            "hehe",
            "rofl",
            "funny",
            "laugh",
        ],
        "funny": [
            "搞笑",
            "滑稽",
            "逗",
            "幽默",
            "笑点",
            "段子",
            "笑话",
            "太逗了",
            "hilarious",
            "joke",
            "comedy",
        ],
        "sad": [
            "伤心",
            "难过",
            "悲哀",
            "悲伤",
            "忧郁",
            "郁闷",
            "沮丧",
            "失望",
            "想哭",
            "难受",
            "不开心",
            "唉",
            "呜呜",
            "sad",
            "upset",
            "unhappy",
            "depressed",
            "sorrow",
            "gloomy",
        ],
        "angry": [
            "生气",
            "愤怒",
            "气死",
            "讨厌",
            "烦人",
            "可恶",
            "烦死了",
            "漏火",
            "暴躁",
            "火大",
            "愤怒",
            "气炸了",
            "angry",
            "mad",
            "annoyed",
            "furious",
            "pissed",
            "hate",
        ],
        "crying": [
            "哭泣",
            "泪流",
            "大哭",
            "伤心欲绝",
            "泪目",
            "流泪",
            "哭死",
            "哭晕",
            "想哭",
            "泪崩",
            "cry",
            "crying",
            "tears",
            "sob",
            "weep",
        ],
        "loving": [
            "爱你",
            "喜欢",
            "爱",
            "亲爱的",
            "宝贝",
            "么么哒",
            "抱抱",
            "想你",
            "思念",
            "最爱",
            "亲亲",
            "喜欢你",
            "love",
            "like",
            "adore",
            "darling",
            "sweetie",
            "honey",
            "miss you",
            "heart",
        ],
        "embarrassed": [
            "尴尬",
            "不好意思",
            "害羞",
            "脸红",
            "难为情",
            "社死",
            "丢脸",
            "出丑",
            "embarrassed",
            "awkward",
            "shy",
            "blush",
        ],
        "surprised": [
            "惊讶",
            "吃惊",
            "天啊",
            "哇塞",
            "哇",
            "居然",
            "竟然",
            "没想到",
            "出乎意料",
            "surprise",
            "wow",
            "omg",
            "oh my god",
            "amazing",
            "unbelievable",
        ],
        "shocked": [
            "震惊",
            "吓到",
            "惊呆了",
            "不敢相信",
            "震撼",
            "吓死",
            "恐怖",
            "害怕",
            "吓人",
            "shocked",
            "shocking",
            "scared",
            "frightened",
            "terrified",
            "horror",
        ],
        "thinking": [
            "思考",
            "考虑",
            "想一下",
            "琢磨",
            "沉思",
            "冥想",
            "想",
            "思考中",
            "在想",
            "think",
            "thinking",
            "consider",
            "ponder",
            "meditate",
        ],
        "winking": [
            "调皮",
            "眨眼",
            "你懂的",
            "坏笑",
            "邪恶",
            "奸笑",
            "使眼色",
            "wink",
            "teasing",
            "naughty",
            "mischievous",
        ],
        "cool": [
            "酷",
            "帅",
            "厉害",
            "棒极了",
            "真棒",
            "牛逼",
            "强",
            "优秀",
            "氛出",
            "出色",
            "完美",
            "cool",
            "awesome",
            "amazing",
            "great",
            "impressive",
            "perfect",
        ],
        "relaxed": [
            "放松",
            "舒服",
            "惬意",
            "悠闲",
            "轻松",
            "舒适",
            "安逸",
            "自在",
            "relax",
            "relaxed",
            "comfortable",
            "cozy",
            "chill",
            "peaceful",
        ],
        "delicious": [
            "好吃",
            "美味",
            "香",
            "馋",
            "可口",
            "香甜",
            "大餐",
            "大快朵颐",
            "流口水",
            "垂涎",
            "delicious",
            "yummy",
            "tasty",
            "yum",
            "appetizing",
            "mouthwatering",
        ],
        "kissy": [
            "亲亲",
            "么么",
            "吻",
            "mua",
            "muah",
            "亲一下",
            "飞吻",
            "kiss",
            "xoxo",
            "hug",
            "muah",
            "smooch",
        ],
        "confident": [
            "自信",
            "肯定",
            "确定",
            "毫无疑问",
            "当然",
            "必须的",
            "毫无疑问",
            "确信",
            "笃信",
            "confident",
            "sure",
            "certain",
            "definitely",
            "positive",
        ],
        "sleepy": [
            "困",
            "睡觉",
            "晚安",
            "想睡",
            "好累",
            "疲惫",
            "疲倦",
            "困了",
            "想休息",
            "睡意",
            "sleep",
            "sleepy",
            "tired",
            "exhausted",
            "bedtime",
            "good night",
        ],
        "silly": [
            "傻",
            "笨",
            "呆",
            "憨",
            "蠢",
            "二",
            "憨憨",
            "傻乎乎",
            "呆萌",
            "silly",
            "stupid",
            "dumb",
            "foolish",
            "goofy",
            "ridiculous",
        ],
        "confused": [
            "疑惑",
            "不明白",
            "不懂",
            "困惑",
            "疑问",
            "为什么",
            "怎么回事",
            "啥意思",
            "不清楚",
            "confused",
            "puzzled",
            "doubt",
            "question",
            "what",
            "why",
            "how",
        ],
    }

    # Special sentence pattern judgment (Chinese and English)
    # Praising others
    if any(
        phrase in text
        for phrase in [
            "你真",
            "你好",
            "您真",
            "你真棒",
            "你好厉害",
            "你太强了",
            "你真好",
            "你真聪明",
            "you are",
            "you're",
            "you look",
            "you seem",
            "so smart",
            "so kind",
        ]
    ):
        return "loving"
    # Self-praise
    if any(
        phrase in text
        for phrase in [
            "我真",
            "我最",
            "我太棒了",
            "我厉害",
            "我聪明",
            "我优秀",
            "i am",
            "i'm",
            "i feel",
            "so good",
            "so happy",
        ]
    ):
        return "cool"
    # Good night/sleep related
    if any(
        phrase in text
        for phrase in [
            "睡觉",
            "晚安",
            "睡了",
            "好梦",
            "休息了",
            "去睡了",
            "sleep",
            "good night",
            "bedtime",
            "go to bed",
        ]
    ):
        return "sleepy"
    # Question sentences
    if has_question and not has_exclamation:
        return "thinking"
    # Strong emotions (exclamation marks)
    if has_exclamation and not has_question:
        # Check if it's positive content
        positive_words = (
            emotion_keywords["happy"]
            + emotion_keywords["laughing"]
            + emotion_keywords["cool"]
        )
        if any(word in text for word in positive_words):
            return "laughing"
        # Check if it's negative content
        negative_words = (
            emotion_keywords["angry"]
            + emotion_keywords["sad"]
            + emotion_keywords["crying"]
        )
        if any(word in text for word in negative_words):
            return "angry"
        return "surprised"
    # Ellipsis (indicating hesitation or thinking)
    if has_ellipsis:
        return "thinking"

    # Keyword matching (with weight)
    emotion_scores = {emotion: 0 for emotion in emoji_map.keys()}

    # Add points for matched keywords
    for emotion, keywords in emotion_keywords.items():
        for keyword in keywords:
            if keyword in text:
                emotion_scores[emotion] += 1

    # Give extra points for repeated keywords in long text
    if len(text) > 20:  # Long text
        for emotion, keywords in emotion_keywords.items():
            for keyword in keywords:
                emotion_scores[emotion] += text.count(keyword) * 0.5

    # Choose the most likely emotion based on scores
    max_score = max(emotion_scores.values())
    if max_score == 0:
        return "happy"  # Default

    # There might be multiple emotions with the same score, choose the most appropriate based on context
    top_emotions = [e for e, s in emotion_scores.items() if s == max_score]

    # If multiple emotions have the same score, use the following priority order
    priority_order = [
        "laughing",
        "crying",
        "angry",
        "surprised",
        "shocked",  # Strong emotions first
        "loving",
        "happy",
        "funny",
        "cool",  # Positive emotions
        "sad",
        "embarrassed",
        "confused",  # Negative emotions
        "thinking",
        "winking",
        "relaxed",  # Neutral emotions
        "delicious",
        "kissy",
        "confident",
        "sleepy",
        "silly",  # Special scenarios
    ]

    for emotion in priority_order:
        if emotion in top_emotions:
            return emotion

    return top_emotions[0]  # If none in priority list, return the first one


def audio_to_data(audio_file_path, is_opus=True):
    # Get file extension
    file_type = os.path.splitext(audio_file_path)[1]
    if file_type:
        file_type = file_type.lstrip(".")
    # Read audio file, -nostdin parameter: don't read data from standard input, otherwise FFmpeg will block
    audio = AudioSegment.from_file(
        audio_file_path, format=file_type, parameters=["-nostdin"]
    )

    # Convert to mono/16kHz sample rate/16-bit little-endian encoding (ensure compatibility with encoder)
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)

    # Audio duration (seconds)
    duration = len(audio) / 1000.0

    # Get raw PCM data (16-bit little-endian)
    raw_data = audio.raw_data
    return pcm_to_data(raw_data, is_opus), duration


def audio_bytes_to_data(audio_bytes, file_type, is_opus=True):
    """
    Directly convert audio binary data to opus/pcm data, supports wav, mp3, p3
    """
    if file_type == "p3":
        # Use p3 decoding directly
        return p3.decode_opus_from_bytes(audio_bytes)
    else:
        # Use pydub for other formats
        audio = AudioSegment.from_file(
            BytesIO(audio_bytes), format=file_type, parameters=["-nostdin"]
        )
        audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
        duration = len(audio) / 1000.0
        raw_data = audio.raw_data
        return pcm_to_data(raw_data, is_opus), duration


def pcm_to_data(raw_data, is_opus=True):
    # Initialize Opus encoder
    encoder = opuslib_next.Encoder(16000, 1, opuslib_next.APPLICATION_AUDIO)

    # Encoding parameters
    frame_duration = 60  # 60ms per frame
    frame_size = int(16000 * frame_duration / 1000)  # 960 samples/frame

    datas = []
    # Process all audio data frame by frame (including the last frame which may be padded with zeros)
    for i in range(0, len(raw_data), frame_size * 2):  # 16bit=2bytes/sample
        # Get binary data for current frame
        chunk = raw_data[i: i + frame_size * 2]

        # If the last frame is insufficient, pad with zeros
        if len(chunk) < frame_size * 2:
            chunk += b"\x00" * (frame_size * 2 - len(chunk))

        if is_opus:
            # Convert to numpy array for processing
            np_frame = np.frombuffer(chunk, dtype=np.int16)
            # Encode Opus data
            frame_data = encoder.encode(np_frame.tobytes(), frame_size)
        else:
            frame_data = chunk if isinstance(chunk, bytes) else bytes(chunk)

        datas.append(frame_data)

    return datas


def opus_datas_to_wav_bytes(opus_datas, sample_rate=16000, channels=1):
    """
    Decode opus frame list to wav byte stream
    """
    decoder = opuslib_next.Decoder(sample_rate, channels)
    pcm_datas = []

    frame_duration = 60  # ms
    frame_size = int(sample_rate * frame_duration / 1000)  # 960

    for opus_frame in opus_datas:
        # Decode to PCM (returns bytes, 2 bytes/sample point)
        pcm = decoder.decode(opus_frame, frame_size)
        pcm_datas.append(pcm)

    pcm_bytes = b"".join(pcm_datas)

    # Write to wav byte stream
    wav_buffer = BytesIO()
    with wave.open(wav_buffer, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    return wav_buffer.getvalue()


def check_vad_update(before_config, new_config):
    if (
        new_config.get("selected_module") is None
        or new_config["selected_module"].get("VAD") is None
    ):
        return False
    update_vad = False
    current_vad_module = before_config["selected_module"]["VAD"]
    new_vad_module = new_config["selected_module"]["VAD"]
    current_vad_type = (
        current_vad_module
        if "type" not in before_config["VAD"][current_vad_module]
        else before_config["VAD"][current_vad_module]["type"]
    )
    new_vad_type = (
        new_vad_module
        if "type" not in new_config["VAD"][new_vad_module]
        else new_config["VAD"][new_vad_module]["type"]
    )
    update_vad = current_vad_type != new_vad_type
    return update_vad


def check_asr_update(before_config, new_config):
    if (
        new_config.get("selected_module") is None
        or new_config["selected_module"].get("ASR") is None
    ):
        return False
    update_asr = False
    current_asr_module = before_config["selected_module"]["ASR"]
    new_asr_module = new_config["selected_module"]["ASR"]
    current_asr_type = (
        current_asr_module
        if "type" not in before_config["ASR"][current_asr_module]
        else before_config["ASR"][current_asr_module]["type"]
    )
    new_asr_type = (
        new_asr_module
        if "type" not in new_config["ASR"][new_asr_module]
        else new_config["ASR"][new_asr_module]["type"]
    )
    update_asr = current_asr_type != new_asr_type
    return update_asr


def filter_sensitive_info(config: dict) -> dict:
    """
    Filter sensitive information in configuration
    Args:
        config: Original configuration dictionary
    Returns:
        Filtered configuration dictionary
    """
    sensitive_keys = [
        "api_key",
        "personal_access_token",
        "access_token",
        "token",
        "secret",
        "access_key_secret",
        "secret_key",
    ]

    def _filter_dict(d: dict) -> dict:
        filtered = {}
        for k, v in d.items():
            if any(sensitive in k.lower() for sensitive in sensitive_keys):
                filtered[k] = "***"
            elif isinstance(v, dict):
                filtered[k] = _filter_dict(v)
            elif isinstance(v, list):
                filtered[k] = [_filter_dict(i) if isinstance(
                    i, dict) else i for i in v]
            else:
                filtered[k] = v
        return filtered

    return _filter_dict(copy.deepcopy(config))


def get_vision_url(config: dict) -> str:
    """Get vision URL

    Args:
        config: Configuration dictionary

    Returns:
        str: vision URL
    """
    server_config = config["server"]
    vision_explain = server_config.get("vision_explain", "")
    if "your" in vision_explain:
        local_ip = get_local_ip()
        port = int(server_config.get("http_port", 8003))
        vision_explain = f"http://{local_ip}:{port}/mcp/vision/explain"
    return vision_explain


def is_valid_image_file(file_data: bytes) -> bool:
    """
    Check if file data is a valid image format

    Args:
        file_data: Binary data of the file

    Returns:
        bool: Returns True if it's a valid image format, False otherwise
    """
    # Common image format magic numbers (file headers)
    image_signatures = {
        b"\xff\xd8\xff": "JPEG",
        b"\x89PNG\r\n\x1a\n": "PNG",
        b"GIF87a": "GIF",
        b"GIF89a": "GIF",
        b"BM": "BMP",
        b"II*\x00": "TIFF",
        b"MM\x00*": "TIFF",
        b"RIFF": "WEBP",
    }

    # Check if file header matches any known image format
    for signature in image_signatures:
        if file_data.startswith(signature):
            return True

    return False


def sanitize_tool_name(name: str) -> str:
    """Sanitize tool names for OpenAI compatibility."""
    # Support Chinese, English letters, numbers, underscores and hyphens
    return re.sub(r"[^a-zA-Z0-9_\-\u4e00-\u9fff]", "_", name)
