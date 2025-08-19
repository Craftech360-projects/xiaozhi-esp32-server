# NCERT Class 6 Science (Curiosity) RAG Setup

## Successfully Indexed Chapters

1. **chapter1.pdf** - 18 chunks indexed
2. **chapter2.pdf** - 26 chunks indexed

Total documents in collection: 578

## How the RAG System Works

### 1. Document Processing Pipeline

```
PDF File → Text Extraction → Chunking → Embedding → Storage → Search
```

#### Text Extraction
- Uses PyPDF2 to extract text from each page
- Preserves page numbers for reference
- Handles text encoding and formatting issues

#### Chunking Strategy
- Each page is split into chunks of ~500 characters
- 50 character overlap between chunks ensures context continuity
- Small chunks (<50 chars) are filtered out
- Each chunk retains metadata:
  - Page number
  - Source file
  - Subject (Science)
  - Grade (Class-6)
  - Chunk index

#### Embedding Generation
- Uses `paraphrase-multilingual-MiniLM-L12-v2` model
- Creates 384-dimensional vector representations
- Captures semantic meaning of text
- Supports multilingual queries (English, Hindi, etc.)

#### Storage in ChromaDB
- Vector database for fast similarity search
- Persists embeddings with metadata
- Enables filtered searches by grade/subject
- Located at `./rag_db`

### 2. Query Processing

When a student asks a question:

1. **Query Embedding**: Question converted to vector using same model
2. **Similarity Search**: Finds most similar chunks in database
3. **Ranking**: Results ordered by relevance score
4. **Context Retrieval**: Top-k chunks returned with metadata
5. **LLM Integration**: Retrieved chunks provide context for answer generation

### 3. Expected Topics in Class 6 Science

Based on NCERT Class 6 Science curriculum, the indexed chapters likely cover:

#### Chapter 1 Topics:
- Components of Food
- Nutrients (Carbohydrates, Proteins, Fats, Vitamins, Minerals)
- Balanced Diet
- Food Sources
- Deficiency Diseases
- Food Tests

#### Chapter 2 Topics:
- Sorting Materials into Groups
- Properties of Materials
- Soluble and Insoluble Substances
- Transparent, Opaque, and Translucent Materials
- Floating and Sinking
- Classification of Objects

#### Other Possible Topics (if in these chapters):
- Living and Non-living Things
- Plant Structure and Functions
- Water and Its Properties
- Air Around Us
- Light and Shadows

## Testing the System

Run the test script:
```bash
python3 test_ncert_class6_science.py
```

## Sample Queries to Test

### English Queries:
- "What are the main components of food?"
- "Explain vitamins and their importance"
- "How do we test for starch in food?"
- "What is a balanced diet?"
- "How can we group materials?"
- "What are transparent and opaque objects?"

### Hindi/Mixed Queries:
- "Khane mein kya nutrients hote hain?"
- "Balanced diet kya hai?"
- "Materials ko kaise sort karte hain?"
- "Vitamin ki kami se kya hota hai?"

## Integration with Xiaozhi

The RAG system integrates with the LLM in the following way:

1. **Intent Detection**: System identifies educational queries
2. **RAG Search**: Relevant textbook content retrieved
3. **Context Enhancement**: Retrieved chunks added to LLM prompt
4. **Answer Generation**: LLM explains concepts using textbook content
5. **Source Attribution**: Can reference specific pages

## Performance Optimization

- **Chunk Size**: 500 chars balances context vs precision
- **Overlap**: 50 chars prevents information loss at boundaries
- **Top-k**: Default 5 results provide good coverage
- **Embedding Model**: Multilingual model handles code-switching

## Troubleshooting

### If search returns no results:
1. Check if documents were indexed: `python3 test_ncert_class6_science.py`
2. Verify ChromaDB path: `./rag_db`
3. Ensure query language matches content language

### If answers are not accurate:
1. Increase top_k parameter for more context
2. Check if query terms match textbook terminology
3. Verify chunks contain complete information

## Future Enhancements

1. Index remaining chapters (3-16)
2. Add diagram descriptions
3. Include exercise questions and answers
4. Cross-reference with other subjects
5. Add grade-appropriate explanations