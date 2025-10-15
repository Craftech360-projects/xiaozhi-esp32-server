"""
Table of Contents Extraction using LLM
Analyzes textbook content and builds structured TOC
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


class TOCExtractor:
    """Extract Table of Contents from educational content using LLM"""

    def __init__(self):
        if not OPENAI_AVAILABLE:
            raise ImportError("openai is required. Install with: pip install openai")

        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    async def extract_toc(self, text: str, chapter_info: Dict) -> Dict:
        """
        Extract structured TOC from text using LLM

        Returns:
            {
                'chapter': int,
                'title': str,
                'sections': [
                    {
                        'id': '1.1',
                        'title': 'What is Science?',
                        'page': 1,
                        'type': 'teaching_text' | 'activity' | 'example' | 'practice',
                        'content_priority': 'high' | 'medium' | 'low',
                        'start_text': 'First 100 chars...'
                    }
                ]
            }
        """

        prompt = self._build_toc_extraction_prompt(text, chapter_info)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing educational textbooks and extracting their structure."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            toc_data = json.loads(response.choices[0].message.content)
            validated_toc = self._validate_toc(toc_data, chapter_info)

            logger.info(f"Extracted TOC with {len(validated_toc['sections'])} sections")
            return validated_toc

        except Exception as e:
            logger.error(f"Failed to extract TOC: {e}")
            return self._create_fallback_toc(chapter_info)

    def _build_toc_extraction_prompt(self, text: str, chapter_info: Dict) -> str:
        """Build prompt for TOC extraction"""

        truncated_text = text[:8000] if len(text) > 8000 else text

        prompt = f"""Analyze this textbook chapter and extract its Table of Contents structure.

Chapter Information:
- Chapter {chapter_info.get('chapter_number', 'Unknown')}
- Title: {chapter_info.get('chapter_title', 'Unknown')}

Chapter Text:
{truncated_text}

Instructions:
1. IGNORE all image descriptions, figure captions, and visual content
2. FOCUS ON:
   - Main section headings (teaching content)
   - Sub-sections and topic divisions
   - Activities (Activity 1.1, Activity 1.2, etc.)
   - Examples and practice problems
   - Key concept introductions
   - "Let us" sections (Let us think, Let us do, Let us explore, etc.)

3. For each section, identify:
   - Section ID (1.1, 1.2, 1.3, or activity_1.1, activity_1.2)
   - Section title (the actual heading text)
   - Type:
     * "teaching_text" - Core concepts, definitions, explanations
     * "activity" - Hands-on activities, experiments, "Let us" sections
     * "example" - Worked examples, demonstrations
     * "practice" - Questions, exercises
   - Content Priority:
     * "high" - Core teaching content (definitions, main concepts)
     * "medium" - Supporting content (examples, elaborations, activities)
     * "low" - Supplementary content (practice, reviews)

4. BE GRANULAR: Extract as many distinct sections as possible
   - Include major sections (1.1, 1.2, 1.3)
   - Include subsections (1.1.1, 1.1.2) if they exist
   - Include all activities separately
   - Aim for 6-10 sections per chapter

Return JSON in this exact format:
{{
    "chapter": {chapter_info.get('chapter_number', 1)},
    "title": "{chapter_info.get('chapter_title', 'Unknown')}",
    "sections": [
        {{
            "id": "1.1",
            "title": "Section Title Here",
            "page": 1,
            "type": "teaching_text",
            "content_priority": "high",
            "start_text": "First 100 characters of this section..."
        }}
    ]
}}"""

        return prompt

    def _validate_toc(self, toc_data: Dict, chapter_info: Dict) -> Dict:
        """Validate and clean TOC data"""

        validated = {
            'chapter': toc_data.get('chapter', chapter_info.get('chapter_number', 1)),
            'title': toc_data.get('title', chapter_info.get('chapter_title', 'Unknown')),
            'sections': []
        }

        seen_ids = set()

        for section in toc_data.get('sections', []):
            if not section.get('id') or not section.get('title'):
                continue

            if section['id'] in seen_ids:
                continue

            seen_ids.add(section['id'])

            validated_section = {
                'id': section['id'],
                'title': section['title'].strip(),
                'page': section.get('page', 1),
                'type': section.get('type', 'teaching_text'),
                'content_priority': section.get('content_priority', 'medium'),
                'start_text': section.get('start_text', '')[:100]
            }

            validated['sections'].append(validated_section)

        return validated

    def _create_fallback_toc(self, chapter_info: Dict) -> Dict:
        """Create minimal fallback TOC if extraction fails"""

        return {
            'chapter': chapter_info.get('chapter_number', 1),
            'title': chapter_info.get('chapter_title', 'Unknown'),
            'sections': [
                {
                    'id': f"{chapter_info.get('chapter_number', 1)}.1",
                    'title': chapter_info.get('chapter_title', 'Main Content'),
                    'page': 1,
                    'type': 'teaching_text',
                    'content_priority': 'high',
                    'start_text': ''
                }
            ]
        }
