#!/usr/bin/env python3
"""
API Test Suite for News User API
Tests all endpoints and generates a report
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE = "http://localhost:5001"  # Change to server URL for production
ADMIN_PASSWORD = "didadi"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

class APITester:
    def __init__(self, base_url, admin_password):
        self.base_url = base_url
        self.admin_password = admin_password
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results = []
        self.test_user_token = None
        self.test_user_id = None
        
    def log(self, message, color=Colors.RESET):
        print(f"{color}{message}{Colors.RESET}")
        
    def test(self, name, method, endpoint, headers=None, data=None, expected_status=200):
        """Execute a test and record result"""
        url = f"{self.base_url}{endpoint}"
        
        self.log(f"\n{'='*70}", Colors.BLUE)
        self.log(f"TEST: {name}", Colors.BLUE)
        self.log(f"{'='*70}", Colors.BLUE)
        self.log(f"Method: {method} {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check status code
            status_match = response.status_code == expected_status
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                response_text = json.dumps(response_data, indent=2)
            except:
                response_text = response.text
            
            self.log(f"Status: {response.status_code} (expected {expected_status})")
            self.log(f"Response:\n{response_text}")
            
            if status_match:
                self.log(f"✅ PASSED", Colors.GREEN)
                self.tests_passed += 1
                self.test_results.append({
                    'name': name,
                    'status': 'PASSED',
                    'endpoint': endpoint,
                    'response_code': response.status_code
                })
                return response_data if 'response_data' in locals() else None
            else:
                self.log(f"❌ FAILED - Status code mismatch", Colors.RED)
                self.tests_failed += 1
                self.test_results.append({
                    'name': name,
                    'status': 'FAILED',
                    'endpoint': endpoint,
                    'response_code': response.status_code,
                    'error': f"Expected {expected_status}, got {response.status_code}"
                })
                return None
                
        except Exception as e:
            self.log(f"❌ FAILED - Exception: {str(e)}", Colors.RED)
            self.tests_failed += 1
            self.test_results.append({
                'name': name,
                'status': 'FAILED',
                'endpoint': endpoint,
                'error': str(e)
            })
            return None
    
    def run_all_tests(self):
        """Run complete test suite"""
        self.log("\n" + "="*70, Colors.YELLOW)
        self.log("NEWS API TEST SUITE", Colors.YELLOW)
        self.log("="*70 + "\n", Colors.YELLOW)
        self.log(f"Target: {self.base_url}")
        self.log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # ====================================================================
        # PUBLIC ENDPOINTS
        # ====================================================================
        
        self.log("\n" + "🔓 PUBLIC ENDPOINTS", Colors.YELLOW)
        
        # Test 1: Health Check
        self.test(
            "Health Check",
            "GET",
            "/api/health"
        )
        
        # Test 2: User Registration
        test_email = f"test_{int(time.time())}@example.com"
        result = self.test(
            "User Registration",
            "POST",
            "/api/user/register",
            data={
                "email": test_email,
                "name": "Test User",
                "reading_style": "enjoy"
            }
        )
        
        if result:
            self.test_user_token = result.get('bootstrap_token')
            self.test_user_id = result.get('user_id')
        
        # Test 3: Token Recovery
        if test_email:
            self.test(
                "Token Recovery",
                "POST",
                "/api/user/token",
                data={"email": test_email}
            )
        
        # Test 4: Stats Sync
        if self.test_user_token:
            self.test(
                "Stats Sync",
                "POST",
                "/api/user/sync-stats",
                headers={"X-User-Token": self.test_user_token},
                data={
                    "stats": {
                        "word_test_123": {
                            "completed": True,
                            "timestamp": int(time.time())
                        }
                    }
                }
            )
        
        # ====================================================================
        # ADMIN ENDPOINTS - USER SUBSCRIPTIONS
        # ====================================================================
        
        self.log("\n" + "🔒 ADMIN ENDPOINTS - USER SUBSCRIPTIONS", Colors.YELLOW)
        
        admin_headers = {"X-Admin-Password": self.admin_password}
        
        # Test 5: Get Subscriptions
        self.test(
            "Get Subscriptions List",
            "GET",
            "/api/admin/subscriptions",
            headers=admin_headers
        )
        
        # Test 6: Export Subscriptions
        self.test(
            "Export Subscriptions",
            "GET",
            "/api/admin/subscriptions/export",
            headers=admin_headers
        )
        
        # ====================================================================
        # ADMIN ENDPOINTS - ADMIN PANEL DATA
        # ====================================================================
        
        self.log("\n" + "🔒 ADMIN ENDPOINTS - ADMIN PANEL DATA", Colors.YELLOW)
        
        # Test 7: Get Feeds
        self.test(
            "Get Feeds",
            "GET",
            "/api/admin/feeds",
            headers=admin_headers
        )
        
        # Test 8: Get Categories
        self.test(
            "Get Categories",
            "GET",
            "/api/admin/categories",
            headers=admin_headers
        )
        
        # Test 9: Get Articles
        self.test(
            "Get Articles (with filters)",
            "GET",
            "/api/admin/articles?limit=5&offset=0",
            headers=admin_headers
        )
        
        # Test 10: Get API Keys
        self.test(
            "Get API Keys",
            "GET",
            "/api/admin/apikeys",
            headers=admin_headers
        )
        
        # Test 11: Get Stats
        self.test(
            "Get System Statistics",
            "GET",
            "/api/admin/stats",
            headers=admin_headers
        )
        
        # Test 12: Get Article Detail (use first article if available)
        # We'll skip this if no articles exist
        articles_result = self.test(
            "Get Articles for Detail Test",
            "GET",
            "/api/admin/articles?limit=1",
            headers=admin_headers
        )
        
        if articles_result and articles_result.get('articles'):
            article_id = articles_result['articles'][0]['id']
            self.test(
                "Get Article Detail",
                "GET",
                f"/api/admin/article/{article_id}",
                headers=admin_headers
            )
        
        # ====================================================================
        # ADMIN ENDPOINTS - CRON MANAGEMENT
        # ====================================================================
        
        self.log("\n" + "🔒 ADMIN ENDPOINTS - CRON MANAGEMENT", Colors.YELLOW)
        
        # Test 13: Get Cron Status
        self.test(
            "Get Cron Status",
            "GET",
            "/api/cron/status",
            headers=admin_headers
        )
        
        # Test 14: Get Cron Logs
        self.test(
            "Get Cron Logs List",
            "GET",
            "/api/cron/logs",
            headers=admin_headers
        )
        
        # Test 15: Enable Cron (dry run - we won't actually change settings)
        # Skip this in automated tests to avoid changing production settings
        self.log("\n⏭️  SKIPPED: Cron Enable/Disable (would modify production settings)", Colors.YELLOW)
        
        # ====================================================================
        # GENERATE REPORT
        # ====================================================================
        
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        self.log("\n\n" + "="*70, Colors.YELLOW)
        self.log("TEST REPORT", Colors.YELLOW)
        self.log("="*70, Colors.YELLOW)
        
        total_tests = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total_tests * 100) if total_tests > 0 else 0
        
        self.log(f"\nTotal Tests: {total_tests}")
        self.log(f"Passed: {self.tests_passed}", Colors.GREEN)
        self.log(f"Failed: {self.tests_failed}", Colors.RED)
        self.log(f"Pass Rate: {pass_rate:.1f}%", Colors.GREEN if pass_rate == 100 else Colors.YELLOW)
        
        if self.tests_failed > 0:
            self.log("\n❌ FAILED TESTS:", Colors.RED)
            for result in self.test_results:
                if result['status'] == 'FAILED':
                    self.log(f"  - {result['name']}: {result.get('error', 'Unknown error')}", Colors.RED)
        
        self.log("\n" + "="*70, Colors.YELLOW)
        self.log(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.YELLOW)
        self.log("="*70 + "\n", Colors.YELLOW)
        
        # Write report to file
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'api_base': self.base_url,
                'total_tests': total_tests,
                'passed': self.tests_passed,
                'failed': self.tests_failed,
                'pass_rate': pass_rate,
                'results': self.test_results
            }, f, indent=2)
        
        self.log(f"📝 Report saved to: {report_file}", Colors.BLUE)
        
        return self.tests_failed == 0


if __name__ == '__main__':
    import sys
    
    # Allow custom URL and password from command line
    api_url = sys.argv[1] if len(sys.argv) > 1 else API_BASE
    admin_pwd = sys.argv[2] if len(sys.argv) > 2 else ADMIN_PASSWORD
    
    print(f"\n🧪 Testing API at: {api_url}")
    
    tester = APITester(api_url, admin_pwd)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
