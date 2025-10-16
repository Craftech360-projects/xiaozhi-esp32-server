import logging
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, Dict, Any
import pytz
import random
import inspect
import asyncio
from livekit.agents import (
    Agent,
    RunContext,
    function_tool,
)
from .filtered_agent import FilteredAgent
from src.utils.database_helper import DatabaseHelper
logger = logging.getLogger("agent")

# Mode name aliases for handling transcript variations
# Keys must match EXACT database mode names
MODE_ALIASES = {
    "Cheeko": ["chiko", "chico", "cheeko", "cheek o", "default", "default mode", "normal mode"],
    "Story": ["story", "story mode", "story time", "storytelling", "storyteller", "tell stories", "tell story", "story teller"],
    "Music": ["music", "music mode", "musician", "music time", "sing", "singing", "song", "songs"],
    "Tutor": ["tutor", "tutor mode", "teacher", "teach", "teaching", "study", "study mode", "learning", "learn"],
    "Chat": ["chat", "chat mode", "talk", "conversation", "friend", "buddy", "chatting"],
    
}

def normalize_mode_name(mode_input: str) -> str:
    """
    Normalize mode name input to handle transcript variations

    Args:
        mode_input: Raw mode name from speech transcript

    Returns:
        Normalized canonical mode name or original input if no match
    """
    if not mode_input:
        return mode_input

    # Normalize: lowercase, strip whitespace, remove special chars
    normalized = mode_input.lower().strip()
    normalized = normalized.replace("-", " ").replace("_", " ")

    # Direct match first (case-insensitive comparison with canonical names)
    for canonical_name in MODE_ALIASES.keys():
        if normalized == canonical_name.lower():
            return canonical_name

    # Check aliases
    for canonical_name, aliases in MODE_ALIASES.items():
        if normalized in [alias.lower() for alias in aliases]:
            logger.info(f"🔍 Matched '{mode_input}' → '{canonical_name}' via alias")
            return canonical_name

    # Check if input matches canonical name when spaces are removed
    # (e.g., "music maestro" -> "musicmaestro" -> "MusicMaestro")
    normalized_no_space = normalized.replace(" ", "")
    for canonical_name in MODE_ALIASES.keys():
        if normalized_no_space == canonical_name.lower():
            logger.info(f"🔍 Matched '{mode_input}' → '{canonical_name}' via space removal")
            return canonical_name

    # No match found - return original for backend to handle
    logger.warning(f"⚠️ No alias match found for '{mode_input}', passing as-is")
    return mode_input

class Assistant(FilteredAgent):
    """Main AI Assistant agent class with TTS text filtering"""

    def __init__(self, instructions: str = None, tts_provider=None) -> None:
        # Use provided instructions or fallback to a basic prompt
        if instructions is None:
            instructions = "You are a helpful AI assistant."

        super().__init__(instructions=instructions, tts_provider=tts_provider)

        # These will be injected by main.py
        self.music_service = None
        self.story_service = None
        self.audio_player = None
        self.unified_audio_player = None
        self.device_control_service = None
        self.mcp_executor = None

        # Room and device information
        self.room_name = None
        self.device_mac = None

        # Session reference for dynamic updates
        self._agent_session = None

        # Log registered function tools (for debugging)
        logger.info("🔧 Assistant initialized, checking function tools...")
        try:
            # Log check_battery_level function signature specifically
            if hasattr(self, 'check_battery_level'):
                battery_func = getattr(self, 'check_battery_level')
                sig = inspect.signature(battery_func)
                logger.info(f"🔋 check_battery_level signature: {sig}")
                logger.info(f"🔋 check_battery_level parameters: {sig.parameters}")
                for param_name, param in sig.parameters.items():
                    if param_name not in ['self', 'context']:
                        logger.info(f"🔋   - {param_name}: default={param.default}, annotation={param.annotation}")
                logger.info(f"🔋 check_battery_level return annotation: {sig.return_annotation}")
                logger.info(f"🔋 check_battery_level docstring: {battery_func.__doc__}")

            # Try to access function tools from the agent's internal attributes
            if hasattr(self, '_function_tools'):
                logger.info(f"🔧 Found {len(self._function_tools)} function tools")
                for tool_name, tool in self._function_tools.items():
                    logger.info(f"🔧   - {tool_name}: {tool}")
                    if tool_name == 'check_battery_level':
                        logger.info(f"🔋 DETAILED check_battery_level tool info: {dir(tool)}")
                        if hasattr(tool, 'schema'):
                            logger.info(f"🔋 check_battery_level schema: {tool.schema}")
                        if hasattr(tool, 'parameters'):
                            logger.info(f"🔋 check_battery_level parameters: {tool.parameters}")
            else:
                logger.info("🔧 No _function_tools attribute found")
        except Exception as e:
            logger.warning(f"🔧 Error inspecting function tools: {e}")
            import traceback
            logger.warning(f"🔧 Traceback: {traceback.format_exc()}")



    def set_services(self, music_service, story_service, audio_player, unified_audio_player=None, device_control_service=None, mcp_executor=None):
        """Set the music, story, device control services, and MCP executor"""
        self.music_service = music_service
        self.story_service = story_service
        self.audio_player = audio_player
        self.unified_audio_player = unified_audio_player
        self.device_control_service = device_control_service
        self.mcp_executor = mcp_executor

    def set_room_info(self, room_name: str = None, device_mac: str = None):
        """Set room name and device MAC address"""
        self.room_name = room_name
        self.device_mac = device_mac
        logger.info(f"📍 Room info set - Room: {room_name}, MAC: {device_mac}")

    def set_agent_session(self, session):
        """Set session reference for dynamic updates"""
        self._agent_session = session
        logger.info(f"🔗 Session reference stored for dynamic updates")

    @function_tool
    async def update_agent_mode(self, context: RunContext, mode_name: str) -> str:
        """Update agent configuration mode by applying a template

        Args:
            mode_name: Template mode name (e.g., "Cheeko", "StudyHelper")

        Returns:
            Success or error message
        """
        try:
            import os
            import aiohttp

            # 1. Validate device MAC
            if not self.device_mac:
                return "Device MAC address is not available"

            # 2. Get Manager API configuration
            manager_api_url = os.getenv("MANAGER_API_URL")
            manager_api_secret = os.getenv("MANAGER_API_SECRET")

            if not manager_api_url or not manager_api_secret:
                return "Manager API is not configured"

            # 3. Fetch agent_id using DatabaseHelper
            db_helper = DatabaseHelper(manager_api_url, manager_api_secret)
            agent_id = await db_helper.get_agent_id(self.device_mac)

            if not agent_id:
                return f"No agent found for device MAC: {self.device_mac}"

            # Normalize mode name to handle transcript variations
            normalized_mode = normalize_mode_name(mode_name)
            if normalized_mode != mode_name:
                logger.info(f"🔄 Mode name normalized: '{mode_name}' → '{normalized_mode}'")

            logger.info(f"🔄 Updating agent {agent_id} to mode: {normalized_mode}")

            # 4. Call update-mode API
            url = f"{manager_api_url}/agent/update-mode"
            headers = {
                "Authorization": f"Bearer {manager_api_secret}",
                "Content-Type": "application/json"
            }
            payload = {
                "agentId": agent_id,
                "modeName": normalized_mode
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.put(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ Agent mode updated in database to '{normalized_mode}' for agent: {agent_id}")
                        data = result.get('data')
                        logger.info(f"📦 API Response: code={result.get('code')}, has_data={bool(data)}, data_length={len(data) if data else 0}")

                        # 5. Get the new prompt from the API response directly
                        if result.get('code') == 0 and result.get('data'):
                            new_prompt = result.get('data')

                            # 6. Update the agent's instructions dynamically
                            # Note: self.instructions is read-only, so we update the internal attribute
                            self._instructions = new_prompt
                            logger.info(f"📝 Instructions updated dynamically (length: {len(new_prompt)} chars)")
                            logger.info(f"📝 New prompt preview: {new_prompt[:100]}...")

                            # 7. Update session if available (for immediate effect)
                            if self._agent_session:
                                try:
                                    # Update session's agent internal instructions
                                    self._agent_session._agent._instructions = new_prompt
                                    logger.info(f"🔄 Session instructions updated in real-time!")
                                except Exception as e:
                                    logger.warning(f"⚠️ Could not update session directly: {e}")

                            return f"Successfully updated agent mode to '{normalized_mode}' and reloaded the new prompt! The changes are now active in this conversation."
                        else:
                            logger.warning(f"⚠️ No prompt data in response, but mode updated in database")
                            return f"Mode updated to '{normalized_mode}' in database. Please reconnect to apply changes."
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to update mode: {response.status} - {error_text}")
                        return f"Failed to update mode: {error_text}"

        except aiohttp.ClientError as e:
            logger.error(f"Network error updating agent mode: {e}")
            return f"Network error: Unable to connect to server"
        except Exception as e:
            logger.error(f"Error updating agent mode: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return f"Error updating agent mode: {str(e)}"

    @function_tool
    async def lookup_weather(self, context: RunContext, location: str):
        """Look up weather information for a specific location"""
        logger.info(f"Looking up weather for {location}")
        return "sunny with a temperature of 70 degrees."

    @function_tool
    async def play_music(
        self,
        context: RunContext,
        song_name: Optional[str] = None,
        language: Optional[str] = None
    ):
        """Play music - either a specific song or random music

        Args:
            song_name: Optional specific song to search for
            language: Optional language preference (English, Hindi, Telugu, etc.)
        """
        try:
            logger.info(f"Music request - song: '{song_name}', language: '{language}'")

            if not self.music_service:
                return "Sorry, music service is not available right now."

            # Use unified audio player which injects music into TTS queue
            player = self.unified_audio_player if self.unified_audio_player else self.audio_player
            if not player:
                return "Sorry, audio player is not available right now."

            if song_name:
                # Search for specific song
                songs = await self.music_service.search_songs(song_name, language)
                if songs:
                    song = songs[0]  # Take first match
                    logger.info(f"Found song: {song['title']} in {song['language']}")
                else:
                    logger.info(f"No songs found for '{song_name}', playing random song")
                    song = await self.music_service.get_random_song(language)
            else:
                # Play random song
                song = await self.music_service.get_random_song(language)

            if not song:
                return "Sorry, I couldn't find any music to play right now."

            # Send music start signal to device via data channel FIRST
            try:
                import json
                music_start_data = {
                    "type": "music_playback_started",
                    "title": song['title'],
                    "language": song.get('language', 'Unknown'),
                    "message": f"Now playing: {song['title']}"
                }
                # Try different ways to access the room
                room = None
                if hasattr(context, 'room'):
                    room = context.room
                elif self.unified_audio_player and self.unified_audio_player.context:
                    room = self.unified_audio_player.context.room
                elif self.audio_player and self.audio_player.context:
                    room = self.audio_player.context.room

                if room:
                    await room.local_participant.publish_data(
                        json.dumps(music_start_data).encode(),
                        topic="music_control"
                    )
                    logger.info(f"Sent music_playback_started via data channel: {song['title']}")
            except Exception as e:
                logger.warning(f"Failed to send music start signal: {e}")

            # Start playing the song through TTS channel - this will queue it
            await player.play_from_url(song['url'], song['title'])

            # Return special instruction to suppress immediate response
            # The agent should stay silent while music plays
            return "[MUSIC_PLAYING - STAY_SILENT]"

        except Exception as e:
            logger.error(f"Error playing music: {e}")
            return "Sorry, I encountered an error while trying to play music."

    @function_tool
    async def play_story(
        self,
        context: RunContext,
        story_name: Optional[str] = None,
        category: Optional[str] = None
    ):
        """Play a story - either a specific story or random story

        Args:
            story_name: Optional specific story to search for
            category: Optional category preference (Adventure, Bedtime, Educational, etc.)
        """
        try:
            logger.info(f"Story request - story: '{story_name}', category: '{category}'")

            if not self.story_service:
                return "Sorry, story service is not available right now."

            # Use unified audio player which injects music into TTS queue
            player = self.unified_audio_player if self.unified_audio_player else self.audio_player
            if not player:
                return "Sorry, audio player is not available right now."

            if story_name:
                # Search for specific story
                stories = await self.story_service.search_stories(story_name, category)
                if stories:
                    story = stories[0]  # Take first match
                    logger.info(f"Found story: {story['title']} in {story['category']}")
                else:
                    logger.info(f"No stories found for '{story_name}', playing random story")
                    story = await self.story_service.get_random_story(category)
            else:
                # Play random story
                story = await self.story_service.get_random_story(category)

            if not story:
                return "Sorry, I couldn't find any stories to play right now."

            # Start playing the story through TTS channel
            await player.play_from_url(story['url'], story['title'])

            # Return special instruction to suppress immediate response
            # The agent should stay silent while story plays
            return "[STORY_PLAYING - STAY_SILENT]"

        except Exception as e:
            logger.error(f"Error playing story: {e}")
            return "Sorry, I encountered an error while trying to play the story."

    @function_tool
    async def stop_audio(self, context: RunContext):
        """Stop any currently playing audio (music or story) and return to listening state"""
        try:
            from ..utils.audio_state_manager import audio_state_manager
            import json

            # Send music stop signal to device via data channel
            try:
                music_stop_data = {
                    "type": "music_playback_stopped"
                }
                # Try different ways to access the room
                room = None
                if hasattr(context, 'room'):
                    room = context.room
                elif self.unified_audio_player and self.unified_audio_player.context:
                    room = self.unified_audio_player.context.room
                elif self.audio_player and self.audio_player.context:
                    room = self.audio_player.context.room

                if room:
                    await room.local_participant.publish_data(
                        json.dumps(music_stop_data).encode(),
                        topic="music_control"
                    )
                    logger.info("Sent music_playback_stopped via data channel")
                else:
                    logger.warning("Could not access room for data channel")
            except Exception as e:
                logger.warning(f"Failed to send music stop signal: {e}")

            # Stop both audio players
            stopped_any = False

            if self.unified_audio_player:
                try:
                    await self.unified_audio_player.stop()
                    stopped_any = True
                    logger.info("Stopped unified audio player")
                except Exception as e:
                    logger.warning(f"Error stopping unified audio player: {e}")

            if self.audio_player:
                try:
                    await self.audio_player.stop()
                    stopped_any = True
                    logger.info("Stopped foreground audio player")
                except Exception as e:
                    logger.warning(f"Error stopping foreground audio player: {e}")

            # Force the system back to listening state
            was_playing = audio_state_manager.force_listening_state()

            if was_playing or stopped_any:
                # Send explicit agent state change to ensure device returns to listening
                try:
                    agent_state_data = {
                        "type": "agent_state_changed",
                        "data": {
                            "old_state": "speaking",
                            "new_state": "listening"
                        }
                    }
                    # Try different ways to access the room
                    room = None
                    if hasattr(context, 'room'):
                        room = context.room
                    elif self.unified_audio_player and self.unified_audio_player.context:
                        room = self.unified_audio_player.context.room
                    elif self.audio_player and self.audio_player.context:
                        room = self.audio_player.context.room

                    if room:
                        await room.local_participant.publish_data(
                            json.dumps(agent_state_data).encode(),
                            reliable=True
                        )
                        logger.info("Sent forced agent_state_changed to listening")
                    else:
                        logger.warning("Could not access room for listening state signal")
                except Exception as e:
                    logger.warning(f"Failed to send listening state signal: {e}")

                return "Stopped playing audio. Ready to listen."
            else:
                return "No audio is currently playing."

        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
            return "Sorry, I encountered an error while trying to stop audio."

    @function_tool
    async def set_device_volume(self, context: RunContext, volume: int):
        """Set device volume to a specific level (0-100)

        Args:
            volume: Volume level from 0 (mute) to 100 (maximum)
        """
        if not self.mcp_executor:
            return "Sorry, device control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.set_volume(volume)

    @function_tool
    async def adjust_device_volume(self, context: RunContext, action: str, step: int = 10):
        """Adjust device volume up or down

        Args:
            action: Either "up", "down", "increase", "decrease"
            step: Volume step size (default 10)
        """
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.adjust_volume(action, step)

    @function_tool
    async def get_device_volume(self, context: RunContext):
        """Get current device volume level"""
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.get_volume()


    @function_tool
    async def get_time_date(
        self,
        context: RunContext,
        query_type: str = "time"
    ) -> str:
        """
        Get current time, date, or calendar information.

        Args:
            query_type: "time", "date", "calendar", or "both"

        Examples:
            - "what time is it?" -> query_type="time"
            - "what's today's date?" -> query_type="date"
            - "tell me date and time" -> query_type="both"
        """
        try:
            # Get Indian Standard Time
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.now(ist)

            if query_type == "time":
                time_str = now.strftime('%I:%M %p IST')
                return f"The current time is {time_str}"

            elif query_type == "date":
                date_str = now.strftime('%A, %B %d, %Y')
                return f"Today's date is {date_str}"

            elif query_type == "both":
                time_str = now.strftime('%I:%M %p IST')
                date_str = now.strftime('%A, %B %d, %Y')
                return f"Today is {date_str} and the time is {time_str}"

            elif query_type == "calendar":
                # Basic Hindu calendar info
                vikram_year = now.year + 57
                hindu_months = [
                    "Paush", "Magh", "Falgun", "Chaitra", "Vaishakh", "Jyeshtha",
                    "Ashadh", "Shravan", "Bhadrapada", "Ashwin", "Kartik", "Margashirsha"
                ]
                hindu_month = hindu_months[now.month - 1]

                calendar_info = (
                    f"Today is {now.strftime('%A, %B %d, %Y')} ({now.strftime('%I:%M %p IST')}). "
                    f"According to the Hindu calendar, this is {hindu_month} in Vikram Samvat year {vikram_year}."
                )
                return calendar_info

            else:
                # Default to both
                time_str = now.strftime('%I:%M %p IST')
                date_str = now.strftime('%A, %B %d, %Y')
                return f"Today is {date_str} and the time is {time_str}"

        except Exception as e:
            logger.error(f"Time/date tool error: {e}")
            return f"Sorry, I encountered an error getting the time and date: {str(e)}"

    @function_tool
    async def get_weather(
        self,
        context: RunContext,
        location: Optional[str] = None
    ) -> str:
        """
        Get weather for specified or default location.

        Args:
            location: City name (optional, defaults to Bangalore)

        Examples:
            - "weather in bangalore" -> location="bangalore"
            - "how's the weather?" -> location=None (uses default)
            - "mumbai weather" -> location="mumbai"
        """
        try:
            import os

            # Get API key from environment
            api_key = os.getenv('WEATHER_API')
            if not api_key:
                return "Weather service is not configured. Please set the WEATHER_API environment variable."

            # Default location if none specified
            if not location:
                location = "Bangalore"

            # Normalize location name for Indian cities
            location = self._normalize_indian_city_name(location)

            # Fetch weather data
            weather_data = await self._fetch_weather_data(location, api_key)

            if weather_data:
                return self._format_weather_response(weather_data, location)
            else:
                return f"Unable to get weather data for {location}. Please check the city name and try again."

        except Exception as e:
            logger.error(f"Weather tool error: {e}")
            return f"Sorry, I encountered an error getting the weather: {str(e)}"

    def _normalize_indian_city_name(self, city_name: str) -> str:
        """Normalize Indian city names for better API recognition"""
        if not city_name:
            return city_name

        # Indian city mappings
        city_mappings = {
            "bombay": "Mumbai",
            "calcutta": "Kolkata",
            "madras": "Chennai",
            "bangalore": "Bengaluru",
            "poona": "Pune",
            "delhi": "New Delhi"
        }

        city_lower = city_name.lower().strip()
        return city_mappings.get(city_lower, city_name.title())

    async def _fetch_weather_data(self, location: str, api_key: str) -> Optional[Dict]:
        """Fetch weather data from OpenWeatherMap API"""
        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": location,
                "appid": api_key,
                "units": "metric",
                "lang": "en"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return None

    def _format_weather_response(self, weather_data: Dict, location: str) -> str:
        """Format weather data into a readable response"""
        try:
            temp = round(weather_data["main"]["temp"])
            feels_like = round(weather_data["main"]["feels_like"])
            humidity = weather_data["main"]["humidity"]
            description = weather_data["weather"][0]["description"].title()

            weather_report = (
                f"The weather in {location} is currently {temp}°C with {description}. "
                f"It feels like {feels_like}°C and the humidity is {humidity}%."
            )

            return weather_report

        except Exception as e:
            logger.error(f"Error formatting weather response: {e}")
            return f"Weather data received for {location} but formatting failed."

    @function_tool
    async def get_news(
        self,
        context: RunContext,
        source: str = "random"
    ) -> str:
        """
        Get latest Indian news from major sources.

        Args:
            source: News source name or "random" for random source

        Examples:
            - "tell me news" -> source="random"
            - "latest news" -> source="random"
            - "times of india news" -> source="times of india"
        """
        try:
            # Indian news sources
            news_sources = {
                "times_of_india": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
                "hindu": "https://www.thehindu.com/feeder/default.rss",
                "indian_express": "https://indianexpress.com/feed/",
                "ndtv": "https://feeds.feedburner.com/ndtvnews-top-stories"
            }

            # Select source
            if source == "random":
                source_key = random.choice(list(news_sources.keys()))
            else:
                source_key = None
                source_lower = source.lower().replace(" ", "_")
                for key in news_sources.keys():
                    if key.replace("_", " ") in source.lower() or source.lower() in key.replace("_", " "):
                        source_key = key
                        break
                if not source_key:
                    source_key = "times_of_india"

            # Fetch news
            news_data = await self._fetch_news_data(news_sources[source_key])

            if news_data:
                # Select random news item
                selected_news = random.choice(news_data)
                return self._format_news_response(selected_news, source_key.replace("_", " ").title())
            else:
                return "Unable to fetch news. Please try again later."

        except Exception as e:
            logger.error(f"News tool error: {e}")
            return f"Sorry, I encountered an error getting the news: {str(e)}"

    async def _fetch_news_data(self, rss_url: str) -> Optional[list]:
        """Fetch news from RSS feed"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(rss_url, headers=headers, timeout=15)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)
            news_items = []

            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else "No title"
                description = item.find("description").text if item.find("description") is not None else "No description"
                pubDate = item.find("pubDate").text if item.find("pubDate") is not None else "Unknown time"

                # Clean HTML from description if present
                if description and description != "No description":
                    try:
                        # Simple HTML tag removal
                        import re
                        description = re.sub('<[^<]+?>', '', description).strip()
                    except:
                        pass  # Use as is if regex fails

                news_items.append({
                    "title": title,
                    "description": description,
                    "pubDate": pubDate
                })

            return news_items[:10]  # Return top 10 news items

        except Exception as e:
            logger.error(f"Error fetching news data: {e}")
            return None

    def _format_news_response(self, news_item: Dict, source: str) -> str:
        """Format news item into a readable response"""
        try:
            title = news_item.get("title", "Unknown title") or "Unknown title"
            description = news_item.get("description", "No description available") or "No description available"

            # Ensure description is a string and limit length
            if description and isinstance(description, str) and len(description) > 200:
                description = description[:200] + "..."
            elif not isinstance(description, str):
                description = "No description available"

            news_report = (
                f"Here's a news update from {source}: {title}. "
                f"{description}"
            )

            return news_report

        except Exception as e:
            logger.error(f"Error formatting news response: {e}")
            return f"News item received from {source} but formatting failed."

    # Volume Control Function Tools
    @function_tool
    async def self_set_volume(self, context: RunContext, volume: int):
        """Set device volume to a specific level (0-100)

        Args:
            volume: Volume level between 0 and 100
        """
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.set_volume(volume)

    @function_tool
    async def self_get_volume(self, context: RunContext):
        """Get current device volume level"""
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.get_volume()

    @function_tool
    async def self_volume_up(self, context: RunContext):
        """Increase device volume"""
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.adjust_volume("up")

    @function_tool
    async def self_volume_down(self, context: RunContext):
        """Decrease device volume"""
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.adjust_volume("down")

    @function_tool
    async def self_mute(self, context: RunContext):
        """Mute the device"""
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.mute_device()

    @function_tool
    async def self_unmute(self, context: RunContext):
        """Unmute the device"""
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.unmute_device()

    @function_tool
    async def set_light_color(self, context: RunContext, color: str):
        """Set device light color

        Args:
            color: Color name (red, blue, green, white, yellow, purple, pink, etc.)
        """
        if not self.mcp_executor:
            return "Light control is not available right now."

        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)
        return await self.mcp_executor.set_light_color(color)

    @function_tool
    async def check_battery_level(self, context: RunContext, unused: str = ""):
        """Check the device battery percentage.

        Use this to find out how much battery charge remains on the device.
        Call this function without any parameters.

        Args:
            unused: Internal parameter, leave empty or omit

        Returns:
            str: Battery percentage status message
        """
        logger.info("🔋 check_battery_level called")
        logger.info(f"🔋 context type: {type(context)}")
        logger.info(f"🔋 unused parameter received: '{unused}'")
        logger.info(f"🔋 mcp_executor available: {self.mcp_executor is not None}")

        if not self.mcp_executor:
            logger.warning("🔋 mcp_executor is not available")
            return "Battery status is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)
        logger.info("🔋 Context set on mcp_executor, calling get_battery_status")

        result = await self.mcp_executor.get_battery_status()
        logger.info(f"🔋 check_battery_level result: {result}")
        return result
    
    
    @function_tool
    async def set_light_mode(self, context: RunContext, mode: str):
        """Set device light mode

        Args:
            mode: Mode name (rainbow, default, custom)
        """
        if not self.mcp_executor:
            return "Light Mode control is not available right now."

        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)
        return await self.mcp_executor.set_light_mode(mode)
    
    @function_tool
    async def set_rainbow_speed(self, context: RunContext, speed_ms: str):
        """Set rainbow mode speed

       Args:
            mode: Mode speed (integer, 50-1000)
        """
        if not self.mcp_executor:
            return "rainbow Mode speed control is not available right now."

        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)
        return await self.mcp_executor.set_rainbow_speed(speed_ms)