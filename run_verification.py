#!/usr/bin/env python3
"""
Simple verification runner that installs dependencies and runs tests
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "-r", "requirements_verification.txt"
        ])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_basic_verification():
    """Run basic database verification"""
    print("\n🔍 Running Basic Database Verification...")
    try:
        result = subprocess.run([sys.executable, "db_verification.py"],
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running verification: {e}")
        return False

def run_migration_test():
    """Run migration test (creates temporary database)"""
    print("\n🧪 Running Migration Test...")
    try:
        result = subprocess.run([sys.executable, "migration_tester.py"],
                              capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running migration test: {e}")
        return False

def main():
    """Main function"""
    print("🚀 Xiaozhi ESP32 Database Verification Suite")
    print("=" * 60)

    # Check if we're in the right directory
    if not os.path.exists("complete_main_migration.sql"):
        print("❌ Migration file not found. Please run this script from the project directory.")
        return 1

    # Install dependencies
    if not install_dependencies():
        return 1

    # Run basic verification first
    verification_passed = run_basic_verification()

    # Ask user if they want to run migration test (which creates temp database)
    print("\n" + "=" * 60)
    if verification_passed:
        print("✅ Basic verification passed!")

        while True:
            response = input("\n🤔 Do you want to run the migration test? (creates temporary database) [y/n]: ").lower().strip()
            if response in ['y', 'yes']:
                migration_test_passed = run_migration_test()
                if migration_test_passed:
                    print("\n🎉 ALL TESTS PASSED! Your migration script is ready for production.")
                    return 0
                else:
                    print("\n❌ Migration test failed. Check the logs for details.")
                    return 1
            elif response in ['n', 'no']:
                print("\n✅ Basic verification completed. Migration test skipped.")
                return 0
            else:
                print("Please enter 'y' or 'n'")
    else:
        print("❌ Basic verification failed. Fix issues before running migration test.")
        return 1

if __name__ == "__main__":
    sys.exit(main())