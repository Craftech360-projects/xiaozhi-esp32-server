"""
Educational Agent Test Suite for Grade 6 Science
Tests agent's ability to answer questions appropriate for 11-12 year old students
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set proper Python path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(src_dir))
os.chdir(current_dir)

# Now import - this will work with relative imports
from src.services.education_service import EducationService

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# TEST QUESTIONS - Designed for 6th grade students (ages 11-12)
# ============================================================================

CHAPTER_1_QUESTIONS = [
    {
        "question": "What is the scientific method?",
        "type": "definition",
        "expected_concepts": ["observation", "hypothesis", "experiment", "conclusion"],
        "difficulty": "basic",
        "age_appropriate": True
    },
    {
        "question": "How do scientists make observations?",
        "type": "procedural",
        "expected_concepts": ["senses", "tools", "recording", "careful"],
        "difficulty": "basic",
        "age_appropriate": True
    },
    {
        "question": "Why is curiosity important in science?",
        "type": "conceptual",
        "expected_concepts": ["questions", "discovery", "learning", "wonder"],
        "difficulty": "medium",
        "age_appropriate": True
    },
    {
        "question": "Give me an example of a scientific question",
        "type": "application",
        "expected_concepts": ["testable", "measurable", "observation"],
        "difficulty": "medium",
        "age_appropriate": True
    }
]

CHAPTER_2_QUESTIONS = [
    {
        "question": "What is biodiversity?",
        "type": "definition",
        "expected_concepts": ["variety", "species", "living things", "diversity"],
        "difficulty": "basic",
        "age_appropriate": True
    },
    {
        "question": "How do we classify plants?",
        "type": "procedural",
        "expected_concepts": ["characteristics", "groups", "flowering", "non-flowering"],
        "difficulty": "medium",
        "age_appropriate": True
    },
    {
        "question": "What are the different types of animals?",
        "type": "conceptual",
        "expected_concepts": ["mammals", "birds", "insects", "classification"],
        "difficulty": "basic",
        "age_appropriate": True
    },
    {
        "question": "Why do we need to protect biodiversity?",
        "type": "conceptual",
        "expected_concepts": ["ecosystem", "environment", "balance", "conservation"],
        "difficulty": "medium",
        "age_appropriate": True
    },
    {
        "question": "Can you give examples of different types of plants?",
        "type": "application",
        "expected_concepts": ["herbs", "shrubs", "trees", "examples"],
        "difficulty": "basic",
        "age_appropriate": True
    }
]

CROSS_CHAPTER_QUESTIONS = [
    {
        "question": "How do scientists study living things?",
        "type": "integration",
        "expected_concepts": ["observation", "scientific method", "classification", "experiment"],
        "difficulty": "medium",
        "age_appropriate": True
    },
    {
        "question": "What tools do scientists use to observe plants and animals?",
        "type": "integration",
        "expected_concepts": ["microscope", "magnifying glass", "observation", "tools"],
        "difficulty": "medium",
        "age_appropriate": True
    }
]

# Simple conversational questions
CONVERSATIONAL_QUESTIONS = [
    {
        "question": "Tell me about chapter 1",
        "type": "conversational",
        "expected_concepts": ["science", "scientific method", "curiosity"],
        "difficulty": "basic",
        "age_appropriate": True
    },
    {
        "question": "What did I learn in chapter 2?",
        "type": "conversational",
        "expected_concepts": ["biodiversity", "plants", "animals", "diversity"],
        "difficulty": "basic",
        "age_appropriate": True
    }
]


# ============================================================================
# MOCK RUN CONTEXT
# ============================================================================

class MockRunContext:
    """Mock RunContext for testing function tools"""
    def __init__(self):
        self.room = None
        self.agent = None


# ============================================================================
# AGE-APPROPRIATENESS CHECKER
# ============================================================================

class AgeAppropriatenessChecker:
    """Check if agent responses are appropriate for 6th grade students (11-12 years)"""

    # Indicators of age-appropriate content
    AGE_APPROPRIATE_INDICATORS = [
        "simple", "clear", "example", "like", "imagine", "think about",
        "you know", "remember", "let's", "try", "see", "look"
    ]

    # Indicators of content that might be too complex
    TOO_COMPLEX_INDICATORS = [
        "sophisticated", "intricate", "comprehend", "utilize", "facilitate",
        "implement", "paradigm", "methodology", "conceptualize"
    ]

    # Good phrases for 6th graders
    GOOD_PHRASES = [
        "let me explain", "for example", "think of it like", "imagine",
        "you might have seen", "remember when", "it's like", "just like"
    ]

    @staticmethod
    def check_response(response: str) -> Dict:
        """Check if response is age-appropriate for 6th grade"""
        response_lower = response.lower()

        # Count indicators
        appropriate_count = sum(1 for indicator in AgeAppropriatenessChecker.AGE_APPROPRIATE_INDICATORS
                               if indicator in response_lower)
        complex_count = sum(1 for indicator in AgeAppropriatenessChecker.TOO_COMPLEX_INDICATORS
                           if indicator in response_lower)
        good_phrases_count = sum(1 for phrase in AgeAppropriatenessChecker.GOOD_PHRASES
                                if phrase in response_lower)

        # Check sentence length (6th graders prefer shorter sentences)
        sentences = response.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        # Check for examples (good for 6th graders)
        has_examples = "example" in response_lower or "for instance" in response_lower

        # Age appropriateness score
        score = 0
        feedback = []

        # Positive factors
        if appropriate_count >= 2:
            score += 2
            feedback.append(f"✓ Uses {appropriate_count} age-appropriate words")
        if good_phrases_count >= 1:
            score += 2
            feedback.append(f"✓ Uses {good_phrases_count} student-friendly phrases")
        if has_examples:
            score += 2
            feedback.append("✓ Includes examples")
        if avg_sentence_length < 20:
            score += 2
            feedback.append(f"✓ Good sentence length (avg: {avg_sentence_length:.1f} words)")

        # Negative factors
        if complex_count > 2:
            score -= 2
            feedback.append(f"✗ Uses {complex_count} complex words")
        if avg_sentence_length > 30:
            score -= 1
            feedback.append(f"✗ Sentences too long (avg: {avg_sentence_length:.1f} words)")

        # Length check (shouldn't be too long for voice)
        word_count = len(response.split())
        if word_count > 150:
            score -= 1
            feedback.append(f"⚠ Response quite long ({word_count} words) for voice interaction")
        elif word_count < 20:
            feedback.append(f"⚠ Response very brief ({word_count} words)")

        is_appropriate = score >= 4
        grade = "🟢 EXCELLENT" if score >= 6 else "🟡 GOOD" if score >= 4 else "🟠 FAIR" if score >= 2 else "🔴 NEEDS WORK"

        return {
            "score": score,
            "is_appropriate": is_appropriate,
            "grade": grade,
            "feedback": feedback,
            "stats": {
                "appropriate_indicators": appropriate_count,
                "complex_indicators": complex_count,
                "good_phrases": good_phrases_count,
                "avg_sentence_length": avg_sentence_length,
                "word_count": word_count,
                "has_examples": has_examples
            }
        }


# ============================================================================
# AGENT TESTER
# ============================================================================

class EducationalAgentTester:
    """Test educational agent with 6th grade questions"""

    def __init__(self):
        self.service = None
        self.context = MockRunContext()
        self.results = {
            "chapter_1": [],
            "chapter_2": [],
            "cross_chapter": [],
            "conversational": [],
            "overall_stats": {}
        }

    async def initialize(self):
        """Initialize the education service"""
        print("\n[INIT] Initializing Education Service...")
        self.service = EducationService()
        success = await self.service.initialize()

        if success:
            # Set to Grade 6 Science
            await self.service.set_student_context(6, "science")
            print("  ✓ Service initialized successfully")
            print(f"  ✓ Pre-configured for Grade 6 Science")
            return True
        else:
            print("  ✗ Failed to initialize service")
            return False

    async def test_question(self, question_data: Dict) -> Dict:
        """Test a single question"""
        question = question_data["question"]
        print(f"\n[Q] {question}")
        print(f"  Type: {question_data['type']}, Difficulty: {question_data['difficulty']}")

        try:
            # Call the education service directly
            result = await self.service.answer_question(
                question=question,
                grade=6,
                subject="science",
                include_examples=True,
                include_visual_aids=True
            )

            # Extract answer
            response = result.get("answer", "")

            # Check if we got a meaningful response
            if not response or len(response.strip()) < 20:
                print(f"  ✗ Response too short or empty")
                return {
                    "question": question,
                    "response": response,
                    "success": False,
                    "error": "Empty or too short response"
                }

            # Check age appropriateness
            age_check = AgeAppropriatenessChecker.check_response(response)

            # Check for expected concepts
            concepts_found = sum(1 for concept in question_data["expected_concepts"]
                                if concept.lower() in response.lower())
            concepts_ratio = concepts_found / len(question_data["expected_concepts"])

            # Display response preview
            preview = response[:200] + "..." if len(response) > 200 else response
            print(f"  ✓ Response: {preview}")
            print(f"  Concepts found: {concepts_found}/{len(question_data['expected_concepts'])} ({concepts_ratio:.0%})")
            print(f"  Age appropriateness: {age_check['grade']} (score: {age_check['score']})")

            return {
                "question": question,
                "type": question_data["type"],
                "difficulty": question_data["difficulty"],
                "response": response,
                "success": True,
                "concepts_found": concepts_found,
                "concepts_total": len(question_data["expected_concepts"]),
                "concepts_ratio": concepts_ratio,
                "age_check": age_check,
                "word_count": len(response.split())
            }

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return {
                "question": question,
                "response": None,
                "success": False,
                "error": str(e)
            }

    async def test_chapter_1(self):
        """Test Chapter 1 questions"""
        print("\n" + "="*80)
        print("CHAPTER 1: THE WONDERFUL WORLD OF SCIENCE")
        print("="*80)

        for question_data in CHAPTER_1_QUESTIONS:
            result = await self.test_question(question_data)
            self.results["chapter_1"].append(result)
            await asyncio.sleep(0.5)  # Small delay between questions

    async def test_chapter_2(self):
        """Test Chapter 2 questions"""
        print("\n" + "="*80)
        print("CHAPTER 2: DIVERSITY IN THE LIVING WORLD")
        print("="*80)

        for question_data in CHAPTER_2_QUESTIONS:
            result = await self.test_question(question_data)
            self.results["chapter_2"].append(result)
            await asyncio.sleep(0.5)

    async def test_cross_chapter(self):
        """Test cross-chapter integration questions"""
        print("\n" + "="*80)
        print("CROSS-CHAPTER INTEGRATION QUESTIONS")
        print("="*80)

        for question_data in CROSS_CHAPTER_QUESTIONS:
            result = await self.test_question(question_data)
            self.results["cross_chapter"].append(result)
            await asyncio.sleep(0.5)

    async def test_conversational(self):
        """Test conversational questions"""
        print("\n" + "="*80)
        print("CONVERSATIONAL QUESTIONS")
        print("="*80)

        for question_data in CONVERSATIONAL_QUESTIONS:
            result = await self.test_question(question_data)
            self.results["conversational"].append(result)
            await asyncio.sleep(0.5)

    def calculate_overall_stats(self):
        """Calculate overall statistics"""
        all_results = (
            self.results["chapter_1"] +
            self.results["chapter_2"] +
            self.results["cross_chapter"] +
            self.results["conversational"]
        )

        successful = [r for r in all_results if r.get("success")]
        failed = [r for r in all_results if not r.get("success")]

        if not successful:
            return

        # Success rate
        success_rate = len(successful) / len(all_results)

        # Average concept coverage
        avg_concepts = sum(r["concepts_ratio"] for r in successful) / len(successful)

        # Age appropriateness stats
        age_scores = [r["age_check"]["score"] for r in successful]
        avg_age_score = sum(age_scores) / len(age_scores)
        appropriate_count = sum(1 for r in successful if r["age_check"]["is_appropriate"])
        age_appropriate_rate = appropriate_count / len(successful)

        # Word count stats
        word_counts = [r["word_count"] for r in successful]
        avg_word_count = sum(word_counts) / len(word_counts)

        # By difficulty
        by_difficulty = {}
        for result in successful:
            diff = result.get("difficulty", "unknown")
            if diff not in by_difficulty:
                by_difficulty[diff] = {"correct": 0, "total": 0}
            by_difficulty[diff]["total"] += 1
            if result["concepts_ratio"] >= 0.5:  # At least 50% concepts found
                by_difficulty[diff]["correct"] += 1

        self.results["overall_stats"] = {
            "total_questions": len(all_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": success_rate,
            "avg_concept_coverage": avg_concepts,
            "avg_age_appropriateness_score": avg_age_score,
            "age_appropriate_rate": age_appropriate_rate,
            "avg_word_count": avg_word_count,
            "by_difficulty": by_difficulty
        }

    def print_final_report(self):
        """Print comprehensive final report"""
        self.calculate_overall_stats()
        stats = self.results["overall_stats"]

        print("\n" + "="*80)
        print("EDUCATIONAL AGENT QUALITY REPORT")
        print("="*80)

        print(f"\n📊 OVERALL STATISTICS")
        print(f"  Total Questions: {stats['total_questions']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Success Rate: {stats['success_rate']:.1%}")

        print(f"\n🎯 ANSWER QUALITY")
        print(f"  Avg Concept Coverage: {stats['avg_concept_coverage']:.1%}")
        print(f"  Avg Word Count: {stats['avg_word_count']:.0f} words")

        print(f"\n👶 AGE APPROPRIATENESS (6th Grade)")
        print(f"  Avg Score: {stats['avg_age_appropriateness_score']:.1f}/10")
        print(f"  Age-Appropriate Rate: {stats['age_appropriate_rate']:.1%}")

        # Grade age appropriateness
        age_score = stats['avg_age_appropriateness_score']
        if age_score >= 6:
            age_grade = "🟢 EXCELLENT"
        elif age_score >= 4:
            age_grade = "🟡 GOOD"
        elif age_score >= 2:
            age_grade = "🟠 FAIR"
        else:
            age_grade = "🔴 NEEDS WORK"
        print(f"  Overall Grade: {age_grade}")

        print(f"\n📚 PERFORMANCE BY DIFFICULTY")
        for diff, data in stats['by_difficulty'].items():
            rate = data['correct'] / data['total'] if data['total'] > 0 else 0
            print(f"  {diff.capitalize()}: {data['correct']}/{data['total']} ({rate:.0%})")

        print(f"\n📖 PERFORMANCE BY CHAPTER")
        for chapter_name, results in [
            ("Chapter 1", self.results["chapter_1"]),
            ("Chapter 2", self.results["chapter_2"]),
            ("Cross-Chapter", self.results["cross_chapter"]),
            ("Conversational", self.results["conversational"])
        ]:
            if results:
                successful = [r for r in results if r.get("success")]
                rate = len(successful) / len(results)
                avg_concepts = sum(r["concepts_ratio"] for r in successful) / len(successful) if successful else 0
                print(f"  {chapter_name}: {len(successful)}/{len(results)} ({rate:.0%}), Concepts: {avg_concepts:.0%}")

        # Overall grade
        print(f"\n" + "="*80)
        print("FINAL ASSESSMENT")
        print("="*80)

        overall_score = (
            stats['success_rate'] * 0.3 +
            stats['avg_concept_coverage'] * 0.3 +
            stats['age_appropriate_rate'] * 0.4
        )

        print(f"\nOverall Score: {overall_score:.1%}")

        if overall_score >= 0.75:
            print("✅ AGENT QUALITY: EXCELLENT - Ready to help 6th grade students")
        elif overall_score >= 0.60:
            print("✅ AGENT QUALITY: GOOD - Suitable for 6th grade students")
        elif overall_score >= 0.45:
            print("⚠️ AGENT QUALITY: FAIR - Some improvements needed")
        else:
            print("❌ AGENT QUALITY: NEEDS IMPROVEMENT")

        print(f"\n" + "="*80 + "\n")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def main():
    """Run all educational agent tests"""
    print("\n" + "="*80)
    print("EDUCATIONAL AGENT TEST SUITE - Grade 6 Science")
    print("Testing agent's ability to help 11-12 year old students")
    print("="*80)

    tester = EducationalAgentTester()

    # Initialize
    success = await tester.initialize()
    if not success:
        print("\n❌ Failed to initialize agent. Exiting...")
        return

    # Run tests
    await tester.test_chapter_1()
    await tester.test_chapter_2()
    await tester.test_cross_chapter()
    await tester.test_conversational()

    # Print final report
    tester.print_final_report()


if __name__ == "__main__":
    asyncio.run(main())
