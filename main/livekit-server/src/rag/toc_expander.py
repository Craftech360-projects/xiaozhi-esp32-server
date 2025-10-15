"""
TOC Expansion using LLM
Enriches TOC entries with rich educational metadata
"""

import logging
import json
from typing import Dict, List, Optional
import asyncio
import os

logger = logging.getLogger(__name__)

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("openai not available. Install with: pip install openai")


class TOCExpander:
    """Expand TOC entries with rich educational metadata"""

    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is required. Install with: pip install openai")

        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def expand_toc(self, toc: Dict, full_text: str) -> Dict:
        """
        Expand each TOC section with rich metadata

        Adds:
        - expanded_description
        - key_concepts
        - learning_objectives
        - difficulty_level
        - cognitive_level
        - related_activities
        """

        expanded_toc = {
            'chapter': toc['chapter'],
            'title': toc['title'],
            'sections': []
        }

        # Process in batches of 3
        batch_size = 3
        sections = toc['sections']

        for i in range(0, len(sections), batch_size):
            batch = sections[i:i + batch_size]

            tasks = [
                self._expand_section(section, full_text, toc['chapter'])
                for section in batch
            ]

            expanded_batch = await asyncio.gather(*tasks)
            expanded_toc['sections'].extend(expanded_batch)

        logger.info(f"Expanded {len(expanded_toc['sections'])} TOC sections")
        return expanded_toc

    async def _expand_section(self, section: Dict, full_text: str, chapter_num: int) -> Dict:
        """Expand a single TOC section with metadata"""

        section_content = self._extract_section_content(
            full_text,
            section['start_text'],
            max_chars=2000
        )

        prompt = self._build_expansion_prompt(section, section_content, chapter_num)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational content analyst specializing in curriculum design."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )

            metadata = json.loads(response.choices[0].message.content)
            expanded_section = {**section, **metadata}

            return expanded_section

        except Exception as e:
            logger.error(f"Failed to expand section {section['id']}: {e}")
            return self._add_default_metadata(section)

    def _extract_section_content(self, full_text: str, start_text: str, max_chars: int = 2000) -> str:
        """Extract section content from full text"""

        if not start_text:
            return full_text[:max_chars]

        start_idx = full_text.find(start_text)
        if start_idx == -1:
            return full_text[:max_chars]

        section_content = full_text[start_idx:start_idx + max_chars]
        return section_content

    def _build_expansion_prompt(self, section: Dict, content: str, chapter_num: int) -> str:
        """Build prompt for section expansion"""

        prompt = f"""Analyze this textbook section and provide rich educational metadata.

Section Information:
- ID: {section['id']}
- Title: {section['title']}
- Type: {section['type']}
- Priority: {section['content_priority']}
- Chapter: {chapter_num}

Section Content:
{content}

Provide metadata:

1. **expanded_description**: 2-3 sentences summarizing what this section teaches

2. **key_concepts**: List 3-5 key concepts/terms introduced

3. **learning_objectives**: 1-2 objectives - what students should be able to do

4. **difficulty_level**:
   - "beginner": Basic introductory concepts
   - "intermediate": Builds on basics
   - "advanced": Complex, multiple prerequisites

5. **cognitive_level** (Bloom's Taxonomy):
   - "remember": Recall facts, list, identify
   - "understand": Explain, describe, interpret
   - "apply": Solve problems, demonstrate, use
   - "analyze": Compare, examine, distinguish

6. **related_activities**: List activity IDs mentioned (e.g., ["activity_1.1"])

Return JSON:
{{
    "expanded_description": "...",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "learning_objectives": ["objective1", "objective2"],
    "difficulty_level": "beginner",
    "cognitive_level": "understand",
    "related_activities": []
}}"""

        return prompt

    def _add_default_metadata(self, section: Dict) -> Dict:
        """Add default metadata if expansion fails"""

        defaults = {
            'expanded_description': f"Content from section: {section['title']}",
            'key_concepts': [section['title'].lower()],
            'learning_objectives': [f"Understand {section['title'].lower()}"],
            'difficulty_level': 'beginner',
            'cognitive_level': 'understand',
            'related_activities': []
        }

        return {**section, **defaults}
