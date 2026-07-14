#!/usr/bin/env python3
"""
Quick test script for SCONIA.
Tests all major components and provides a health report.
"""
import requests
import json
import time
import sys
from typing import Dict, Any, List, Tuple


class SCONIATester:
    """Quick tester for SCONIA components."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Tuple[str, bool, str]] = []
    
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Dict[Any, Any] = None, headers: Dict[str, str] = None,
                     expected_status: int = 200) -> bool:
        """Test a single endpoint."""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, timeout=10)
            else:
                self.results.append((name, False, f"Unsupported method: {method}"))
                return False
            
            if response.status_code == expected_status:
                self.results.append((name, True, f"✅ Status {response.status_code}"))
                return True
            else:
                self.results.append((name, False, f"❌ Status {response.status_code}, expected {expected_status}"))
                return False
                
        except requests.exceptions.ConnectionError:
            self.results.append((name, False, "❌ Connection refused - service not running"))
            return False
        except requests.exceptions.Timeout:
            self.results.append((name, False, "❌ Request timeout"))
            return False
        except Exception as e:
            self.results.append((name, False, f"❌ Error: {str(e)}"))
            return False
    
    def test_websocket_basic(self) -> bool:
        """Test WebSocket connection (basic check)."""
        try:
            # We'll just test if the WebSocket endpoint is reachable
            # Full WebSocket testing requires a WebSocket client
            response = requests.get(f"{self.base_url}/api/v1/websocket/health", timeout=5)
            if response.status_code == 200:
                self.results.append(("WebSocket Health", True, "✅ WebSocket service healthy"))
                return True
            else:
                self.results.append(("WebSocket Health", False, f"❌ Status {response.status_code}"))
                return False
        except Exception as e:
            self.results.append(("WebSocket Health", False, f"❌ Error: {str(e)}"))
            return False
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting SCONIA Quick Test Suite")
        print("=" * 50)
        
        # 1. Basic Health Check
        print("\n📋 Testing Basic Health...")
        self.test_endpoint("Health Check", "GET", "/health")
        
        # 2. API Documentation
        print("\n📚 Testing API Documentation...")
        self.test_endpoint("API Docs", "GET", "/docs", expected_status=200)
        
        # 3. Chat API
        print("\n💬 Testing Chat API...")
        chat_data = {
            "query": "What is the Supreme Court of Nigeria?",
            "session_id": "test-session"
        }
        self.test_endpoint("Chat Query", "POST", "/api/v1/chat/", data=chat_data)
        
        # 4. Search APIs
        print("\n🔍 Testing Search APIs...")
        self.test_endpoint("Semantic Search", "GET", "/api/v1/search/semantic?query=rights&limit=3")
        self.test_endpoint("Search Suggestions", "GET", "/api/v1/search/suggestions?query=const")
        self.test_endpoint("Search Stats", "GET", "/api/v1/search/stats")
        
        # 5. Legal Content APIs
        print("\n⚖️ Testing Legal Content APIs...")
        self.test_endpoint("Judges API", "GET", "/api/v1/judges/")
        self.test_endpoint("Constitution API", "GET", "/api/v1/constitution/")
        self.test_endpoint("Cases API", "GET", "/api/v1/cases/")
        self.test_endpoint("Procedures API", "GET", "/api/v1/procedures/")
        self.test_endpoint("Fees API", "GET", "/api/v1/fees/")
        
        # 6. Advanced Search
        print("\n🔍 Testing Advanced Search...")
        self.test_endpoint("Faceted Search", "GET", "/api/v1/search/faceted?query=rights")
        self.test_endpoint("Search Filters", "GET", "/api/v1/search/filters")
        
        # 7. WebSocket
        print("\n🌐 Testing WebSocket...")
        self.test_websocket_basic()
        
        # 8. Monitoring
        print("\n📊 Testing Monitoring...")
        self.test_endpoint("System Health", "GET", "/api/v1/monitoring/health")
        
        # 9. Specific Legal Content
        print("\n📖 Testing Specific Content...")
        self.test_endpoint("Chief Justice", "GET", "/api/v1/judges/chief-justice", expected_status=200)
        self.test_endpoint("Constitution Chapters", "GET", "/api/v1/constitution/chapters")
        self.test_endpoint("Fundamental Rights", "GET", "/api/v1/constitution/fundamental-rights")
        self.test_endpoint("Recent Cases", "GET", "/api/v1/cases/recent/judgments")
        self.test_endpoint("Fee Service Types", "GET", "/api/v1/fees/service-types")
        
        # 10. Performance Test
        print("\n⚡ Testing Performance...")
        start_time = time.time()
        success = self.test_endpoint("Performance Test", "GET", "/health")
        response_time = time.time() - start_time
        
        if success and response_time < 1.0:
            self.results.append(("Response Time", True, f"✅ {response_time:.3f}s"))
        else:
            self.results.append(("Response Time", False, f"❌ {response_time:.3f}s (slow)"))
    
    def print_results(self):
        """Print test results."""
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS")
        print("=" * 50)
        
        passed = 0
        failed = 0
        
        for test_name, success, message in self.results:
            status = "PASS" if success else "FAIL"
            print(f"{test_name:<25} {status:<6} {message}")
            
            if success:
                passed += 1
            else:
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"📈 SUMMARY: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! SCONIA is ready to go!")
            return True
        else:
            print(f"⚠️  {failed} tests failed. Check the issues above.")
            return False
    
    def get_system_info(self):
        """Get system information."""
        print("\n🔧 SYSTEM INFORMATION")
        print("=" * 50)
        
        try:
            # Get system health
            response = requests.get(f"{self.base_url}/api/v1/monitoring/health", timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                print(f"System Status: {health_data.get('status', 'unknown')}")
                print(f"Active Requests: {health_data.get('active_requests', 'unknown')}")
                print(f"Uptime: {health_data.get('uptime_seconds', 0):.0f} seconds")
            
            # Get API stats
            response = requests.get(f"{self.base_url}/api/v1/search/stats", timeout=5)
            if response.status_code == 200:
                stats_data = response.json()
                print(f"Vector Database: {stats_data.get('status', 'unknown')}")
        
        except Exception as e:
            print(f"Could not retrieve system info: {e}")


def main():
    """Main test function."""
    print("SCONIA Quick Test Suite")
    print("Testing all major components...")
    
    # Check if services are likely running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print("❌ SCONIA API is not responding correctly.")
            print("💡 Make sure to run: docker-compose up -d")
            return 1
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to SCONIA API at http://localhost:8000")
        print("💡 Make sure to run: docker-compose up -d")
        return 1
    
    # Run tests
    tester = SCONIATester()
    tester.run_all_tests()
    tester.get_system_info()
    success = tester.print_results()
    
    if success:
        print("\n🚀 NEXT STEPS:")
        print("1. ✅ All systems operational")
        print("2. 🌐 Test WebSocket: wscat -c ws://localhost:8000/api/v1/chat/ws/test")
        print("3. 📱 Ready for frontend development (Phase 4)")
        print("4. 📖 View API docs: http://localhost:8000/docs")
        return 0
    else:
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Check services: docker-compose ps")
        print("2. View logs: docker-compose logs api")
        print("3. Restart: docker-compose restart")
        print("4. Initialize data: docker-compose exec api python scripts/init_data.py")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
