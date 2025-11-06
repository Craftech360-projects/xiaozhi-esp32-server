"""
Riddle Generator Service
Uses Groq API to generate varied riddles for children
"""

import os
import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RiddleGeneratorService:
    """Generate riddle banks using Groq API"""

    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self._initialized = False

    async def initialize(self):
        """Initialize the service"""
        try:
            if not self.groq_api_key:
                logger.error("❌ Cannot initialize RiddleGeneratorService: GROQ_API_KEY not set")
                return False

            logger.info("✅ Riddle Generator Service initialized with Groq API")
            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"❌ Error initializing RiddleGeneratorService: {e}")
            self._initialized = False
            return False

    def is_available(self) -> bool:
        """Check if service is ready"""
        return self._initialized and bool(self.groq_api_key)

    async def generate_riddle_bank(self, count: int = 5, difficulty: str = "easy") -> Dict[str, Any]:
        """
        Generate a bank of riddles with answers

        Args:
            count: Number of riddles to generate (default 5)
            difficulty: Difficulty level: "easy", "medium", "hard"

        Returns:
            dict: {
                'success': bool,
                'riddles': [
                    {'riddle': str, 'answer': str},
                    ...
                ],
                'error': str or None
            }
        """
        try:
            if not self.is_available():
                logger.warning("⚠️ Riddle generator not available")
                return {
                    'success': False,
                    'riddles': [],
                    'error': 'Service not initialized'
                }

            from openai import AsyncOpenAI

            # Use direct Groq API call
            client = AsyncOpenAI(
                api_key=self.groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )

            prompt = self._create_prompt(count, difficulty)

            response = await client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # Higher temperature for variety
                max_tokens=800
            )

            raw_response = response.choices[0].message.content.strip()
            logger.debug(f"Raw riddle bank response: {raw_response}")

            # Parse JSON response
            riddles = self._parse_response(raw_response)

            if riddles:
                logger.info(f"✅ Generated {len(riddles)} riddles")
                return {
                    'success': True,
                    'riddles': riddles,
                    'error': None
                }
            else:
                logger.warning("⚠️ Failed to parse riddles from response")
                return {
                    'success': False,
                    'riddles': [],
                    'error': 'Failed to parse riddles'
                }

        except Exception as e:
            logger.error(f"❌ Error generating riddle bank: {e}")
            return {
                'success': False,
                'riddles': [],
                'error': str(e)
            }

    def _create_prompt(self, count: int, difficulty: str) -> str:
        """Create prompt for riddle generation"""

        difficulty_guidelines = {
            "easy": "Simple riddles about everyday objects (animals, household items, body parts). Example: 'I have hands but cannot clap. What am I?' Answer: 'clock'",
            "medium": "Riddles about concepts, nature, abstract ideas. Example: 'I can fly without wings. I can cry without eyes. What am I?' Answer: 'cloud'",
            "hard": "Wordplay riddles, logic puzzles. Example: 'The more you take, the more you leave behind. What am I?' Answer: 'footsteps'"
        }

        guidelines = difficulty_guidelines.get(difficulty, difficulty_guidelines["easy"])

        return f"""You are a riddle master creating riddles for children.

Generate {count} DIFFERENT riddles. Each riddle must be UNIQUE and VARIED.

**Requirements:**
- Difficulty: {difficulty} - {guidelines}
- Make riddles diverse (don't repeat similar patterns)
- Riddles should be simple and clear for children
- Each riddle must have ONE clear answer (single word or simple phrase)
- Answer should be straightforward (no multiple interpretations)
- Return ONLY valid JSON, no other text

**Output Format (JSON only):**
{{
  "riddles": [
    {{"riddle": "I have hands but cannot clap. What am I?", "answer": "clock"}},
    {{"riddle": "I have a face and two hands, but no arms or legs. What am I?", "answer": "clock"}},
    {{"riddle": "I'm tall when I'm young, and short when I'm old. What am I?", "answer": "candle"}},
    {{"riddle": "What has keys but no locks?", "answer": "piano"}},
    {{"riddle": "I have a neck but no head. What am I?", "answer": "bottle"}}
  ]
}}

**CRITICAL:**
- Return ONLY the JSON
- Each riddle must be different
- Answer must be a simple word or short phrase (1-3 words)
- Answer should be the MOST COMMON/EXPECTED answer

Generate {count} riddles now:"""

    def _parse_response(self, raw_response: str) -> List[Dict[str, Any]]:
        """Parse JSON response from LLM"""
        try:
            # Try to extract JSON from response
            # Sometimes LLM adds markdown code blocks
            if "```json" in raw_response:
                # Extract JSON from markdown
                start = raw_response.find("```json") + 7
                end = raw_response.find("```", start)
                json_str = raw_response[start:end].strip()
            elif "```" in raw_response:
                # Extract JSON from generic code block
                start = raw_response.find("```") + 3
                end = raw_response.find("```", start)
                json_str = raw_response[start:end].strip()
            else:
                json_str = raw_response.strip()

            # Parse JSON
            data = json.loads(json_str)

            if 'riddles' in data and isinstance(data['riddles'], list):
                # Validate each riddle
                valid_riddles = []
                for r in data['riddles']:
                    if 'riddle' in r and 'answer' in r:
                        # Ensure both are strings
                        valid_riddles.append({
                            'riddle': str(r['riddle']),
                            'answer': str(r['answer']).strip()
                        })
                    else:
                        logger.warning(f"⚠️ Invalid riddle format: {r}")
                        continue

                return valid_riddles

            return []

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {e}")
            logger.debug(f"Raw response: {raw_response}")
            return []
        except Exception as e:
            logger.error(f"❌ Error parsing response: {e}")
            return []
