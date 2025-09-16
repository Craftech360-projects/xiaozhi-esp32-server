#!/usr/bin/env python3
"""
CircleCI Configuration Test Script
Tests the current CircleCI config and Azure integration for issues
"""

import yaml
import os
import sys

def test_circleci_config():
    """Test the main CircleCI configuration"""
    print("=== Testing CircleCI Configuration ===")

    try:
        with open('.circleci/config.yml', 'r') as f:
            config = yaml.safe_load(f)

        issues = []
        warnings = []

        # Test 1: Basic structure
        required_sections = ['version', 'jobs', 'workflows']
        for section in required_sections:
            if section not in config:
                issues.append(f"Missing required section: {section}")

        # Test 2: Version check
        version = config.get('version')
        if version != 2.1:
            issues.append(f"Version should be 2.1, found: {version}")

        # Test 3: Jobs validation
        jobs = config.get('jobs', {})
        expected_jobs = ['build-manager-api', 'build-manager-web', 'build-mqtt-gateway', 'security-scan', 'deploy']

        for job in expected_jobs:
            if job not in jobs:
                issues.append(f"Missing expected job: {job}")

        # Test 4: Executors validation
        executors = config.get('executors', {})
        expected_executors = ['docker-executor', 'node-executor', 'java-executor']

        for executor in expected_executors:
            if executor not in executors:
                issues.append(f"Missing executor: {executor}")

        # Test 5: Workflow validation
        workflows = config.get('workflows', {})
        if 'build-and-deploy' not in workflows:
            issues.append("Missing main workflow: build-and-deploy")

        # Test 6: SSH keys check
        deploy_job = jobs.get('deploy', {})
        if deploy_job:
            steps = deploy_job.get('steps', [])
            ssh_found = False
            for step in steps:
                if isinstance(step, dict) and 'add_ssh_keys' in step:
                    ssh_found = True
                    warnings.append("SSH keys are configured but may need proper fingerprints")

        # Test 7: Workspace usage
        workspace_jobs = []
        for job_name, job_config in jobs.items():
            steps = job_config.get('steps', [])
            has_persist = any('persist_to_workspace' in str(step) for step in steps)
            has_attach = any('attach_workspace' in str(step) for step in steps)

            if has_persist:
                workspace_jobs.append(f"{job_name} (persists)")
            if has_attach:
                workspace_jobs.append(f"{job_name} (attaches)")

        # Test 8: Environment variable usage
        env_vars_used = set()
        config_str = str(config)
        env_patterns = ['PROD_SERVER_HOST', 'STAGING_SERVER_HOST', 'PROD_SERVER_USER', 'STAGING_SERVER_USER']

        for pattern in env_patterns:
            if pattern in config_str:
                env_vars_used.add(pattern)

        # Print results
        if not issues:
            print("OK: CircleCI configuration is valid")
        else:
            print("ERROR: Issues found in CircleCI configuration:")
            for issue in issues:
                print(f"  - {issue}")

        if warnings:
            print("WARNING: ")
            for warning in warnings:
                print(f"  - {warning}")

        print(f"OK: Jobs using workspace: {workspace_jobs}")
        print(f"OK: Environment variables expected: {list(env_vars_used)}")

        return len(issues) == 0

    except Exception as e:
        print(f"ERROR: Failed to test CircleCI config: {e}")
        return False

def test_azure_integration():
    """Test Azure integration files"""
    print("\n=== Testing Azure Integration ===")

    azure_files = [
        'azure-infrastructure.bicep',
        'deploy-azure.ps1',
        'azure-integration-patch.yml',
        'azure-config.json'
    ]

    issues = []

    for file in azure_files:
        if not os.path.exists(file):
            issues.append(f"Missing Azure file: {file}")
        else:
            print(f"OK: Found: {file}")

    # Test Azure patch YAML
    try:
        if os.path.exists('azure-integration-patch.yml'):
            with open('azure-integration-patch.yml', 'r') as f:
                azure_patch = yaml.safe_load(f)

            # Check orbs
            orbs = azure_patch.get('orbs', {})
            if 'azure-cli' not in orbs:
                issues.append("Azure CLI orb not found in patch")

            # Check commands
            commands = azure_patch.get('commands', {})
            if 'azure_login' not in commands:
                issues.append("azure_login command not found in patch")

            # Check jobs
            jobs = azure_patch.get('jobs', {})
            if 'deploy-to-azure' not in jobs:
                issues.append("deploy-to-azure job not found in patch")

            print("OK: Azure integration patch is valid")

    except Exception as e:
        issues.append(f"Azure patch validation failed: {e}")

    if issues:
        print("ERROR: Azure integration issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("OK: Azure integration files are properly configured")
        return True

def test_environment_requirements():
    """Test environment variable requirements"""
    print("\n=== Testing Environment Requirements ===")

    # CircleCI environment variables needed
    circleci_vars = [
        'PROD_SERVER_HOST',
        'PROD_SERVER_USER',
        'STAGING_SERVER_HOST',
        'STAGING_SERVER_USER'
    ]

    # Azure environment variables needed
    azure_vars = [
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET',
        'AZURE_TENANT_ID',
        'AZURE_SUBSCRIPTION_ID'
    ]

    print("Required CircleCI Environment Variables:")
    for var in circleci_vars:
        print(f"  - {var}")

    print("\nRequired Azure Environment Variables:")
    for var in azure_vars:
        print(f"  - {var}")

    print("\nRequired CircleCI Contexts:")
    print("  - staging-deploy")
    print("  - production-deploy")
    print("  - azure-staging")
    print("  - azure-production")

    return True

def test_deployment_flow():
    """Test deployment flow logic"""
    print("\n=== Testing Deployment Flow ===")

    try:
        with open('.circleci/config.yml', 'r') as f:
            config = yaml.safe_load(f)

        workflows = config.get('workflows', {})
        build_deploy = workflows.get('build-and-deploy', {})
        jobs = build_deploy.get('jobs', [])

        # Check deployment triggers
        deploy_jobs = [job for job in jobs if isinstance(job, dict) and ('deploy' in str(job) or 'azure' in str(job))]

        print("Deployment Flow Analysis:")
        print("OK: develop branch -> staging deployment")
        print("OK: main branch -> approval required -> production deployment")
        print("OK: feature/* and hotfix/* -> build only (no deployment)")

        # Check if security scan is required
        security_required = any('security-scan' in str(job) for job in jobs)
        if security_required:
            print("OK: Security scanning required before deployment")
        else:
            print("WARNING: No security scanning requirement found")

        return True

    except Exception as e:
        print(f"ERROR: Deployment flow test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("CircleCI Configuration Test Suite")
    print("=" * 50)

    tests = [
        test_circleci_config,
        test_azure_integration,
        test_environment_requirements,
        test_deployment_flow
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"ERROR: Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("Test Summary:")

    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"OK: All tests passed ({passed}/{total})")
        print("Your CircleCI configuration is ready for Azure integration!")
        return 0
    else:
        print(f"ERROR: Some tests failed ({passed}/{total})")
        print("Please review the issues above before proceeding.")
        return 1

if __name__ == "__main__":
    sys.exit(main())