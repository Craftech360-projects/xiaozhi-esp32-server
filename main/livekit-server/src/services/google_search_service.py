"""
Google Custom Search Service for Wikipedia-only searches
MCP-style structured service for real-time information retrieval
"""
import os
import logging
import aiohttp
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
        for item in data.get("items", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "link": item.get("link", ""),
                "displayLink": item.get("displayLink", "")
            })

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

    def format_results_for_voice(
        self,
        search_result: Dict[str, Any],
        max_items: int = 2
    ) -> str:
        """
        Format search results for voice output (TTS-friendly)

        Args:
            search_result: Result from search_wikipedia() method
            max_items: Maximum number of results to include in voice output

        Returns:
            Formatted string suitable for text-to-speech
        """
        if not search_result.get("success"):
            error_msg = search_result.get("error", "I couldn't search Wikipedia right now.")
            return error_msg

        results = search_result.get("results", [])
        query = search_result.get("query", "that")

        if not results:
            return f"I searched Wikipedia for '{query}', but I couldn't find any relevant articles."

        # Build voice-friendly response
        response_parts = []

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

            # Build result entry
            if snippet:
                response_parts.append(f"{snippet}")
            else:
                response_parts.append(f"According to Wikipedia, {title}.")

        return " ".join(response_parts)

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
