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

STORY_CACHE = {}

# Story categories mapping for better recognition
STORY_CATEGORIES = {
    "bedtime": ["Bedtime", "bedtime story", "sleep story", "night story"],
    "fantasy": ["Fantasy", "fantasy story", "magical story", "magic story"],
    "fairy tales": ["Fairy Tales", "fairy tale", "fairytale"],
    "educational": ["Educational", "educational story", "learning story", "education"],
    "adventure": ["Adventure", "adventure story", "exciting story"]
}

play_story_function_desc = {
    "type": "function",
    "function": {
        "name": "play_story",
        "description": (
            "ALWAYS use this function when user asks to play, tell, or hear ANY story in ANY language. "
            "This plays pre-recorded English story audio files from the story collection. "
            "DO NOT generate stories, always call this function for story requests. "
            "Note: All stories are in English regardless of requested language. "
            "Examples: 'play story', 'tell me a story', 'play bedtime story', 'I want to hear a fantasy story', "
            "'tell me a fairy tale', 'play an adventure story', 'educational story please', "
            "'play A Golden Gift', 'play The Boy Who Cried Wolf story', "
            "'कहानी सुनाओ' (Hindi), 'ಕಥೆ ಹೇಳಿ' (Kannada), 'கதை சொல்லுங்கள்' (Tamil)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "story_category": {
                    "type": "string",
                    "description": (
                        "Story category to play from. MUST be one of: 'bedtime', 'fantasy', 'fairy tales', 'educational', 'adventure', or 'random'. "
                        "Examples: User says 'bedtime story' -> use 'bedtime'. "
                        "User says 'fantasy story' -> use 'fantasy'. "
                        "User says 'fairy tale' -> use 'fairy tales'. "
                        "User says 'educational story' -> use 'educational'. "
                        "User says 'adventure story' -> use 'adventure'. "
                        "User says 'play story' or 'tell me a story' -> use 'random'. "
                        "If user mentions a specific story name, still use 'random' for category."
                    ),
                },
                "story_name": {
                    "type": "string",
                    "description": "Specific story name if user mentions one. Examples: If user says 'play A Golden Gift' -> use 'A Golden Gift'. If user says 'play The Boy Who Cried Wolf story' -> use 'The Boy Who Cried Wolf'. Leave empty if no specific story is mentioned.",
                },
                "requested_language": {
                    "type": "string",
                    "description": "Language user requested (e.g., 'hindi', 'kannada', 'tamil', 'english'). Optional - only set if user explicitly mentions a language. Note: All stories play in English regardless.",
                }
            },
            "required": ["story_category"],
        },
    },
}


@register_function("play_story", play_story_function_desc, ToolType.SYSTEM_CTL)
def play_story(conn, story_category: str = "random", story_name: str = None, requested_language: str = None):
    try:
        if story_name:
            story_intent = f"Playing story: {story_name}"
        elif story_category != "random":
            story_intent = f"Playing {story_category} story"
        else:
            story_intent = "Playing random story"
        
        if requested_language and requested_language.lower() != "english":
            story_intent += f" (Requested in {requested_language}, playing in English)"

        # Check event loop status
        if not conn.loop.is_running():
            conn.logger.bind(tag=TAG).error("Event loop not running, cannot submit task")
            return ActionResponse(
                action=Action.RESPONSE, result="System busy", response="Please try again later"
            )

        # Submit async task
        task = conn.loop.create_task(
            handle_story_command(conn, story_category, story_name, requested_language)
        )

        # Non-blocking callback handling
        def handle_done(f):
            try:
                f.result()
                conn.logger.bind(tag=TAG).info("Story playback completed")
            except Exception as e:
                conn.logger.bind(tag=TAG).error(f"Story playback failed: {e}")

        task.add_done_callback(handle_done)

        return ActionResponse(
            action=Action.NONE, result="Command received", response="Preparing to play your story"
        )
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Error handling story intent: {e}")
        return ActionResponse(
            action=Action.RESPONSE, result=str(e), response="Error occurred while playing story"
        )


def normalize_category_name(category_input):
    """Normalize story category name to match folder names"""
    if not category_input:
        return None
    
    category_lower = category_input.lower().strip()
    
    # Direct mapping for exact matches from LLM
    direct_mappings = {
        "bedtime": "Bedtime",
        "fantasy": "Fantasy", 
        "fairy tales": "Fairy Tales",
        "educational": "Educational",
        "adventure": "Adventure",
        "random": None  # None means select random category
    }
    
    # Check direct mappings first
    if category_lower in direct_mappings:
        return direct_mappings[category_lower]
    
    # Check against category variations
    for key, variations in STORY_CATEGORIES.items():
        for variation in variations:
            if variation.lower() in category_lower or category_lower in variation.lower():
                # Return the actual folder name
                if key == "bedtime":
                    return "Bedtime"
                elif key == "fantasy":
                    return "Fantasy"
                elif key == "fairy tales":
                    return "Fairy Tales"
                elif key == "educational":
                    return "Educational"
                elif key == "adventure":
                    return "Adventure"
    
    # If no match, return None to trigger random selection
    return None


def get_story_files(story_dir, story_ext):
    """Get all story files organized by category"""
    story_dir = Path(story_dir)
    story_files_by_category = {}
    all_story_files = []
    
    # Check if stories directory exists
    if not story_dir.exists():
        return {}, []
    
    # Iterate through category folders
    for category_folder in story_dir.iterdir():
        if category_folder.is_dir():
            category_name = category_folder.name
            story_files_by_category[category_name] = []
            
            # Get all story files in this category
            for file in category_folder.rglob("*"):
                if file.is_file():
                    ext = file.suffix.lower()
                    if ext in story_ext:
                        relative_path = str(file.relative_to(story_dir))
                        story_files_by_category[category_name].append(relative_path)
                        all_story_files.append(relative_path)
    
    return story_files_by_category, all_story_files


def initialize_story_handler(conn):
    """Initialize story handler with configuration"""
    global STORY_CACHE
    if STORY_CACHE == {}:
        if "play_story" in conn.config["plugins"]:
            STORY_CACHE["story_config"] = conn.config["plugins"]["play_story"]
            STORY_CACHE["story_dir"] = os.path.abspath(
                STORY_CACHE["story_config"].get("story_dir", "./stories")
            )
            STORY_CACHE["story_ext"] = STORY_CACHE["story_config"].get(
                "story_ext", (".mp3", ".wav", ".p3")
            )
            STORY_CACHE["refresh_time"] = STORY_CACHE["story_config"].get(
                "refresh_time", 300  # Refresh every 5 minutes
            )
        else:
            STORY_CACHE["story_dir"] = os.path.abspath("./stories")
            STORY_CACHE["story_ext"] = (".mp3", ".wav", ".p3")
            STORY_CACHE["refresh_time"] = 300
        
        # Get story files organized by category
        STORY_CACHE["story_files_by_category"], STORY_CACHE["all_story_files"] = get_story_files(
            STORY_CACHE["story_dir"], STORY_CACHE["story_ext"]
        )
        STORY_CACHE["scan_time"] = time.time()
        
        # Log available categories
        if STORY_CACHE["story_files_by_category"]:
            conn.logger.bind(tag=TAG).info(
                f"Found story categories: {list(STORY_CACHE['story_files_by_category'].keys())}"
            )
            for category, files in STORY_CACHE["story_files_by_category"].items():
                conn.logger.bind(tag=TAG).info(f"  {category}: {len(files)} stories")
    
    return STORY_CACHE


def find_best_story_match(story_name, story_files):
    """Find the best matching story from available files"""
    best_match = None
    highest_ratio = 0
    
    for story_file in story_files:
        # Extract just the filename without path and extension
        file_name = os.path.splitext(os.path.basename(story_file))[0]
        ratio = difflib.SequenceMatcher(None, story_name.lower(), file_name.lower()).ratio()
        if ratio > highest_ratio and ratio > 0.5:  # Higher threshold for stories
            highest_ratio = ratio
            best_match = story_file
    
    return best_match


async def handle_story_command(conn, category, specific_story=None, requested_language=None):
    """Handle story playback command"""
    initialize_story_handler(conn)
    global STORY_CACHE
    
    conn.logger.bind(tag=TAG).debug(f"Handling story command - Category: {category}, Story: {specific_story}, Language: {requested_language}")
    
    # Check if stories directory exists
    if not os.path.exists(STORY_CACHE["story_dir"]):
        conn.logger.bind(tag=TAG).error(f"Story directory does not exist: {STORY_CACHE['story_dir']}")
        await send_stt_message(conn, "Sorry, I couldn't find the story collection.")
        return
    
    # Refresh cache if needed
    if time.time() - STORY_CACHE["scan_time"] > STORY_CACHE["refresh_time"]:
        STORY_CACHE["story_files_by_category"], STORY_CACHE["all_story_files"] = get_story_files(
            STORY_CACHE["story_dir"], STORY_CACHE["story_ext"]
        )
        STORY_CACHE["scan_time"] = time.time()
    
    selected_story = None
    
    # If specific story name is provided, try to find it
    if specific_story:
        selected_story = find_best_story_match(specific_story, STORY_CACHE["all_story_files"])
        if selected_story:
            conn.logger.bind(tag=TAG).info(f"Found matching story: {selected_story}")
    
    # If no specific story found, select based on category
    if not selected_story:
        if category and category.lower() != "random":
            # Normalize category name
            normalized_category = normalize_category_name(category)
            
            # Try to find the category
            matching_category = None
            for cat_name in STORY_CACHE["story_files_by_category"].keys():
                if cat_name.lower() == normalized_category.lower():
                    matching_category = cat_name
                    break
            
            if matching_category and STORY_CACHE["story_files_by_category"][matching_category]:
                selected_story = random.choice(STORY_CACHE["story_files_by_category"][matching_category])
                conn.logger.bind(tag=TAG).info(f"Selected {matching_category} story: {selected_story}")
            else:
                conn.logger.bind(tag=TAG).warning(f"Category '{category}' not found or empty, selecting random story")
                if STORY_CACHE["all_story_files"]:
                    selected_story = random.choice(STORY_CACHE["all_story_files"])
        else:
            # Select random story from all available
            if STORY_CACHE["all_story_files"]:
                selected_story = random.choice(STORY_CACHE["all_story_files"])
                conn.logger.bind(tag=TAG).info(f"Selected random story: {selected_story}")
    
    if selected_story:
        await play_story_file(conn, selected_story, requested_language)
    else:
        conn.logger.bind(tag=TAG).error("No stories found in the collection")
        await send_stt_message(conn, "I'm sorry, I couldn't find any stories to play.")


def get_story_intro(story_file, requested_language=None):
    """Generate an introduction for the story"""
    # Extract story name and category
    parts = story_file.split(os.sep)
    if len(parts) > 1:
        category = parts[0]
        story_name = os.path.splitext(parts[-1])[0]
    else:
        category = "story"
        story_name = os.path.splitext(story_file)[0]
    
    # Clean up the story name (remove underscores, etc.)
    story_name = story_name.replace("_", " ").replace("-", " ")
    
    # Always use English intros since stories are in English
    intros = [
        f"Let me tell you a wonderful {category.lower()} story called '{story_name}'",
        f"Here's a {category.lower()} story for you: '{story_name}'",
        f"Get comfortable and enjoy this {category.lower()} story: '{story_name}'",
        f"I have a special {category.lower()} story for you called '{story_name}'",
        f"Listen carefully to this amazing story: '{story_name}'",
        f"Once upon a time... Let's begin '{story_name}'",
    ]
    
    intro = random.choice(intros)
    
    # Add note if requested in another language
    if requested_language and requested_language != "english":
        intro = f"Playing English story. {intro}"
    
    return intro


async def play_story_file(conn, story_file, requested_language=None):
    """Play the selected story file"""
    try:
        story_path = os.path.join(STORY_CACHE["story_dir"], story_file)
        
        if not os.path.exists(story_path):
            conn.logger.bind(tag=TAG).error(f"Story file does not exist: {story_path}")
            return
        
        # Generate and send introduction (always in English)
        intro_text = get_story_intro(story_file, requested_language)
        await send_stt_message(conn, intro_text)
        conn.dialogue.put(Message(role="assistant", content=intro_text))
        
        # Send TTS messages to play the story
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
                content_detail=intro_text,
            )
        )
        
        conn.tts.tts_text_queue.put(
            TTSMessageDTO(
                sentence_id=conn.sentence_id,
                sentence_type=SentenceType.MIDDLE,
                content_type=ContentType.FILE,
                content_file=story_path,
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
        
        conn.logger.bind(tag=TAG).info(f"Playing story: {story_path}")
        
    except Exception as e:
        conn.logger.bind(tag=TAG).error(f"Failed to play story: {str(e)}")
        conn.logger.bind(tag=TAG).error(f"Detailed error: {traceback.format_exc()}")