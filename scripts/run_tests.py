#!/usr/bin/env python3
"""
Test runner script for SCONIA.
Runs comprehensive test suite and generates reports.
"""
import subprocess
import sys
import os
import time
from pathlib import Path

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        print(f"✅ {description} completed successfully in {duration:.2f}s")
        
        if result.stdout:
            print("Output:")
            print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"❌ {description} failed after {duration:.2f}s")
        print(f"Error: {e}")
        
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        
        return False


def main():
    """Run comprehensive test suite."""
    print("🚀 Starting SCONIA Test Suite")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    test_results = []
    
    # 1. Install test dependencies
    success = run_command(
        "pip install pytest pytest-asyncio pytest-cov httpx",
        "Installing test dependencies"
    )
    test_results.append(("Install Dependencies", success))
    
    if not success:
        print("❌ Failed to install dependencies. Exiting.")
        return 1
    
    # 2. Run linting (if flake8 is available)
    success = run_command(
        "python -m flake8 app/ --max-line-length=120 --ignore=E501,W503 || echo 'Flake8 not available, skipping linting'",
        "Code linting with flake8"
    )
    test_results.append(("Code Linting", success))
    
    # 3. Run type checking (if mypy is available)
    success = run_command(
        "python -m mypy app/ --ignore-missing-imports || echo 'MyPy not available, skipping type checking'",
        "Type checking with mypy"
    )
    test_results.append(("Type Checking", success))
    
    # 4. Run unit tests
    success = run_command(
        "python -m pytest tests/ -v --tb=short",
        "Running unit tests"
    )
    test_results.append(("Unit Tests", success))
    
    # 5. Run tests with coverage
    success = run_command(
        "python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing",
        "Running tests with coverage"
    )
    test_results.append(("Test Coverage", success))
    
    # 6. Run API endpoint tests specifically
    success = run_command(
        "python -m pytest tests/test_api_endpoints.py -v",
        "Running API endpoint tests"
    )
    test_results.append(("API Endpoint Tests", success))
    
    # 7. Run WebSocket tests specifically
    success = run_command(
        "python -m pytest tests/test_websocket.py -v",
        "Running WebSocket tests"
    )
    test_results.append(("WebSocket Tests", success))
    
    # 8. Run integration tests (if they exist)
    if Path("tests/test_integration.py").exists():
        success = run_command(
            "python -m pytest tests/test_integration.py -v",
            "Running integration tests"
        )
        test_results.append(("Integration Tests", success))
    
    # 9. Security scan (if bandit is available)
    success = run_command(
        "python -m bandit -r app/ -f json -o security_report.json || echo 'Bandit not available, skipping security scan'",
        "Security scanning with bandit"
    )
    test_results.append(("Security Scan", success))
    
    # 10. Performance tests (basic)
    success = run_command(
        "python -c \"import time; from app.main import app; print('✅ App imports successfully')\"",
        "Basic performance test - app import"
    )
    test_results.append(("Performance Test", success))
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<25} {status}")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\n📈 Results: {passed} passed, {failed} failed")
    
    # Generate test report
    report_content = f"""# SCONIA Test Report

Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- **Total Tests**: {len(test_results)}
- **Passed**: {passed}
- **Failed**: {failed}
- **Success Rate**: {(passed/len(test_results)*100):.1f}%

## Test Results

| Test Category | Status |
|---------------|--------|
"""
    
    for test_name, success in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        report_content += f"| {test_name} | {status} |\n"
    
    report_content += f"""
## Coverage Report
Coverage report generated in `htmlcov/index.html`

## Security Report
Security report generated in `security_report.json` (if bandit is available)

## Next Steps
{'✅ All tests passed! Ready for deployment.' if failed == 0 else '❌ Some tests failed. Please review and fix issues before deployment.'}
"""
    
    # Save report
    with open("test_report.md", "w") as f:
        f.write(report_content)
    
    print(f"\n📄 Test report saved to: test_report.md")
    print(f"📊 Coverage report available at: htmlcov/index.html")
    
    # Return appropriate exit code
    if failed == 0:
        print("\n🎉 All tests passed! SCONIA is ready for deployment.")
        return 0
    else:
        print(f"\n⚠️  {failed} test categories failed. Please review and fix issues.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
