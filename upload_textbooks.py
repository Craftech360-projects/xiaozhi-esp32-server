#!/usr/bin/env python3
"""
Script to upload Class-6-mathematics PDFs to the RAG system
Tests the complete pipeline: PDF upload -> Processing -> Qdrant vector database
"""

import os
import requests
import json
import time
import glob
from pathlib import Path

# Server configuration
BASE_URL = "http://localhost:8002"
API_BASE = f"{BASE_URL}/toy"

def wait_for_server():
    """Wait for the server to be ready"""
    print("Waiting for server to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{BASE_URL}/actuator/health", timeout=5)
            if response.status_code == 200:
                print("+ Server is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"  Waiting... ({i+1}/30)")
        time.sleep(1)
    
    print("✗ Server did not become ready in time")
    return False

def upload_textbook(pdf_path, subject="mathematics", standard=6):
    """Upload a single PDF textbook"""
    filename = os.path.basename(pdf_path)
    print(f"\n📚 Uploading: {filename}")
    
    # Extract chapter info from filename
    chapter_number = 1
    chapter_title = "Unknown Chapter"
    if "Chapter" in filename:
        try:
            parts = filename.replace(".pdf", "").split()
            if len(parts) >= 2:
                chapter_number = int(parts[1])
                chapter_title = " ".join(parts[2:]) if len(parts) > 2 else f"Chapter {chapter_number}"
        except:
            pass
    
    try:
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            files = {
                'file': (filename, f, 'application/pdf')
            }
            data = {
                'subject': subject,
                'standard': standard,
                'chapterNumber': chapter_number,
                'chapterTitle': chapter_title,
                'language': 'English'
            }
            
            # Upload to RAG system
            response = requests.post(
                f"{API_BASE}/api/rag/textbook/upload",
                files=files,
                data=data,
                timeout=30  # 30 second timeout for upload initiation
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0:  # Success
                print(f"  ✓ Upload initiated successfully")
                textbook_id = result.get('data', {}).get('textbook_id')
                print(f"  📋 Textbook ID: {textbook_id}")
                print(f"  ⏳ Processing in background...")
                
                # Check processing status
                if textbook_id:
                    time.sleep(2)  # Brief wait
                    status_response = requests.get(f"{API_BASE}/api/rag/textbook/{textbook_id}/status")
                    if status_response.status_code == 200:
                        status_data = status_response.json().get('data', {})
                        print(f"  📊 Status: {status_data.get('processedStatus', 'unknown')}")
                        print(f"  📈 Progress: {status_data.get('progressPercentage', 0)}%")
                        
                return True
            else:
                print(f"  ✗ Upload failed: {result.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"  ✗ Upload failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  ✗ Upload timed out (file may be too large)")
        return False
    except Exception as e:
        print(f"  ✗ Upload error: {e}")
        return False

def test_rag_search(query, subject="Mathematics", standard=6):
    """Test RAG search functionality"""
    print(f"\n🔍 Testing RAG search: '{query}'")
    
    try:
        data = {
            'query': query,
            'subject': subject,
            'standard': standard,
            'limit': 5
        }
        
        response = requests.post(
            f"{API_BASE}/rag/search",
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"  ✓ Search successful")
            print(f"  📝 Found {len(results.get('results', []))} relevant chunks")
            
            # Display top results
            for i, result in enumerate(results.get('results', [])[:3]):
                score = result.get('score', 'N/A')
                content = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                print(f"    {i+1}. Score: {score} - {content}")
            
            return True
        else:
            print(f"  ✗ Search failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ Search error: {e}")
        return False

def check_qdrant_status():
    """Check Qdrant vector database status"""
    print(f"\n📊 Checking Qdrant status...")
    
    try:
        response = requests.get(f"{API_BASE}/rag/status", timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print(f"  ✓ Qdrant connection: {status.get('qdrant_status', 'Unknown')}")
            print(f"  📚 Total collections: {status.get('collections_count', 'N/A')}")
            print(f"  🔢 Total vectors: {status.get('total_vectors', 'N/A')}")
            return True
        else:
            print(f"  ✗ Status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  ✗ Status check error: {e}")
        return False

def main():
    print("Starting Class-6-mathematics textbook upload and RAG testing")
    print("=" * 60)
    
    # Wait for server to be ready
    if not wait_for_server():
        return
    
    # Check Qdrant status first
    check_qdrant_status()
    
    # Find all PDF files in the Class-6-mathematics directory
    pdf_dir = r"D:\cheekofinal\xiaozhi-esp32-server\main\Class-6-mathematics"
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"✗ No PDF files found in {pdf_dir}")
        return
    
    print(f"\n📁 Found {len(pdf_files)} PDF files to upload:")
    for pdf in pdf_files:
        print(f"  • {os.path.basename(pdf)}")
    
    # Upload each PDF
    successful_uploads = 0
    failed_uploads = 0
    
    for pdf_path in sorted(pdf_files):
        if upload_textbook(pdf_path):
            successful_uploads += 1
        else:
            failed_uploads += 1
        
        # Small delay between uploads
        time.sleep(2)
    
    # Summary
    print(f"\n📈 Upload Summary:")
    print(f"  ✅ Successful: {successful_uploads}")
    print(f"  ❌ Failed: {failed_uploads}")
    
    # Test RAG functionality if uploads were successful
    if successful_uploads > 0:
        print(f"\n🧪 Testing RAG Search Functionality:")
        
        # Test queries for Class 6 Mathematics
        test_queries = [
            "What is the area of a rectangle?",
            "How do you add fractions?", 
            "What are prime numbers?",
            "Explain multiplication of decimals",
            "What is the perimeter of a triangle?"
        ]
        
        for query in test_queries:
            test_rag_search(query)
            time.sleep(1)
        
        # Final Qdrant status check
        print(f"\n🏁 Final Status Check:")
        check_qdrant_status()
    
    print(f"\n✅ RAG system testing completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()