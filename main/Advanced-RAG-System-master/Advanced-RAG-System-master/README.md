# RAG System: Ask Questions About Your PDFs!

# Sample Working Video
https://drive.google.com/file/d/1u1by62j8OaY3srCORFj7m0XsGutu3-0Y/view?usp=sharing

## Tech Stack

- **Programming Language:** Python 3.11
- **Web Framework:** [Streamlit](https://streamlit.io/) (for the user interface)
- **Vector Database:** [ChromaDB](https://www.trychroma.com/) (stores and searches document chunks)
- **Large Language Model (LLM):** [Groq Llama-3.1-8B-Instant](https://groq.com/) (cloud API, configurable)
- **Embedding Model:** [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) (local), with fallback to TF-IDF (scikit-learn)
- **PDF Processing:**
  - [PyMuPDF](https://pymupdf.readthedocs.io/) (text and image extraction)
  - [pdfplumber](https://github.com/jsvine/pdfplumber) (table extraction)
  - [pytesseract](https://github.com/madmaze/pytesseract) (OCR for images)
  - [Pillow](https://python-pillow.org/) (image handling)
- **Data Processing:** [pandas](https://pandas.pydata.org/), [numpy](https://numpy.org/)
- **Other Libraries:**
  - [transformers](https://huggingface.co/docs/transformers/index)
  - [sentence-transformers](https://www.sbert.net/)
  - [scikit-learn](https://scikit-learn.org/) (for TF-IDF fallback)
  - [tqdm](https://tqdm.github.io/) (progress bars)
  - [matplotlib](https://matplotlib.org/) (optional, for data visualization)

---

## Overview

**RAG System** is an easy-to-use tool that lets you upload PDF documents and ask questions about their content. It uses advanced AI to read, understand, and answer your questions using the information inside your PDFs. No technical knowledge is required—just upload, ask, and get answers!

---

## Key Features

- **Upload PDFs**: Add one or more PDF files (books, reports, notes, etc.).
- **Ask Anything**: Type your question in plain English and get answers based on your documents.
- **Understands Text, Tables, and Images**: Extracts information from text, tables, and even images (using OCR).
- **Smart Search**: Finds the most relevant parts of your documents to answer your question.
- **Web Interface**: Simple, user-friendly interface powered by Streamlit.
- **Statistics & Details**: See how many pages, tables, and images were processed.

---

## How It Works (Simple Explanation)

1. **Upload**: You upload one or more PDF files.
2. **Processing**: The system reads the text, tables, and images from your PDFs.
3. **Ask a Question**: You type a question (e.g., "What are the main topics in this document?").
4. **AI Search & Answer**: The system finds the most relevant information and uses AI to generate a clear answer.
5. **See Results**: The answer appears instantly, with details about where the information came from.

---

## Getting Started

### 1. Requirements

- **Windows** (recommended, but should work on other OS)
- **Python 3.11**

### 2. Installation Steps

1. **Clone or Download the Project**
   - Download the ZIP or use Git to clone:  
     `git clone <your-repo-url>`
2. **Open a Terminal/Command Prompt**
   - Navigate to the project folder:  
     `cd rag_system`
3. **Create a Virtual Environment (Recommended)**
   - `python -m venv rag_env`
   - Activate it:
     - Windows: `rag_env\Scripts\activate`
     - Mac/Linux: `source rag_env/bin/activate`
4. **Install Dependencies**
   - `pip install -r requirements.txt`
5. **Set Up API Keys**
   - Create a `.env` file.
   - Add your [Groq API key](https://console.groq.com/keys):
     ```
     GROQ_API_KEY=your_groq_api_key_here
     ```
6. **Run the App**
   - `streamlit run demo.py`
   - The app will open in your browser.

---

## Usage Guide

1. **Upload PDFs**: Use the sidebar to upload one or more PDF files.
2. **Loaded Documents**: See a list of uploaded documents.
3. **Ask Questions**: Type your question in the main area and press Enter.
4. **See Answers**: The answer appears, along with details like sources used, confidence, and content type.
5. **Example Questions**: Click on example buttons for inspiration.
6. **System Stats**: View statistics about your document database.
7. **Clear Conversation**: Reset the chat history if needed.

---

## Project Structure

- `demo.py` — Main web app (Streamlit interface)
- `src/` — Core logic:
  - `rag_system.py` — Orchestrates the whole process
  - `pdf_processor.py` — Extracts text, tables, and images from PDFs
  - `llm_handler.py` — Handles AI question answering
  - `retriever.py` — Finds the most relevant document parts
  - `vector_store_windows_safe.py` — Stores and searches document data (Windows-safe)
- `config/` — Configuration files
- `data/pdfs/` — Where your uploaded PDFs are stored
- `models/` — Local AI models (if used)
- `requirements.txt` — List of required Python packages

---

## Troubleshooting & FAQ

- **App won’t start?**
  - Make sure you have Python 3.11 and all dependencies installed.
  - Check that your virtual environment is activated.
- **Groq API errors?**
  - Double-check your API key in `config/.env`.
- **PDF not uploading/processing?**
  - Ensure the file is a valid PDF and not too large.
- **No answer or low confidence?**
  - Try rephrasing your question or uploading more relevant documents.
- **Other issues?**
  - Check the terminal for error messages.
  - Restart the app after fixing any issues.

---

## Contact & Credits

- **Author**: Kiran V Choudhari
- **For Help**: Open an issue on GitHub or contact the author directly.
- **Credits**: Built using [Streamlit](https://streamlit.io/), [ChromaDB](https://www.trychroma.com/), [Groq](https://groq.com/), [PyMuPDF](https://pymupdf.readthedocs.io/), [pdfplumber](https://github.com/jsvine/pdfplumber), [pytesseract](https://github.com/madmaze/pytesseract), and more.

---

Enjoy exploring your documents with AI! 🚀
