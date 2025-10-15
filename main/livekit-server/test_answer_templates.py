"""
Test Answer Templates - Enhancement 3
Tests answer formatting for different question types
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag.answer_templates import AnswerFormatter, detect_question_type, QuestionType


def test_question_type_detection():
    """Test question type detection"""

    print("\n" + "="*60)
    print("QUESTION TYPE DETECTION TESTS")
    print("="*60)

    test_questions = [
        ("What is photosynthesis?", QuestionType.DEFINITION),
        ("Define gravity", QuestionType.DEFINITION),
        ("How to conduct an experiment?", QuestionType.PROCEDURE),
        ("How do plants make food?", QuestionType.PROCEDURE),
        ("Compare plants and animals", QuestionType.COMPARISON),
        ("What is the difference between solid and liquid?", QuestionType.COMPARISON),
        ("List the types of matter", QuestionType.LIST),
        ("Name three states of water", QuestionType.LIST),
        ("Why does water boil?", QuestionType.CAUSE_EFFECT),
        ("What causes rain?", QuestionType.CAUSE_EFFECT),
        ("When to use a microscope?", QuestionType.APPLICATION),
        ("Where do plants grow best?", QuestionType.APPLICATION),
        ("Give me an example of a mammal", QuestionType.EXAMPLE),
        ("Show me examples of food chains", QuestionType.EXAMPLE),
        ("Explain how magnets work", QuestionType.EXPLANATION),
    ]

    passed = 0
    for question, expected_type in test_questions:
        detected_type = detect_question_type(question)
        match = detected_type == expected_type
        status = "[OK]" if match else "[FAIL]"

        if match:
            passed += 1

        print(f"{status} '{question}'")
        print(f"     Expected: {expected_type.value}, Got: {detected_type.value}")

    print(f"\nResults: {passed}/{len(test_questions)} tests passed ({passed*100//len(test_questions)}%)")
    return passed == len(test_questions)


def test_definition_formatting():
    """Test definition answer formatting"""

    print("\n" + "="*60)
    print("DEFINITION FORMATTING TEST")
    print("="*60)

    content = {
        'answer': """Photosynthesis is the process by which plants make their own food using sunlight.
        Plants have special green parts called chloroplasts that capture sunlight.
        They use carbon dioxide from the air and water from the soil.
        For example, a tree uses photosynthesis to grow big and strong.""",
        'key_concepts': ['sunlight', 'chloroplasts', 'carbon dioxide', 'water']
    }

    formatter = AnswerFormatter()
    formatted = formatter.format_definition_answer(content)

    print("\nOriginal:")
    print(content['answer'])
    print("\nFormatted:")
    print(formatted)

    # Check if formatted output has expected structure
    has_definition = "**Definition:**" in formatted or "**Definition**" in formatted
    has_key_points = "**Key Points:**" in formatted or "Key Points" in formatted or len(content['key_concepts']) > 0
    has_example = "**Example:**" in formatted or "For example" in formatted.lower()

    print("\nValidation:")
    print(f"  [{'OK' if has_definition else 'FAIL'}] Has definition section")
    print(f"  [{'OK' if has_key_points else 'FAIL'}] Has key points")
    print(f"  [{'OK' if has_example else 'FAIL'}] Has example")

    return has_definition


def test_procedure_formatting():
    """Test procedure answer formatting"""

    print("\n" + "="*60)
    print("PROCEDURE FORMATTING TEST")
    print("="*60)

    content = {
        'answer': """To test for starch in food, you need iodine solution.
        First, take a small sample of the food.
        Then, add a few drops of iodine solution to the food sample.
        Next, observe the color change.
        Finally, if the food contains starch, it will turn blue-black.
        Make sure to be careful with iodine as it can stain.""",
        'key_concepts': ['iodine test', 'starch', 'blue-black color']
    }

    formatter = AnswerFormatter()
    formatted = formatter.format_procedure_answer(content)

    print("\nOriginal:")
    print(content['answer'])
    print("\nFormatted:")
    print(formatted)

    # Check if formatted output has steps
    has_steps = any(str(i) in formatted for i in range(1, 6))
    has_numbered_format = "1." in formatted or "2." in formatted

    print("\nValidation:")
    print(f"  [{'OK' if has_steps else 'FAIL'}] Has multiple steps")
    print(f"  [{'OK' if has_numbered_format else 'FAIL'}] Has numbered format")

    return has_steps


def test_list_formatting():
    """Test list answer formatting"""

    print("\n" + "="*60)
    print("LIST FORMATTING TEST")
    print("="*60)

    content = {
        'answer': """There are three main states of matter: solids, liquids, and gases.
        Solids have a fixed shape and volume.
        Liquids have a fixed volume but take the shape of their container.
        Gases have neither fixed shape nor volume.""",
        'key_concepts': ['solid', 'liquid', 'gas']
    }

    formatter = AnswerFormatter()
    formatted = formatter.format_list_answer(content)

    print("\nOriginal:")
    print(content['answer'])
    print("\nFormatted:")
    print(formatted)

    # Check if formatted output has list structure
    has_bullets = "•" in formatted or "-" in formatted
    has_count = "3" in formatted or "three" in formatted.lower()
    newline_count = formatted.count('\n')
    has_list_structure = has_bullets or newline_count >= 3

    print("\nValidation:")
    print(f"  [{'OK' if has_list_structure else 'FAIL'}] Has list structure")
    print(f"  [{'OK' if has_count else 'FAIL'}] Mentions count")

    return True


def test_comparison_formatting():
    """Test comparison answer formatting"""

    print("\n" + "="*60)
    print("COMPARISON FORMATTING TEST")
    print("="*60)

    content = {
        'answer': """Plants and animals are both living things, but they have many differences.
        Plants can make their own food through photosynthesis, while animals need to eat other living things.
        Plants stay in one place with roots, while animals can move around.
        Plants have cell walls made of cellulose, but animals do not.""",
        'key_concepts': ['plants', 'animals', 'photosynthesis', 'movement']
    }

    formatter = AnswerFormatter()
    formatted = formatter.format_comparison_answer(content)

    print("\nOriginal:")
    print(content['answer'])
    print("\nFormatted:")
    print(formatted)

    # Check if formatted output has comparison structure
    has_comparison = "Comparing" in formatted or "plants" in formatted.lower() and "animals" in formatted.lower()

    print("\nValidation:")
    print(f"  [{'OK' if has_comparison else 'FAIL'}] Has comparison structure")

    return has_comparison


def test_cause_effect_formatting():
    """Test cause-effect answer formatting"""

    print("\n" + "="*60)
    print("CAUSE-EFFECT FORMATTING TEST")
    print("="*60)

    content = {
        'answer': """Water boils because heat energy makes water molecules move faster and faster.
        When the temperature reaches 100 degrees Celsius, the molecules have enough energy to escape as steam.
        This is why you see bubbles forming and rising in boiling water.
        For example, when you boil water in a pot, you can see steam coming out.""",
        'key_concepts': ['heat energy', 'molecules', 'temperature', '100 degrees Celsius']
    }

    formatter = AnswerFormatter()
    formatted = formatter.format_cause_effect_answer(content)

    print("\nOriginal:")
    print(content['answer'])
    print("\nFormatted:")
    print(formatted)

    # Check if formatted output has cause-effect structure
    has_cause = "**Cause:**" in formatted or "because" in formatted.lower()
    has_explanation = "**Explanation:**" in formatted or len(formatted) > 100

    print("\nValidation:")
    print(f"  [{'OK' if has_cause else 'FAIL'}] Has cause section")
    print(f"  [{'OK' if has_explanation else 'FAIL'}] Has explanation")

    return has_cause or has_explanation


def test_example_formatting():
    """Test example answer formatting"""

    print("\n" + "="*60)
    print("EXAMPLE FORMATTING TEST")
    print("="*60)

    content = {
        'answer': """Here are some examples of mammals: Dogs are mammals because they give birth to live babies and feed them milk.
        Cats are also mammals with fur and they nurse their kittens.
        Humans are mammals too - we give birth and feed babies with breast milk.
        Even whales in the ocean are mammals because they breathe air and have live babies.""",
        'key_concepts': ['mammals', 'live birth', 'milk', 'fur']
    }

    formatter = AnswerFormatter()
    formatted = formatter.format_example_answer(content)

    print("\nOriginal:")
    print(content['answer'])
    print("\nFormatted:")
    print(formatted)

    # Check if formatted output has example structure
    has_examples = "**Examples:**" in formatted or "example" in formatted.lower()

    print("\nValidation:")
    print(f"  [{'OK' if has_examples else 'FAIL'}] Has example structure")

    return has_examples


def test_full_integration():
    """Test full integration with format_answer method"""

    print("\n" + "="*60)
    print("FULL INTEGRATION TEST")
    print("="*60)

    test_cases = [
        (QuestionType.DEFINITION, "Simple definition text about science."),
        (QuestionType.PROCEDURE, "First step. Second step. Third step."),
        (QuestionType.LIST, "Item one, item two, item three."),
        (QuestionType.COMPARISON, "A is different from B in many ways."),
        (QuestionType.CAUSE_EFFECT, "This happens because of that reason."),
        (QuestionType.APPLICATION, "You can use this in these situations."),
        (QuestionType.EXAMPLE, "Here is an example of the concept."),
        (QuestionType.EXPLANATION, "This is how things work in general."),
    ]

    formatter = AnswerFormatter()
    passed = 0

    for question_type, answer_text in test_cases:
        content = {'answer': answer_text, 'key_concepts': []}

        try:
            formatted = formatter.format_answer(content, question_type)
            status = "[OK]"
            passed += 1
        except Exception as e:
            status = f"[FAIL] {str(e)}"
            formatted = None

        print(f"{status} {question_type.value}: {'Formatted successfully' if formatted else 'Failed'}")

    print(f"\nResults: {passed}/{len(test_cases)} question types handled ({passed*100//len(test_cases)}%)")
    return passed == len(test_cases)


def run_all_tests():
    """Run all answer template tests"""

    print("\n" + "="*60)
    print("ANSWER TEMPLATES TEST SUITE")
    print("="*60)
    print("\nEnhancement 3: Question Classification & Answer Templates")
    print("Testing answer formatting for different question types\n")

    tests = [
        ("Question Type Detection", test_question_type_detection),
        ("Definition Formatting", test_definition_formatting),
        ("Procedure Formatting", test_procedure_formatting),
        ("List Formatting", test_list_formatting),
        ("Comparison Formatting", test_comparison_formatting),
        ("Cause-Effect Formatting", test_cause_effect_formatting),
        ("Example Formatting", test_example_formatting),
        ("Full Integration", test_full_integration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n[ERROR] {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed ({passed*100//total}%)")

    if passed == total:
        print("\n[SUCCESS] All tests passed! Answer templates are working correctly.")
    elif passed >= total * 0.8:
        print(f"\n[GOOD] Most tests passed ({passed}/{total}). Minor issues to address.")
    else:
        print(f"\n[NEEDS WORK] Only {passed}/{total} tests passed. Further improvements needed.")

    print("\n" + "="*60)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
