import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class Grade(Enum):
    CLASS_6 = "class-6"
    CLASS_7 = "class-7"
    CLASS_8 = "class-8"
    CLASS_9 = "class-9"
    CLASS_10 = "class-10"

class Subject(Enum):
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    SOCIAL_STUDIES = "social-studies"
    HINDI = "hindi"

@dataclass
class Chapter:
    number: int
    title: str
    topics: List[str]
    learning_objectives: List[str]
    difficulty_level: str = "medium"

@dataclass
class SubjectConfig:
    grade: Grade
    subject: Subject
    chapters: List[Chapter]
    collection_name: str
    description: str

# Define curriculum structure
CURRICULUM = {
    (Grade.CLASS_6, Subject.MATHEMATICS): SubjectConfig(
        grade=Grade.CLASS_6,
        subject=Subject.MATHEMATICS,
        collection_name="class-6-mathematics",
        description="Class 6 Mathematics - Foundation concepts in numbers, geometry, and data",
        chapters=[
            Chapter(1, "Patterns in Mathematics", 
                   ["Number patterns", "Shape patterns", "Pattern recognition"],
                   ["Identify patterns in numbers and shapes", "Create pattern sequences"]),
            Chapter(2, "Lines and Angles",
                   ["Types of lines", "Measuring angles", "Angle relationships"],
                   ["Identify different types of lines", "Measure and draw angles"]),
            Chapter(3, "Number Play",
                   ["Place value", "Comparing numbers", "Number operations"],
                   ["Understand place value system", "Compare and order numbers"]),
            Chapter(4, "Data Handling and Presentation",
                   ["Data collection", "Tables and charts", "Bar graphs"],
                   ["Collect and organize data", "Create simple graphs"]),
            Chapter(5, "Prime Time",
                   ["Prime numbers", "Composite numbers", "Factorization"],
                   ["Identify prime and composite numbers", "Find factors"]),
            Chapter(6, "Perimeter and Area",
                   ["Perimeter calculation", "Area of rectangles", "Units of measurement"],
                   ["Calculate perimeter of shapes", "Find area of rectangles"]),
            Chapter(7, "Fractions",
                   ["Understanding fractions", "Equivalent fractions", "Adding fractions"],
                   ["Represent fractions visually", "Compare fractions"]),
            Chapter(8, "Playing with Constructions",
                   ["Geometric constructions", "Using compass and ruler", "Drawing shapes"],
                   ["Use geometric tools", "Construct basic shapes"]),
            Chapter(9, "Symmetry",
                   ["Line symmetry", "Rotational symmetry", "Symmetric shapes"],
                   ["Identify symmetric shapes", "Draw symmetric figures"]),
            Chapter(10, "The Other Side of Zero",
                   ["Negative numbers", "Number line", "Comparing integers"],
                   ["Understand negative numbers", "Use number line with integers"])
        ]
    ),
    (Grade.CLASS_6, Subject.SCIENCE): SubjectConfig(
        grade=Grade.CLASS_6,
        subject=Subject.SCIENCE,
        collection_name="class-6-science",
        description="Class 6 Science - Introduction to scientific concepts, nature, and experiments",
        chapters=[
            Chapter(1, "Food and Its Sources",
                   ["Food variety", "Food sources", "Plant and animal products"],
                   ["Identify food sources", "Classify food items"]),
            Chapter(2, "Components of Food",
                   ["Nutrients", "Balanced diet", "Food tests"],
                   ["Understand nutrients", "Plan balanced meals"]),
            Chapter(3, "Fibre to Fabric",
                   ["Natural fibres", "Synthetic fibres", "Fabric making"],
                   ["Identify fibre types", "Understand fabric production"]),
            Chapter(4, "Sorting Materials",
                   ["Material properties", "Classification", "Uses of materials"],
                   ["Classify materials", "Identify properties"]),
            Chapter(5, "Separation of Substances",
                   ["Separation methods", "Filtration", "Evaporation"],
                   ["Apply separation techniques", "Choose appropriate methods"]),
            Chapter(6, "Changes Around Us",
                   ["Reversible changes", "Irreversible changes", "Physical and chemical changes"],
                   ["Identify change types", "Understand reversibility"]),
            Chapter(7, "Getting to Know Plants",
                   ["Plant parts", "Types of plants", "Plant functions"],
                   ["Identify plant parts", "Understand plant life"]),
            Chapter(8, "Body Movements",
                   ["Joints", "Muscles", "Skeleton"],
                   ["Understand body mechanics", "Identify movement types"]),
            Chapter(9, "Living Organisms",
                   ["Characteristics of living things", "Habitat", "Adaptation"],
                   ["Identify living things", "Understand habitats"]),
            Chapter(10, "Motion and Measurement",
                   ["Types of motion", "Measurement units", "Distance and displacement"],
                   ["Measure accurately", "Understand motion"]),
            Chapter(11, "Light, Shadows and Reflections",
                   ["Light sources", "Shadow formation", "Reflection"],
                   ["Understand light behavior", "Create shadows"]),
            Chapter(12, "Electricity and Circuits",
                   ["Electric current", "Circuits", "Conductors and insulators"],
                   ["Build simple circuits", "Identify conductors"])
        ]
    )
}

# Educational prompts for different types of queries
EDUCATIONAL_PROMPTS = {
    "concept_explanation": """
You are a friendly math teacher for Class 6 students. Explain the concept in simple, easy-to-understand language.
Use examples from daily life that children can relate to.

Context from textbook:
{context}

Student's question: {question}

Provide a clear explanation with:
1. Simple definition
2. Real-life example
3. Step-by-step process if applicable
4. Common mistakes to avoid

Answer in a warm, encouraging tone suitable for 11-12 year old students.
""",
    
    "problem_solving": """
You are a helpful math tutor. The student needs help solving a problem.

Context from textbook:
{context}

Student's problem: {question}

Help the student by:
1. Breaking down the problem step-by-step
2. Explaining the reasoning behind each step
3. Providing similar examples
4. Suggesting practice problems

Be patient and encouraging. Use simple language appropriate for Class 6 level.
""",
    
    "doubt_clarification": """
You are a caring teacher helping a confused student. The student has a doubt or misconception.

Context from textbook:
{context}

Student's doubt: {question}

Help by:
1. Acknowledging their confusion (it's normal!)
2. Clarifying the concept clearly
3. Comparing with what they might be thinking
4. Giving memory tricks or tips
5. Encouraging them to ask more questions

Be very patient and supportive.
""",
    
    "chapter_summary": """
You are summarizing a chapter for Class 6 students for revision.

Context from textbook:
{context}

Create a comprehensive yet simple summary including:
1. Key concepts learned
2. Important formulas or rules
3. Types of problems covered
4. Tips for remembering concepts

Make it engaging and easy to revise from.
"""
}

def get_collection_name(grade: Grade, subject: Subject) -> str:
    """Generate collection name for a grade-subject combination"""
    return f"{grade.value}-{subject.value}"

def get_chapter_metadata(grade: Grade, subject: Subject, chapter_number: int) -> Dict:
    """Get metadata for a specific chapter"""
    config = CURRICULUM.get((grade, subject))
    if not config:
        return {}
    
    chapter = next((ch for ch in config.chapters if ch.number == chapter_number), None)
    if not chapter:
        return {}
    
    return {
        "grade": grade.value,
        "subject": subject.value,
        "chapter_number": chapter.number,
        "chapter_title": chapter.title,
        "topics": chapter.topics,
        "learning_objectives": chapter.learning_objectives,
        "difficulty_level": chapter.difficulty_level
    }

def get_subject_config(grade: Grade, subject: Subject) -> Optional[SubjectConfig]:
    """Get configuration for a grade-subject combination"""
    return CURRICULUM.get((grade, subject))

def list_available_subjects(grade: Grade) -> List[Subject]:
    """List all available subjects for a grade"""
    return [subject for (g, subject) in CURRICULUM.keys() if g == grade]

def get_chapter_by_title(grade: Grade, subject: Subject, title_query: str) -> Optional[Chapter]:
    """Find chapter by partial title match"""
    config = get_subject_config(grade, subject)
    if not config:
        return None
    
    title_query = title_query.lower()
    for chapter in config.chapters:
        if title_query in chapter.title.lower():
            return chapter
    return None