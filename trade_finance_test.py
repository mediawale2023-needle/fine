import requests
import sys
import json
from datetime import datetime

class TradeFinanceAPITester:
    def __init__(self, base_url="https://tradecor.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.exporter_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.deal_id = None
        self.finance_request_id = None

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
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code} - {response.text[:200]}")
                return None

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return None

    def setup_auth(self):
        """Setup authentication tokens"""
        print("🔐 Setting up authentication...")
        
        # Admin login
        admin_data = {"email": "admin@tradenexus.com", "password": "admin123"}
        admin_result = self.run_test("Admin Login", "POST", "auth/login", 200, admin_data)
        if admin_result and 'access_token' in admin_result:
            self.admin_token = admin_result['access_token']
        
        # Exporter login
        exporter_data = {"email": "agrimax@export.in", "password": "exporter123"}
        exporter_result = self.run_test("Exporter Login", "POST", "auth/login", 200, exporter_data)
        if exporter_result and 'access_token' in exporter_result:
            self.exporter_token = exporter_result['access_token']

        return self.admin_token and self.exporter_token

    def test_subscription_endpoints(self):
        """Test subscription management endpoints"""
        if not self.exporter_token:
            return
        
        print("\n💳 Testing Subscription Endpoints...")
        headers = {'Authorization': f'Bearer {self.exporter_token}'}
        
        # Test get subscription status
        result = self.run_test("GET /api/subscription/me", "GET", "subscription/me", 200, headers=headers)
        if result:
            print(f"   Current plan: {result.get('plan', 'Unknown')}")
            print(f"   Status: {result.get('status', 'Unknown')}")
            print(f"   Valid: {result.get('is_valid', False)}")
        
        # Test subscription upgrade
        upgrade_data = {"plan": "Premium"}
        upgrade_result = self.run_test("POST /api/subscription/upgrade", "POST", "subscription/upgrade", 200, upgrade_data, headers)
        if upgrade_result:
            print(f"   Upgraded to Premium plan")

    def test_finance_request_flow(self):
        """Test complete finance request flow"""
        if not self.exporter_token or not self.admin_token:
            return
        
        print("\n💰 Testing Finance Request Flow...")
        
        # First, create a deal for the exporter
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        exporter_headers = {'Authorization': f'Bearer {self.exporter_token}'}
        
        # Get exporter profile ID
        profile_result = self.run_test("Get Exporter Profile", "GET", "exporter-profiles/me", 200, headers=exporter_headers)
        if not profile_result:
            print("❌ Cannot get exporter profile")
            return
        
        exporter_profile_id = profile_result.get('id')
        
        # Get an opportunity to create deal
        opps_result = self.run_test("Get Opportunities", "GET", "opportunities", 200, headers=admin_headers)
        if not opps_result or len(opps_result) == 0:
            print("❌ No opportunities available")
            return
        
        opportunity_id = opps_result[0]['id']
        
        # Create a deal
        deal_data = {
            "opportunity_id": opportunity_id,
            "exporter_id": exporter_profile_id
        }
        deal_result = self.run_test("Create Deal", "POST", "deals", 201, deal_data, admin_headers)
        if not deal_result:
            print("❌ Cannot create deal")
            return
        
        self.deal_id = deal_result['id']
        print(f"   Created deal: {self.deal_id}")
        
        # Now test finance request creation
        finance_data = {
            "deal_id": self.deal_id,
            "purchase_order_value": 5000000,
            "financing_amount_requested": 3500000,
            "production_time_days": 45,
            "shipment_date": "2025-03-15",
            "buyer_country": "Nigeria",
            "payment_method": "LC",
            "exporter_bank_details": "HDFC Bank, Acc: 123456789, IFSC: HDFC0001234",
            "past_export_turnover": 50000000
        }
        
        finance_result = self.run_test("Create Finance Request", "POST", "finance-requests", 201, finance_data, exporter_headers)
        if finance_result:
            self.finance_request_id = finance_result['id']
            print(f"   Created finance request: {self.finance_request_id}")
            print(f"   Risk score: {finance_result.get('risk_score')} ({finance_result.get('risk_category')})")

    def test_admin_finance_management(self):
        """Test admin finance request management"""
        if not self.admin_token or not self.finance_request_id:
            return
        
        print("\n🏛️ Testing Admin Finance Management...")
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test get all finance requests
        self.run_test("GET /api/finance-requests", "GET", "finance-requests", 200, headers=admin_headers)
        
        # Test status update
        status_result = self.run_test("Update Finance Status", "PUT", f"finance-requests/{self.finance_request_id}/status?status=sent_to_nbfc", 200, headers=admin_headers)
        
        # Test NBFC offer recording
        nbfc_data = {
            "nbfc_partner": "HDFC Bank",
            "offer_amount": 3200000,
            "interest_rate": 12.5,
            "admin_notes": "Approved with standard terms"
        }
        nbfc_result = self.run_test("Record NBFC Offer", "PUT", f"finance-requests/{self.finance_request_id}/nbfc-offer", 200, nbfc_data, admin_headers)

    def test_exporter_offer_acceptance(self):
        """Test exporter accepting NBFC offer"""
        if not self.exporter_token or not self.finance_request_id:
            return
        
        print("\n✅ Testing Offer Acceptance...")
        exporter_headers = {'Authorization': f'Bearer {self.exporter_token}'}
        
        # Test accept offer
        accept_result = self.run_test("Accept NBFC Offer", "POST", f"finance-requests/{self.finance_request_id}/accept", 200, headers=exporter_headers)
        if accept_result:
            print(f"   Financing commission: ₹{accept_result.get('financing_commission', 0):,.0f}")

    def test_revenue_endpoints(self):
        """Test revenue tracking endpoints"""
        if not self.admin_token:
            return
        
        print("\n📊 Testing Revenue Endpoints...")
        admin_headers = {'Authorization': f'Bearer {self.admin_token}'}
        
        # Test revenue summary
        summary_result = self.run_test("GET /api/revenue/summary", "GET", "revenue/summary", 200, headers=admin_headers)
        if summary_result:
            print(f"   Total revenue: ₹{summary_result.get('total_revenue', 0):,.0f}")
            print(f"   Subscription revenue: ₹{summary_result.get('subscription_revenue', 0):,.0f}")
            print(f"   Deal commission: ₹{summary_result.get('deal_commission_revenue', 0):,.0f}")
            print(f"   Financing commission: ₹{summary_result.get('financing_commission_revenue', 0):,.0f}")
        
        # Test revenue records
        self.run_test("GET /api/revenue", "GET", "revenue", 200, headers=admin_headers)

    def test_risk_scoring(self):
        """Test risk scoring engine"""
        if not self.exporter_token or not self.deal_id:
            return
        
        print("\n⚠️ Testing Risk Scoring Engine...")
        exporter_headers = {'Authorization': f'Bearer {self.exporter_token}'}
        
        # Test risk score calculation
        risk_data = {
            "years_in_business": 8,
            "export_turnover": 50000000,
            "past_shipments": 75
        }
        
        risk_result = self.run_test("Calculate Risk Score", "POST", f"risk-scores/calculate?deal_id={self.deal_id}", 200, risk_data, exporter_headers)
        if risk_result:
            print(f"   Risk score: {risk_result.get('risk_score')}")
            print(f"   Risk category: {risk_result.get('risk_category')}")
            print(f"   Recommended financing: {risk_result.get('recommended_financing_ratio', 0)*100:.0f}%")

    def run_all_tests(self):
        """Run complete trade finance test suite"""
        print("🚀 Starting Trade Finance Engine Test Suite")
        print("=" * 60)

        # Setup authentication
        if not self.setup_auth():
            print("❌ Authentication setup failed")
            return 1

        # Test subscription management
        self.test_subscription_endpoints()
        
        # Test finance request flow
        self.test_finance_request_flow()
        
        # Test admin finance management
        self.test_admin_finance_management()
        
        # Test exporter offer acceptance
        self.test_exporter_offer_acceptance()
        
        # Test revenue tracking
        self.test_revenue_endpoints()
        
        # Test risk scoring
        self.test_risk_scoring()

        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Trade Finance Test Results: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All trade finance tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    tester = TradeFinanceAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())