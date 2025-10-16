"""
RAG Quality Test Suite for Grade 6 Science Chapters 1 & 2
Tests text retrieval, visual retrieval, metadata filtering, and overall quality
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag.embeddings import EmbeddingManager
from rag.visual_embeddings import VisualEmbeddingManager


# ============================================================================
# TEST QUERIES - Designed to evaluate different aspects of RAG quality
# ============================================================================

TEXT_TEST_QUERIES = {
    "chapter_1": [
        {
            "query": "What is the scientific method?",
            "expected_concepts": ["observation", "hypothesis", "experiment", "conclusion"],
            "chapter": 1,
            "type": "conceptual"
        },
        {
            "query": "How do scientists make observations?",
            "expected_concepts": ["senses", "instruments", "recording", "careful"],
            "chapter": 1,
            "type": "procedural"
        },
        {
            "query": "What are the steps in scientific investigation?",
            "expected_concepts": ["question", "hypothesis", "test", "analyze", "conclude"],
            "chapter": 1,
            "type": "activity"
        }
    ],
    "chapter_2": [
        {
            "query": "What are the different groups of living organisms?",
            "expected_concepts": ["plants", "animals", "fungi", "bacteria", "classification"],
            "chapter": 2,
            "type": "conceptual"
        },
        {
            "query": "How do we classify plants?",
            "expected_concepts": ["flowering", "non-flowering", "seeds", "characteristics"],
            "chapter": 2,
            "type": "procedural"
        },
        {
            "query": "What is biodiversity and why is it important?",
            "expected_concepts": ["variety", "species", "ecosystem", "conservation"],
            "chapter": 2,
            "type": "conceptual"
        }
    ],
    "cross_chapter": [
        {
            "query": "How do scientists study living things?",
            "expected_concepts": ["observation", "classification", "experiment", "diversity"],
            "chapter": None,
            "type": "integration"
        }
    ]
}

VISUAL_TEST_QUERIES = {
    "figures": [
        {
            "query": "diagram of scientific method steps",
            "expected_type": "figure",
            "chapter": 1
        },
        {
            "query": "classification chart of living organisms",
            "expected_type": "figure",
            "chapter": 2
        },
        {
            "query": "plant diversity examples",
            "expected_type": "figure",
            "chapter": 2
        }
    ],
    "tables": [
        {
            "query": "comparison of different plant groups",
            "expected_type": "table",
            "chapter": 2
        }
    ]
}

METADATA_TEST_CASES = [
    {
        "name": "Activity Filtering",
        "filter": {"is_activity": True},
        "min_expected": 2,
        "description": "Retrieve only activity chunks"
    },
    {
        "name": "Chapter 1 Only",
        "filter": {"chapter_number": 1},
        "min_expected": 15,
        "description": "Retrieve only Chapter 1 content"
    },
    {
        "name": "Chapter 2 Only",
        "filter": {"chapter_number": 2},
        "min_expected": 25,
        "description": "Retrieve only Chapter 2 content"
    },
    {
        "name": "High Priority Content",
        "filter": {"content_priority": "high"},
        "min_expected": 5,
        "description": "Retrieve high-priority teaching content"
    }
]


# ============================================================================
# QUALITY METRICS
# ============================================================================

class RAGQualityMetrics:
    """Calculate RAG quality metrics"""

    def __init__(self):
        self.results = {
            "text_retrieval": [],
            "visual_retrieval": [],
            "metadata_filtering": [],
            "overall_stats": {}
        }

    def calculate_relevance_score(self, result_content: str, expected_concepts: List[str]) -> float:
        """Calculate how many expected concepts appear in result"""
        content_lower = result_content.lower()
        matches = sum(1 for concept in expected_concepts if concept.lower() in content_lower)
        return matches / len(expected_concepts) if expected_concepts else 0.0

    def calculate_precision_at_k(self, results: List[Dict], expected_concepts: List[str], k: int = 3) -> float:
        """Precision@K - how many of top K results are relevant"""
        relevant_count = 0
        for result in results[:k]:
            content = result.get('content', '') + ' ' + ' '.join(result.get('key_concepts', []))
            if self.calculate_relevance_score(content, expected_concepts) > 0.3:
                relevant_count += 1
        return relevant_count / min(k, len(results)) if results else 0.0

    def calculate_mrr(self, results: List[Dict], expected_concepts: List[str]) -> float:
        """Mean Reciprocal Rank - position of first relevant result"""
        for i, result in enumerate(results, 1):
            content = result.get('content', '') + ' ' + ' '.join(result.get('key_concepts', []))
            if self.calculate_relevance_score(content, expected_concepts) > 0.3:
                return 1.0 / i
        return 0.0

    def add_text_result(self, query: str, results: List[Dict], expected_concepts: List[str],
                       expected_chapter: int = None, query_type: str = "general"):
        """Add text retrieval result"""
        if not results:
            self.results["text_retrieval"].append({
                "query": query,
                "type": query_type,
                "precision@3": 0.0,
                "precision@5": 0.0,
                "mrr": 0.0,
                "avg_score": 0.0,
                "chapter_accuracy": 0.0,
                "result_count": 0
            })
            return

        # Calculate metrics
        p_at_3 = self.calculate_precision_at_k(results, expected_concepts, k=3)
        p_at_5 = self.calculate_precision_at_k(results, expected_concepts, k=5)
        mrr = self.calculate_mrr(results, expected_concepts)
        avg_score = sum(r.get('score', 0) for r in results[:5]) / min(5, len(results))

        # Chapter accuracy (if expected chapter specified)
        chapter_accuracy = 1.0
        if expected_chapter:
            chapter_matches = sum(1 for r in results[:5] if r.get('chapter_number') == expected_chapter)
            chapter_accuracy = chapter_matches / min(5, len(results))

        self.results["text_retrieval"].append({
            "query": query,
            "type": query_type,
            "precision@3": p_at_3,
            "precision@5": p_at_5,
            "mrr": mrr,
            "avg_score": avg_score,
            "chapter_accuracy": chapter_accuracy,
            "result_count": len(results)
        })

    def add_visual_result(self, query: str, results: List[Dict], expected_type: str,
                         expected_chapter: int = None):
        """Add visual retrieval result"""
        if not results:
            self.results["visual_retrieval"].append({
                "query": query,
                "type_accuracy": 0.0,
                "chapter_accuracy": 0.0,
                "avg_score": 0.0,
                "result_count": 0
            })
            return

        # Type accuracy
        type_matches = sum(1 for r in results[:5] if r.get('type') == expected_type)
        type_accuracy = type_matches / min(5, len(results))

        # Chapter accuracy
        chapter_accuracy = 1.0
        if expected_chapter:
            chapter_matches = sum(1 for r in results[:5] if r.get('chapter_number') == expected_chapter)
            chapter_accuracy = chapter_matches / min(5, len(results))

        avg_score = sum(r.get('score', 0) for r in results[:5]) / min(5, len(results))

        self.results["visual_retrieval"].append({
            "query": query,
            "type_accuracy": type_accuracy,
            "chapter_accuracy": chapter_accuracy,
            "avg_score": avg_score,
            "result_count": len(results)
        })

    def add_metadata_result(self, name: str, result_count: int, expected_min: int):
        """Add metadata filtering result"""
        self.results["metadata_filtering"].append({
            "name": name,
            "result_count": result_count,
            "expected_min": expected_min,
            "passed": result_count >= expected_min
        })

    def calculate_overall_stats(self):
        """Calculate overall statistics"""
        # Text retrieval stats
        text_results = self.results["text_retrieval"]
        if text_results:
            self.results["overall_stats"]["text"] = {
                "avg_precision@3": sum(r["precision@3"] for r in text_results) / len(text_results),
                "avg_precision@5": sum(r["precision@5"] for r in text_results) / len(text_results),
                "avg_mrr": sum(r["mrr"] for r in text_results) / len(text_results),
                "avg_chapter_accuracy": sum(r["chapter_accuracy"] for r in text_results) / len(text_results),
                "total_queries": len(text_results)
            }

        # Visual retrieval stats
        visual_results = self.results["visual_retrieval"]
        if visual_results:
            self.results["overall_stats"]["visual"] = {
                "avg_type_accuracy": sum(r["type_accuracy"] for r in visual_results) / len(visual_results),
                "avg_chapter_accuracy": sum(r["chapter_accuracy"] for r in visual_results) / len(visual_results),
                "avg_score": sum(r["avg_score"] for r in visual_results) / len(visual_results),
                "total_queries": len(visual_results)
            }

        # Metadata filtering stats
        metadata_results = self.results["metadata_filtering"]
        if metadata_results:
            self.results["overall_stats"]["metadata"] = {
                "passed_tests": sum(1 for r in metadata_results if r["passed"]),
                "total_tests": len(metadata_results),
                "pass_rate": sum(1 for r in metadata_results if r["passed"]) / len(metadata_results)
            }


# ============================================================================
# RAG QUALITY TESTER
# ============================================================================

class RAGQualityTester:
    """Test RAG system quality"""

    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv('QDRANT_URL'),
            api_key=os.getenv('QDRANT_API_KEY')
        )
        self.embedding_manager = EmbeddingManager()
        self.visual_manager = VisualEmbeddingManager()
        self.metrics = RAGQualityMetrics()

        self.text_collection = "grade_06_science"
        self.visual_collection = "grade_06_science_visual"

    async def initialize(self):
        """Initialize embedding models"""
        print("\n[INIT] Loading embedding models...")
        await self.embedding_manager.initialize()
        print("  ✓ Text embedding model loaded")

        self.visual_manager.initialize()
        print("  ✓ Visual embedding model loaded")

    async def test_text_retrieval(self):
        """Test text retrieval quality"""
        print("\n" + "="*80)
        print("TEXT RETRIEVAL TESTS")
        print("="*80)

        all_queries = (
            TEXT_TEST_QUERIES["chapter_1"] +
            TEXT_TEST_QUERIES["chapter_2"] +
            TEXT_TEST_QUERIES["cross_chapter"]
        )

        for i, test_case in enumerate(all_queries, 1):
            query = test_case["query"]
            expected_concepts = test_case["expected_concepts"]
            expected_chapter = test_case["chapter"]
            query_type = test_case["type"]

            print(f"\n[{i}/{len(all_queries)}] Query: {query}")
            print(f"  Type: {query_type}")
            if expected_chapter:
                print(f"  Expected Chapter: {expected_chapter}")

            # Generate embedding
            embedding = await self.embedding_manager.get_text_embedding(query)

            # Search
            search_filter = None
            if expected_chapter:
                search_filter = Filter(
                    must=[FieldCondition(key="chapter_number", match=MatchValue(value=expected_chapter))]
                )

            results = self.client.search(
                collection_name=self.text_collection,
                query_vector=embedding,
                query_filter=search_filter,
                limit=5,
                with_payload=True
            )

            # Convert to dict
            results_dict = []
            for result in results:
                results_dict.append({
                    'content': result.payload.get('content', ''),
                    'score': result.score,
                    'chapter_number': result.payload.get('chapter_number'),
                    'key_concepts': result.payload.get('key_concepts', []),
                    'section_type': result.payload.get('section_type', ''),
                    'is_activity': result.payload.get('is_activity', False)
                })

            # Add to metrics
            self.metrics.add_text_result(query, results_dict, expected_concepts, expected_chapter, query_type)

            # Display top result
            if results_dict:
                top = results_dict[0]
                print(f"  ✓ Top result (score: {top['score']:.3f}):")
                print(f"    Chapter: {top['chapter_number']}, Type: {top['section_type']}")
                print(f"    Content preview: {top['content'][:100]}...")
            else:
                print(f"  ✗ No results found")

    async def test_visual_retrieval(self):
        """Test visual content retrieval"""
        print("\n" + "="*80)
        print("VISUAL RETRIEVAL TESTS")
        print("="*80)

        all_queries = VISUAL_TEST_QUERIES["figures"] + VISUAL_TEST_QUERIES["tables"]

        for i, test_case in enumerate(all_queries, 1):
            query = test_case["query"]
            expected_type = test_case["expected_type"]
            expected_chapter = test_case["chapter"]

            print(f"\n[{i}/{len(all_queries)}] Query: {query}")
            print(f"  Expected Type: {expected_type}, Chapter: {expected_chapter}")

            # Generate text embedding for visual search
            query_embedding = self.visual_manager._generate_text_embedding(query)

            # Search
            search_filter = Filter(
                must=[FieldCondition(key="chapter_number", match=MatchValue(value=expected_chapter))]
            )

            results = self.client.search(
                collection_name=self.visual_collection,
                query_vector=query_embedding.tolist(),
                query_filter=search_filter,
                limit=5,
                with_payload=True
            )

            # Convert to dict
            results_dict = []
            for result in results:
                results_dict.append({
                    'type': result.payload.get('type', ''),
                    'score': result.score,
                    'chapter_number': result.payload.get('chapter_number'),
                    'caption': result.payload.get('caption', ''),
                    'visual_id': result.payload.get('visual_id', ''),
                    'page': result.payload.get('page', 0)
                })

            # Add to metrics
            self.metrics.add_visual_result(query, results_dict, expected_type, expected_chapter)

            # Display top result
            if results_dict:
                top = results_dict[0]
                print(f"  ✓ Top result (score: {top['score']:.3f}):")
                print(f"    Type: {top['type']}, ID: {top['visual_id']}, Page: {top['page']}")
                print(f"    Caption: {top['caption'][:100]}...")
            else:
                print(f"  ✗ No results found")

    async def test_metadata_filtering(self):
        """Test metadata-based filtering"""
        print("\n" + "="*80)
        print("METADATA FILTERING TESTS")
        print("="*80)

        for i, test_case in enumerate(METADATA_TEST_CASES, 1):
            name = test_case["name"]
            filter_dict = test_case["filter"]
            min_expected = test_case["min_expected"]
            description = test_case["description"]

            print(f"\n[{i}/{len(METADATA_TEST_CASES)}] Test: {name}")
            print(f"  Description: {description}")
            print(f"  Filter: {filter_dict}")

            # Build Qdrant filter
            must_conditions = []
            for key, value in filter_dict.items():
                must_conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))

            search_filter = Filter(must=must_conditions)

            # Scroll to count results
            points, _ = self.client.scroll(
                collection_name=self.text_collection,
                scroll_filter=search_filter,
                limit=100,
                with_payload=False
            )

            result_count = len(points)
            passed = result_count >= min_expected

            self.metrics.add_metadata_result(name, result_count, min_expected)

            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status}: Found {result_count} results (expected: {min_expected}+)")

    async def test_collection_stats(self):
        """Get collection statistics"""
        print("\n" + "="*80)
        print("COLLECTION STATISTICS")
        print("="*80)

        # Text collection
        text_info = self.client.get_collection(self.text_collection)
        print(f"\n{self.text_collection}:")
        print(f"  Points: {text_info.points_count}")
        print(f"  Vector dim: {text_info.config.params.vectors.size}")

        # Visual collection
        visual_info = self.client.get_collection(self.visual_collection)
        print(f"\n{self.visual_collection}:")
        print(f"  Points: {visual_info.points_count}")
        print(f"  Vector dim: {visual_info.config.params.vectors.size}")

    def print_quality_report(self):
        """Print quality assessment report"""
        self.metrics.calculate_overall_stats()

        print("\n" + "="*80)
        print("QUALITY ASSESSMENT REPORT")
        print("="*80)

        # Text retrieval summary
        if "text" in self.metrics.results["overall_stats"]:
            text_stats = self.metrics.results["overall_stats"]["text"]
            print(f"\n📝 TEXT RETRIEVAL QUALITY")
            print(f"  Total Queries: {text_stats['total_queries']}")
            print(f"  Avg Precision@3: {text_stats['avg_precision@3']:.2%}")
            print(f"  Avg Precision@5: {text_stats['avg_precision@5']:.2%}")
            print(f"  Avg MRR: {text_stats['avg_mrr']:.3f}")
            print(f"  Avg Chapter Accuracy: {text_stats['avg_chapter_accuracy']:.2%}")

            # Quality grade
            avg_precision = text_stats['avg_precision@3']
            if avg_precision >= 0.8:
                grade = "🟢 EXCELLENT"
            elif avg_precision >= 0.6:
                grade = "🟡 GOOD"
            elif avg_precision >= 0.4:
                grade = "🟠 FAIR"
            else:
                grade = "🔴 NEEDS IMPROVEMENT"

            print(f"\n  Overall Grade: {grade}")

        # Visual retrieval summary
        if "visual" in self.metrics.results["overall_stats"]:
            visual_stats = self.metrics.results["overall_stats"]["visual"]
            print(f"\n🖼️ VISUAL RETRIEVAL QUALITY")
            print(f"  Total Queries: {visual_stats['total_queries']}")
            print(f"  Avg Type Accuracy: {visual_stats['avg_type_accuracy']:.2%}")
            print(f"  Avg Chapter Accuracy: {visual_stats['avg_chapter_accuracy']:.2%}")
            print(f"  Avg Score: {visual_stats['avg_score']:.3f}")

            # Quality grade
            type_accuracy = visual_stats['avg_type_accuracy']
            if type_accuracy >= 0.8:
                grade = "🟢 EXCELLENT"
            elif type_accuracy >= 0.6:
                grade = "🟡 GOOD"
            elif type_accuracy >= 0.4:
                grade = "🟠 FAIR"
            else:
                grade = "🔴 NEEDS IMPROVEMENT"

            print(f"\n  Overall Grade: {grade}")

        # Metadata filtering summary
        if "metadata" in self.metrics.results["overall_stats"]:
            metadata_stats = self.metrics.results["overall_stats"]["metadata"]
            print(f"\n🔍 METADATA FILTERING")
            print(f"  Tests Passed: {metadata_stats['passed_tests']}/{metadata_stats['total_tests']}")
            print(f"  Pass Rate: {metadata_stats['pass_rate']:.2%}")

            if metadata_stats['pass_rate'] >= 0.9:
                grade = "🟢 EXCELLENT"
            elif metadata_stats['pass_rate'] >= 0.7:
                grade = "🟡 GOOD"
            else:
                grade = "🔴 NEEDS IMPROVEMENT"

            print(f"\n  Overall Grade: {grade}")

        # Overall assessment
        print("\n" + "="*80)
        print("OVERALL ASSESSMENT")
        print("="*80)

        text_precision = self.metrics.results["overall_stats"].get("text", {}).get("avg_precision@3", 0)
        visual_accuracy = self.metrics.results["overall_stats"].get("visual", {}).get("avg_type_accuracy", 0)
        metadata_pass_rate = self.metrics.results["overall_stats"].get("metadata", {}).get("pass_rate", 0)

        overall_score = (text_precision + visual_accuracy + metadata_pass_rate) / 3

        print(f"\nOverall Score: {overall_score:.2%}")

        if overall_score >= 0.75:
            print("✅ RAG SYSTEM QUALITY: EXCELLENT - Ready for production")
        elif overall_score >= 0.60:
            print("✅ RAG SYSTEM QUALITY: GOOD - Minor improvements recommended")
        elif overall_score >= 0.45:
            print("⚠️ RAG SYSTEM QUALITY: FAIR - Some improvements needed")
        else:
            print("❌ RAG SYSTEM QUALITY: NEEDS IMPROVEMENT - Significant work required")

        # Benchmarks
        print("\n" + "-"*80)
        print("BENCHMARK COMPARISON")
        print("-"*80)
        print("\nExpected Quality Targets:")
        print(f"  Text Precision@3: ≥ 60%  (Current: {text_precision:.1%})")
        print(f"  Visual Type Accuracy: ≥ 70%  (Current: {visual_accuracy:.1%})")
        print(f"  Metadata Pass Rate: ≥ 90%  (Current: {metadata_pass_rate:.1%})")
        print(f"  Overall Score: ≥ 65%  (Current: {overall_score:.1%})")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def main():
    """Run all quality tests"""
    print("\n" + "="*80)
    print("RAG QUALITY TEST SUITE - Grade 6 Science Chapters 1 & 2")
    print("="*80)

    tester = RAGQualityTester()

    # Initialize
    await tester.initialize()

    # Run tests
    await tester.test_collection_stats()
    await tester.test_text_retrieval()
    await tester.test_visual_retrieval()
    await tester.test_metadata_filtering()

    # Print report
    tester.print_quality_report()

    print("\n" + "="*80)
    print("TEST SUITE COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
