#!/bin/bash

# Script to index NCERT Class 12 Physics textbooks

echo "=== Indexing NCERT Class 12 Physics Textbooks ==="
echo ""

# Change to the xiaozhi-server directory
cd /mnt/d/cheekofinal/xiaozhi-esp32-server/main/xiaozhi-server/

# First, let's install the required dependencies if not already installed
echo "Checking and installing dependencies..."
pip install chromadb sentence-transformers PyPDF2

echo ""
echo "Starting textbook indexing..."
echo ""

# Index Physics Part 1
echo "1. Indexing NCERT Class 12 Physics Part 1..."
python scripts/index_textbook.py ./textbooks/NCERT-Class-12-Physics-Part-1.pdf "Physics" "Class-12"

echo ""
echo "2. Indexing NCERT Class 12 Physics Part 2..."
python scripts/index_textbook.py ./textbooks/NCERT-Class-12-Physics-Part-2.pdf "Physics" "Class-12"

echo ""
echo "=== Indexing Complete! ==="
echo ""
echo "You can now ask questions about Class 12 Physics topics such as:"
echo "- What is electromagnetic induction?"
echo "- Explain the photoelectric effect"
echo "- What are Maxwell's equations?"
echo "- Describe the wave-particle duality"
echo ""
echo "The system will search through both textbooks to find relevant answers."