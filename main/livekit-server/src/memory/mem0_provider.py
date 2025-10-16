import logging
from mem0 import MemoryClient

logger = logging.getLogger("mem0_provider")

class Mem0MemoryProvider:
    def __init__(self, api_key: str, role_id: str):
        """Initialize mem0 client

        Args:
            api_key: Mem0 API key
            role_id: Unique user identifier (device MAC address)
        """
        self.api_key = api_key
        self.role_id = role_id
        self.client = MemoryClient(api_key=api_key)
        logger.info(f"💭 Mem0 initialized for user: {role_id}")

    async def save_memory(self, history_dict: dict, child_name: str = None):
        """Save session history to mem0

        Args:
            history_dict: session.history.to_dict() output
                Format: {'messages': [{'role': 'user', 'content': '...'}, ...]}
            child_name: Optional child name to provide context to mem0
        """
        messages = history_dict.get('messages', [])
        if len(messages) < 2:
            logger.info(f"💭 Skipping mem0 save - insufficient messages ({len(messages)})")
            return None

        # Convert to conversation text with proper role identification
        conversation_text = ""

        # Add child name context if available to help mem0 identify the user correctly
        if child_name:
            conversation_text += f"[Context: The user's name is {child_name}, and Cheeko is the AI assistant]\n\n"

        for msg in messages:
            if msg.get('role') != 'system':
                # Clearly label roles to prevent confusion
                if msg.get('role') == 'user':
                    role_label = f"Child ({child_name})" if child_name else "Child"
                else:
                    role_label = "Cheeko (AI Assistant)"

                content = msg.get('content', '')
                if isinstance(content, list):
                    content = ' '.join(str(item) for item in content)
                conversation_text += f"{role_label}: {content}\n"

        # Save to mem0 with v1.1 output format and metadata
        metadata = {}
        if child_name:
            metadata["child_name"] = child_name
            metadata["assistant_name"] = "Cheeko"

        result = self.client.add(
            conversation_text,
            user_id=self.role_id,
            metadata=metadata if metadata else None,
            output_format="v1.1"
        )
        logger.info(f"💭✅ Saved to mem0: {len(messages)} messages (child: {child_name or 'unknown'})")
        logger.debug(f"💭 Save result: {result}")
        return result

    async def query_memory(self, query: str) -> str:
        """Query memories from mem0

        Args:
            query: Search query

        Returns:
            Formatted memory string
        """
        try:
            logger.info(f"💭 Querying mem0 - user_id: {self.role_id}, query: '{query[:50]}...'")
            results = self.client.search(
                query,
                user_id=self.role_id,
                output_format="v1.1"
            )

            # logger.debug(f"💭 Raw mem0 results: {results}")

            if not results or "results" not in results:
                logger.info(f"💭 No memories found - results empty or invalid format")
                return ""

            results_list = results["results"]
            logger.info(f"💭 Mem0 returned {len(results_list)} result entries")

            # Format memories with timestamps
            memories = []
            for i, entry in enumerate(results_list):
                timestamp = entry.get("updated_at", "")
                if timestamp:
                    timestamp = timestamp.split(".")[0].replace("T", " ")
                memory = entry.get("memory", "")
                if memory:
                    memories.append(f"[{timestamp}] {memory}")
                    logger.debug(f"💭 Memory {i}: {memory[:50]}...")

            logger.info(f"💭 Found {len(memories)} formatted memories")
            return "\n".join(f"- {m}" for m in memories)
        except Exception as e:
            logger.error(f"💭 Error querying mem0: {e}")
            import traceback
            logger.error(f"💭 Traceback: {traceback.format_exc()}")
            return ""
