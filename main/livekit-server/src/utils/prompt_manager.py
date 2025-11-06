"""
PromptManager: Handles template-based prompt system
Responsible for loading base template, fetching personalities, gathering context, and rendering prompts
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from jinja2 import Template
import pytz

logger = logging.getLogger("prompt_manager")

# Weekday mapping
WEEKDAY_MAP = {
    "Monday": "Monday",
    "Tuesday": "Tuesday",
    "Wednesday": "Wednesday",
    "Thursday": "Thursday",
    "Friday": "Friday",
    "Saturday": "Saturday",
    "Sunday": "Sunday",
}

# Emoji list for prompts
EMOJI_LIST = [
    "😶", "🙂", "😆", "😂", "😔", "😠", "😭", "😍",
    "😳", "😲", "😱", "🤔", "😉", "😎", "😌", "🤤",
    "😘", "😏", "😴", "😜", "🙄"
]


class PromptManager:
    """Manages template-based prompts with dynamic context injection"""

    def __init__(self, db_helper, config: Dict[str, Any]):
        """
        Initialize PromptManager

        Args:
            db_helper: DatabaseHelper instance for API calls
            config: Configuration dictionary from config.yaml
        """
        self.db_helper = db_helper
        self.config = config
        self.base_template = None  # Cached base template (loaded once)
        self.personality_cache = {}  # Cache personalities {template_id: {content, timestamp}}
        self.location_cache = {}  # Cache locations {device_mac: {location, timestamp}}
        self.weather_cache = {}  # Cache weather {location: {weather, timestamp}}

        # Cache timeouts (in seconds)
        self.personality_cache_timeout = 3600  # 1 hour
        self.location_cache_timeout = 86400  # 1 day
        self.weather_cache_timeout = 300  # 5 minutes

        # Load base template on initialization
        self._load_base_template()

    def _load_base_template(self) -> str:
        """
        Load base template from disk (cached in memory forever)

        Returns:
            str: Base template content
        """
        if self.base_template is not None:
            return self.base_template

        try:
            # Get the livekit-server root directory
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            template_path = os.path.join(current_dir, "base-agent-template.txt")

            if not os.path.exists(template_path):
                logger.error(f"Base template file not found: {template_path}")
                raise FileNotFoundError(f"base-agent-template.txt not found at {template_path}")

            with open(template_path, 'r', encoding='utf-8') as f:
                self.base_template = f.read()

            logger.info(f"✅ Loaded base template from {template_path} ({len(self.base_template)} chars)")
            return self.base_template

        except Exception as e:
            logger.error(f"Failed to load base template: {e}")
            raise

    async def get_personality_from_db(self, template_id: str) -> str:
        """
        Get agent personality from database (cached for 1 hour)

        Args:
            template_id: Template ID from database

        Returns:
            str: Agent personality/prompt
        """
        import time

        # Check cache first
        if template_id in self.personality_cache:
            cached = self.personality_cache[template_id]
            if (time.time() - cached['timestamp']) < self.personality_cache_timeout:
                logger.debug(f"📦 Using cached personality for template_id: {template_id}")
                return cached['content']

        # Fetch from database via API
        try:
            personality = await self.db_helper.fetch_template_content(template_id)

            if personality:
                # Cache the result
                self.personality_cache[template_id] = {
                    'content': personality,
                    'timestamp': time.time()
                }
                logger.info(f"✅ Fetched personality for template_id: {template_id} ({len(personality)} chars)")
                return personality
            else:
                logger.warning(f"No personality found for template_id: {template_id}")
                return "You are a helpful AI assistant for children."

        except Exception as e:
            logger.error(f"Error fetching personality for template_id {template_id}: {e}")
            return "You are a helpful AI assistant for children."

    def _get_current_time_info(self) -> tuple:
        """
        Get current time information (no cache - always current)

        Returns:
            tuple: (today_date, today_weekday, indian_date, current_time)
        """
        try:
            # Use Indian Standard Time (IST)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)

            today_date = now.strftime("%Y-%m-%d")
            today_weekday = WEEKDAY_MAP[now.strftime("%A")]
            current_time = now.strftime("%H:%M")

            # Indian date format (e.g., "15 January 2025")
            indian_date = now.strftime("%d %B %Y")

            return today_date, today_weekday, indian_date, current_time

        except Exception as e:
            logger.error(f"Error getting time info: {e}")
            # Fallback to basic datetime
            now = datetime.now()
            return (
                now.strftime("%Y-%m-%d"),
                WEEKDAY_MAP[now.strftime("%A")],
                now.strftime("%d %B %Y"),
                now.strftime("%H:%M")
            )

    async def _get_location(self, device_mac: str) -> str:
        """
        Get device location (cached for 1 day)

        Args:
            device_mac: Device MAC address

        Returns:
            str: Location (city name)
        """
        import time

        # Check cache first
        if device_mac in self.location_cache:
            cached = self.location_cache[device_mac]
            if (time.time() - cached['timestamp']) < self.location_cache_timeout:
                logger.debug(f"📦 Using cached location for MAC: {device_mac}")
                return cached['location']

        # Fetch from database/API
        try:
            location = await self.db_helper.get_device_location(device_mac)

            if location:
                # Cache the result
                self.location_cache[device_mac] = {
                    'location': location,
                    'timestamp': time.time()
                }
                logger.info(f"✅ Fetched location for MAC {device_mac}: {location}")
                return location
            else:
                logger.warning(f"No location found for MAC: {device_mac}")
                return "Unknown location"

        except Exception as e:
            logger.error(f"Error fetching location for MAC {device_mac}: {e}")
            return "Unknown location"

    async def _get_weather(self, location: str) -> str:
        """
        Get weather forecast for location (cached for 5 minutes)

        Args:
            location: City name

        Returns:
            str: Weather forecast (7-day)
        """
        import time

        if not location or location == "Unknown location":
            return "Weather information not available"

        # Check cache first
        if location in self.weather_cache:
            cached = self.weather_cache[location]
            if (time.time() - cached['timestamp']) < self.weather_cache_timeout:
                logger.debug(f"📦 Using cached weather for location: {location}")
                return cached['weather']

        # Fetch from weather API
        try:
            weather = await self.db_helper.get_weather_forecast(location)

            if weather:
                # Cache the result
                self.weather_cache[location] = {
                    'weather': weather,
                    'timestamp': time.time()
                }
                logger.info(f"✅ Fetched weather for {location}")
                return weather
            else:
                logger.warning(f"No weather data found for location: {location}")
                return "Weather information not available"

        except Exception as e:
            logger.error(f"Error fetching weather for {location}: {e}")
            return "Weather information not available"

    async def get_context_info(self, device_mac: str, child_profile: dict = None) -> Dict[str, Any]:
        """
        Gather all context variables for template rendering

        Args:
            device_mac: Device MAC address
            child_profile: Optional child profile data

        Returns:
            dict: Context variables
        """
        # Get time info (always current)
        today_date, today_weekday, indian_date, current_time = self._get_current_time_info()

        # NOTE: Location and weather removed from template - API calls skipped for performance
        # If you need them again, uncomment the lines below:
        # local_address = await self._get_location(device_mac)
        # weather_info = await self._get_weather(local_address)

        context = {
            'current_time': current_time,
            'today_date': today_date,
            'today_weekday': today_weekday,
            'lunar_date': indian_date,
            'emojiList': ', '.join(EMOJI_LIST)
        }

        # Add child profile variables if available
        if child_profile:
            context['child_name'] = child_profile.get('name', '')
            context['child_age'] = child_profile.get('age', '')
            context['age_group'] = child_profile.get('ageGroup', '')
            context['child_gender'] = child_profile.get('gender', '')
            context['child_interests'] = child_profile.get('interests', '')
            logger.debug(f"👶 Added child profile to context: {context['child_name']}, age {context['child_age']}")
        else:
            # Provide empty strings for child profile variables (template will hide them)
            context['child_name'] = ''
            context['child_age'] = ''
            context['age_group'] = ''
            context['child_gender'] = ''
            context['child_interests'] = ''

        logger.debug(f"📋 Gathered context for {device_mac}: {today_date}")
        return context

    async def build_enhanced_prompt(
        self,
        template_id: str,
        device_mac: str,
        child_profile: dict = None
    ) -> str:
        """
        Build fully enhanced prompt by:
        1. Loading base template
        2. Fetching personality from database
        3. Gathering context info (including child profile)
        4. Rendering template with Jinja2

        Args:
            template_id: Template ID from database
            device_mac: Device MAC address
            child_profile: Optional child profile data

        Returns:
            str: Fully rendered prompt with all placeholders replaced
        """
        try:
            # Step 1: Load base template (from memory cache)
            base_template_str = self._load_base_template()

            # Step 2: Fetch personality (cached 1 hour)
            personality = await self.get_personality_from_db(template_id)

            # Step 3: Gather context (various cache levels, including child profile)
            context = await self.get_context_info(device_mac, child_profile)

            # Step 4: Render template
            context['base_prompt'] = personality  # Insert personality into {{base_prompt}}

            # IMPORTANT: Configure Jinja2 to preserve Python format() placeholders like {self.start_word}
            # By using variable_start_string and variable_end_string with triple braces,
            # we avoid conflicts with single-brace Python format syntax
            from jinja2 import Environment
            env = Environment(
                variable_start_string='{{{',  # Use {{{ instead of {{
                variable_end_string='}}}',    # Use }}} instead of }}
                block_start_string='{%',
                block_end_string='%}',
                comment_start_string='{#',
                comment_end_string='#}'
            )
            template = env.from_string(base_template_str)

            # First pass: Render with Jinja2 (child profile, dates, etc.)
            jinja_rendered = template.render(**context)

            # Second pass: The {self.xxx} placeholders remain intact for Python format() later
            enhanced_prompt = jinja_rendered

            logger.info(
                f"✅ Built enhanced prompt: template_id={template_id}, "
                f"device_mac={device_mac}, length={len(enhanced_prompt)} chars"
            )

            return enhanced_prompt

        except Exception as e:
            logger.error(f"Failed to build enhanced prompt: {e}")
            # Fallback to basic prompt
            return personality if 'personality' in locals() else "You are a helpful AI assistant for children."

    def clear_caches(self):
        """Clear all caches (for testing/debugging)"""
        self.personality_cache.clear()
        self.location_cache.clear()
        self.weather_cache.clear()
        logger.info("🗑️ Cleared all prompt caches")

    def clear_personality_cache(self, template_id: str = None):
        """Clear personality cache (optionally for specific template_id)"""
        if template_id:
            self.personality_cache.pop(template_id, None)
            logger.info(f"🗑️ Cleared personality cache for template_id: {template_id}")
        else:
            self.personality_cache.clear()
            logger.info("🗑️ Cleared all personality caches")

    def clear_location_cache(self, device_mac: str = None):
        """Clear location cache (optionally for specific device)"""
        if device_mac:
            self.location_cache.pop(device_mac, None)
            logger.info(f"🗑️ Cleared location cache for MAC: {device_mac}")
        else:
            self.location_cache.clear()
            logger.info("🗑️ Cleared all location caches")

    def clear_weather_cache(self, location: str = None):
        """Clear weather cache (optionally for specific location)"""
        if location:
            self.weather_cache.pop(location, None)
            logger.info(f"🗑️ Cleared weather cache for location: {location}")
        else:
            self.weather_cache.clear()
            logger.info("🗑️ Cleared all weather caches")
