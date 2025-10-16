# How to Add Chapters to Qdrant Vector Database

**Last Updated:** 2025-10-15

---

## Quick Answer

```bash
cd D:\cheekofinal\xiaozhi-esp32-server\main\livekit-server
python process_textbook_with_visuals.py
```

This will process **both Chapter 1 and Chapter 2** and add them to the **same collection**: `grade_06_science`

---

## What Collections Are Created?

### Text Collection (384-dim)
- **Name:** `grade_06_science`
- **Vector Size:** 384 dimensions
- **Model:** `all-MiniLM-L6-v2` (Sentence Transformers)
- **Contains:** All chapters for Grade 6 Science

### Visual Collection (512-dim)
- **Name:** `grade_06_science_visual`
- **Vector Size:** 512 dimensions
- **Model:** `CLIP ViT-B/32`
- **Contains:** All figures and tables from Grade 6 Science chapters

---

## Key Features

### ✅ Unified Collection
- **All chapters** go into the **same collection** (`grade_06_science`)
- No separate `ch1`, `ch2` collections
- Chapters are distinguished by `chapter_number` metadata

### ✅ Auto-Creation
- Collections are **automatically created** if they don't exist
- No manual setup needed

### ✅ Dual Embeddings
- **Text:** 384-dim (faster, efficient, good quality)
- **Visual:** 512-dim (multimodal CLIP embeddings)

---

## What Gets Processed?

### Chapter 1: The Wonderful World of Science
- **Pages:** 8
- **Text Chunks:** ~19
- **Figures:** 31
- **Tables:** 1
- **Total Visual Items:** 32

### Chapter 2: Diversity in the Living World
- **Pages:** 26
- **Text Chunks:** ~30
- **Figures:** 81
- **Tables:** 9
- **Total Visual Items:** 90

### Combined Total
- **Text Chunks:** ~49
- **Visual Items:** ~122
- **All in one collection:** `grade_06_science`

---

## Prerequisites

### 1. Make Sure Qdrant is Running

```bash
docker-compose up -d qdrant
```

### 2. Verify Qdrant is Accessible

```bash
curl http://localhost:6333
```

You should see:
```json
{"title":"qdrant - vector search engine","version":"..."}
```

---

## Processing Pipeline Steps

The script performs these steps **automatically**:

### Step 1: PDF Extraction
- Extracts clean text from PDF
- Detects chapter info (number, title)

### Step 2: TOC Extraction
- Uses LLM to extract Table of Contents
- Detects sections, activities, teaching content
- **Target:** 6-10 sections per chapter

### Step 3: TOC Metadata Expansion
- Enriches each section with 11 metadata fields:
  - Key concepts
  - Learning objectives
  - Difficulty level
  - Cognitive level
  - Keywords
  - Estimated time
  - Prerequisites
  - Related sections
  - Teaching notes
  - Assessment focus
  - Common misconceptions

### Step 4: Semantic Chunking
- Creates chunks guided by TOC structure
- **CRITICAL:** Preserves activities as single chunks
- Applies content weighting (teaching: 1.0, activity: 0.95)

### Step 5: Chunk Validation
- Validates quality with similarity threshold
- **Target:** 60%+ validation rate

### Step 6: Visual Extraction
- Extracts figures and tables using pdfplumber
- Detects captions, page numbers, context

### Step 7: Text Embeddings
- Generates 384-dim embeddings for text chunks
- Batch processing for efficiency

### Step 8: Visual Embeddings
- Generates 512-dim CLIP embeddings for figures/tables
- Combines image + caption for multimodal embeddings

### Step 9: Qdrant Storage
- **Auto-creates** collections if they don't exist:
  - `grade_06_science` (384-dim for text)
  - `grade_06_science_visual` (512-dim for visual)
- Stores all chunks with metadata
- Creates payload indexes for fast filtering

### Step 10: Knowledge Graph
- Builds concept relationship graph
- Tracks cross-references

---

## Expected Output

```
================================================================================
TOC-GUIDED RAG PIPELINE WITH MULTI-MODAL SUPPORT
================================================================================

Processing: Chapter 1 The Wonderful World of Science.pdf
Collection: grade_06_science

================================================================================

[INIT] Initializing pipeline components...
  [OK] All components initialized

[STEP 0] Setting up Qdrant collections...
  [OK] Created main collection: grade_06_science
  [OK] Visual collection ready: grade_06_science_visual

[STEP 0.5] Loading embedding models...
  [OK] Text embedding model loaded (384-dim)
  [OK] CLIP visual model loaded (512-dim)

[STEP 1] Extracting PDF content...
  [OK] Extracted 8 pages
  [OK] Chapter 1: The Wonderful World of Science
  [OK] Total text: 10020 characters

[STEP 1.5] Extracting figures and tables...
  [OK] Extracted 31 figures
  [OK] Extracted 1 tables

[STEP 2] Extracting TOC structure...
  [OK] Extracted 8 TOC sections

[STEP 3] Expanding TOC with rich metadata...
  [OK] Expanded 8 sections with metadata

[STEP 4] Creating semantic chunks...
  [OK] Created 19 chunks
  [OK] Activity chunks: 2
  [OK] Teaching chunks: 17

[STEP 5] Validating chunks...
  [OK] Valid: 12, Flagged: 7
  [OK] Validation rate: 63.2%

[STEP 6] Detecting cross-references...
  [OK] Detected 14 references in 8 chunks

[STEP 6.5] Generating visual embeddings...
  [OK] Generated 32 visual embeddings

[STEP 7] Generating text embeddings...
  [OK] Generated 19 text embeddings

[STEP 7.5] Storing visual content in Qdrant...
  [OK] Stored 32 visual items

[STEP 8] Storing text content in Qdrant...
  [OK] Stored 19 text chunks

[STEP 9] Building knowledge graph...
  [OK] Graph built successfully

================================================================================
PROCESSING COMPLETE
================================================================================

Chapter 1 Results:
  - Text chunks: 19
  - Visual items: 32
  - Figures: 31
  - Tables: 1

Chapter 2 Results:
  - Text chunks: 30
  - Visual items: 90
  - Figures: 81
  - Tables: 9

Combined in Collection: grade_06_science
  - Total text chunks: 49
  - Total visual items: 122
  - Total figures: 112
  - Total tables: 10
  - Text collection: grade_06_science (384-dim)
  - Visual collection: grade_06_science_visual (512-dim)

================================================================================
```

---

## Verification

### Check Collections Were Created

```bash
curl http://localhost:6333/collections
```

You should see:
- `grade_06_science`
- `grade_06_science_visual`

### Check Collection Stats

```bash
curl http://localhost:6333/collections/grade_06_science
```

Look for:
- `points_count`: ~49 (text chunks from both chapters)
- `vectors_config.size`: 384

```bash
curl http://localhost:6333/collections/grade_06_science_visual
```

Look for:
- `points_count`: ~122 (visual items from both chapters)
- `vectors_config.size`: 512

---

## Adding More Chapters

To add Chapter 3, 4, etc., modify `process_textbook_with_visuals.py`:

```python
async def main():
    """Process Grade 6 Science textbooks - ALL chapters to same collection"""

    # Chapter 1
    result1 = await process_textbook_with_visuals(
        pdf_path="scripts/grade_06_science/Chapter 1 The Wonderful World of Science.pdf",
        collection_name="grade_06_science",
        skip_existing=False
    )

    # Chapter 2
    result2 = await process_textbook_with_visuals(
        pdf_path="scripts/grade_06_science/Chapter 2 Diversity in the Living World.pdf",
        collection_name="grade_06_science",
        skip_existing=False
    )

    # Chapter 3 (NEW)
    result3 = await process_textbook_with_visuals(
        pdf_path="scripts/grade_06_science/Chapter 3 Your Chapter Name.pdf",
        collection_name="grade_06_science",  # Same collection!
        skip_existing=False
    )
```

All chapters will be **added to the same collection** (`grade_06_science`).

---

## Metadata for Filtering

Each chunk has metadata for filtering:

### Text Chunks
```python
{
    "content": "...",
    "chapter_number": 1,  # Use this to filter by chapter
    "chapter": "The Wonderful World of Science",
    "grade": 6,
    "subject": "science",
    "section_type": "teaching_text",  # or "activity"
    "is_activity": false,
    "content_weight": 1.0,
    "difficulty_level": "beginner",
    "key_concepts": ["science", "observation", ...],
    "page_number": 5
}
```

### Visual Items
```python
{
    "type": "figure",  # or "table"
    "figure_id": "fig_1_2",
    "caption": "Diagram of scientific method",
    "page": 3,
    "chapter_number": 1,
    "nearby_text": "Context text...",
    "has_image_data": false
}
```

---

## Searching the Collection

### Example: Search Text

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

client = QdrantClient(url="http://localhost:6333")

# Search in Chapter 1 only
results = client.search(
    collection_name="grade_06_science",
    query_vector=[...],  # Your query embedding
    query_filter=Filter(
        must=[
            FieldCondition(key="chapter_number", match=MatchValue(value=1))
        ]
    ),
    limit=5
)
```

### Example: Search Visual Content

```python
# Search for figures in Chapter 2
results = client.search(
    collection_name="grade_06_science_visual",
    query_vector=[...],  # Your CLIP embedding
    query_filter=Filter(
        must=[
            FieldCondition(key="chapter_number", match=MatchValue(value=2)),
            FieldCondition(key="type", match=MatchValue(value="figure"))
        ]
    ),
    limit=5
)
```

---

## Troubleshooting

### Issue: Qdrant connection refused

**Solution:**
```bash
docker-compose up -d qdrant
```

### Issue: Collection already exists

The script handles this automatically. If you want to **recreate** the collection:

```bash
# Delete existing collection
curl -X DELETE http://localhost:6333/collections/grade_06_science
curl -X DELETE http://localhost:6333/collections/grade_06_science_visual

# Run script again
python process_textbook_with_visuals.py
```

### Issue: CLIP model download fails

The visual embedding manager will handle this gracefully:
- Falls back to caption-only embeddings
- Visual extraction still works
- Text embeddings unaffected

---

## Summary

✅ **One command** processes all chapters
✅ **Auto-creates** collections if needed
✅ **Unified collection** for all chapters (`grade_06_science`)
✅ **Dual embeddings:** 384-dim text + 512-dim visual
✅ **Complete pipeline:** TOC → Chunking → Validation → Embeddings → Storage
✅ **Rich metadata** for filtering by chapter, section, difficulty, etc.

**Total Processing Time:** ~2-3 minutes for both chapters

---

**Ready to run?**

```bash
cd D:\cheekofinal\xiaozhi-esp32-server\main\livekit-server
python process_textbook_with_visuals.py
```
