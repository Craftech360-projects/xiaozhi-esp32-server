import logging
import aiohttp
import asyncio
from typing import Optional
import yaml
import os
from pathlib import Path

logger = logging.getLogger("prompt_service")

class PromptService:
    """Service for fetching agent prompts from API or config file"""

    def __init__(self):
        self.config = None
        self.prompt_cache = {}
        self.cache_timeout = 300  # 5 minutes cache
        self.last_cache_time = 0

    def load_config(self):
        """Load configuration from config.yaml"""
        if self.config is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
            try:
                with open(config_path, 'r', encoding='utf-8') as file:
                    self.config = yaml.safe_load(file)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
                raise
        return self.config

    def get_default_prompt(self) -> str:
        """Get default prompt from config.yaml"""
        config = self.load_config()
        default_prompt = config.get('default_prompt', '')
        if not default_prompt:
            logger.warning("No default_prompt found in config.yaml")
            # Fallback to a basic prompt
            return "You are a helpful AI assistant."
        return default_prompt.strip()

    def should_read_from_api(self) -> bool:
        """Check if we should read prompt from API based on config"""
        config = self.load_config()
        return config.get('read_config_from_api', False)

    async def fetch_prompt_from_api(self, mac_address: str) -> Optional[str]:
        """Fetch prompt from manager API using device MAC address"""
        try:
            config = self.load_config()
            manager_api = config.get('manager_api', {})

            if not manager_api:
                logger.error("Manager API configuration not found")
                return None

            base_url = manager_api.get('url', '')
            secret = manager_api.get('secret', '')
            timeout = manager_api.get('timeout', 5)

            if not base_url or not secret:
                logger.error("Manager API URL or secret not configured")
                return None

            # Keep MAC address format as-is (database stores with colons)
            clean_mac = mac_address.lower()

            # API endpoint to get prompt by MAC address (using config endpoint)
            url = f"{base_url}/config/agent-prompt"

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {secret}'  # Server secret authentication
            }

            # Request payload with MAC address
            payload = {
                'macAddress': clean_mac
            }

            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Expected response format: {"code": 0, "data": "prompt_text"}
                        if data.get('code') == 0 and 'data' in data:
                            prompt = data['data']
                            if prompt and prompt.strip():
                                logger.info(f"Successfully fetched prompt from API for MAC: {mac_address}")
                                return prompt.strip()
                            else:
                                logger.warning(f"Empty prompt received from API for MAC: {mac_address}")
                                return None
                        else:
                            logger.warning(f"API returned error: {data}")
                            return None
                    else:
                        logger.warning(f"API request failed with status {response.status} for MAC: {mac_address}")
                        return None

        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching prompt from API for MAC: {mac_address}")
            return None
        except Exception as e:
            logger.error(f"Error fetching prompt from API for MAC {mac_address}: {e}")
            return None

    def extract_mac_from_participant_identity(self, participant_identity: str) -> Optional[str]:
        """Extract MAC address from participant identity"""
        try:
            # Participant identity might be the MAC address directly
            if not participant_identity:
                return None

            # Remove common separators and check if it's a valid MAC
            clean_identity = participant_identity.replace(':', '').replace('-', '').lower()

            # Check if it's a 12-character hex string (MAC address)
            if len(clean_identity) == 12 and all(c in '0123456789abcdef' for c in clean_identity):
                # Format as MAC address with colons
                mac = ':'.join(clean_identity[i:i+2] for i in range(0, 12, 2))
                logger.info(f"Extracted MAC from participant identity: {participant_identity} -> {mac}")
                return mac

            # Try with existing colons (already formatted MAC)
            if len(participant_identity) == 17 and participant_identity.count(':') == 5:
                # Validate MAC format
                parts = participant_identity.split(':')
                if len(parts) == 6 and all(len(part) == 2 and all(c in '0123456789abcdefABCDEF' for c in part) for part in parts):
                    mac = participant_identity.lower()
                    logger.info(f"Validated MAC from participant identity: {mac}")
                    return mac

            return None
        except Exception as e:
            logger.error(f"Error extracting MAC from participant identity '{participant_identity}': {e}")
            return None

    def extract_mac_from_room_name(self, room_name: str) -> Optional[str]:
        """Extract MAC address from room name format"""
        try:
            # New format: UUID_mac_MACADDRESS (from MQTT gateway)
            if '_mac_' in room_name:
                parts = room_name.split('_mac_')
                if len(parts) >= 2:
                    mac_part = parts[-1]  # Get the MAC part after '_mac_'
                    # Validate MAC address format (12 hex characters)
                    if len(mac_part) == 12 and all(c in '0123456789abcdefABCDEF' for c in mac_part):
                        # Format as MAC address with colons
                        mac = ':'.join(mac_part[i:i+2] for i in range(0, 12, 2)).lower()
                        logger.info(f"Extracted MAC from room name with _mac_ format: {room_name} -> {mac}")
                        return mac

            # Legacy format: device_<mac_address>
            if room_name.startswith('device_'):
                mac_part = room_name.replace('device_', '')
                # Validate MAC address format (12 hex characters)
                if len(mac_part) == 12 and all(c in '0123456789abcdefABCDEF' for c in mac_part):
                    # Format as MAC address with colons
                    mac = ':'.join(mac_part[i:i+2] for i in range(0, 12, 2)).lower()
                    logger.info(f"Extracted MAC from device_ format: {room_name} -> {mac}")
                    return mac

            # Alternative: room name might be the MAC address directly
            clean_name = room_name.replace(':', '').replace('-', '')
            if len(clean_name) == 12 and all(c in '0123456789abcdefABCDEF' for c in clean_name):
                mac = ':'.join(clean_name[i:i+2] for i in range(0, 12, 2)).lower()
                logger.info(f"Extracted MAC from direct format: {room_name} -> {mac}")
                return mac

            logger.warning(f"Could not extract MAC from room name: {room_name}")
            return None
        except Exception as e:
            logger.error(f"Error extracting MAC from room name '{room_name}': {e}")
            return None

    def is_cache_valid(self, mac_address: str) -> bool:
        """Check if cached prompt is still valid"""
        import time
        if mac_address not in self.prompt_cache:
            return False

        cache_entry = self.prompt_cache[mac_address]
        return (time.time() - cache_entry['timestamp']) < self.cache_timeout

    def cache_prompt(self, mac_address: str, prompt: str):
        """Cache prompt for given MAC address"""
        import time
        self.prompt_cache[mac_address] = {
            'prompt': prompt,
            'timestamp': time.time()
        }

    def get_cached_prompt(self, mac_address: str) -> Optional[str]:
        """Get cached prompt if valid"""
        if self.is_cache_valid(mac_address):
            return self.prompt_cache[mac_address]['prompt']
        return None

    async def get_prompt(self, room_name: str, participant_identity: str = None) -> str:
        """
        Get prompt for the agent based on room name/participant identity and configuration.

        Args:
            room_name: LiveKit room name (used to extract device MAC)
            participant_identity: Participant identity (may contain MAC address)

        Returns:
            Agent prompt string
        """
        try:
            # If not reading from API, return default prompt
            if not self.should_read_from_api():
                logger.info("Using default prompt from config (read_config_from_api=false)")
                return self.get_default_prompt()

            # Extract MAC address from room name or participant identity
            mac_address = None

            # Try participant identity first (more reliable)
            if participant_identity:
                mac_address = self.extract_mac_from_participant_identity(participant_identity)

            # Fallback to room name extraction
            if not mac_address:
                mac_address = self.extract_mac_from_room_name(room_name)

            if not mac_address:
                logger.warning(f"Could not extract MAC address from room name: {room_name} or participant: {participant_identity}")
                logger.info("Falling back to default prompt")
                return self.get_default_prompt()

            # Check cache first
            cached_prompt = self.get_cached_prompt(mac_address)
            if cached_prompt:
                logger.info(f"Using cached prompt for MAC: {mac_address}")
                return cached_prompt

            # Fetch from API
            logger.info(f"Fetching prompt from API for MAC: {mac_address}")
            api_prompt = await self.fetch_prompt_from_api(mac_address)

            if api_prompt:
                # Cache the result
                self.cache_prompt(mac_address, api_prompt)
                return api_prompt
            else:
                logger.warning(f"Failed to fetch prompt from API for MAC: {mac_address}")
                logger.info("Falling back to default prompt")
                return self.get_default_prompt()

        except Exception as e:
            logger.error(f"Error in get_prompt: {e}")
            logger.info("Falling back to default prompt")
            return self.get_default_prompt()

    def clear_cache(self):
        """Clear prompt cache"""
        self.prompt_cache.clear()
        logger.info("Prompt cache cleared")