import re

test_strings = [
    "Chapter 1 of Grade 6 Science",
    "chapter 1",
    "What is chapter 1 about?",
    "Tell me about chapter 1",
    "Chapter 1",
    "CHAPTER 1"
]

pattern = r'chapter\s*(\d+)'

for test in test_strings:
    match = re.search(pattern, test.lower())
    if match:
        print(f"MATCHED '{test}' -> Chapter {match.group(1)}")
    else:
        print(f"NO MATCH for '{test}'")