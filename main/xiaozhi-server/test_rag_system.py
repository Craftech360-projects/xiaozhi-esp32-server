#!/usr/bin/env python3
"""
Test script for RAG system integration with Standard 6 Mathematics queries
Tests the complete pipeline: xiaozhi-server -> manager-api -> RAG system

Usage: python test_rag_system.py
"""

import asyncio
import sys
import os
import yaml
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from core.providers.memory.rag_math.rag_math import MemoryProvider
from config.logger import setup_logging

logger = setup_logging()

# Test queries for Standard 6 Mathematics
STANDARD_6_MATH_QUERIES = [
    # Basic arithmetic
    "What is 25 + 37?",
    "How do you subtract 45 from 82?",
    "Explain multiplication tables for 7",
    
    # Fractions
    "What is a fraction? Give me examples",
    "How do you add fractions with different denominators?",
    "Convert 3/4 to decimal",
    
    # Geometry
    "What is the area of a rectangle?",
    "How many sides does a triangle have?",
    "Explain what is perimeter",
    
    # Word problems
    "A garden is 12 meters long and 8 meters wide. What is its area?",
    "If I have 24 apples and want to share them equally among 6 friends, how many does each get?",
    
    # Decimals
    "What is 2.5 + 3.7?",
    "Convert 0.75 to fraction",
    
    # Patterns and data
    "What comes next in the pattern: 2, 4, 6, 8, ?",
    "How do you read a bar graph?",
    
    # Mixed queries (educational vs non-educational)
    "Hello, how are you?",  # Non-educational
    "What's the weather like?",  # Non-educational
    "Tell me a story",  # Non-educational
]

class RAGSystemTester:
    def __init__(self):
        self.config = self.load_config()
        self.memory_provider = None
        self.test_results = []
    
    def load_config(self):
        """Load configuration from .config.yaml"""
        config_path = project_root / "data" / ".config.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    async def setup_memory_provider(self):
        """Initialize the RAG memory provider"""
        try:
            memory_config = self.config.get("Memory", {}).get("rag_math", {})
            
            # Add manager-api config
            if "manager-api" in self.config:
                memory_config["manager-api"] = self.config["manager-api"]
            
            self.memory_provider = MemoryProvider(memory_config)
            logger.info("RAG Memory Provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up memory provider: {e}")
            raise
    
    async def test_query(self, query: str) -> dict:
        """Test a single query through the RAG system"""
        logger.info(f"Testing query: {query}")
        
        result = {
            "query": query,
            "timestamp": asyncio.get_event_loop().time(),
            "success": False,
            "response": "",
            "error": None,
            "metadata": {}
        }
        
        try:
            # Test the query memory function
            response = await self.memory_provider.query_memory(query)
            
            result["success"] = True
            result["response"] = response
            result["response_length"] = len(response) if response else 0
            result["has_educational_content"] = bool(response and len(response) > 50)
            
            # Log the result
            if response:
                logger.info(f"✅ Query successful - Response length: {len(response)} chars")
                if len(response) > 200:
                    logger.debug(f"Response preview: {response[:200]}...")
                else:
                    logger.debug(f"Full response: {response}")
            else:
                logger.info("ℹ️  Query returned empty response (likely non-educational)")
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Query failed: {e}")
        
        return result
    
    async def run_all_tests(self):
        """Run all test queries"""
        logger.info("=== Starting RAG System Tests ===")
        
        await self.setup_memory_provider()
        
        for i, query in enumerate(STANDARD_6_MATH_QUERIES, 1):
            logger.info(f"\n--- Test {i}/{len(STANDARD_6_MATH_QUERIES)} ---")
            
            result = await self.test_query(query)
            self.test_results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate and display test results report"""
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        educational_responses = sum(1 for r in self.test_results if r.get("has_educational_content", False))
        
        logger.info("\n" + "="*60)
        logger.info("📊 RAG SYSTEM TEST RESULTS")
        logger.info("="*60)
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful Queries: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
        logger.info(f"Educational Responses: {educational_responses} ({educational_responses/total_tests*100:.1f}%)")
        
        # Categorize results
        math_queries = []
        non_educational_queries = []
        failed_queries = []
        
        for result in self.test_results:
            if not result["success"]:
                failed_queries.append(result)
            elif result.get("has_educational_content", False):
                math_queries.append(result)
            else:
                non_educational_queries.append(result)
        
        logger.info(f"\n📚 Educational Math Queries: {len(math_queries)}")
        for result in math_queries[:5]:  # Show first 5
            logger.info(f"  ✅ {result['query'][:50]}... -> {result['response_length']} chars")
        
        logger.info(f"\n🚫 Non-Educational Queries: {len(non_educational_queries)}")
        for result in non_educational_queries:
            logger.info(f"  ℹ️  {result['query'][:50]}... -> Empty (Expected)")
        
        if failed_queries:
            logger.error(f"\n❌ Failed Queries: {len(failed_queries)}")
            for result in failed_queries:
                logger.error(f"  ❌ {result['query'][:50]}... -> {result['error']}")
        
        # Save detailed results to file
        self.save_test_results()
        
        logger.info(f"\n🎯 RAG System Status: {'✅ OPERATIONAL' if successful_tests > total_tests * 0.8 else '⚠️  NEEDS ATTENTION'}")
        logger.info("="*60)
    
    def save_test_results(self):
        """Save test results to JSON file"""
        try:
            results_file = project_root / "rag_test_results.json"
            
            report = {
                "test_timestamp": asyncio.get_event_loop().time(),
                "total_tests": len(self.test_results),
                "successful_tests": sum(1 for r in self.test_results if r["success"]),
                "educational_responses": sum(1 for r in self.test_results if r.get("has_educational_content", False)),
                "test_results": self.test_results,
                "config_used": {
                    "memory_type": "rag_math",
                    "manager_api_url": self.config.get("manager-api", {}).get("base_url", ""),
                    "redis_enabled": self.config.get("Memory", {}).get("rag_math", {}).get("redis", {}).get("enabled", False)
                }
            }
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📄 Detailed results saved to: {results_file}")
            
        except Exception as e:
            logger.error(f"Error saving test results: {e}")

async def main():
    """Main test execution"""
    print("🚀 Starting RAG System Integration Tests...")
    print("This will test the complete xiaozhi-server -> manager-api -> RAG pipeline\n")
    
    tester = RAGSystemTester()
    await tester.run_all_tests()
    
    print("\n✅ RAG testing complete!")
    print("Check rag_test_results.json for detailed results.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)