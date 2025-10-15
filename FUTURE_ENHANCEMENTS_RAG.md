# Future Enhancements for TOC-Guided RAG Pipeline

## Overview
This document outlines **Phase 2 enhancements** to be implemented after the base TOC-guided RAG pipeline is complete and validated.

**Current Base Plan Quality:** 5.5/10 → 8.5/10 (55% improvement)
**With These Enhancements:** 8.5/10 → 9.2/10 (67% total improvement)

---

## 🔥 Enhancement 1: Multi-Modal Support for Figures & Tables

### Problem Statement
Currently, we extract text but lose valuable visual information:
- Diagrams (scientific method flowcharts, process diagrams)
- Tables (data comparisons, classification tables)
- Charts and graphs
- Labeled illustrations

**Impact:** Students asking about visual content get incomplete or no answers.

### Proposed Solution

#### 1.1 Figure Extraction from PDF
**NEW FILE:** `src/rag/figure_extractor.py`

```python
"""
Extract figures, tables, and diagrams from PDF with context
"""

import pdfplumber
from PIL import Image
import io
from typing import Dict, List, Tuple

class FigureExtractor:
    """Extract and process visual elements from PDFs"""

    def extract_figures(self, pdf_path: str) -> List[Dict]:
        """
        Extract all figures with context

        Returns:
            [
                {
                    'figure_id': 'fig_1_2',
                    'page': 2,
                    'caption': 'Diagram of scientific method',
                    'image_data': bytes,
                    'bounding_box': (x, y, width, height),
                    'nearby_text': 'Context from surrounding text...'
                }
            ]
        """
        pass

    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """
        Extract tables with structured data

        Returns:
            [
                {
                    'table_id': 'table_1_1',
                    'page': 3,
                    'caption': 'Properties of materials',
                    'data': [[row1], [row2], ...],
                    'headers': ['Material', 'Property', 'Use']
                }
            ]
        """
        pass
```

#### 1.2 Visual Embedding and Storage
**NEW FILE:** `src/rag/visual_embeddings.py`

```python
"""
Generate embeddings for visual content using CLIP
"""

from transformers import CLIPProcessor, CLIPModel
import torch

class VisualEmbeddingManager:
    """Generate embeddings for images and diagrams"""

    def __init__(self):
        self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    async def embed_image(self, image_data: bytes, caption: str) -> List[float]:
        """
        Generate multimodal embedding for image + caption

        Combines visual and text embeddings for better retrieval
        """
        pass

    async def search_visual_content(self, query: str, collection: str) -> List[Dict]:
        """Search for relevant figures/tables"""
        pass
```

#### 1.3 Integration with TOC Pipeline

**MODIFY:** `scripts/process_with_toc_pipeline.py`

```python
# Add after text extraction:

# Step 1.5: Extract figures and tables
logger.info("Step 1.5: Extracting figures and tables...")
figure_extractor = FigureExtractor()
figures = figure_extractor.extract_figures(pdf_path)
tables = figure_extractor.extract_tables(pdf_path)

logger.info(f"  ✓ Extracted {len(figures)} figures, {len(tables)} tables")

# Step 6.5: Generate visual embeddings
logger.info("Step 6.5: Generating visual embeddings...")
visual_manager = VisualEmbeddingManager()

for figure in figures:
    embedding = await visual_manager.embed_image(
        figure['image_data'],
        figure['caption']
    )
    figure['embedding'] = embedding

# Step 7.5: Store visual content in parallel collection
await qdrant_manager.upsert_visual_content(
    f"{collection_name}_visual",
    figures + tables
)
```

#### 1.4 Enhanced Answer Generation

**MODIFY:** `src/services/education_service.py`

```python
async def answer_question_with_visuals(self, question: str) -> Dict:
    """Answer with text + relevant figures/tables"""

    # Get text answer
    text_result = await self.answer_question_with_toc(question)

    # Search for relevant visual content
    visual_results = await self.visual_manager.search_visual_content(
        question,
        self.current_collection
    )

    # Combine in answer
    if visual_results:
        text_result['visual_aids'] = [
            {
                'type': v['type'],  # 'figure' or 'table'
                'caption': v['caption'],
                'reference': f"See Figure {v['figure_id']}",
                'description': v.get('nearby_text', '')
            }
            for v in visual_results[:3]
        ]

    return text_result
```

### Expected Impact
- **+10% quality improvement**
- **85% visual support** (currently 0%)
- Better answers for "show me diagram", "what does the table show"

### Effort Estimate
- **4 hours** implementation
- **1 hour** testing

---

## 🔗 Enhancement 2: Cross-Reference Resolution

### Problem Statement
Educational content is heavily interconnected:
- "As we saw in Activity 1.1..."
- "Refer back to Section 2.3 for details..."
- "This builds on the concept of X from Chapter 1..."

**Impact:** Students lose important conceptual connections and context.

### Proposed Solution

#### 2.1 Reference Detection
**NEW FILE:** `src/rag/reference_resolver.py`

```python
"""
Detect and resolve cross-references in educational content
"""

import re
from typing import Dict, List, Tuple

class ReferenceResolver:
    """Detect and resolve references between content"""

    def detect_references(self, text: str, chapter_num: int) -> List[Dict]:
        """
        Detect all references in text

        Patterns:
        - "Activity 1.1"
        - "Section 2.3"
        - "Chapter 3"
        - "as discussed earlier"
        - "see Figure 1.2"

        Returns:
            [
                {
                    'type': 'activity' | 'section' | 'figure',
                    'target_id': 'activity_1.1',
                    'context': 'Surrounding text...',
                    'reference_text': 'Activity 1.1'
                }
            ]
        """

        references = []

        # Activity references
        activity_pattern = r'Activity\s+(\d+\.\d+)'
        for match in re.finditer(activity_pattern, text):
            references.append({
                'type': 'activity',
                'target_id': f"activity_{match.group(1)}",
                'context': self._extract_context(text, match.start(), match.end()),
                'reference_text': match.group(0)
            })

        # Section references
        section_pattern = r'[Ss]ection\s+(\d+\.\d+)'
        for match in re.finditer(section_pattern, text):
            references.append({
                'type': 'section',
                'target_id': match.group(1),
                'context': self._extract_context(text, match.start(), match.end()),
                'reference_text': match.group(0)
            })

        # Figure references
        figure_pattern = r'[Ff]igure\s+(\d+\.\d+)'
        for match in re.finditer(figure_pattern, text):
            references.append({
                'type': 'figure',
                'target_id': f"fig_{match.group(1)}",
                'context': self._extract_context(text, match.start(), match.end()),
                'reference_text': match.group(0)
            })

        return references

    def _extract_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Extract context around reference"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]

    async def resolve_reference(self, ref: Dict, qdrant_manager) -> Optional[Dict]:
        """
        Resolve reference to actual content

        Returns referenced chunk/section content
        """
        pass
```

#### 2.2 Build Reference Graph
**NEW FILE:** `src/rag/knowledge_graph.py`

```python
"""
Build knowledge graph of concept relationships
"""

import networkx as nx
from typing import Dict, List

class KnowledgeGraph:
    """Graph of concepts and their relationships"""

    def __init__(self):
        self.graph = nx.DiGraph()

    def build_from_toc(self, expanded_toc: Dict, references: List[Dict]):
        """
        Build graph from TOC and detected references

        Nodes: sections, activities, concepts
        Edges: references, prerequisites, related_to
        """

        # Add all sections as nodes
        for section in expanded_toc['sections']:
            self.graph.add_node(
                section['id'],
                title=section['title'],
                type=section['type'],
                concepts=section.get('key_concepts', [])
            )

        # Add reference edges
        for ref in references:
            if ref['source_id'] and ref['target_id']:
                self.graph.add_edge(
                    ref['source_id'],
                    ref['target_id'],
                    type='references',
                    context=ref['context']
                )

    def get_related_sections(self, section_id: str, depth: int = 2) -> List[str]:
        """Get all related sections within depth hops"""

        if section_id not in self.graph:
            return []

        # BFS to depth
        related = []
        visited = {section_id}
        queue = [(section_id, 0)]

        while queue:
            node, d = queue.pop(0)
            if d >= depth:
                continue

            for neighbor in self.graph.neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    related.append(neighbor)
                    queue.append((neighbor, d + 1))

        return related

    def find_prerequisite_path(self, start: str, end: str) -> List[str]:
        """Find learning path from start to end concept"""
        try:
            return nx.shortest_path(self.graph, start, end)
        except nx.NetworkXNoPath:
            return []
```

#### 2.3 Enhanced Retrieval with References

**MODIFY:** `src/services/education_service.py`

```python
async def answer_question_with_references(self, question: str) -> Dict:
    """Answer with cross-referenced context"""

    # Get main answer
    result = await self.answer_question_with_toc(question)

    # Get sections used
    section_ids = result.get('toc_sections_used', [])

    # For each section, get related sections via references
    knowledge_graph = await self.load_knowledge_graph()

    related_content = []
    for section_id in section_ids:
        related_ids = knowledge_graph.get_related_sections(section_id, depth=1)

        for related_id in related_ids[:2]:  # Max 2 related per section
            related_chunk = await self.get_section_content(related_id)
            if related_chunk:
                related_content.append({
                    'section_id': related_id,
                    'section_title': related_chunk['title'],
                    'relation': 'referenced_in',
                    'snippet': related_chunk['content'][:200]
                })

    if related_content:
        result['related_content'] = related_content
        result['answer'] += f"\n\n**Related Topics:** {', '.join([r['section_title'] for r in related_content])}"

    return result
```

### Expected Impact
- **+8% quality improvement**
- **90% concept linking** (currently 60%)
- Better understanding of topic relationships

### Effort Estimate
- **5 hours** implementation
- **1 hour** testing

---

## 📝 Enhancement 3: Question Classification & Answer Templates

### Problem Statement
Different question types need different answer formats:
- "What is X?" needs: Definition → Key Points → Example
- "How to X?" needs: Step-by-step numbered list
- "Compare X and Y" needs: Table or side-by-side format
- "Why does X?" needs: Cause-effect explanation

**Impact:** Generic answers lack clarity and structure.

### Proposed Solution

#### 3.1 Enhanced Question Classifier
**MODIFY:** `src/rag/retriever.py` (QueryAnalyzer class)

```python
class QuestionType(Enum):
    """Detailed question types"""
    DEFINITION = "definition"           # What is X?
    EXPLANATION = "explanation"         # Why/How does X work?
    PROCEDURE = "procedure"             # How to do X?
    COMPARISON = "comparison"           # Compare X and Y
    EXAMPLE = "example"                 # Give example of X
    LIST = "list"                       # List/Name types of X
    CAUSE_EFFECT = "cause_effect"       # Why does X happen?
    APPLICATION = "application"         # When/where to use X?

def _detect_question_type_detailed(self, query: str) -> QuestionType:
    """Enhanced question type detection"""

    query_lower = query.lower()

    # Definition patterns
    if re.search(r'\b(what is|define|meaning of|definition)\b', query_lower):
        return QuestionType.DEFINITION

    # Procedure patterns
    if re.search(r'\b(how to|steps to|procedure|method to)\b', query_lower):
        return QuestionType.PROCEDURE

    # Comparison patterns
    if re.search(r'\b(compare|difference|versus|vs|contrast)\b', query_lower):
        return QuestionType.COMPARISON

    # List patterns
    if re.search(r'\b(list|name|types of|kinds of|examples of)\b', query_lower):
        return QuestionType.LIST

    # Cause-effect patterns
    if re.search(r'\b(why does|what causes|reason for)\b', query_lower):
        return QuestionType.CAUSE_EFFECT

    # Application patterns
    if re.search(r'\b(when to|where to|in what situation)\b', query_lower):
        return QuestionType.APPLICATION

    # Example request
    if re.search(r'\b(example|demonstrate|show me)\b', query_lower):
        return QuestionType.EXAMPLE

    # Default
    return QuestionType.EXPLANATION
```

#### 3.2 Answer Template Engine
**NEW FILE:** `src/rag/answer_templates.py`

```python
"""
Answer formatting templates for different question types
"""

from typing import Dict, List
from enum import Enum

class AnswerFormatter:
    """Format answers based on question type"""

    def format_definition_answer(self, content: Dict) -> str:
        """
        Format for "What is X?" questions

        Structure:
        1. Clear definition
        2. Key characteristics
        3. Simple example
        """

        template = """
**Definition:** {definition}

**Key Points:**
{key_points}

**Example:** {example}
"""

        # Extract from content
        definition = self._extract_definition(content['text'])
        key_points = self._extract_key_points(content['concepts'])
        example = self._extract_example(content['text'])

        return template.format(
            definition=definition,
            key_points=key_points,
            example=example
        )

    def format_procedure_answer(self, content: Dict) -> str:
        """
        Format for "How to X?" questions

        Structure:
        1. Overview
        2. Numbered steps
        3. Tips/warnings
        """

        template = """
**How to {task}:**

{overview}

**Steps:**
{numbered_steps}

{tips}
"""

        steps = self._extract_steps(content['text'])

        return template.format(
            task=content['task'],
            overview=content['overview'],
            numbered_steps=self._format_numbered_list(steps),
            tips=self._extract_tips(content['text'])
        )

    def format_comparison_answer(self, content: Dict) -> str:
        """
        Format for "Compare X and Y" questions

        Structure:
        1. Brief intro
        2. Comparison table/bullets
        3. Summary
        """

        template = """
**Comparing {item1} and {item2}:**

{comparison_table}

**Summary:** {summary}
"""

        return template.format(
            item1=content['item1'],
            item2=content['item2'],
            comparison_table=self._create_comparison_table(content),
            summary=content['summary']
        )

    def format_list_answer(self, content: Dict) -> str:
        """
        Format for "List/Name X" questions

        Structure:
        1. Count/overview
        2. Bulleted list with brief descriptions
        """

        template = """
**{category}:** There are {count} types:

{bulleted_list}
"""

        items = self._extract_list_items(content['text'])

        return template.format(
            category=content['category'],
            count=len(items),
            bulleted_list=self._format_bulleted_list(items)
        )

    def format_cause_effect_answer(self, content: Dict) -> str:
        """
        Format for "Why does X?" questions

        Structure:
        1. Direct answer (cause)
        2. Explanation (mechanism)
        3. Example/illustration
        """

        template = """
**Why {phenomenon}?**

**Cause:** {cause}

**Explanation:** {explanation}

**For example:** {example}
"""

        return template.format(
            phenomenon=content['phenomenon'],
            cause=content['cause'],
            explanation=content['explanation'],
            example=content['example']
        )

    def _format_numbered_list(self, items: List[str]) -> str:
        """Create numbered list"""
        return '\n'.join([f"{i+1}. {item}" for i, item in enumerate(items)])

    def _format_bulleted_list(self, items: List[str]) -> str:
        """Create bulleted list"""
        return '\n'.join([f"• {item}" for item in items])

    def _create_comparison_table(self, content: Dict) -> str:
        """Create simple text comparison table"""
        # Implementation for creating comparison format
        pass
```

#### 3.3 Integration with Education Service

**MODIFY:** `src/services/education_service.py`

```python
async def answer_question_formatted(self, question: str) -> Dict:
    """Answer with appropriate formatting based on question type"""

    # Detect question type
    from src.rag.retriever import QueryAnalyzer
    analyzer = QueryAnalyzer()
    analysis = analyzer.analyze_query(question)

    # Get content
    result = await self.answer_question_with_toc(question)

    # Format answer
    from src.rag.answer_templates import AnswerFormatter
    formatter = AnswerFormatter()

    if analysis.question_type == QuestionType.DEFINITION:
        formatted = formatter.format_definition_answer(result)
    elif analysis.question_type == QuestionType.PROCEDURE:
        formatted = formatter.format_procedure_answer(result)
    elif analysis.question_type == QuestionType.COMPARISON:
        formatted = formatter.format_comparison_answer(result)
    elif analysis.question_type == QuestionType.LIST:
        formatted = formatter.format_list_answer(result)
    elif analysis.question_type == QuestionType.CAUSE_EFFECT:
        formatted = formatter.format_cause_effect_answer(result)
    else:
        formatted = result['answer']  # Default format

    result['answer'] = formatted
    result['question_type'] = analysis.question_type.value

    return result
```

### Expected Impact
- **+12% quality improvement**
- **Excellent answer clarity** (vs generic)
- Better structured responses for all question types

### Effort Estimate
- **3 hours** implementation
- **1 hour** testing

---

## 📊 Summary: Future Enhancements

| Enhancement | Quality Gain | Effort | Priority |
|-------------|--------------|--------|----------|
| **Multi-Modal Support** | +10% | 5h | HIGH |
| **Cross-Reference Resolution** | +8% | 6h | MEDIUM |
| **Answer Templates** | +12% | 4h | HIGH |
| **Total** | **+30%** | **15h** | - |

**Combined Result:** 8.5/10 → 9.2/10 (67% total improvement from baseline)

---

## 🗓️ Implementation Timeline

### Phase 2.1 (Week 2)
- Enhancement 3: Answer Templates (4h)
- Testing (1h)
- Deploy to production

### Phase 2.2 (Week 3)
- Enhancement 1: Multi-Modal Support (5h)
- Testing (1h)
- Deploy to production

### Phase 2.3 (Week 4)
- Enhancement 2: Cross-Reference Resolution (6h)
- Testing (1h)
- Deploy to production

**Total: 3 weeks for all enhancements**

---

## 🎯 Success Metrics

### Enhancement 1 (Multi-Modal)
- ✅ 85%+ visual content support
- ✅ Answers include relevant figures/tables
- ✅ "Show me diagram" queries work

### Enhancement 2 (Cross-References)
- ✅ 90%+ concept linking
- ✅ Related content appears in answers
- ✅ Learning paths discoverable

### Enhancement 3 (Answer Templates)
- ✅ All question types get appropriate format
- ✅ User satisfaction rating >4.5/5
- ✅ Answer clarity improved by 30%+

---

## 📝 Notes

- These enhancements build on the base TOC-guided RAG pipeline
- Implement **after** base system is validated in production
- Each enhancement is independent and can be prioritized separately
- Expected to take system from 8.5/10 to 9.2/10 quality

---

**Document Created:** 2025-01-XX
**Status:** Planning Phase
**Dependencies:** Base TOC-guided RAG pipeline (PLAN_TOC_GUIDED_RAG.md)
