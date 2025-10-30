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
from src.services.google_search_service import GoogleSearchService
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
        self.google_search_service = None

        # Room and device information
        self.room_name = None
        self.device_mac = None

        # Session reference for dynamic updates
        self._agent_session = None

        # Loop mode state (for continuous playback of random content)
        self.loop_enabled = False
        self.loop_content_type = None  # 'music' or 'story'

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



    def set_services(self, music_service, story_service, audio_player, unified_audio_player=None, device_control_service=None, mcp_executor=None, google_search_service=None):
        """Set the music, story, device control services, MCP executor, and Google Search service"""
        self.music_service = music_service
        self.story_service = story_service
        self.audio_player = audio_player
        self.unified_audio_player = unified_audio_player
        self.device_control_service = device_control_service
        self.mcp_executor = mcp_executor
        self.google_search_service = google_search_service

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
            from src.services.prompt_service import PromptService

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

            # 4. Call update-mode API (updates template_id in database)
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

                        # 5. Initialize PromptService and use template system
                        prompt_service = PromptService()
                        await prompt_service.initialize_template_system()

                        # Check if template system is enabled
                        if prompt_service.is_template_system_enabled():
                            logger.info("🎨 Using template-based prompt system for mode switch")

                            # 6. Get enhanced prompt using template system
                            try:
                                # Clear cache to force fresh fetch
                                prompt_service.clear_enhanced_cache(self.device_mac)

                                # Get new enhanced prompt with updated template_id
                                new_prompt = await prompt_service.get_enhanced_prompt(
                                    room_name=self.room_name,
                                    device_mac=self.device_mac
                                )

                                logger.info(f"🎨✅ Retrieved enhanced prompt for mode '{normalized_mode}' (length: {len(new_prompt)} chars)")

                            except Exception as e:
                                logger.error(f"Failed to get enhanced prompt: {e}")
                                # Fallback to legacy method
                                if result.get('code') == 0 and result.get('data'):
                                    new_prompt = result.get('data')
                                    logger.info("📄 Fallback to prompt from API response")
                                else:
                                    logger.error("No prompt available, mode switch incomplete")
                                    return f"Mode updated to '{normalized_mode}' in database. Please reconnect to apply changes."

                        else:
                            # Legacy system - get prompt from API response
                            logger.info("📄 Using legacy prompt system for mode switch")
                            if result.get('code') == 0 and result.get('data'):
                                new_prompt = result.get('data')
                                logger.info(f"📄 Retrieved prompt from API (length: {len(new_prompt)} chars)")
                            else:
                                logger.warning(f"⚠️ No prompt data in response")
                                return f"Mode updated to '{normalized_mode}' in database. Please reconnect to apply changes."

                        # 7. Inject memory into new prompt (if available)
                        try:
                            if self._agent_session and hasattr(self._agent_session, '_memory_provider'):
                                memory_provider = self._agent_session._memory_provider
                                if memory_provider:
                                    memories = await memory_provider.query_memory("conversation history")
                                    if memories:
                                        new_prompt = new_prompt.replace("<memory>", f"<memory>\n{memories}")
                                        logger.info(f"💭 Injected memories into new prompt ({len(memories)} chars)")
                        except Exception as e:
                            logger.warning(f"Could not inject memories: {e}")

                        # 8. Update the agent's instructions dynamically
                        self._instructions = new_prompt
                        logger.info(f"📝 Instructions updated dynamically (length: {len(new_prompt)} chars)")

                        # 9. Update session if available (for immediate effect)
                        if self._agent_session:
                            try:
                                # Update session's agent internal instructions
                                self._agent_session._agent._instructions = new_prompt

                                # Also update session chat context if possible
                                if hasattr(self._agent_session, 'history') and hasattr(self._agent_session.history, 'messages'):
                                    # Update the system message in history
                                    if len(self._agent_session.history.messages) > 0:
                                        if hasattr(self._agent_session.history.messages[0], 'content'):
                                            self._agent_session.history.messages[0].content = new_prompt
                                            logger.info(f"🔄 Session chat context updated!")

                                logger.info(f"🔄 Session instructions updated in real-time!")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not update session directly: {e}")

                        return f"Successfully updated agent mode to '{normalized_mode}' and reloaded the new prompt! The changes are now active in this conversation."

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
    async def search_wikipedia(
        self,
        context: RunContext,
        query: str
    ) -> str:
        """Search Wikipedia for current information and events after January 2025

        ⚠️ CRITICAL DECISION RULES - Read carefully and follow exactly:

        ═══════════════════════════════════════════════════════════════════
        🟡 FIRST CHECK: CONFIDENCE & ACCURACY
        ═══════════════════════════════════════════════════════════════════

        🚨 CRITICAL RULE: If you are NOT 100% CONFIDENT about factual information,
        USE WIKIPEDIA to verify! It's BETTER to search than give WRONG information!

        ⚠️ ALWAYS USE WIKIPEDIA if:
        1. You're uncertain about specific facts (scores, winners, dates, names)
        2. The query asks for precise data (scorecards, statistics, results)
        3. You're not confident in your answer
        4. The information could have multiple versions or interpretations

        Examples where you SHOULD use Wikipedia even for old events:
        ✅ "Who won 2021 IPL?" → If unsure, USE WIKIPEDIA (verify the winner!)
        ✅ "2008 cricket scorecard" → If unsure about exact scores, USE WIKIPEDIA
        ✅ "2019 election results" → If unsure about exact numbers, USE WIKIPEDIA
        ✅ "List of IPL winners" → USE WIKIPEDIA (precise list needed!)

        💡 RULE OF THUMB:
        - Factual queries requiring 100% accuracy → USE WIKIPEDIA to verify
        - Uncertain or could be wrong → USE WIKIPEDIA to verify
        - Confident and simple fact → Answer directly

        ═══════════════════════════════════════════════════════════════════
        🟡 SECOND CHECK: HISTORICAL vs CURRENT QUERY
        ═══════════════════════════════════════════════════════════════════

        ❌ ONLY skip Wikipedia if you are COMPLETELY CONFIDENT about historical data:
           - Simple, well-known facts you're 100% sure about
           - General knowledge questions with clear answers
           - NOT specific statistics, scorecards, or detailed results

        ✅ USE WIKIPEDIA for 2024, 2025, or temporal keywords:
           - "2024 elections" → USE Wikipedia (recent!)
           - "2025 IPL winner" → USE Wikipedia (beyond cutoff!)
           - "Current president" → USE Wikipedia (could have changed!)
           - "Latest news" → USE Wikipedia (after your training!)

        ═══════════════════════════════════════════════════════════════════
        🔴 MANDATORY WIKIPEDIA SEARCH (You MUST use this tool):
        ═══════════════════════════════════════════════════════════════════

        1. KEYWORD TRIGGERS (If query contains ANY of these words):
           ✅ "latest" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "recent" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "current" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "now" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "today" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "yesterday" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "this week/month/year" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "last week/month" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "news" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "updates" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "developments" → ALWAYS use Wikipedia (NO EXCEPTIONS)
           ✅ "happening" → ALWAYS use Wikipedia (NO EXCEPTIONS)

           ⚠️ CRITICAL EXAMPLES THAT MUST TRIGGER WIKIPEDIA:
           - "Who is the current president of America?" → USE WIKIPEDIA (current = could have changed!)
           - "What's the current population of India?" → USE WIKIPEDIA (current = needs latest data!)
           - "Who is the latest CEO of Tesla?" → USE WIKIPEDIA (latest = might have changed!)
           - "What's the recent news about SpaceX?" → USE WIKIPEDIA (recent = after your cutoff!)
           - "What's happening now in politics?" → USE WIKIPEDIA (now = beyond your knowledge!)
           - "What's the latest GDP of USA?" → USE WIKIPEDIA (latest = new data!)
           - "Who won the recent elections?" → USE WIKIPEDIA (recent = you don't know!)
           - "What's the current stock price?" → USE WIKIPEDIA (current = live data!)
           - "Tell me today's weather" → USE WIKIPEDIA (today = you don't know!)
           - "Give me yesterday's news" → USE WIKIPEDIA (yesterday = Oct 23, 2025!)

           🚨 IMPORTANT: Even if you THINK you know the answer, these keywords mean
           the information could have CHANGED after January 2025. ALWAYS use Wikipedia!

        2. ANY 2025 DATES (explicit or implicit):
           ✅ "What happened in June 2025?" → USE WIKIPEDIA
           ✅ "Tell me about 2025" → USE WIKIPEDIA
           ✅ "Events this year" (it's Oct 2025) → USE WIKIPEDIA
           ✅ "What happened last month?" (Sept 2025) → USE WIKIPEDIA
           ✅ "Yesterday's news" (Oct 23, 2025) → USE WIKIPEDIA

        3. EXPLICIT WIKIPEDIA REQUESTS:
           ✅ "Search Wikipedia for..." → USE WIKIPEDIA
           ✅ "Look up on Wikipedia..." → USE WIKIPEDIA
           ✅ "Check Wikipedia about..." → USE WIKIPEDIA

        4. STATISTICS/DATA QUERIES:
           ✅ "What's the current population of..." → USE WIKIPEDIA
           ✅ "Latest GDP of..." → USE WIKIPEDIA
           ✅ "Recent stock prices..." → USE WIKIPEDIA

        5. BIOGRAPHICAL QUERIES - PATTERN MATCHING (CRITICAL):
           🚨 ANY query matching these patterns → ALWAYS use Wikipedia FIRST:

           Pattern: "Who is [PERSON_NAME]?"
           Pattern: "Tell me about [PERSON_NAME]"
           Pattern: "What do you know about [PERSON_NAME]?"
           Pattern: "Give me information about [PERSON_NAME]"

           ✅ EXAMPLES (but NOT limited to these names):
           - "Who is Charlie Chaplin?" → USE WIKIPEDIA
           - "Who is Rohit Sharma?" → USE WIKIPEDIA
           - "Who is Elon Musk?" → USE WIKIPEDIA
           - "Tell me about Albert Einstein" → USE WIKIPEDIA
           - "Who is Narendra Modi?" → USE WIKIPEDIA
           - "Who is Taylor Swift?" → USE WIKIPEDIA
           - "What do you know about Steve Jobs?" → USE WIKIPEDIA

           🔴 IMPORTANT: These are just EXAMPLES. The rule applies to ANY person's name!
           "Who is [ANY_NAME]?" → ALWAYS search Wikipedia first!

           💡 WHY Wikipedia for people?
           - Career changes (team, company, position)
           - Recent achievements and awards
           - Current projects and activities
           - Biographical updates and life events
           - Death/retirement information (if applicable)

           Even if you think you know the person, Wikipedia has MORE CURRENT information!

        ═══════════════════════════════════════════════════════════════════
        🟢 DO NOT USE WIKIPEDIA (Only if you are 100% CONFIDENT):
        ═══════════════════════════════════════════════════════════════════

        ⚠️ IMPORTANT: Only skip Wikipedia if you are ABSOLUTELY CERTAIN!

        ❌ Simple, well-known general knowledge (if 100% confident):
           - "What is the capital of France?" → Paris (you know this!)
           - "Who invented the telephone?" → Alexander Graham Bell (you know this!)
           - "When did WW2 end?" → 1945 (you know this!)

        🟡 Historical sports/events (ONLY if 100% confident, otherwise USE WIKIPEDIA):
           - "Who won 2010 World Cup?" → Spain (if 100% sure!)
           - BUT if asking for scorecards, detailed results, statistics → USE WIKIPEDIA!
           - Better safe than sorry - when in doubt, USE WIKIPEDIA!

        ❌ Conceptual explanations:
           - "What is artificial intelligence?" → Don't use Wikipedia
           - "How does a computer work?" → Don't use Wikipedia
           - "Explain quantum physics" → Don't use Wikipedia

        ❌ Conversational/Creative:
           - "Tell me a joke" → Don't use Wikipedia
           - "How are you?" → Don't use Wikipedia
           - "I'm sad" → Don't use Wikipedia

        ═══════════════════════════════════════════════════════════════════
        ⚡ DECISION FRAMEWORK:
        ═══════════════════════════════════════════════════════════════════

        Your knowledge cutoff: January 2025
        Current date: October 2025

        📊 USE WIKIPEDIA if ANY of these are true:
        1. 🎯 NOT 100% confident in your answer
        2. 📅 Year 2024 or 2025 mentioned
        3. 🔑 Temporal keywords (current, latest, recent, now, today)
        4. 📈 Specific statistics, scorecards, or detailed results requested
        5. 👤 Biographical queries (people's current status/position)
        6. ❓ Any uncertainty about facts

        ✅ ONLY answer directly if:
        - 100% confident AND
        - Simple general knowledge AND
        - NOT asking for detailed/precise data

        💡 GOLDEN RULE: When in doubt → USE WIKIPEDIA!
        Better to verify than give wrong information!

        ═══════════════════════════════════════════════════════════════════

        Args:
            query: Topic to search (e.g., "latest AI news", "current affairs", "what happened today")

        Returns:
            Current verified information from Wikipedia with temporal context warnings
        """
        try:
            logger.info(f"📚 Wikipedia search request: '{query}'")

            # Check if search service is available
            if not self.google_search_service:
                logger.warning("⚠️ Wikipedia search requested but service not initialized")
                return "Sorry, Wikipedia search is not available right now."

            if not self.google_search_service.is_available():
                logger.warning("⚠️ Wikipedia search requested but service not configured")
                return "Sorry, Wikipedia search is not configured. Please ask the administrator to enable it."

            # Perform Wikipedia search
            search_result = await self.google_search_service.search_wikipedia(query)

            # Check if search was successful
            if not search_result.get("success"):
                error_msg = search_result.get("error", "Unknown error")
                logger.warning(f"⚠️ Wikipedia search failed: {error_msg}")

                # Instead of blocking with error, instruct LLM to use its own knowledge
                return f"WIKIPEDIA_UNAVAILABLE: {error_msg}. Please answer the question using your own knowledge base instead."

            # Format results for voice output
            voice_response = self.google_search_service.format_results_for_voice(
                search_result,
                max_items=2  # Limit to top 2 results for voice clarity
            )

            logger.info(f"✅ Wikipedia search completed for '{query}': {len(search_result.get('results', []))} results found")

            return voice_response

        except Exception as e:
            logger.error(f"❌ Error during Wikipedia search: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Fallback to LLM knowledge on exception
            return f"WIKIPEDIA_UNAVAILABLE: Search error occurred. Please answer the question using your own knowledge base instead."

    @function_tool
    async def play_music(
        self,
        context: RunContext,
        song_name: Optional[str] = None,
        language: Optional[str] = None,
        loop_enabled: bool = False
    ):
        """Play music - either a specific song or random music

        Args:
            song_name: Optional specific song to search for
            language: Optional language preference (English, Hindi, Telugu, etc.)
            loop_enabled: Enable continuous playback of different songs from same language
        """
        try:
            logger.info(f"Music request - song: '{song_name}', language: '{language}'")

            if not self.music_service:
                return "Sorry, music service is not available right now."

            # Check if music service is initialized, if not initialize it now
            if not hasattr(self.music_service, 'is_initialized') or not self.music_service.is_initialized:
                logger.warning("Music service not initialized yet, initializing now...")
                try:
                    init_result = await self.music_service.initialize()
                    if init_result:
                        logger.info("✅ Music service initialized successfully")
                    else:
                        logger.error("❌ Music service initialization returned False (Qdrant not available)")
                        return "Sorry, the music library is not available right now. Please make sure Qdrant is configured and running."
                except Exception as init_error:
                    logger.error(f"❌ Failed to initialize music service: {init_error}")
                    return "Sorry, I'm having trouble accessing the music library right now. Please try again in a moment."

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

            # Store loop state if loop mode is enabled
            if loop_enabled:
                self.loop_enabled = True
                self.loop_content_type = 'music'
                logger.info(f"🔁 Loop mode enabled for music (will play ANY random songs)")
            else:
                # Clear loop state if not looping
                self.loop_enabled = False
                self.loop_content_type = None

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
            # Register completion callback if loop mode is enabled
            if loop_enabled:
                await player.play_from_url(
                    song['url'],
                    song['title'],
                    on_completion_callback=lambda: self._handle_music_completion(language)
                )
            else:
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
        category: Optional[str] = None,
        loop_enabled: bool = False
    ):
        """Play a story - either a specific story or random story

        Args:
            story_name: Optional specific story to search for
            category: Optional category preference (Adventure, Bedtime, Educational, etc.)
            loop_enabled: Enable continuous playback of different stories from same category
        """
        try:
            logger.info(f"Story request - story: '{story_name}', category: '{category}'")

            if not self.story_service:
                return "Sorry, story service is not available right now."

            # Check if story service is initialized, if not initialize it now
            if not hasattr(self.story_service, 'is_initialized') or not self.story_service.is_initialized:
                logger.warning("Story service not initialized yet, initializing now...")
                try:
                    init_result = await self.story_service.initialize()
                    if init_result:
                        logger.info("✅ Story service initialized successfully")
                    else:
                        logger.error("❌ Story service initialization returned False (Qdrant not available)")
                        return "Sorry, the story library is not available right now. Please make sure Qdrant is configured and running."
                except Exception as init_error:
                    logger.error(f"❌ Failed to initialize story service: {init_error}")
                    return "Sorry, I'm having trouble accessing the story library right now. Please try again in a moment."

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

            # Store loop state if loop mode is enabled
            if loop_enabled:
                self.loop_enabled = True
                self.loop_content_type = 'story'
                logger.info(f"🔁 Loop mode enabled for stories (will play ANY random stories)")
            else:
                # Clear loop state if not looping
                self.loop_enabled = False
                self.loop_content_type = None

            # Start playing the story through TTS channel
            # Register completion callback if loop mode is enabled
            if loop_enabled:
                await player.play_from_url(
                    story['url'],
                    story['title'],
                    on_completion_callback=lambda: self._handle_story_completion(category)
                )
            else:
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

            # Clear loop state to stop continuous playback
            was_looping = self.loop_enabled
            self.loop_enabled = False
            self.loop_content_type = None
            if was_looping:
                logger.info("🔁 Loop mode disabled via stop_audio")

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

    async def _handle_music_completion(self, language: Optional[str] = None):
        """Handle music completion in loop mode
        
        Args:
            language: Optional language preference to maintain for next song
        """
        try:
            # Check if loop is still enabled
            if not self.loop_enabled:
                logger.info("🔁 Loop mode disabled, stopping music continuation")
                return

            logger.info(f"🔁 Music completed, playing next random song (language: {language or 'ANY'})")

            # Get context for the next playback
            context = None
            if self.unified_audio_player and self.unified_audio_player.context:
                context = self.unified_audio_player.context
            elif self.audio_player and self.audio_player.context:
                context = self.audio_player.context

            if not context:
                logger.error("🔁 No context available for music loop continuation")
                self.loop_enabled = False
                return

            # Play next random song with same language preference
            await self.play_music(
                context=context,
                song_name=None,  # Random selection
                language=language,  # Maintain language preference
                loop_enabled=True  # Continue looping
            )

        except Exception as e:
            logger.error(f"🔁 Error continuing music loop: {e}")
            import traceback
            logger.error(f"🔁 Traceback: {traceback.format_exc()}")
            # Disable loop on error to prevent infinite error loop
            self.loop_enabled = False

    async def _handle_story_completion(self, category: Optional[str] = None):
        """Handle story completion in loop mode
        
        Args:
            category: Optional category preference to maintain for next story
        """
        try:
            # Check if loop is still enabled
            if not self.loop_enabled:
                logger.info("🔁 Loop mode disabled, stopping story continuation")
                return

            logger.info(f"🔁 Story completed, playing next random story (category: {category or 'ANY'})")

            # Get context for the next playback
            context = None
            if self.unified_audio_player and self.unified_audio_player.context:
                context = self.unified_audio_player.context
            elif self.audio_player and self.audio_player.context:
                context = self.audio_player.context

            if not context:
                logger.error("🔁 No context available for story loop continuation")
                self.loop_enabled = False
                return

            # Play next random story with same category preference
            await self.play_story(
                context=context,
                story_name=None,  # Random selection
                category=category,  # Maintain category preference
                loop_enabled=True  # Continue looping
            )

        except Exception as e:
            logger.error(f"🔁 Error continuing story loop: {e}")
            import traceback
            logger.error(f"🔁 Traceback: {traceback.format_exc()}")
            # Disable loop on error to prevent infinite error loop
            self.loop_enabled = False

    async def _continue_loop_playback(self):
        """Continue loop playback by playing next random song/story from same category"""
        try:
            # Check if loop is still enabled
            if not self.loop_enabled:
                logger.info("🔁 Loop mode disabled, stopping continuation")
                return

            logger.info(f"🔁 Continuing loop playback - Type: {self.loop_content_type} (ANY random content)")

            # Get context for the next playback
            # We need a RunContext, but we can access it through the player
            context = None
            if self.unified_audio_player and self.unified_audio_player.context:
                context = self.unified_audio_player.context
            elif self.audio_player and self.audio_player.context:
                context = self.audio_player.context

            if not context:
                logger.error("🔁 No context available for loop continuation")
                self.loop_enabled = False
                return

            # Play next item based on content type (ANY random, no language/category filter)
            if self.loop_content_type == 'music':
                await self.play_music(
                    context=context,
                    song_name=None,  # Random selection
                    language=None,    # ANY language - no filter
                    loop_enabled=True  # Continue looping
                )
            elif self.loop_content_type == 'story':
                await self.play_story(
                    context=context,
                    story_name=None,  # Random selection
                    category=None,    # ANY category - no filter
                    loop_enabled=True  # Continue looping
                )
            else:
                logger.warning(f"🔁 Unknown content type for loop: {self.loop_content_type}")
                self.loop_enabled = False

        except Exception as e:
            logger.error(f"🔁 Error continuing loop playback: {e}")
            import traceback
            logger.error(f"🔁 Traceback: {traceback.format_exc()}")
            # Disable loop on error to prevent infinite error loop
            self.loop_enabled = False

    async def handle_mobile_music_request(self, data: Dict[str, Any]):
        """Handle music/story play request from mobile app
        
        Args:
            data: Request data containing song_name, content_type, language, loop_enabled
        """
        try:
            logger.info(f"📱 [MOBILE] Processing music request from mobile app")
            
            # Extract request parameters
            song_name = data.get('song_name')
            content_type = data.get('content_type', 'music')
            language = data.get('language')
            loop_enabled = data.get('loop_enabled', False)
            
            logger.info(f"📱 [MOBILE] Content: {content_type}, Song: {song_name}, Language: {language}, Loop: {loop_enabled}")
            
            # Get context for playback
            context = None
            if self.unified_audio_player and self.unified_audio_player.context:
                context = self.unified_audio_player.context
            elif self.audio_player and self.audio_player.context:
                context = self.audio_player.context
            
            if not context:
                logger.error("📱 [MOBILE] No context available for playback")
                return
            
            # Call appropriate play function based on content type
            if content_type == 'story':
                await self.play_story(
                    context=context,
                    story_name=song_name,
                    category=language,  # For stories, language field is used as category
                    loop_enabled=loop_enabled
                )
            else:  # Default to music
                await self.play_music(
                    context=context,
                    song_name=song_name,
                    language=language,
                    loop_enabled=loop_enabled
                )
            
            logger.info(f"✅ [MOBILE] Successfully processed {content_type} request")
            
        except Exception as e:
            logger.error(f"❌ [MOBILE] Error handling mobile music request: {e}")
            import traceback
            logger.error(f"❌ [MOBILE] Traceback: {traceback.format_exc()}")

    async def handle_stop_loop_request(self):
        """Handle stop loop request from mobile app"""
        try:
            logger.info("🔁 [LOOP-STOP] Processing stop loop request from mobile app")
            
            # Get context for stop action
            context = None
            if self.unified_audio_player and self.unified_audio_player.context:
                context = self.unified_audio_player.context
            elif self.audio_player and self.audio_player.context:
                context = self.audio_player.context
            
            if not context:
                logger.error("🔁 [LOOP-STOP] No context available for stop action")
                return
            
            # Call stop_audio to stop playback and clear loop state
            await self.stop_audio(context)
            
            logger.info("✅ [LOOP-STOP] Successfully stopped loop playback")
            
        except Exception as e:
            logger.error(f"❌ [LOOP-STOP] Error handling stop loop request: {e}")
            import traceback
            logger.error(f"❌ [LOOP-STOP] Traceback: {traceback.format_exc()}")

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
                #jsadkjha
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
    async def self_volume_up(self, context: RunContext, step: int = 10):
        """Increase device volume"""
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.adjust_volume("up", step=step)

    @function_tool
    async def self_volume_down(self, context: RunContext, step: int = 10):
        """Decrease device volume"""
        if not self.mcp_executor:
            return "Volume control is not available right now."

        # Always set context for each call to ensure correct room access
        self.mcp_executor.set_context(context, self.audio_player, self.unified_audio_player)

        return await self.mcp_executor.adjust_volume("down", step=step)

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