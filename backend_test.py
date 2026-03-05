import requests
import sys
import json
from datetime import datetime

class TradeNexusAPITester:
    def __init__(self, base_url="https://tradecor.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.exporter_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.log_test(name, True)
                try:
                    return response.json() if response.content else {}
                except:
                    return {}
            else:
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}")
                return None

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return None

    def test_health_check(self):
        """Test basic health endpoints"""
        print("\n🔍 Testing Health Endpoints...")
        self.run_test("Health Check", "GET", "", 200)
        self.run_test("API Root", "GET", "health", 200)

    def test_seed_data(self):
        """Seed demo data"""
        print("\n🌱 Seeding Demo Data...")
        result = self.run_test("Seed Demo Data", "POST", "seed", 200)
        return result is not None

    def test_admin_login(self):
        """Test admin login"""
        print("\n🔐 Testing Admin Authentication...")
        data = {
            "email": "admin@tradenexus.com",
            "password": "admin123"
        }
        result = self.run_test("Admin Login", "POST", "auth/login", 200, data)
        if result and 'access_token' in result:
            self.admin_token = result['access_token']
            return True
        return False

    def test_exporter_login(self):
        """Test exporter login"""
        print("\n🔐 Testing Exporter Authentication...")
        data = {
            "email": "agrimax@export.in",
            "password": "exporter123"
        }
        result = self.run_test("Exporter Login", "POST", "auth/login", 200, data)
        if result and 'access_token' in result:
            self.exporter_token = result['access_token']
            return True
        return False

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        if not self.admin_token:
            print("❌ No admin token available")
            return

        print("\n👑 Testing Admin Endpoints...")
        headers = {'Authorization': f'Bearer {self.admin_token}'}

        # Test stats
        self.run_test("Get Stats", "GET", "stats", 200, headers=headers)
        
        # Test opportunities
        self.run_test("Get Opportunities", "GET", "opportunities", 200, headers=headers)
        
        # Test create opportunity
        opp_data = {
            "sector": "Agriculture",
            "source_country": "Nigeria",
            "region": "Africa",
            "product_name": "Test Rice",
            "quantity": "1000 MT",
            "delivery_timeline": "Q1 2025",
            "compliance_requirements": ["FSSAI"],
            "engagement_mode": "Introduction-only"
        }
        result = self.run_test("Create Opportunity", "POST", "opportunities", 201, opp_data, headers)
        
        if result and 'id' in result:
            opp_id = result['id']
            
            # Test opportunity detail
            self.run_test("Get Opportunity Detail", "GET", f"opportunities/{opp_id}", 200, headers=headers)
            
            # Test AI matchmaking
            self.run_test("AI Matchmaking", "POST", f"opportunities/{opp_id}/match", 200, headers=headers)
            
            # Test status update
            self.run_test("Update Status", "PUT", f"opportunities/{opp_id}/status?status=Matched", 200, headers=headers)

        # Test AI parsing
        parse_data = {
            "raw_text": "We need 500 MT of premium basmati rice from India for delivery to Nigeria by March 2025. Must have FSSAI certification."
        }
        self.run_test("AI Parse Document", "POST", "opportunities/parse", 200, parse_data, headers)

        # Test interests and deals
        self.run_test("Get Interests", "GET", "interests", 200, headers=headers)
        self.run_test("Get Deals", "GET", "deals", 200, headers=headers)

    def test_exporter_endpoints(self):
        """Test exporter endpoints"""
        if not self.exporter_token:
            print("❌ No exporter token available")
            return

        print("\n🏭 Testing Exporter Endpoints...")
        headers = {'Authorization': f'Bearer {self.exporter_token}'}

        # Test profile endpoints
        profile_data = {
            "sectors": ["Agriculture"],
            "products": ["Basmati Rice", "Wheat"],
            "capacity": "5000 MT/year",
            "certifications": ["FSSAI", "ISO 22000"],
            "country_experience": ["Nigeria", "UAE"]
        }
        
        # Try to get existing profile first
        existing_profile = self.run_test("Get My Profile", "GET", "exporter-profiles/me", 200, headers=headers)
        
        if not existing_profile:
            # Create profile if doesn't exist
            self.run_test("Create Profile", "POST", "exporter-profiles", 201, profile_data, headers)
        else:
            # Update existing profile
            self.run_test("Update Profile", "PUT", "exporter-profiles/me", 200, profile_data, headers)

        # Test opportunities (exporter view)
        self.run_test("Get Opportunities (Exporter)", "GET", "opportunities", 200, headers=headers)
        
        # Test my interests
        self.run_test("Get My Interests", "GET", "my-interests", 200, headers=headers)
        
        # Test my deals
        self.run_test("Get My Deals", "GET", "deals", 200, headers=headers)

    def test_ai_integration(self):
        """Test AI integration specifically"""
        if not self.admin_token:
            return

        print("\n🤖 Testing AI Integration...")
        headers = {'Authorization': f'Bearer {self.admin_token}'}

        # Test AI parsing with different types of content
        test_cases = [
            {
                "name": "Agriculture Brief",
                "text": "Embassy of Nigeria requires 2000 MT of premium basmati rice for Q1 2025 delivery. Must have FSSAI and ISO 22000 certifications. HS Code: 1006.30"
            },
            {
                "name": "Pharma Brief", 
                "text": "German pharmaceutical company needs 100 MT of Paracetamol API with WHO-GMP certification for Q2 2025 delivery to Hamburg."
            },
            {
                "name": "Marine Brief",
                "text": "UAE importer seeking 500 MT frozen shrimp with HACCP and Halal certification for February 2025 delivery to Dubai."
            }
        ]

        for case in test_cases:
            parse_data = {"raw_text": case["text"]}
            result = self.run_test(f"AI Parse - {case['name']}", "POST", "opportunities/parse", 200, parse_data, headers)
            
            if result:
                # Verify parsed data has required fields
                required_fields = ["sector", "source_country", "product_name", "quantity"]
                missing_fields = [f for f in required_fields if not result.get(f)]
                if missing_fields:
                    self.log_test(f"AI Parse Validation - {case['name']}", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test(f"AI Parse Validation - {case['name']}", True)

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting TradeNexus API Test Suite")
        print("=" * 50)

        # Basic health checks
        self.test_health_check()
        
        # Seed data
        if not self.test_seed_data():
            print("⚠️  Demo data seeding failed, continuing with existing data...")

        # Authentication tests
        admin_login_success = self.test_admin_login()
        exporter_login_success = self.test_exporter_login()

        if not admin_login_success:
            print("❌ Admin login failed - cannot test admin endpoints")
        else:
            self.test_admin_endpoints()
            self.test_ai_integration()

        if not exporter_login_success:
            print("❌ Exporter login failed - cannot test exporter endpoints")
        else:
            self.test_exporter_endpoints()

        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = TradeNexusAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())