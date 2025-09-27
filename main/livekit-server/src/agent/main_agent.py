import logging
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, Dict, Any
import pytz
import random
from livekit.agents import (
    Agent,
    RunContext,
    function_tool,
)
from .filtered_agent import FilteredAgent

logger = logging.getLogger("agent")

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
        


    def set_services(self, music_service, story_service, audio_player, unified_audio_player=None):
        """Set the music and story services"""
        self.music_service = music_service
        self.story_service = story_service
        self.audio_player = audio_player
        self.unified_audio_player = unified_audio_player

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
        location: str = None
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