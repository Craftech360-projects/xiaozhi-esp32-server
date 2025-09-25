"""
Test script to validate the prewarm improvements
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")

# Test shared component manager initialization
async def test_shared_components():
    print("Testing shared component initialization...")
    
    from src.services.shared_component_manager import initialize_shared_components, SharedEducationalComponents
    
    success = await initialize_shared_components()
    if success:
        print("[SUCCESS] Shared components initialized successfully")
        print(f"[SUCCESS] Shared components are initialized: {SharedEducationalComponents.is_initialized()}")
        return True
    else:
        print("[ERROR] Failed to initialize shared components")
        return False

async def test_education_service_with_shared_components():
    print("\nTesting EducationService initialization with shared components...")
    
    from src.services.education_service import EducationService
    
    service = EducationService()
    success = await service.initialize(use_shared_components=True)
    
    if success:
        print("[SUCCESS] Educational service initialized with shared components successfully")
        await service.set_student_context(6, "science")
        print("[SUCCESS] Student context set successfully")
        return True
    else:
        print("[ERROR] Failed to initialize educational service with shared components")
        return False

async def test_education_service_without_shared_components():
    print("\nTesting EducationService initialization without shared components (for comparison)...")
    
    from src.services.education_service import EducationService
    
    service = EducationService()
    success = await service.initialize(use_shared_components=False)
    
    if success:
        print("[SUCCESS] Educational service initialized without shared components successfully")
        await service.set_student_context(6, "science")
        print("[SUCCESS] Student context set successfully")
        return True
    else:
        print("[ERROR] Failed to initialize educational service without shared components")
        return False

async def main():
    print("Running prewarm improvements validation tests...\n")
    
    # Test 1: Shared component initialization
    shared_success = await test_shared_components()
    
    if shared_success:
        # Test 2: Education service with shared components (fast)
        shared_service_success = await test_education_service_with_shared_components()
        
        # Test 3: Education service without shared components (slow, for comparison)
        # Only run this if the user wants it (it will take longer)
        import sys
        if len(sys.argv) > 1 and sys.argv[1] == "--full":
            individual_service_success = await test_education_service_without_shared_components()
        else:
            print("\nSkipping individual component test (run with --full to include)")
            individual_service_success = True
    
    print("\n" + "="*50)
    print("Test Summary:")
    print(f"- Shared components: {'[PASS]' if shared_success else '[FAIL]'}")
    print(f"- Education service with shared components: {'[PASS]' if shared_service_success else '[FAIL]'}")
    if 'individual_service_success' in locals():
        print(f"- Education service without shared components: {'[PASS]' if individual_service_success else '[FAIL]'}")
    print("="*50)
    
    all_passed = shared_success and shared_service_success
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)