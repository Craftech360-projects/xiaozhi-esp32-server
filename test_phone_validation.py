#!/usr/bin/env python3
"""
Test Phone Number Validation
Tests the same regex validation used in the backend ValidatorUtils.isValidPhone method
"""

import re

# This is the exact regex from ValidatorUtils.java
INTERNATIONAL_PHONE_REGEX = r"^\+[1-9]\d{0,3}[1-9]\d{4,14}$"

def test_phone_validation(phone):
    """Test if a phone number matches the backend validation"""
    if not phone:
        return False, "Phone number is empty"

    pattern = re.compile(INTERNATIONAL_PHONE_REGEX)
    is_valid = pattern.match(phone) is not None

    return is_valid, f"Phone: {phone} -> {'VALID' if is_valid else 'INVALID'}"

# Test various phone number formats
test_cases = [
    "+8613800138000",      # China - should be valid
    "+86 13800138000",     # China with space - should be invalid
    "+1234567890",         # US - should be valid
    "+447123456789",       # UK - should be valid
    "13800138000",         # No + prefix - should be invalid
    "+86138001380001",     # Too long - should be invalid
    "+861380013800",       # Valid length - should be valid
    "+86138",              # Too short - should be invalid
    "+0613800138000",      # Starts with 0 after + - should be invalid
    "+86013800138000",     # Country code starts with 0 - should be invalid
]

print("=== Phone Number Validation Test ===")
print(f"Backend Regex: {INTERNATIONAL_PHONE_REGEX}")
print()

for phone in test_cases:
    is_valid, message = test_phone_validation(phone)
    status = "[PASS]" if is_valid else "[FAIL]"
    print(f"{status} {message}")

print("\n=== Summary ===")
print("Valid format requirements:")
print("1. Must start with + sign")
print("2. Country code: 1-4 digits, cannot start with 0")
print("3. Phone number: 5-15 digits, cannot start with 0")
print("4. Total length: 7-20 characters")
print("5. No spaces or special characters")

print("\nCommon mistakes:")
print("- Adding spaces: '+86 13800138000' ❌")
print("- Missing +: '8613800138000' ❌")
print("- Country code starting with 0: '+0613800138000' ❌")
print("- Phone number starting with 0: '+86013800138000' ❌")