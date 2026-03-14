#!/usr/bin/env python
"""
Comprehensive Test Runner for Thredion Engine
Executes all test suites with coverage reporting and validation
"""

import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime


class TestRunner:
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = datetime.now()
    
    def run_test_suite(self, test_file, description):
        """Run a specific test file and capture results."""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"File: {test_file}")
        print('='*60)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short", "-x"],
                cwd="c:\\Users\\iters\\Downloads\\thredion\\thredion-engine",
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per suite
            )
            
            self.results[test_file] = {
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'passed': result.returncode == 0,
            }
            
            print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            if result.returncode == 0:
                self.passed += 1
                print(f"✅ {description} - PASSED")
            else:
                self.failed += 1
                print(f"❌ {description} - FAILED")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"⏱️  {description} - TIMEOUT (>5 min)")
            self.failed += 1
            return False
        except Exception as e:
            print(f"💥 {description} - ERROR: {e}")
            self.failed += 1
            return False
    
    def run_all_tests(self):
        """Run all test suites."""
        test_suites = [
            ("tests/test_transcriber.py", "Transcriber Unit Tests"),
            ("tests/test_llm_processor.py", "LLM Processor Unit Tests"),
            ("tests/test_pipeline_integration.py", "Pipeline Integration Tests"),
            ("tests/test_api_endpoints.py", "API Endpoint Tests"),
            ("tests/test_worker.py", "Worker Integration Tests"),
            ("tests/test_e2e.py", "End-to-End Workflow Tests"),
            ("tests/test_schema_validation.py", "Database Schema Tests"),
            ("tests/test_performance.py", "Performance & Load Tests"),
        ]
        
        print("\n" + "🚀 THREDION ENGINE - COMPREHENSIVE TEST SUITE")
        print("="*60)
        print(f"Start Time: {self.start_time}")
        print(f"Total Test Suites: {len(test_suites)}")
        
        for test_file, description in test_suites:
            self.run_test_suite(test_file, description)
        
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Suites: {len(self.results)}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏱️  Total Time: {elapsed:.2f}s")
        print("="*60)
        
        if self.failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("Ready to push to main branch.")
            return 0
        else:
            print(f"\n⚠️  {self.failed} test suite(s) failed.")
            print("Fix failures before pushing to main.")
            return 1
    
    def generate_report(self):
        """Generate JSON report for CI/CD integration."""
        report = {
            'timestamp': self.start_time.isoformat(),
            'total_suites': len(self.results),
            'passed': self.passed,
            'failed': self.failed,
            'skipped': self.skipped,
            'results': self.results,
        }
        
        report_path = Path("test_results.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_path}")


if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
    exit_code = runner.print_summary()
    runner.generate_report()
    sys.exit(exit_code)
