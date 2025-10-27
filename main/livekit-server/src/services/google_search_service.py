"""
Google Custom Search Service for Wikipedia-only searches
MCP-style structured service for real-time information retrieval
"""
import os
import logging
import aiohttp
import asyncio
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger("google_search")


class GoogleSearchService:
    """
    Service for performing Google Custom Search API queries
    Restricted to Wikipedia only for accurate, reliable information

    MCP-style service architecture:
    - Stateless design
    - Clear error handling
    - Configuration-driven
    - Logging and monitoring
    """

    def __init__(self):
        """Initialize Google Search Service with Wikipedia restriction"""
        # Configuration from environment
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.enabled = os.getenv("GOOGLE_SEARCH_ENABLED", "false").lower() == "true"
        self.max_results = int(os.getenv("GOOGLE_SEARCH_MAX_RESULTS", "3"))

        # Wikipedia-only restriction
        self.search_domain = "wikipedia.org"

        # API endpoint
        self.api_url = "https://www.googleapis.com/customsearch/v1"

        # Service state
        self._initialized = False

        # Validate configuration
        if self.enabled:
            self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate service configuration"""
        if not self.api_key or self.api_key == "your_google_api_key_here":
            logger.warning("⚠️ Google Search enabled but API key not configured")
            self.enabled = False
            return

        if not self.search_engine_id or "your_" in self.search_engine_id:
            logger.warning("⚠️ Google Search enabled but Search Engine ID not configured")
            self.enabled = False
            return

        self._initialized = True
        logger.info(f"✅ Google Search Service initialized (Wikipedia-only, max results: {self.max_results})")

    def is_available(self) -> bool:
        """
        Check if Google Search service is available and configured

        Returns:
            bool: True if service is ready to use
        """
        return self.enabled and self._initialized

    async def search_wikipedia(
        self,
        query: str,
        num_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search Wikipedia using Google Custom Search API

        Args:
            query: Search query string
            num_results: Number of results to return (defaults to max_results)

        Returns:
            Dict containing:
            {
                "success": bool,
                "query": str,
                "results": List[Dict],
                "totalResults": str,
                "error": str (if failed)
            }
        """
        if not self.enabled:
            logger.warning("🔍 Search attempted but service is disabled")
            return {
                "success": False,
                "error": "Wikipedia search is not enabled. Please check configuration."
            }

        try:
            # Limit results
            num_results = num_results or self.max_results
            num_results = min(num_results, 10)  # Google API max is 10

            # Build request parameters with Wikipedia restriction
            params = {
                "key": self.api_key,
                "cx": self.search_engine_id,
                "q": f"{query} site:{self.search_domain}",  # Force Wikipedia-only
                "num": num_results,
                "safe": "active"  # Safe search
            }

            logger.info(f"🔍 Searching Wikipedia: '{query}' (results: {num_results})")

            # Make API request with timeout
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.api_url, params=params) as response:
                    # Handle different response codes
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_success_response(query, data)

                    elif response.status == 429:
                        logger.error("❌ Google Search API quota exceeded")
                        return {
                            "success": False,
                            "error": "Search quota exceeded. Please try again later."
                        }

                    elif response.status == 400:
                        error_text = await response.text()
                        logger.error(f"❌ Bad request to Google API: {error_text}")
                        return {
                            "success": False,
                            "error": "Invalid search request."
                        }

                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Google Search API error: {response.status} - {error_text}")
                        return {
                            "success": False,
                            "error": f"Search service error (code: {response.status})"
                        }

        except aiohttp.ClientError as e:
            logger.error(f"❌ Network error during Wikipedia search: {e}")
            return {
                "success": False,
                "error": "Network error while searching. Please check your connection."
            }

        except asyncio.TimeoutError:
            logger.error(f"❌ Timeout during Wikipedia search")
            return {
                "success": False,
                "error": "Search request timed out. Please try again."
            }

        except Exception as e:
            logger.error(f"❌ Unexpected error during Wikipedia search: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "An unexpected error occurred while searching."
            }

    def _parse_success_response(self, query: str, data: Dict) -> Dict[str, Any]:
        """
        Parse successful Google API response

        Args:
            query: Original search query
            data: API response data

        Returns:
            Structured result dictionary
        """
        # Extract search results
        results = []
        for idx, item in enumerate(data.get("items", []), 1):
            result = {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
                "displayLink": item.get("displayLink", "")
            }
            results.append(result)

            # Log each individual result for debugging
            logger.info(f"📄 Result #{idx}:")
            logger.info(f"   Title: {result['title']}")
            logger.info(f"   Snippet: {result['snippet'][:100]}..." if len(result['snippet']) > 100 else f"   Snippet: {result['snippet']}")
            logger.info(f"   Link: {result['link']}")

        # Extract search metadata
        search_info = data.get("searchInformation", {})
        total_results = search_info.get("totalResults", "0")
        search_time = search_info.get("searchTime", 0)

        logger.info(f"✅ Found {len(results)} Wikipedia results for '{query}' (total: {total_results}, time: {search_time}s)")

        return {
            "success": True,
            "query": query,
            "results": results,
            "totalResults": total_results,
            "searchTime": search_time,
            "source": "Wikipedia"
        }

    def _detect_completed_event(self, query: str) -> Dict[str, Any]:
        """
        Detect if query is asking about a completed event

        Args:
            query: Search query string

        Returns:
            Dict with event detection information
        """
        query_lower = query.lower()
        current_date = datetime.now()
        current_month = current_date.month

        # Past tense indicators suggesting completed events
        COMPLETION_VERBS = ['won', 'happened', 'occurred', 'finished', 'ended', 'completed', 'concluded']

        # Sports tournaments and their typical months
        TOURNAMENT_SCHEDULES = {
            'ipl': {'name': 'IPL', 'typical_months': [3, 4, 5], 'typical_end_month': 5},  # March-May
            'world cup cricket': {'name': 'Cricket World Cup', 'typical_months': [10, 11], 'typical_end_month': 11},
            'world cup football': {'name': 'Football World Cup', 'typical_months': [11, 12], 'typical_end_month': 12},
            't20 world cup': {'name': 'T20 World Cup', 'typical_months': [10, 11], 'typical_end_month': 11},
            'olympics': {'name': 'Olympics', 'typical_months': [7, 8], 'typical_end_month': 8},
            'wimbledon': {'name': 'Wimbledon', 'typical_months': [6, 7], 'typical_end_month': 7},
        }

        event_info = {
            'is_completed_event': False,
            'has_completion_verb': False,
            'tournament_name': None,
            'should_be_completed': False,
            'validation_message': None
        }

        # Check for completion verbs
        for verb in COMPLETION_VERBS:
            if re.search(rf'\b{verb}\b', query_lower):
                event_info['has_completion_verb'] = True
                event_info['is_completed_event'] = True
                logger.info(f"🎯 Detected completion verb: '{verb}'")
                break

        # Check for tournament queries
        for tournament_key, tournament_data in TOURNAMENT_SCHEDULES.items():
            if tournament_key in query_lower:
                event_info['tournament_name'] = tournament_data['name']
                typical_end_month = tournament_data['typical_end_month']

                # Check if we're past the typical completion date
                if current_month > typical_end_month:
                    event_info['should_be_completed'] = True
                    logger.info(f"🏆 Tournament '{tournament_data['name']}' should be completed by now (current month: {current_month}, typical end: {typical_end_month})")
                else:
                    event_info['should_be_completed'] = False
                    event_info['validation_message'] = f"Note: {tournament_data['name']} typically occurs around {'-'.join([datetime(2000, m, 1).strftime('%B') for m in tournament_data['typical_months']])}. It may not have occurred yet as we're currently in {datetime(2000, current_month, 1).strftime('%B')}."
                    logger.info(f"⚠️ Tournament '{tournament_data['name']}' may not have completed yet")
                break

        return event_info

    def _validate_search_results(self, query: str, results: List[Dict], event_info: Dict[str, Any]) -> str:
        """
        Validate search results for event queries to detect incorrect/incomplete information

        Args:
            query: Original search query
            results: Search results from Wikipedia
            event_info: Event information from _detect_completed_event

        Returns:
            Validation warning message if needed, or None
        """
        if not event_info.get('is_completed_event') or not event_info.get('tournament_name'):
            return None

        query_lower = query.lower()

        # Extract year from query
        year_match = re.search(r'\b(20\d{2})\b', query)
        if not year_match:
            return None

        query_year = int(year_match.group(1))

        # Check if any result snippet contains uncertainty indicators
        uncertainty_indicators = [
            'scheduled', 'upcoming', 'will be held', 'will take place',
            'is expected', 'projected', 'anticipated', 'to be held',
            'has not yet', 'not yet occurred', 'not yet taken place'
        ]

        for result in results[:2]:  # Check top 2 results
            snippet = result.get('snippet', '').lower()
            title = result.get('title', '').lower()

            # Check for uncertainty in snippet
            for indicator in uncertainty_indicators:
                if indicator in snippet:
                    logger.warning(f"⚠️ Found uncertainty indicator '{indicator}' in Wikipedia result")
                    return f"Important: Based on Wikipedia, the {event_info['tournament_name']} {query_year} may not have concluded yet or information is incomplete. Please verify independently."

            # Check if snippet mentions the correct year
            if str(query_year) not in snippet and str(query_year) not in title:
                logger.warning(f"⚠️ Wikipedia result doesn't clearly mention year {query_year}")

        return None

    def _detect_query_timeframe(self, query: str) -> Dict[str, Any]:
        """
        Detect if query is about future, current, or past timeframe
        Also detects temporal keywords like "latest", "recent", "current", etc.

        IMPORTANT: LLM knowledge cutoff is January 2025, so ANY 2025 query
        needs context since the information may be incomplete or projected.

        Args:
            query: Search query string

        Returns:
            Dict with temporal context information
        """
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        query_lower = query.lower()

        # LLM knowledge cutoff
        KNOWLEDGE_CUTOFF_YEAR = 2025
        KNOWLEDGE_CUTOFF_MONTH = 1  # January 2025

        # Temporal keywords that imply "current" information
        CURRENT_KEYWORDS = [
            'latest', 'recent', 'current', 'now', 'today', 'yesterday',
            'this week', 'this month', 'this year', 'last week', 'last month',
            'news', 'updates', 'developments', 'happening'
        ]

        # Extract year and month from query
        year_match = re.search(r'\b(20\d{2})\b', query)
        month_match = re.search(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b', query, re.IGNORECASE)

        timeframe = {
            "is_future": False,
            "is_beyond_cutoff": False,
            "is_current_year": False,
            "detected_year": None,
            "detected_month": None,
            "context_message": None,
            "has_temporal_keyword": False
        }

        # Check for temporal keywords
        for keyword in CURRENT_KEYWORDS:
            if keyword in query_lower:
                timeframe["has_temporal_keyword"] = True
                logger.info(f"📅 Detected temporal keyword: '{keyword}' in query")

                # Since current date is October 2025 (beyond January 2025 cutoff)
                # ANY query with these keywords needs Wikipedia context
                if not year_match:  # Only if no explicit year mentioned
                    timeframe["is_beyond_cutoff"] = True
                    timeframe["context_message"] = f"Note: Information is from Wikipedia based on '{keyword}' in your query. Data current as of {current_date.strftime('%B %Y')}."
                    logger.info(f"⏰ Keyword '{keyword}' triggered temporal context (no explicit year)")
                break

        if year_match:
            detected_year = int(year_match.group(1))
            timeframe["detected_year"] = detected_year

            if detected_year > current_year:
                # Future year
                timeframe["is_future"] = True
                timeframe["is_beyond_cutoff"] = True
                timeframe["context_message"] = f"Note: {detected_year} is in the future. These are scheduled or projected events from Wikipedia."
                logger.info(f"📅 Detected future year: {detected_year} (current: {current_year})")

            elif detected_year == KNOWLEDGE_CUTOFF_YEAR:
                # 2025 queries - beyond LLM knowledge cutoff
                timeframe["is_current_year"] = True
                timeframe["is_beyond_cutoff"] = True

                if month_match:
                    month_name = month_match.group(1)
                    month_num = datetime.strptime(month_name, "%B").month
                    timeframe["detected_month"] = month_name

                    # Check if beyond knowledge cutoff (after January 2025)
                    if month_num > KNOWLEDGE_CUTOFF_MONTH:
                        # This is beyond LLM's training data
                        if detected_year == current_year and month_num > current_month:
                            # Future month in current year
                            timeframe["is_future"] = True
                            timeframe["context_message"] = f"Note: {month_name} {detected_year} hasn't occurred yet. These are scheduled or upcoming events from Wikipedia."
                            logger.info(f"📅 Future month beyond cutoff: {month_name} {detected_year}")
                        else:
                            # Past/current month but beyond training cutoff
                            timeframe["context_message"] = f"Note: Information about {month_name} {detected_year} is from Wikipedia. Events may be incomplete or projected."
                            logger.info(f"📅 Past month beyond cutoff: {month_name} {detected_year}")
                    else:
                        # January 2025 or earlier - within training
                        logger.info(f"📅 Month within knowledge cutoff: {month_name} {detected_year}")
                else:
                    # Just "2025" without specific month
                    timeframe["context_message"] = f"Note: Information about 2025 is from Wikipedia. Some events may be incomplete or projected."
                    logger.info(f"📅 Year 2025 detected (beyond training cutoff)")

            elif detected_year < KNOWLEDGE_CUTOFF_YEAR:
                # Historical queries (pre-2025) - LLM should know these
                logger.info(f"📅 Historical query: {detected_year} (within LLM knowledge)")

        return timeframe

    def format_results_for_voice(
        self,
        search_result: Dict[str, Any],
        max_items: int = 2
    ) -> str:
        """
        Format search results for voice output (TTS-friendly)
        Includes temporal context for future/past events

        Args:
            search_result: Result from search_wikipedia() method
            max_items: Maximum number of results to include in voice output

        Returns:
            Formatted string suitable for text-to-speech
        """
        logger.info(f"🎤 Formatting results for voice (max_items: {max_items})")

        if not search_result.get("success"):
            error_msg = search_result.get("error", "I couldn't search Wikipedia right now.")
            logger.warning(f"⚠️ Formatting failed result: {error_msg}")
            return error_msg

        results = search_result.get("results", [])
        query = search_result.get("query", "that")

        if not results:
            no_results_msg = f"I searched Wikipedia for '{query}', but I couldn't find any relevant articles."
            logger.info(f"📭 No results found, returning: {no_results_msg}")
            return no_results_msg

        logger.info(f"📊 Total results available: {len(results)}, using top {min(len(results), max_items)}")

        # Detect if this is a completed event query
        event_info = self._detect_completed_event(query)

        # Validate search results for event queries
        result_validation_warning = self._validate_search_results(query, results, event_info)

        # Detect temporal context
        timeframe = self._detect_query_timeframe(query)

        # Build voice-friendly response
        response_parts = []

        # Add result validation warning if present (highest priority)
        if result_validation_warning:
            response_parts.append(result_validation_warning)
            logger.info(f"⚠️ Added result validation warning: {result_validation_warning}")
        # Add event validation message if applicable
        elif event_info.get('validation_message'):
            response_parts.append(event_info['validation_message'])
            logger.info(f"🏆 Added event validation: {event_info['validation_message']}")
        # Add temporal context if query is about future events OR beyond knowledge cutoff
        elif timeframe.get("context_message"):
            response_parts.append(timeframe["context_message"])
            logger.info(f"⏰ Added temporal context: {timeframe['context_message']}")

        # Introduction
        if len(results) == 1:
            response_parts.append(f"I found one Wikipedia article about {query}.")
        else:
            response_parts.append(f"I found {len(results)} Wikipedia articles about {query}.")

        # Add top results
        for i, result in enumerate(results[:max_items], 1):
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            # Clean up snippet for voice
            snippet = self._clean_snippet_for_voice(snippet)

            # Remove "Wikipedia" from title if present
            title = title.replace(" - Wikipedia", "").strip()

            logger.info(f"🗣️ Using result #{i} for voice:")
            logger.info(f"   Title (cleaned): {title}")
            logger.info(f"   Snippet (cleaned): {snippet[:150]}..." if len(snippet) > 150 else f"   Snippet (cleaned): {snippet}")

            # Build result entry
            if snippet:
                response_parts.append(f"{snippet}")
            else:
                response_parts.append(f"According to Wikipedia, {title}.")

        final_response = " ".join(response_parts)

        logger.info(f"✅ Final voice response ({len(final_response)} chars):")
        logger.info(f"   {final_response[:200]}..." if len(final_response) > 200 else f"   {final_response}")

        return final_response

    def _clean_snippet_for_voice(self, snippet: str) -> str:
        """
        Clean snippet text for voice output

        Args:
            snippet: Raw snippet from Google API

        Returns:
            Cleaned text suitable for TTS
        """
        if not snippet:
            return ""

        # Remove special characters and formatting
        snippet = snippet.replace("...", " ")
        snippet = snippet.replace("\n", " ")
        snippet = snippet.replace("  ", " ")

        # Remove dates in parentheses (e.g., "(2024)")
        import re
        snippet = re.sub(r'\(\d{4}\)', '', snippet)

        # Trim whitespace
        snippet = snippet.strip()

        return snippet

    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status for monitoring

        Returns:
            Status dictionary
        """
        return {
            "enabled": self.enabled,
            "initialized": self._initialized,
            "search_domain": self.search_domain,
            "max_results": self.max_results,
            "api_configured": bool(self.api_key and self.search_engine_id)
        }
