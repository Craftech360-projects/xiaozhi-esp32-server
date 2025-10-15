"""
Answer formatting templates for different question types
Formats RAG answers based on question type for better clarity
"""

import re
from typing import Dict, List, Optional
from enum import Enum


class QuestionType(Enum):
    """Detailed question types for answer formatting"""
    DEFINITION = "definition"           # What is X?
    EXPLANATION = "explanation"         # Why/How does X work?
    PROCEDURE = "procedure"             # How to do X?
    COMPARISON = "comparison"           # Compare X and Y
    EXAMPLE = "example"                 # Give example of X
    LIST = "list"                       # List/Name types of X
    CAUSE_EFFECT = "cause_effect"       # Why does X happen?
    APPLICATION = "application"         # When/where to use X?


class AnswerFormatter:
    """Format answers based on question type for improved clarity"""

    def format_answer(self, content: Dict, question_type: QuestionType) -> str:
        """
        Format answer based on question type

        Args:
            content: Dict with 'answer', 'sources', 'concepts', etc.
            question_type: Type of question being answered

        Returns:
            Formatted answer string
        """

        if question_type == QuestionType.DEFINITION:
            return self.format_definition_answer(content)
        elif question_type == QuestionType.PROCEDURE:
            return self.format_procedure_answer(content)
        elif question_type == QuestionType.COMPARISON:
            return self.format_comparison_answer(content)
        elif question_type == QuestionType.LIST:
            return self.format_list_answer(content)
        elif question_type == QuestionType.CAUSE_EFFECT:
            return self.format_cause_effect_answer(content)
        elif question_type == QuestionType.APPLICATION:
            return self.format_application_answer(content)
        elif question_type == QuestionType.EXAMPLE:
            return self.format_example_answer(content)
        else:
            return self.format_explanation_answer(content)

    def format_definition_answer(self, content: Dict) -> str:
        """
        Format for "What is X?" questions

        Structure:
        1. Clear definition
        2. Key characteristics/points
        3. Simple example (if available)
        """

        answer_text = content.get('answer', '')

        # Extract definition (usually first sentence or paragraph)
        definition = self._extract_definition(answer_text)

        # Extract key points
        key_points = self._extract_key_points(answer_text, content.get('key_concepts', []))

        # Extract example if present
        example = self._extract_example(answer_text)

        # Build formatted answer
        formatted_parts = []

        if definition:
            formatted_parts.append(f"**Definition:**\n{definition}")

        if key_points:
            formatted_parts.append(f"\n**Key Points:**")
            for point in key_points:
                formatted_parts.append(f"- {point}")

        if example:
            formatted_parts.append(f"\n**Example:**\n{example}")

        return '\n'.join(formatted_parts) if formatted_parts else answer_text

    def format_procedure_answer(self, content: Dict) -> str:
        """
        Format for "How to X?" questions

        Structure:
        1. Overview/purpose
        2. Numbered steps
        3. Tips/important notes
        """

        answer_text = content.get('answer', '')

        # Extract overview (first paragraph usually)
        overview = self._extract_overview(answer_text)

        # Extract steps
        steps = self._extract_steps(answer_text)

        # Extract tips/notes
        tips = self._extract_tips(answer_text)

        formatted_parts = []

        if overview:
            formatted_parts.append(overview)

        if steps:
            formatted_parts.append("\n**Steps:**")
            for i, step in enumerate(steps, 1):
                formatted_parts.append(f"{i}. {step}")

        if tips:
            formatted_parts.append(f"\n**Important Notes:**")
            for tip in tips:
                formatted_parts.append(f"- {tip}")

        return '\n'.join(formatted_parts) if formatted_parts else answer_text

    def format_comparison_answer(self, content: Dict) -> str:
        """
        Format for "Compare X and Y" questions

        Structure:
        1. Brief introduction
        2. Comparison points (side-by-side or table format)
        3. Summary/conclusion
        """

        answer_text = content.get('answer', '')

        # Extract comparison items
        items = self._extract_comparison_items(answer_text)

        # Extract comparison points
        comparison_points = self._extract_comparison_points(answer_text)

        formatted_parts = []

        if items and len(items) == 2:
            formatted_parts.append(f"**Comparing {items[0]} and {items[1]}:**\n")

        if comparison_points:
            for aspect, values in comparison_points.items():
                formatted_parts.append(f"**{aspect}:**")
                for item, value in values.items():
                    formatted_parts.append(f"- {item}: {value}")
                formatted_parts.append("")
        else:
            # Fallback: just format the text nicely
            formatted_parts.append(answer_text)

        return '\n'.join(formatted_parts)

    def format_list_answer(self, content: Dict) -> str:
        """
        Format for "List/Name X" questions

        Structure:
        1. Count/overview statement
        2. Bulleted list with brief descriptions
        """

        answer_text = content.get('answer', '')

        # Extract list items
        items = self._extract_list_items(answer_text)

        formatted_parts = []

        if items:
            # Add count if available
            formatted_parts.append(f"There are **{len(items)}** types:\n")

            for item in items:
                formatted_parts.append(f"• {item}")
        else:
            # Fallback to original text
            formatted_parts.append(answer_text)

        return '\n'.join(formatted_parts)

    def format_cause_effect_answer(self, content: Dict) -> str:
        """
        Format for "Why does X?" questions

        Structure:
        1. Direct answer (cause)
        2. Detailed explanation (mechanism)
        3. Example/illustration
        """

        answer_text = content.get('answer', '')

        # Extract cause
        cause = self._extract_cause(answer_text)

        # Extract explanation
        explanation = self._extract_explanation(answer_text)

        # Extract example
        example = self._extract_example(answer_text)

        formatted_parts = []

        if cause:
            formatted_parts.append(f"**Cause:**\n{cause}")

        if explanation:
            formatted_parts.append(f"\n**Explanation:**\n{explanation}")

        if example:
            formatted_parts.append(f"\n**Example:**\n{example}")

        return '\n'.join(formatted_parts) if formatted_parts else answer_text

    def format_application_answer(self, content: Dict) -> str:
        """
        Format for "When/where to use X?" questions

        Structure:
        1. Main uses/applications
        2. Specific contexts/scenarios
        3. Examples of application
        """

        answer_text = content.get('answer', '')

        # Extract applications
        applications = self._extract_applications(answer_text)

        formatted_parts = []

        if applications:
            formatted_parts.append("**Applications:**\n")
            for app in applications:
                formatted_parts.append(f"• {app}")
        else:
            formatted_parts.append(answer_text)

        return '\n'.join(formatted_parts)

    def format_example_answer(self, content: Dict) -> str:
        """
        Format for "Give example of X" questions

        Structure:
        1. Brief context
        2. Example(s) with details
        """

        answer_text = content.get('answer', '')

        # Extract examples
        examples = self._extract_examples_list(answer_text)

        formatted_parts = []

        if examples:
            formatted_parts.append("**Examples:**\n")
            for i, example in enumerate(examples, 1):
                if len(examples) > 1:
                    formatted_parts.append(f"{i}. {example}\n")
                else:
                    formatted_parts.append(example)
        else:
            formatted_parts.append(answer_text)

        return '\n'.join(formatted_parts)

    def format_explanation_answer(self, content: Dict) -> str:
        """
        Default format for general explanation questions

        Structure:
        1. Main explanation
        2. Key concepts (if available)
        3. Additional context
        """

        answer_text = content.get('answer', '')
        key_concepts = content.get('key_concepts', [])

        formatted_parts = [answer_text]

        if key_concepts:
            formatted_parts.append("\n**Key Concepts:**")
            for concept in key_concepts[:5]:  # Max 5 concepts
                formatted_parts.append(f"- {concept}")

        return '\n'.join(formatted_parts)

    # Helper methods for extracting content patterns

    def _extract_definition(self, text: str) -> str:
        """Extract definition (usually first 1-2 sentences)"""
        sentences = re.split(r'[.!?]+', text)
        if sentences:
            # First sentence is usually the definition
            return sentences[0].strip() + '.'
        return text[:200]  # Fallback to first 200 chars

    def _extract_key_points(self, text: str, concepts: List[str]) -> List[str]:
        """Extract key points from text"""
        points = []

        # Look for bulleted lists
        bullet_pattern = r'[-•*]\s*(.+?)(?=[-•*]|\n\n|$)'
        bullets = re.findall(bullet_pattern, text, re.DOTALL)
        if bullets:
            points.extend([b.strip() for b in bullets[:5]])

        # If no bullets, use concepts
        if not points and concepts:
            points = concepts[:5]

        # If still no points, extract sentences with keywords
        if not points:
            keywords = ['is', 'are', 'has', 'have', 'can', 'include', 'consist']
            sentences = re.split(r'[.!?]+', text)
            for sentence in sentences[1:4]:  # Skip first (definition), take next 3
                if any(kw in sentence.lower() for kw in keywords):
                    points.append(sentence.strip())

        return points[:5]  # Max 5 points

    def _extract_example(self, text: str) -> Optional[str]:
        """Extract example from text"""
        # Look for "for example", "such as", "e.g."
        example_patterns = [
            r'(?:for example|for instance|such as|e\.g\.|example:)\s*(.+?)(?:\.|$)',
            r'(?:consider|let\'s say)\s+(.+?)(?:\.|$)'
        ]

        for pattern in example_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        return None

    def _extract_overview(self, text: str) -> str:
        """Extract overview/introduction"""
        paragraphs = text.split('\n\n')
        if paragraphs:
            return paragraphs[0].strip()
        return text[:300]  # Fallback

    def _extract_steps(self, text: str) -> List[str]:
        """Extract numbered or sequential steps"""
        steps = []

        # Look for numbered steps (1., 2., etc.)
        numbered_pattern = r'(?:^|\n)\s*(\d+)[.)]\s*(.+?)(?=\n\s*\d+[.)]|\n\n|$)'
        matches = re.findall(numbered_pattern, text, re.DOTALL)
        if matches:
            steps = [match[1].strip() for match in matches]

        # Look for bulleted steps if no numbered ones
        if not steps:
            bullet_pattern = r'[-•*]\s*(.+?)(?=[-•*]|\n\n|$)'
            bullets = re.findall(bullet_pattern, text, re.DOTALL)
            if bullets:
                steps = [b.strip() for b in bullets]

        # Look for "first", "then", "next", "finally" keywords
        if not steps:
            step_keywords = r'(?:first|then|next|after that|finally)[,:]?\s*(.+?)(?=first|then|next|after that|finally|\n\n|$)'
            step_matches = re.findall(step_keywords, text, re.IGNORECASE | re.DOTALL)
            if step_matches:
                steps = [s.strip() for s in step_matches]

        return steps

    def _extract_tips(self, text: str) -> List[str]:
        """Extract tips, notes, or important points"""
        tips = []

        # Look for "note:", "tip:", "important:", "remember:"
        tip_patterns = [
            r'(?:note|tip|important|remember)[:\s]+(.+?)(?:\.|$)',
            r'(?:make sure|be careful|warning)[:\s]+(.+?)(?:\.|$)'
        ]

        for pattern in tip_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tips.extend([m.strip() for m in matches])

        return tips[:3]  # Max 3 tips

    def _extract_comparison_items(self, text: str) -> List[str]:
        """Extract items being compared"""
        # Look for "X and Y", "X vs Y", "X versus Y"
        patterns = [
            r'(?:compare|comparing)\s+(.+?)\s+(?:and|vs|versus)\s+(.+?)(?:\.|:|$)',
            r'(.+?)\s+(?:and|vs|versus)\s+(.+?)(?:\s+are|\s+differ|$)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return [match.group(1).strip(), match.group(2).strip()]

        return []

    def _extract_comparison_points(self, text: str) -> Dict[str, Dict[str, str]]:
        """Extract comparison points (aspects and values for each item)"""
        # This is complex - for now return empty dict
        # Could be enhanced with more sophisticated NLP
        return {}

    def _extract_list_items(self, text: str) -> List[str]:
        """Extract list items from text"""
        items = []

        # Look for numbered items
        numbered_pattern = r'(?:^|\n)\s*(\d+)[.)]\s*(.+?)(?=\n\s*\d+[.)]|\n\n|$)'
        matches = re.findall(numbered_pattern, text, re.DOTALL)
        if matches:
            items = [match[1].strip() for match in matches]

        # Look for bulleted items
        if not items:
            bullet_pattern = r'[-•*]\s*(.+?)(?=[-•*]|\n\n|$)'
            bullets = re.findall(bullet_pattern, text, re.DOTALL)
            if bullets:
                items = [b.strip() for b in bullets]

        # Look for comma-separated items after "are:", "include:", etc.
        if not items:
            list_intro_pattern = r'(?:are|include|consist of)[:\s]+(.+?)(?:\.|$)'
            match = re.search(list_intro_pattern, text, re.IGNORECASE)
            if match:
                list_text = match.group(1)
                items = [item.strip() for item in list_text.split(',')]

        return items

    def _extract_cause(self, text: str) -> Optional[str]:
        """Extract cause from text"""
        # Look for "because", "due to", "caused by"
        cause_patterns = [
            r'(?:because|due to|caused by)\s+(.+?)(?:\.|$)',
            r'(?:the reason is)\s+(.+?)(?:\.|$)'
        ]

        for pattern in cause_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()

        # Fallback: first sentence
        sentences = re.split(r'[.!?]+', text)
        if sentences:
            return sentences[0].strip() + '.'

        return None

    def _extract_explanation(self, text: str) -> str:
        """Extract detailed explanation"""
        # Usually middle paragraphs contain explanation
        paragraphs = text.split('\n\n')
        if len(paragraphs) > 1:
            return '\n\n'.join(paragraphs[1:])

        # Fallback: sentences after first one
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) > 1:
            return '. '.join(sentences[1:]).strip() + '.'

        return text

    def _extract_applications(self, text: str) -> List[str]:
        """Extract applications/uses"""
        apps = []

        # Look for "used for", "used to", "applied in", "useful for"
        app_patterns = [
            r'(?:used for|used to|applied in|useful for)\s+(.+?)(?:\.|,|$)',
            r'(?:application|use)[:\s]+(.+?)(?:\.|$)'
        ]

        for pattern in app_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            apps.extend([m.strip() for m in matches])

        # Look for bulleted lists
        if not apps:
            bullet_pattern = r'[-•*]\s*(.+?)(?=[-•*]|\n\n|$)'
            bullets = re.findall(bullet_pattern, text, re.DOTALL)
            if bullets:
                apps = [b.strip() for b in bullets]

        return apps[:5]  # Max 5 applications

    def _extract_examples_list(self, text: str) -> List[str]:
        """Extract multiple examples from text"""
        examples = []

        # Look for "example 1:", "example 2:", etc.
        numbered_examples = r'example\s+(\d+)[:\s]+(.+?)(?=example\s+\d+|\n\n|$)'
        matches = re.findall(numbered_examples, text, re.IGNORECASE | re.DOTALL)
        if matches:
            examples = [match[1].strip() for match in matches]

        # Look for multiple sentences starting with example keywords
        if not examples:
            example_sentences = re.findall(
                r'(?:for example|for instance|such as)[,:\s]+(.+?)(?:\.|$)',
                text,
                re.IGNORECASE
            )
            if example_sentences:
                examples = [e.strip() for e in example_sentences]

        return examples


def detect_question_type(query: str) -> QuestionType:
    """
    Detect question type from query string

    Args:
        query: User's question

    Returns:
        QuestionType enum value
    """

    query_lower = query.lower()

    # Definition patterns
    if re.search(r'\b(what is|what are|define|definition of|meaning of)\b', query_lower):
        return QuestionType.DEFINITION

    # Procedure patterns
    if re.search(r'\b(how to|how do|steps to|procedure|method to|process of)\b', query_lower):
        return QuestionType.PROCEDURE

    # Comparison patterns
    if re.search(r'\b(compare|comparison|difference between|differ|versus|vs|contrast)\b', query_lower):
        return QuestionType.COMPARISON

    # List patterns
    if re.search(r'\b(list|name|types of|kinds of|what are the)\b', query_lower):
        return QuestionType.LIST

    # Cause-effect patterns
    if re.search(r'\b(why does|why is|why do|what causes|reason for|cause of)\b', query_lower):
        return QuestionType.CAUSE_EFFECT

    # Application patterns
    if re.search(r'\b(when to|where to|when is|where is|in what situation|application)\b', query_lower):
        return QuestionType.APPLICATION

    # Example request patterns
    if re.search(r'\b(example|examples of|give example|show example|demonstrate|illustrate)\b', query_lower):
        return QuestionType.EXAMPLE

    # Default to explanation
    return QuestionType.EXPLANATION
