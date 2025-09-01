#!/usr/bin/env python3
"""
Symphony Test Runner

Comprehensive test runner for Symphony onboarding system with
coverage reporting and CI/CD integration support.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "libs" / "symphony-core" / "src"))
sys.path.insert(0, str(project_root / "libs" / "symphony-integrations" / "src"))
sys.path.insert(0, str(project_root / "apps" / "symphony-cli" / "src"))


def run_tests(
    test_pattern: str = "test_*.py",
    coverage: bool = False,
    verbose: bool = False,
    html_coverage: bool = False,
    fast_fail: bool = False
):
    """Run test suite with optional coverage reporting"""
    
    # Base pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test directory
    test_dir = Path(__file__).parent
    cmd.append(str(test_dir))
    
    # Add pattern if specified
    if test_pattern != "test_*.py":
        cmd.extend(["-k", test_pattern])
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("--tb=short")
    
    # Add fast fail
    if fast_fail:
        cmd.append("-x")
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=symphony_core.onboarding",
            "--cov=symphony_core.auth",
            "--cov-report=term-missing"
        ])
        
        if html_coverage:
            cmd.extend(["--cov-report=html:htmlcov"])
    
    # Add additional pytest options
    cmd.extend([
        "--disable-warnings",
        "--color=yes"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run tests
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode


def install_test_dependencies():
    """Install required test dependencies"""
    
    dependencies = [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0"
    ]
    
    print("Installing test dependencies...")
    
    for dep in dependencies:
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", dep
            ], check=True, capture_output=True)
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {dep}")
            return False
    
    return True


def check_environment():
    """Check test environment setup"""
    
    print("Checking test environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher required")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    
    # Check required modules
    required_modules = ["pytest", "asyncio"]
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} available")
        except ImportError:
            print(f"❌ {module} not available")
            return False
    
    # Check project structure
    project_paths = [
        "libs/symphony-core/src/symphony_core",
        "libs/symphony-integrations/src/symphony_integrations",
        "apps/symphony-cli/src/symphony_cli"
    ]
    
    for path in project_paths:
        full_path = project_root / path
        if full_path.exists():
            print(f"✅ {path}")
        else:
            print(f"⚠️  {path} not found")
    
    return True


def generate_test_report():
    """Generate comprehensive test report"""
    
    print("\nGenerating test report...")
    
    # Run tests with coverage and JUnit XML output
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent),
        "--cov=symphony_core.onboarding",
        "--cov=symphony_core.auth", 
        "--cov-report=html:test_reports/coverage",
        "--cov-report=xml:test_reports/coverage.xml",
        "--junitxml=test_reports/junit.xml",
        "--tb=short",
        "-v"
    ]
    
    # Create reports directory
    reports_dir = project_root / "test_reports"
    reports_dir.mkdir(exist_ok=True)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Test report generated successfully")
        print(f"📄 Reports available in: {reports_dir}")
        print(f"   - Coverage HTML: {reports_dir}/coverage/index.html")
        print(f"   - Coverage XML: {reports_dir}/coverage.xml")
        print(f"   - JUnit XML: {reports_dir}/junit.xml")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test report generation failed: {e}")
        return False


def run_integration_tests():
    """Run integration tests specifically"""
    
    print("Running integration tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_onboarding_workflow.py::TestIntegration"),
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Integration tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Integration tests failed: {e}")
        return False


def run_unit_tests():
    """Run unit tests specifically"""
    
    print("Running unit tests...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(Path(__file__).parent / "test_onboarding_workflow.py"),
        "-k", "not TestIntegration",
        "-v",
        "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("✅ Unit tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Unit tests failed: {e}")
        return False


def main():
    """Main test runner entry point"""
    
    parser = argparse.ArgumentParser(
        description="Symphony Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                           # Run all tests
  python run_tests.py --coverage               # Run with coverage
  python run_tests.py --pattern "test_auth*"   # Run specific tests
  python run_tests.py --install-deps           # Install dependencies
  python run_tests.py --check-env              # Check environment
  python run_tests.py --report                 # Generate full report
  python run_tests.py --unit                   # Run unit tests only
  python run_tests.py --integration            # Run integration tests only
        """
    )
    
    parser.add_argument(
        "--pattern", "-p",
        default="test_*.py",
        help="Test pattern to match (default: test_*.py)"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage report"
    )
    
    parser.add_argument(
        "--html-coverage",
        action="store_true",
        help="Generate HTML coverage report"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--fast-fail", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies"
    )
    
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Check test environment"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate comprehensive test report"
    )
    
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only"
    )
    
    parser.add_argument(
        "--integration",
        action="store_true",
        help="Run integration tests only"
    )
    
    args = parser.parse_args()
    
    # Handle special commands
    if args.install_deps:
        if not install_test_dependencies():
            return 1
        return 0
    
    if args.check_env:
        if not check_environment():
            return 1
        return 0
    
    if args.report:
        if not generate_test_report():
            return 1
        return 0
    
    if args.unit:
        if not run_unit_tests():
            return 1
        return 0
    
    if args.integration:
        if not run_integration_tests():
            return 1
        return 0
    
    # Run normal tests
    return run_tests(
        test_pattern=args.pattern,
        coverage=args.coverage,
        verbose=args.verbose,
        html_coverage=args.html_coverage,
        fast_fail=args.fast_fail
    )


if __name__ == "__main__":
    sys.exit(main())