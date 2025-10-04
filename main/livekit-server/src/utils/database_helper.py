import logging
import aiohttp
import asyncio
from typing import Optional

logger = logging.getLogger("database_helper")

class DatabaseHelper:
    """Helper class for database-related operations via Manager API"""

    def __init__(self, manager_api_url: str, secret: str):
        """
        Initialize database helper

        Args:
            manager_api_url: Base URL of Manager API
            secret: API authentication secret
        """
        self.manager_api_url = manager_api_url.rstrip('/')
        self.secret = secret
        self.retry_attempts = 3

    async def get_agent_id(self, device_mac: str) -> Optional[str]:
        """
        Get agent_id from database using device MAC address

        Args:
            device_mac: Device MAC address

        Returns:
            str: Agent ID if found, None if not found or on error
        """
        url = f"{self.manager_api_url}/agent/device/{device_mac}/agent-id"
        headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json"
        }

        for attempt in range(self.retry_attempts):
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            # Check for Result<String> format: {code: 0, data: "agent_id"}
                            if data.get('code') == 0 and data.get('data'):
                                agent_id = data.get('data')
                                logger.info(f"🆔✅ Retrieved agent_id: {agent_id} for MAC: {device_mac}")
                                return str(agent_id)
                            # Fallback to direct fields
                            agent_id = data.get('agentId') or data.get('agent_id')
                            if agent_id:
                                logger.info(f"🆔✅ Retrieved agent_id: {agent_id} for MAC: {device_mac}")
                                return str(agent_id)
                            else:
                                logger.warning(f"🆔⚠️ No agent_id found in response for MAC: {device_mac}. Response: {data}")
                                return None
                        elif response.status == 404:
                            logger.warning(f"No agent found for MAC: {device_mac}")
                            return None
                        else:
                            error_text = await response.text()
                            logger.warning(f"API request failed: {response.status} - {error_text}")

                            # Don't retry client errors (4xx)
                            if 400 <= response.status < 500:
                                logger.error(f"Client error, not retrying: {response.status}")
                                return None

            except asyncio.TimeoutError:
                logger.warning(f"API request timeout (attempt {attempt + 1}/{self.retry_attempts})")
            except aiohttp.ClientError as e:
                logger.warning(f"API client error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
            except Exception as e:
                logger.error(f"Unexpected error getting agent_id (attempt {attempt + 1}/{self.retry_attempts}): {e}")

            # Wait before retry with exponential backoff
            if attempt < self.retry_attempts - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)

        logger.error(f"Failed to get agent_id after {self.retry_attempts} attempts for MAC: {device_mac}")
        return None

    async def verify_manager_api_connection(self) -> bool:
        """
        Verify connection to Manager API

        Returns:
            bool: True if connection successful, False otherwise
        """
        url = f"{self.manager_api_url}/health"
        headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json"
        }

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        logger.info("Manager API connection verified")
                        return True
                    else:
                        logger.warning(f"Manager API health check failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Failed to verify Manager API connection: {e}")
            return False