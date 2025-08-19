# NCERT Class 12 Physics Textbook Setup

You have successfully prepared the RAG system for NCERT Class 12 Physics textbooks! 

## Textbooks Ready for Indexing

1. **NCERT-Class-12-Physics-Part-1.pdf** (4.6 MB)
2. **NCERT-Class-12-Physics-Part-2.pdf** (4.7 MB)

## Setup Instructions

Since the environment doesn't have pip installed, you'll need to run these commands on your actual server:

### 1. Install Dependencies

```bash
cd main/xiaozhi-server
pip install chromadb sentence-transformers PyPDF2
```

### 2. Index the Physics Textbooks

```bash
# Index Part 1
python scripts/index_textbook.py ./textbooks/NCERT-Class-12-Physics-Part-1.pdf "Physics" "Class-12"

# Index Part 2  
python scripts/index_textbook.py ./textbooks/NCERT-Class-12-Physics-Part-2.pdf "Physics" "Class-12"
```

### 3. Restart xiaozhi-server

After indexing, restart your xiaozhi-server to load the new plugin.

## Example Questions to Test

Once indexed, you can ask questions like:

**English:**
- "What is electromagnetic induction?"
- "Explain the photoelectric effect"
- "What are Maxwell's equations?"
- "Describe wave-particle duality"
- "What is the principle of a transformer?"
- "Explain Faraday's law"

**Hindi/Mixed:**
- "electromagnetic induction kya hai?"
- "photoelectric effect kaise kaam karta hai?"
- "transformer ka principle kya hai?"

## Expected Topics Coverage

### Part 1 Topics:
- Electric Charges and Fields
- Electrostatic Potential and Capacitance
- Current Electricity
- Moving Charges and Magnetism
- Magnetism and Matter
- Electromagnetic Induction
- Alternating Current

### Part 2 Topics:
- Electromagnetic Waves
- Ray Optics and Optical Instruments
- Wave Optics
- Dual Nature of Radiation and Matter
- Atoms
- Nuclei
- Semiconductor Electronics

## How It Works

When a student asks a physics question:
1. The system searches through both textbooks
2. Finds relevant sections using semantic search
3. Returns the most relevant content with page references
4. The LLM explains it in student-friendly language

## Tips for Better Results

1. **Be specific** - "Explain Lenz's law" works better than just "magnetism"
2. **Use keywords** - Include specific physics terms from NCERT
3. **Grade context** - The system knows these are Class 12 books
4. **Multi-language** - Works with English, Hindi, or mixed queries

## Monitoring

After indexing, you can check the status:
```bash
python test_rag_system.py
```

This will show you how many documents were indexed from each textbook.