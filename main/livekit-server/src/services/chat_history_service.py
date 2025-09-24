import logging
import json
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import os
from pathlib import Path

logger = logging.getLogger("chat_history")

class ChatHistoryService:
    """Service for capturing and saving chat history to Manager API"""

    def __init__(self, manager_api_url: str, secret: str, device_mac: str, session_id: str, agent_id: str = None):
        """
        Initialize chat history service

        Args:
            manager_api_url: Base URL of Manager API
            secret: API authentication secret
            device_mac: Device MAC address
            session_id: Session identifier (room name)
            agent_id: Agent identifier (optional)
        """
        self.manager_api_url = manager_api_url.rstrip('/')
        self.secret = secret
        self.device_mac = device_mac
        self.session_id = session_id
        self.agent_id = agent_id

        # Configuration
        self.batch_size = 5
        self.send_interval = 30  # seconds
        self.retry_attempts = 3
        self.backup_enabled = True

        # State
        self.conversation_buffer = []
        self._send_task = None
        self._is_running = False
        self.total_messages = 0

        # Create transcripts directory
        self.transcript_dir = Path("transcripts")
        self.transcript_dir.mkdir(exist_ok=True)

        logger.info(f"📝✅ Chat history service initialized - MAC: {device_mac}, Session: {session_id}")
        logger.info(f"📝📊 Configuration - API: {manager_api_url}, Batch: {self.batch_size}, Interval: {self.send_interval}s")

    def start_periodic_sending(self):
        """Start background task for periodic message sending"""
        if not self._send_task or self._send_task.done():
            self._is_running = True
            self._send_task = asyncio.create_task(self._periodic_sender())
            logger.info("📝🔄 Started periodic chat history sending")

    def stop_periodic_sending(self):
        """Stop background sending task"""
        self._is_running = False
        if self._send_task and not self._send_task.done():
            self._send_task.cancel()
            logger.info("Stopped periodic chat history sending")

    async def _periodic_sender(self):
        """Background task that sends buffered messages periodically"""
        while self._is_running:
            try:
                await asyncio.sleep(self.send_interval)
                if len(self.conversation_buffer) > 0:
                    await self.flush_messages()
            except asyncio.CancelledError:
                logger.info("Periodic sender task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic sender: {e}")

    def add_message(self, chat_type: int, content: str, timestamp: float = None):
        """
        Add a message to the conversation buffer

        Args:
            chat_type: 1 for user, 2 for agent
            content: Message text content
            timestamp: Message timestamp (defaults to current time)
        """
        if not content or not content.strip():
            logger.debug("Skipping empty message")
            return

        # Validate chat type
        if chat_type not in [1, 2]:
            logger.warning(f"Invalid chat type: {chat_type}, defaulting to 2 (agent)")
            chat_type = 2

        message = {
            "macAddress": self.device_mac,
            "sessionId": self.session_id,
            "chatType": chat_type,
            "content": content.strip()[:1000],  # Limit content length
            "audioBase64": None,  # Reserved for future audio support
            "reportTime": int(timestamp or datetime.now().timestamp())
        }

        self.conversation_buffer.append(message)
        self.total_messages += 1

        chat_type_str = "👤 User" if chat_type == 1 else "🤖 Agent"
        logger.info(f"📝➕ Added {chat_type_str} message to buffer: '{content[:50]}...' (length: {len(content)}, buffer size: {len(self.conversation_buffer)})")

        # Send immediately if batch size reached
        if len(self.conversation_buffer) >= self.batch_size:
            asyncio.create_task(self.flush_messages())

    async def flush_messages(self):
        """Send all buffered messages to the Manager API"""
        if not self.conversation_buffer:
            return

        messages_to_send = self.conversation_buffer.copy()
        self.conversation_buffer.clear()

        logger.info(f"📝📤 Flushing {len(messages_to_send)} messages to Manager API")

        success_count = 0
        for message in messages_to_send:
            if await self._send_to_api(message):
                success_count += 1

        logger.info(f"📝✅ Successfully sent {success_count}/{len(messages_to_send)} messages to Manager API")

        # If some messages failed, they were re-added to buffer by _send_to_api

    async def _send_to_api(self, message: Dict[str, Any]) -> bool:
        """
        Send individual message to Manager API with retry logic

        Args:
            message: Message dictionary to send

        Returns:
            bool: True if successful, False if failed
        """
        url = f"{self.manager_api_url}/agent/chat-history/report"
        headers = {
            "Authorization": f"Bearer {self.secret}",
            "Content-Type": "application/json"
        }

        for attempt in range(self.retry_attempts):
            try:
                timeout = aiohttp.ClientTimeout(total=10)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=message, headers=headers) as response:
                        if response.status == 200:
                            chat_type_str = "👤 User" if message['chatType'] == 1 else "🤖 Agent"
                            logger.debug(f"📝✅ Sent {chat_type_str} message to API: '{message['content'][:50]}...'")
                            return True
                        else:
                            error_text = await response.text()
                            logger.warning(f"API request failed: {response.status} - {error_text}")

                            # Don't retry client errors (4xx)
                            if 400 <= response.status < 500:
                                logger.error(f"Client error, not retrying: {response.status}")
                                return False

            except asyncio.TimeoutError:
                logger.warning(f"API request timeout (attempt {attempt + 1}/{self.retry_attempts})")
            except aiohttp.ClientError as e:
                logger.warning(f"API client error (attempt {attempt + 1}/{self.retry_attempts}): {e}")
            except Exception as e:
                logger.error(f"Unexpected error sending to API (attempt {attempt + 1}/{self.retry_attempts}): {e}")

            # Wait before retry with exponential backoff
            if attempt < self.retry_attempts - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(wait_time)

        # All attempts failed, re-add to buffer for later retry
        logger.error(f"Failed to send message after {self.retry_attempts} attempts, re-adding to buffer")
        self.conversation_buffer.insert(0, message)  # Add to front for priority
        return False

    async def save_local_backup(self):
        """Save conversation history to local JSON file"""
        if not self.backup_enabled:
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.transcript_dir / f"chat_{self.session_id}_{timestamp}.json"

            backup_data = {
                "session_info": {
                    "session_id": self.session_id,
                    "device_mac": self.device_mac,
                    "agent_id": self.agent_id,
                    "total_messages": self.total_messages,
                    "backup_timestamp": datetime.now().isoformat()
                },
                "buffered_messages": self.conversation_buffer,
                "metadata": {
                    "api_url": self.manager_api_url,
                    "batch_size": self.batch_size,
                    "send_interval": self.send_interval
                }
            }

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved local backup: {filename} ({self.total_messages} total messages)")

        except Exception as e:
            logger.error(f"Failed to save local backup: {e}")

    async def cleanup(self):
        """Cleanup service and send remaining messages"""
        logger.info("📝🧹 Cleaning up chat history service")

        # Stop periodic sending
        self.stop_periodic_sending()

        # Send any remaining messages
        if self.conversation_buffer:
            logger.info(f"Sending {len(self.conversation_buffer)} remaining messages")
            await self.flush_messages()

        # Save local backup
        await self.save_local_backup()

        # Wait for any pending tasks
        if self._send_task and not self._send_task.done():
            try:
                await asyncio.wait_for(self._send_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Cleanup timeout waiting for send task")

        logger.info(f"📝🧹✅ Chat history service cleanup complete. Total messages processed: {self.total_messages}")

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return {
            "session_id": self.session_id,
            "device_mac": self.device_mac,
            "total_messages": self.total_messages,
            "buffered_messages": len(self.conversation_buffer),
            "is_running": self._is_running,
            "batch_size": self.batch_size,
            "send_interval": self.send_interval
        }