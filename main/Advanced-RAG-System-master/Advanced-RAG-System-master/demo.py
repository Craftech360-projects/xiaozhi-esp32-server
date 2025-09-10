# demo.py - FIXED VERSION
import streamlit as st
import os
from pathlib import Path
from config.config import Config
from src.rag_system import RAGSystem

# Page configuration
st.set_page_config(
    page_title="RAG System Demo",
    page_icon="📚",
    layout="wide"
)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = RAGSystem(Config())
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []
if 'documents' not in st.session_state:
    st.session_state.documents = []


def main():
    st.title("🚀 Advanced RAG System Demo")
    st.markdown("Upload PDF documents and ask questions about their content!")

    # Sidebar for document management
    with st.sidebar:
        st.header("📄 Document Management")

        # File upload
        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=['pdf'],
            accept_multiple_files=True
        )

        if uploaded_files:
            for uploaded_file in uploaded_files:
                if uploaded_file.name not in st.session_state.documents:
                    # Save uploaded file
                    pdf_path = f"./data/pdfs/{uploaded_file.name}"
                    os.makedirs("./data/pdfs", exist_ok=True)

                    with open(pdf_path, "wb") as f:
                        f.write(uploaded_file.read())

                    # Process document
                    with st.spinner(f"Processing {uploaded_file.name}..."):
                        result = st.session_state.rag_system.add_document(
                            pdf_path)

                    if result['success']:
                        st.session_state.documents.append(uploaded_file.name)
                        st.success(f"✅ Added {uploaded_file.name}")

                        # Show statistics
                        stats = result['statistics']
                        st.write(f"**Statistics:**")
                        st.write(
                            f"- Text chunks: {stats.get('text_chunks', 0)}")
                        st.write(
                            f"- Table chunks: {stats.get('table_chunks', 0)}")
                        st.write(
                            f"- Image chunks: {stats.get('image_chunks', 0)}")
                    else:
                        st.error(f"❌ Error: {result['message']}")

        # Show loaded documents
        if st.session_state.documents:
            st.subheader("📚 Loaded Documents")
            for doc in st.session_state.documents:
                st.write(f"• {doc}")

        # System statistics
        if st.button("📊 Show System Stats"):
            stats = st.session_state.rag_system.get_system_stats()
            st.json(stats)

        # Clear conversation
        if st.button("🗑️ Clear Conversation"):
            st.session_state.conversation_history = []
            st.session_state.rag_system.clear_conversation_history()
            st.success("Conversation cleared!")

    # Main chat interface
    st.header("💬 Ask Questions")

    # Display conversation history
    if st.session_state.conversation_history:
        st.subheader("Conversation History")
        for i, message in enumerate(st.session_state.conversation_history):
            if i % 2 == 0:  # User message
                st.write(f"🧑 **You:** {message}")
            else:  # Assistant message
                st.write(f"🤖 **Assistant:** {message}")
        st.divider()

    # Query input - USE CALLBACK METHOD (FIXED)
    def process_query():
        """Process the query when submitted"""
        query = st.session_state.query_input
        if query and st.session_state.documents:
            with st.spinner("🔍 Searching and generating response..."):
                response = st.session_state.rag_system.query(
                    query,
                    st.session_state.conversation_history
                )

            # Update conversation history
            st.session_state.conversation_history.append(query)
            st.session_state.conversation_history.append(response['answer'])

            # Store response for display
            st.session_state.last_response = response
        elif query and not st.session_state.documents:
            st.session_state.last_response = {
                'answer': "⚠️ Please upload at least one PDF document first!",
                'sources_used': 0,
                'query_type': 'error',
                'confidence': 0.0
            }

    # Query input with callback (FIXED APPROACH)
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., What are the main topics discussed in the document?",
        key="query_input",
        on_change=process_query  # Process when user submits
    )

    # Example questions
    st.subheader("💡 Example Questions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Show me any tables"):
            st.session_state.example_query = "Show me any tables or data from the documents"

    with col2:
        if st.button("🖼️ What images are there?"):
            st.session_state.example_query = "What images or visual content is in the documents?"

    with col3:
        if st.button("📖 Summarize content"):
            st.session_state.example_query = "Can you provide a summary of the main content?"

    # Process example queries
    if 'example_query' in st.session_state:
        example_query = st.session_state.example_query
        del st.session_state.example_query  # Remove after use

        if st.session_state.documents:
            with st.spinner("🔍 Searching and generating response..."):
                response = st.session_state.rag_system.query(
                    example_query,
                    st.session_state.conversation_history
                )

            # Update conversation history
            st.session_state.conversation_history.append(example_query)
            st.session_state.conversation_history.append(response['answer'])

            # Store response for display
            st.session_state.last_response = response
        else:
            st.session_state.last_response = {
                'answer': "⚠️ Please upload at least one PDF document first!",
                'sources_used': 0,
                'query_type': 'error',
                'confidence': 0.0
            }

    # Display last response
    if 'last_response' in st.session_state:
        response = st.session_state.last_response

        st.subheader("Response")
        st.write(response['answer'])

        # Show metadata
        with st.expander("📋 Response Details"):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Sources Used", response['sources_used'])

            with col2:
                st.metric("Confidence", f"{response['confidence']:.2f}")

            with col3:
                st.write(f"**Query Type:** {response['query_type']}")

            if 'context_types' in response:
                st.write(
                    f"**Content Types:** {', '.join(response['context_types'])}")

            if 'retrieval_stats' in response:
                st.write(f"**Retrieval Stats:** {response['retrieval_stats']}")


if __name__ == "__main__":
    main()
