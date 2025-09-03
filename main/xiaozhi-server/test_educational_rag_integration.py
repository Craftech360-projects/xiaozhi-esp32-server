"""
Test script for Enhanced Educational RAG Integration
Tests the manager agent and subject expert agents
"""

import asyncio
import sys
import os

# Add the xiaozhi-server path to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.logger import setup_logging
from core.providers.memory.educational_rag.educational_rag import MemoryProvider
from core.providers.memory.educational_rag.config import EDUCATIONAL_RAG_CONFIG

logger = setup_logging()

async def test_educational_rag_system():
    """Test the enhanced educational RAG system"""
    print("🧪 Testing Enhanced Educational RAG System")
    print("=" * 50)
    
    try:
        # Initialize the memory provider
        print("1. Initializing Educational RAG Memory Provider...")
        memory_provider = MemoryProvider(EDUCATIONAL_RAG_CONFIG)
        
        # Health check
        print("\n2. Performing system health check...")
        health = await memory_provider.health_check()
        print(f"Health Status: {health}")
        
        # Test mathematics questions
        print("\n3. Testing Mathematics Expert Agent...")
        math_questions = [
            "What are fractions?",
            "How do I add 5 + 3?", 
            "Explain what is a triangle",
            "What is the area of a rectangle?"
        ]
        
        for question in math_questions:
            print(f"\nQ: {question}")
            try:
                response = await memory_provider.query_memory(question)
                print(f"A: {response[:100]}...")
            except Exception as e:
                print(f"Error: {e}")
        
        # Test science questions
        print("\n4. Testing Science Expert Agent...")
        science_questions = [
            "How do plants grow?",
            "What are nutrients?",
            "Why do we need food?",
            "How do animals breathe?"
        ]
        
        for question in science_questions:
            print(f"\nQ: {question}")
            try:
                response = await memory_provider.query_memory(question)
                print(f"A: {response[:100]}...")
            except Exception as e:
                print(f"Error: {e}")
        
        # Test manager routing
        print("\n5. Testing Manager Agent Routing...")
        mixed_questions = [
            "Tell me about shapes",  # Should route to math
            "What do animals eat?",  # Should route to science
            "How to solve 10 - 4?", # Should route to math
            "Why do plants need water?" # Should route to science
        ]
        
        for question in mixed_questions:
            print(f"\nQ: {question}")
            try:
                subject, routing_info = await memory_provider.manager_agent.route_query(question)
                print(f"Routed to: {subject} (confidence: {routing_info.get('confidence', 'N/A')})")
                
                response = await memory_provider.query_memory(question)
                print(f"A: {response[:100]}...")
            except Exception as e:
                print(f"Error: {e}")
        
        print("\n6. Testing Available Subjects...")
        subjects = await memory_provider.get_available_subjects()
        print(f"Available subjects: {subjects}")
        
        print("\n✅ Educational RAG System Test Complete!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def test_configuration():
    """Test configuration loading"""
    print("\n🔧 Testing Configuration...")
    print(f"Config loaded: {bool(EDUCATIONAL_RAG_CONFIG)}")
    print(f"Qdrant URL configured: {'qdrant_url' in EDUCATIONAL_RAG_CONFIG}")
    print(f"Subjects configured: {list(EDUCATIONAL_RAG_CONFIG.get('subjects', {}).keys())}")

if __name__ == "__main__":
    # Test configuration first
    test_configuration()
    
    # Run async tests
    asyncio.run(test_educational_rag_system())