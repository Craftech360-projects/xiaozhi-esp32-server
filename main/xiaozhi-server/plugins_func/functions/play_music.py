import os
import re
import time
import random
import difflib
import traceback
from pathlib import Path
from core.handle.sendAudioHandle import send_stt_message
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.utils.dialogue import Message
from core.providers.tts.dto.dto import TTSMessageDTO, SentenceType, ContentType

TAG = __name__

MUSIC_CACHE = {}

play_music_function_desc = {
    "type": "function",
    "function": {
        "name": "play_music",
        "description": "Method for singing, listening to music, playing music, and any music-related requests. Supports language-specific requests and educational content like phonics. Triggers on phrases like 'sing a song', 'play music', 'can you sing', 'I want to hear music', 'put on some music', 'play any English song', 'sing a Telugu song', 'play phonics', 'learn phonics', etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "song_name": {
                    "type": "string",
                    "description": "Song name, language request, or educational content request. If the user doesn't specify a specific song name, it should be 'random'. For language requests, use the language name. Examples: ```User: sing Two Tigers for me\nParameter: Two Tigers``` ```User: can you sing a song\nParameter: random``` ```User: play any English song\nParameter: any English song``` ```User: sing a Telugu song\nParameter: Telugu song``` ```User: play phonics\nParameter: phonics``` ```User: learn phonics sounds\nParameter: phonics sounds```",
                }
            },
            "required": ["song_name"],
        },
    },
}


@register_function("play_music", play_music_function_desc, ToolType.SYSTEM_CTL)
def play_music(conn, song_name: str):
    try:
        music_intent = (
            f"Play music {song_name}" if song_name != "random" else "Play random music"
        )

        # Check event loop status
        if not conn.loop.is_running():
            conn.logger.bind(tag=TAG).error("Event loop is not running, unable to submit task")
            return ActionResponse(
                action=Action.RESPONSE, result="System busy", response="Please try again later"
            )

        # Submit async task
        task = conn.loop.create_task(
            handle_music_command(conn, music_intent)  # Wrap async logic
        )

        # Non-blocking callback handling
        def handle_done(f):
            try:
                f.result()  # Can handle success logic here
                conn.logger.bind(tag=TAG).info("Playback completed")
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"Playback failed: {e}")

        task.add_done_callback(handle_done)

        return ActionResponse(
            action=Action.NONE, result="Command received", response="Playing music for you"
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Error handling music intent: {e}")
        return ActionResponse(
            action=Action.RESPONSE, result=str(e), response="Error occurred while playing music"
        )


def _extract_song_name(text):
    """Extract song name from user input with multiple trigger patterns"""
    # Define various music-related keywords and patterns
    music_keywords = [
        "play music",
        "play",
        "sing",
        "sing a song",
        "sing me",
        "can you sing",
        "put on some music",
        "put on",
        "I want to hear",
        "listen to",
        "play some music",
        "music"
    ]
    
    text_lower = text.lower()
    
    # Try to extract song name after various patterns
    for keyword in music_keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in text_lower:
            # Find the position of the keyword
            keyword_pos = text_lower.find(keyword_lower)
            
            # Extract everything after the keyword
            after_keyword = text[keyword_pos + len(keyword):].strip()
            
            # Remove common words that might follow
            common_words = ["for me", "please", "now", "some", "a song", "the song"]
            for word in common_words:
                after_keyword = after_keyword.replace(word, "").strip()
            
            # If we found something meaningful after the keyword, return it
            if after_keyword and len(after_keyword) > 1:
                return after_keyword
    
    return None


def _detect_language_request(text):
    """Detect if user is requesting music from a specific language/folder"""
    text_lower = text.lower()
    
    # Define language mappings (you can add more languages as needed)
    language_mappings = {
        # Phonics variations (Educational content)
        "phonics": "phonics",
        "phonics song": "phonics",
        "phonics music": "phonics",
        "play phonics": "phonics",
        "sing phonics": "phonics",
        "learn phonics": "phonics",
        "phonics sounds": "phonics",
        "alphabet sounds": "phonics",
        "letter sounds": "phonics",
        
        # English variations
        "english": "English",
        "english song": "English", 
        "english music": "English",
        "any english": "English",
        
        # Telugu variations
        "telugu": "Telugu",
        "telugu song": "Telugu",
        "telugu music": "Telugu",
        "any telugu": "Telugu",
        
        # Hindi variations
        "hindi": "Hindi",
        "hindi song": "Hindi",
        "hindi music": "Hindi",
        "any hindi": "Hindi",
        
        # Tamil variations
        "tamil": "Tamil",
        "tamil song": "Tamil",
        "tamil music": "Tamil",
        "any tamil": "Tamil",
        
        # Add more languages as needed
        "kannada": "Kannada",
        "malayalam": "Malayalam",
        "bengali": "Bengali",
        "punjabi": "Punjabi",
        "marathi": "Marathi",
        "gujarati": "Gujarati",
    }
    
    # Check for language requests
    for key, folder_name in language_mappings.items():
        if key in text_lower:
            return folder_name
    
    return None


def _get_language_specific_files(music_dir, music_ext, language_folder):
    """Get music files from a specific language folder"""
    language_path = Path(music_dir) / language_folder
    
    if not language_path.exists():
        return [], []
    
    music_files = []
    music_file_names = []
    
    for file in language_path.rglob("*"):
        if file.is_file():
            ext = file.suffix.lower()
            if ext in music_ext:
                # Get relative path from the main music directory
                relative_path = str(file.relative_to(Path(music_dir)))
                music_files.append(relative_path)
                music_file_names.append(os.path.splitext(relative_path)[0])
    
    return music_files, music_file_names


def _find_best_match(potential_song, music_files):
    """Find the best matching song"""
    best_match = None
    highest_ratio = 0

    for music_file in music_files:
        song_name = os.path.splitext(music_file)[0]
        ratio = difflib.SequenceMatcher(None, potential_song, song_name).ratio()
        if ratio > highest_ratio and ratio > 0.4:
            highest_ratio = ratio
            best_match = music_file
    return best_match


def get_music_files(music_dir, music_ext):
    music_dir = Path(music_dir)
    music_files = []
    music_file_names = []
    for file in music_dir.rglob("*"):
        # Check if it's a file
        if file.is_file():
            # Get file extension
            ext = file.suffix.lower()
            # Check if extension is in the list
            if ext in music_ext:
                # Add relative path
                music_files.append(str(file.relative_to(music_dir)))
                music_file_names.append(
                    os.path.splitext(str(file.relative_to(music_dir)))[0]
                )
    return music_files, music_file_names


def initialize_music_handler(conn):
    global MUSIC_CACHE
    if MUSIC_CACHE == {}:
        if "play_music" in conn.config["plugins"]:
            MUSIC_CACHE["music_config"] = conn.config["plugins"]["play_music"]
            MUSIC_CACHE["music_dir"] = os.path.abspath(
                MUSIC_CACHE["music_config"].get("music_dir", "./music")  # Default path modified
            )
            MUSIC_CACHE["music_ext"] = MUSIC_CACHE["music_config"].get(
                "music_ext", (".mp3", ".wav", ".p3")
            )
            MUSIC_CACHE["refresh_time"] = MUSIC_CACHE["music_config"].get(
                "refresh_time", 60
            )
        else:
            MUSIC_CACHE["music_dir"] = os.path.abspath("./music")
            MUSIC_CACHE["music_ext"] = (".mp3", ".wav", ".p3")
            MUSIC_CACHE["refresh_time"] = 60
        # Get music file list
        MUSIC_CACHE["music_files"], MUSIC_CACHE["music_file_names"] = get_music_files(
            MUSIC_CACHE["music_dir"], MUSIC_CACHE["music_ext"]
        )
        MUSIC_CACHE["scan_time"] = time.time()
    return MUSIC_CACHE


async def handle_music_command(conn, text):
    initialize_music_handler(conn)
    global MUSIC_CACHE

    """Handle music playback commands"""
    clean_text = re.sub(r"[^\w\s]", "", text).strip()
    conn.logger.bind(tag=TAG).debug(f"Check if it's a music command: {clean_text}")

    # Check if user is requesting a specific language
    requested_language = _detect_language_request(clean_text)
    
    if os.path.exists(MUSIC_CACHE["music_dir"]):
        if time.time() - MUSIC_CACHE["scan_time"] > MUSIC_CACHE["refresh_time"]:
            # Refresh music file list
            MUSIC_CACHE["music_files"], MUSIC_CACHE["music_file_names"] = (
                get_music_files(MUSIC_CACHE["music_dir"], MUSIC_CACHE["music_ext"])
            )
            MUSIC_CACHE["scan_time"] = time.time()

        # If language is specified, get files from that language folder
        if requested_language:
            conn.logger.bind(tag=TAG).info(f"Language request detected: {requested_language}")
            language_files, language_file_names = _get_language_specific_files(
                MUSIC_CACHE["music_dir"], MUSIC_CACHE["music_ext"], requested_language
            )
            
            if language_files:
                # Play random song from the requested language folder
                selected_music = random.choice(language_files)
                conn.logger.bind(tag=TAG).info(f"Playing {requested_language} song: {selected_music}")
                await play_local_music(conn, specific_file=selected_music)
                return True
            else:
                conn.logger.bind(tag=TAG).warning(f"No {requested_language} songs found")
                # Fall back to general music if no songs found in requested language
        
        # Try to match specific song name
        potential_song = _extract_song_name(clean_text)
        if potential_song:
            best_match = _find_best_match(potential_song, MUSIC_CACHE["music_files"])
            if best_match:
                conn.logger.bind(tag=TAG).info(f"Found best matching song: {best_match}")
                await play_local_music(conn, specific_file=best_match)
                return True
    
    # Check if it's a general play music command
    await play_local_music(conn)
    return True


def _get_random_play_prompt(song_name):
    """Generate random play prompt"""
    # Remove file extension and extract just the filename (not the folder path)
    clean_name = os.path.splitext(os.path.basename(song_name))[0]
    prompts = [
        f"Now playing for you, '{clean_name}'",
        f"Please enjoy the song, '{clean_name}'",
        f"About to play for you, '{clean_name}'",
        f"Now bringing you, '{clean_name}'",
        f"Let's listen together to, '{clean_name}'",
        f"Next, please enjoy, '{clean_name}'",
        f"At this moment, presenting to you, '{clean_name}'",
    ]
     # Use random.choice directly, don't set seed
    return random.choice(prompts)


async def play_local_music(conn, specific_file=None):
    global MUSIC_CACHE
    """Play local music file"""
    try:
        if not os.path.exists(MUSIC_CACHE["music_dir"]):
            conn.logger.bind(tag=TAG).error(
                f"Music directory does not exist: " + MUSIC_CACHE["music_dir"]
            )
            return

        # Ensure path correctness
        if specific_file:
            selected_music = specific_file
            music_path = os.path.join(MUSIC_CACHE["music_dir"], specific_file)
        else:
            if not MUSIC_CACHE["music_files"]:
                conn.logger.bind(tag=TAG).error("No MP3 music files found")
                return
            selected_music = random.choice(MUSIC_CACHE["music_files"])
            music_path = os.path.join(MUSIC_CACHE["music_dir"], selected_music)

        if not os.path.exists(music_path):
            conn.logger.bind(tag=TAG).error(f"Selected music file does not exist: {music_path}")
            return
        text = _get_random_play_prompt(selected_music)
        await send_stt_message(conn, text)
        conn.dialogue.put(Message(role="assistant", content=text))

        if conn.intent_type == "intent_llm":
            conn.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=conn.sentence_id,
                    sentence_type=SentenceType.FIRST,
                    content_type=ContentType.ACTION,
                )
            )
        conn.tts.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=conn.sentence_id,
                sentence_type=SentenceType.MIDDLE,
                content_type=ContentType.TEXT,
                content_detail=text,
            )
        )
        conn.tts.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=conn.sentence_id,
                sentence_type=SentenceType.MIDDLE,
                content_type=ContentType.FILE,
                content_file=music_path,
            )
        )
        if conn.intent_type == "intent_llm":
            conn.tts.tts_text_queue.put(
                TTSMessageDTO(
                    sentence_id=conn.sentence_id,
                    sentence_type=SentenceType.LAST,
                    content_type=ContentType.ACTION,
                )
            )

    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Failed to play music: {str(e)}")
        conn.logger.bind(tag=TAG).error(f"Detailed error: {traceback.format_exc()}")