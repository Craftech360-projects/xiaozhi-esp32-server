# 🎓 Educational RAG System for Class 6 Textbooks

A comprehensive Retrieval-Augmented Generation (RAG) system specifically designed for Class 6 textbook learning. This system helps students clear doubts, understand concepts, and learn interactively using their actual textbooks.

## 📚 Current Collections

### ✅ Available Subjects
- **Class 6 Mathematics** - 582 educational chunks from 10 chapters
- **Class 6 Science** - 698 educational chunks from 12 chapters
- **Total**: 1,280 educational content pieces

## 🎯 Key Features

### 📖 Educational Content Processing
- **Chapter Detection**: Automatically identifies chapters from PDFs
- **Content Classification**: Separates definitions, examples, exercises, formulas
- **Topic Mapping**: Links content to curriculum topics
- **Difficulty Levels**: Organizes content by complexity

### 🤔 Student-Friendly AI Tutor
- **Age-Appropriate Responses**: Tailored for 11-12 year old students
- **Patient Explanations**: Encouraging, supportive tone
- **Real-Life Examples**: Uses relatable analogies and examples
- **Step-by-Step Help**: Breaks down complex problems
- **Memory Techniques**: Provides mnemonics and learning tricks

### 🔧 Advanced Features
- **Multi-subject Support**: Separate collections per subject
- **Smart Retrieval**: Context-aware content search
- **Chapter Summaries**: Comprehensive revision material
- **Related Topics**: Discovers connected concepts
- **Doubt Clarification**: Specialized for clearing misconceptions

## 🛠️ Technology Stack

- **Vector Database**: Qdrant Cloud (1,280+ vectors stored)
- **Embeddings**: HuggingFace sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **LLM**: Groq API with Llama 3.3 70B (fast, cost-effective)
- **PDF Processing**: pypdf for text extraction
- **Framework**: LangChain for document processing and retrieval

## 🚀 Installation & Setup

### Prerequisites
- Python 3.9 or higher
- Qdrant Cloud account (or local Qdrant instance)
- Groq API key (free tier available)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file with your credentials:
```env
# Qdrant Configuration
QDRANT_URL=https://your-cluster-url.aws.cloud.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key

# Groq Configuration
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# LLM Provider
LLM_PROVIDER=groq

# Collection Settings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
CHUNK_SIZE=800
CHUNK_OVERLAP=150
```

### 3. Prepare Textbook PDFs
Organize your PDF textbooks in subject folders:
```
D:\cheekofinal\RAG\
├── Class-6-mathematics/
│   ├── chapter1.pdf
│   ├── chapter2.pdf
│   └── ... (10 chapters total)
└── Class-6-science/
    ├── chapter1.pdf
    ├── chapter2.pdf
    └── ... (12 chapters total)
```

## 📋 Usage Guide

### Ingest Textbooks

#### Mathematics:
```bash
python educational_main.py ingest \
  --grade class-6 \
  --subject mathematics \
  --directory "D:\cheekofinal\RAG\Class-6-mathematics" \
  --recreate
```

#### Science:
```bash
python educational_main.py ingest \
  --grade class-6 \
  --subject science \
  --directory "D:\cheekofinal\RAG\Class-6-science" \
  --recreate
```

### Interactive Learning Sessions

#### Start Mathematics Tutor:
```bash
python educational_main.py learn --grade class-6 --subject mathematics
```

#### Start Science Tutor:
```bash
python educational_main.py learn --grade class-6 --subject science
```

### Quick Questions

#### Mathematics Examples:
```bash
# Concept explanation
python educational_main.py query \
  --grade class-6 --subject mathematics \
  --question "What are equivalent fractions?"

# Problem solving
python educational_main.py query \
  --grade class-6 --subject mathematics \
  --question "How to add fractions with different denominators?"

# Doubt clarification
python educational_main.py query \
  --grade class-6 --subject mathematics \
  --question "I'm confused about negative numbers"
```

#### Science Examples:
```bash
# Concept explanation
python educational_main.py query \
  --grade class-6 --subject science \
  --question "What are nutrients and why do we need them?"

# Process explanation
python educational_main.py query \
  --grade class-6 --subject science \
  --question "How do plants make their food?"

# Experiment understanding
python educational_main.py query \
  --grade class-6 --subject science \
  --question "What is an electric circuit?"
```

### Get Subject Overview
```bash
# Mathematics overview
python educational_main.py overview --grade class-6 --subject mathematics

# Science overview
python educational_main.py overview --grade class-6 --subject science
```

## 💡 Sample Interactions

### Mathematics Query Example:
```
Query: "What are fractions?"

Answer:
I'm so excited to explain fractions to you in a super simple way.

**Simple Definition:** A fraction is a way to show a part of a whole. It's like having a pizza that's cut into equal pieces. If you eat one piece out of the eight pieces, you've eaten 1/8 of the pizza!

**Real-Life Example:** Imagine you have a toy box with 12 crayons, and you want to give 3 of them to your friend. You can write this as a fraction: 3/12.

**Step-by-Step Process:**
1. **Numerator** (top number): Shows how many parts we have
2. **Denominator** (bottom number): Shows total parts the whole is divided into

Sources: Note, Concept (from textbook)
```

### Science Query Example:
```
Query: "What are nutrients and why do we need them?"

Answer:
Nutrients are substances that our bodies need to function properly. Think of nutrients like the building blocks of our bodies.

**NERDS Memory Trick:**
* N: Nourish our bodies (provide energy)
* E: Energize our bodies (carbohydrates give energy)  
* R: Repair our bodies (proteins build muscles)
* D: Defend our bodies (vitamins protect from diseases)
* S: Support growth (help us grow and develop)

Sources: Concept, Exercise (from textbook)
```

## 📊 System Architecture

```
Educational RAG System
├── 📖 Subject Collections
│   ├── class-6-mathematics (582 vectors)
│   └── class-6-science (698 vectors)
├── 🔍 Smart Retrieval Engine
│   ├── Vector Search (HuggingFace embeddings)
│   ├── Metadata Filtering (by chapter, content type)
│   └── Context Ranking
├── 🤖 AI Tutor (Groq + Llama 3.3)
│   ├── Student-Friendly Prompts
│   ├── Age-Appropriate Language
│   └── Encouraging Responses
└── 📚 Content Processing
    ├── PDF Text Extraction (pypdf)
    ├── Educational Chunking
    ├── Chapter Detection
    └── Content Classification
```

## 🗄️ Metadata Structure

Each educational chunk contains rich metadata:
```json
{
  "text": "Equivalent fractions represent the same value...",
  "grade": "class-6",
  "subject": "mathematics",
  "chapter_number": 7,
  "chapter_title": "Fractions",
  "content_category": "definition",
  "topics": ["equivalent fractions", "comparing fractions"],
  "difficulty_level": "medium",
  "page_number": 15,
  "source": "Chapter-7-Fractions.pdf"
}
```

## 📈 Performance Metrics

### Current Statistics:
- **Total Educational Content**: 1,280 chunks
- **Mathematics Coverage**: 10 chapters, 582 chunks
- **Science Coverage**: 12 chapters, 698 chunks
- **Average Query Response Time**: ~2-3 seconds
- **Embedding Dimension**: 384 (optimized for educational content)
- **Chunk Size**: 800 characters (optimal for comprehension)

### Subject Breakdown:

#### Mathematics Chapters:
1. Patterns in Mathematics (25 chunks)
2. Lines and Angles (108 chunks)
3. Number Play (45 chunks)
4. Data Handling and Presentation (81 chunks)
5. Prime Time (39 chunks)
6. Perimeter and Area (38 chunks)
7. Fractions (63 chunks)
8. Playing with Constructions (51 chunks)
9. Symmetry (43 chunks)
10. The Other Side of Zero (89 chunks)

#### Science Chapters:
1. Food and Its Sources (24 chunks)
2. Components of Food (67 chunks)
3. Fibre to Fabric (55 chunks)
4. Sorting Materials (65 chunks)
5. Separation of Substances (54 chunks)
6. Changes Around Us (50 chunks)
7. Getting to Know Plants (66 chunks)
8. Body Movements (52 chunks)
9. Living Organisms (67 chunks)
10. Motion and Measurement (72 chunks)
11. Light, Shadows and Reflections (60 chunks)
12. Electricity and Circuits (66 chunks)

## 🔧 Advanced Features

### 1. Content Filtering
```python
# Find only definitions in Chapter 7
retriever.search_concepts("fractions", content_type="definition", chapter_number=7)

# Find all exercises
retriever.search_concepts("practice problems", content_type="exercise")

# Search by difficulty
retriever.search_by_difficulty("easy")
```

### 2. Chapter Summaries
```python
# Get comprehensive chapter summary
summary = retriever.get_chapter_summary(7)  # Fractions chapter
```

### 3. Related Topics Discovery
```python
# Find connected concepts
related = retriever.find_related_topics("fractions")
```

## 🎯 Educational Benefits

### For Students:
- ✅ **24/7 Availability**: Always ready to help with homework
- ✅ **Patient Explanations**: Never gets frustrated, always encouraging
- ✅ **Personalized Learning**: Adapts to different question styles
- ✅ **Step-by-Step Help**: Breaks down complex problems
- ✅ **Memory Techniques**: Provides mnemonics and learning tricks
- ✅ **Curriculum Aligned**: Based on actual textbook content
- ✅ **Safe Learning Environment**: No inappropriate content risk

### For Teachers/Parents:
- ✅ **Progress Monitoring**: Track what topics students ask about
- ✅ **Curriculum Support**: Reinforces classroom learning
- ✅ **Doubt Identification**: Helps identify common misconceptions
- ✅ **Learning Analytics**: Understand learning patterns
- ✅ **Time Saving**: Reduces repetitive question answering

## 🔍 Troubleshooting

### Common Issues:

#### 1. Connection Errors
```bash
Error: Failed to connect to Qdrant
```
**Solution**: Check your `QDRANT_URL` and `QDRANT_API_KEY` in `.env` file

#### 2. No Results Found
```bash
Error: No relevant documents found
```
**Solution**: Ensure textbooks are ingested correctly. Run overview command to check:
```bash
python educational_main.py overview --grade class-6 --subject mathematics
```

#### 3. LLM Errors
```bash
Error: Groq API error
```
**Solution**: Check your `GROQ_API_KEY` and ensure you have API credits

#### 4. Unicode Display Issues (Windows)
```bash
UnicodeEncodeError: 'charmap' codec can't encode character
```
**Solution**: This is cosmetic only. The system works fine; just emojis don't display properly in Windows CMD.

### Performance Optimization:

#### For Faster Queries:
- Set `CHUNK_SIZE=600` for smaller, more focused chunks
- Use `k=3` instead of `k=5` for fewer retrieved documents

#### For Better Quality:
- Set `CHUNK_SIZE=1000` for more context
- Use `k=7` for more comprehensive answers

## 🔮 Future Enhancements

### Planned Features:
- **More Subjects**: English, Hindi, Social Studies
- **Higher Grades**: Class 7, 8, 9, 10
- **Visual Learning**: Image and diagram understanding
- **Progress Tracking**: Student learning analytics
- **Parent Dashboard**: Progress monitoring interface
- **Offline Mode**: Local deployment option

### Potential Integrations:
- **Web Interface**: Browser-based learning platform
- **Mobile App**: iOS/Android applications
- **Learning Management System**: Integration with school systems
- **Voice Interface**: Speech-to-text query input

## 📞 Support & Contribution

### Getting Help:
- Create issues for bugs or feature requests
- Check troubleshooting section first
- Provide logs and error messages when reporting issues

### Contributing:
- Fork the repository
- Create feature branches
- Submit pull requests with clear descriptions
- Follow existing code style and documentation standards

## 📜 License

MIT License - Feel free to use this system for educational purposes.

---

## 🎓 Educational Impact

This system represents a significant step toward democratizing quality education by making personalized tutoring available to all students. By combining actual textbook content with AI-powered explanations, we ensure that students receive accurate, curriculum-aligned help whenever they need it.

The system has successfully processed and made searchable:
- **1,280 educational content pieces**
- **22 complete chapters** across two subjects
- **Thousands of concepts, examples, and exercises**

Ready to help students learn, understand, and excel in their studies! 🌟

---

*Last Updated: January 2025*
*Total Educational Content: 1,280 chunks*
*Subjects Available: Mathematics, Science*
*Grade Level: Class 6*