"""
Local Memory Provider for LiveKit
Provides file-based local memory storage as an alternative to Mem0 cloud
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalMemoryProvider:
    """Local file-based memory provider"""

    def __init__(
        self,
        *,
        storage_dir: str = "./local_memory",
        role_id: str,
        max_memories: int = 100,
    ):
        """
        Initialize local memory provider

        Args:
            storage_dir: Directory to store memory files
            role_id: Unique identifier for this memory context (e.g., device MAC)
            max_memories: Maximum number of memories to keep
        """
        self.storage_dir = Path(storage_dir)
        self.role_id = role_id
        self.max_memories = max_memories
        self.memory_file = self.storage_dir / f"{role_id}.json"

        # Create storage directory if it doesn't exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Initialized LocalMemoryProvider with storage_dir={storage_dir}, "
            f"role_id={role_id}"
        )

    async def save_memory(self, history_dict: Dict) -> None:
        """
        Save conversation history to local file

        Args:
            history_dict: Dictionary containing conversation history
        """
        try:
            # Load existing memories
            existing_memories = self._load_memories()

            # Add new memory with timestamp
            memory_entry = {
                "timestamp": datetime.now().isoformat(),
                "history": history_dict,
            }

            existing_memories.append(memory_entry)

            # Trim to max_memories (keep most recent)
            if len(existing_memories) > self.max_memories:
                existing_memories = existing_memories[-self.max_memories:]

            # Save to file
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(existing_memories, f, indent=2, ensure_ascii=False)

            logger.debug(
                f"Saved memory for {self.role_id}, "
                f"total memories: {len(existing_memories)}"
            )

        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    async def query_memory(self, query: str = None, limit: int = 10) -> str:
        """
        Query memories from local file

        Args:
            query: Query text (currently unused, returns recent memories)
            limit: Number of recent memories to return

        Returns:
            Formatted memory string
        """
        try:
            memories = self._load_memories()

            if not memories:
                logger.debug(f"No memories found for {self.role_id}")
                return ""

            # Get most recent memories
            recent_memories = memories[-limit:]

            # Format memories for context
            formatted = self._format_memories(recent_memories)

            logger.debug(
                f"Retrieved {len(recent_memories)} memories for {self.role_id}"
            )

            return formatted

        except Exception as e:
            logger.error(f"Error querying memory: {e}")
            return ""

    async def get_all_memories(self) -> List[Dict]:
        """
        Get all memories for this role

        Returns:
            List of memory entries
        """
        try:
            return self._load_memories()
        except Exception as e:
            logger.error(f"Error getting all memories: {e}")
            return []

    async def clear_memories(self) -> None:
        """Clear all memories for this role"""
        try:
            if self.memory_file.exists():
                self.memory_file.unlink()
                logger.info(f"Cleared all memories for {self.role_id}")
        except Exception as e:
            logger.error(f"Error clearing memories: {e}")

    def _load_memories(self) -> List[Dict]:
        """Load memories from file"""
        if not self.memory_file.exists():
            return []

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding memory file: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading memories: {e}")
            return []

    def _format_memories(self, memories: List[Dict]) -> str:
        """
        Format memories for LLM context

        Args:
            memories: List of memory entries

        Returns:
            Formatted memory string
        """
        if not memories:
            return ""

        formatted_lines = ["Previous conversation context:"]

        for idx, memory in enumerate(memories, 1):
            timestamp = memory.get("timestamp", "Unknown time")
            history = memory.get("history", {})

            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = timestamp

            formatted_lines.append(f"\n--- Memory {idx} ({time_str}) ---")

            # Extract key information from history
            if isinstance(history, dict):
                # Handle different history formats
                if "messages" in history:
                    messages = history["messages"][-5:]  # Last 5 messages
                    for msg in messages:
                        role = msg.get("role", "unknown")
                        content = msg.get("content", "")
                        if content:
                            formatted_lines.append(f"{role}: {content[:200]}")
                elif "summary" in history:
                    formatted_lines.append(f"Summary: {history['summary']}")
                else:
                    # Generic format
                    for key, value in list(history.items())[:5]:
                        formatted_lines.append(f"{key}: {str(value)[:200]}")

        return "\n".join(formatted_lines)


class LocalMemoryManager:
    """Manager for multiple local memory providers"""

    def __init__(self, storage_dir: str = "./local_memory"):
        """
        Initialize memory manager

        Args:
            storage_dir: Base directory for all memory files
        """
        self.storage_dir = storage_dir
        self.providers: Dict[str, LocalMemoryProvider] = {}

        logger.info(f"Initialized LocalMemoryManager with storage_dir={storage_dir}")

    def get_provider(self, role_id: str) -> LocalMemoryProvider:
        """
        Get or create a memory provider for a role

        Args:
            role_id: Unique identifier for the memory context

        Returns:
            LocalMemoryProvider instance
        """
        if role_id not in self.providers:
            self.providers[role_id] = LocalMemoryProvider(
                storage_dir=self.storage_dir,
                role_id=role_id,
            )

        return self.providers[role_id]

    async def clear_all_memories(self) -> None:
        """Clear all memories for all roles"""
        storage_path = Path(self.storage_dir)
        if storage_path.exists():
            for memory_file in storage_path.glob("*.json"):
                try:
                    memory_file.unlink()
                    logger.info(f"Deleted memory file: {memory_file}")
                except Exception as e:
                    logger.error(f"Error deleting {memory_file}: {e}")

        # Clear provider cache
        self.providers.clear()
