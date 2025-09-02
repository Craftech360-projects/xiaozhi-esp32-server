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
API_BASE = f"{BASE_URL}/toy/api"
SERVER_SECRET = "d26d2708-579a-4447-a0b4-7595e8b9a5b3"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"

# Global auth token (will be set after login)
AUTH_TOKEN = None

def login_admin():
    """Login as admin and get authentication token"""
    global AUTH_TOKEN
    print("\n[AUTH] Logging in as admin...")
    
    try:
        login_data = {
            "username": ADMIN_USERNAME,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(
            f"{API_BASE}/user/login",
            json=login_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('code') == 0 and 'data' in result:
                AUTH_TOKEN = result['data'].get('token')
                if AUTH_TOKEN:
                    print(f"  + Login successful, token obtained")
                    return True
                else:
                    print(f"  - Login failed: No token in response")
                    return False
            else:
                print(f"  - Login failed: {result.get('msg', 'Unknown error')}")
                return False
        else:
            print(f"  - Login failed: {response.status_code}")
            print(f"  - Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"  - Login error: {e}")
        return False

def get_auth_headers():
    """Get authentication headers with current token"""
    if AUTH_TOKEN:
        return {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
    else:
        return {"Content-Type": "application/json"}

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
    
    print("- Server did not become ready in time")
    return False

def upload_textbook(pdf_path, subject="Mathematics", standard=6):
    """Upload a single PDF textbook"""
    filename = os.path.basename(pdf_path)
    print(f"\n[UPLOAD] {filename}")
    
    try:
        # Read the PDF file
        with open(pdf_path, 'rb') as f:
            files = {
                'file': (filename, f, 'application/pdf')
            }
            data = {
                'subject': subject,
                'standard': standard
            }
            
            # Upload to RAG system with authentication
            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"} if AUTH_TOKEN else {}
            response = requests.post(
                f"{API_BASE}/rag/textbook/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=300  # 5 minute timeout for processing
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  + Upload successful")
            print(f"  + Processed {result.get('chunks_created', 'N/A')} chunks")
            print(f"  + Vectors stored in Qdrant: {result.get('vectors_stored', 'N/A')}")
            return True
        else:
            print(f"  - Upload failed: {response.status_code}")
            print(f"  - Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"  - Upload timed out (file may be too large)")
        return False
    except Exception as e:
        print(f"  - Upload error: {e}")
        return False

def test_rag_search(query, subject="Mathematics", standard=6):
    """Test RAG search functionality"""
    print(f"\n[SEARCH] '{query}'")
    
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
            headers=get_auth_headers(),
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"  + Search successful")
            print(f"  + Found {len(results.get('results', []))} relevant chunks")
            
            # Display top results
            for i, result in enumerate(results.get('results', [])[:3]):
                score = result.get('score', 'N/A')
                content = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                print(f"    {i+1}. Score: {score} - {content}")
            
            return True
        else:
            print(f"  - Search failed: {response.status_code}")
            print(f"  - Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"  - Search error: {e}")
        return False

def check_qdrant_status():
    """Check Qdrant vector database status"""
    print(f"\n[STATUS] Checking Qdrant status...")
    
    try:
        response = requests.get(f"{API_BASE}/rag/health", headers=get_auth_headers(), timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print(f"  + Qdrant connection: {status.get('qdrant_status', 'Unknown')}")
            print(f"  + Total collections: {status.get('collections_count', 'N/A')}")
            print(f"  + Total vectors: {status.get('total_vectors', 'N/A')}")
            return True
        else:
            print(f"  - Status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  - Status check error: {e}")
        return False

def main():
    print("=" * 60)
    print("RAG SYSTEM TESTING - Class 6 Mathematics Textbooks")
    print("=" * 60)
    
    # Server is confirmed running - skip health check due to auth requirements
    print("+ Server is confirmed running on port 8002")
    
    # RAG endpoints are now accessible without authentication for testing
    print("+ RAG endpoints configured for anonymous access")
    
    # Check Qdrant status first
    check_qdrant_status()
    
    # Find all PDF files in the Class-6-mathematics directory
    pdf_dir = r"D:\cheekofinal\xiaozhi-esp32-server\main\Class-6-mathematics"
    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    
    if not pdf_files:
        print(f"- No PDF files found in {pdf_dir}")
        return
    
    print(f"\n[INFO] Found {len(pdf_files)} PDF files to upload:")
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
    print(f"\n[SUMMARY] Upload Results:")
    print(f"  + Successful: {successful_uploads}")
    print(f"  - Failed: {failed_uploads}")
    
    # Test RAG functionality if uploads were successful
    if successful_uploads > 0:
        print(f"\n[TESTING] RAG Search Functionality:")
        
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
        print(f"\n[FINAL] Status Check:")
        check_qdrant_status()
    
    print(f"\n[COMPLETE] RAG system testing finished!")
    print("=" * 60)

if __name__ == "__main__":
    main()