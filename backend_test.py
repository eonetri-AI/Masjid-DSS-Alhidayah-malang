#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class MosqueAPITester:
    def __init__(self, base_url="https://prayer-display-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
            self.failed_tests.append({"test": name, "error": details})
        
        self.test_results.append({
            "test_name": name,
            "status": "PASSED" if success else "FAILED",
            "details": details
        })

    def test_api_endpoint(self, name, method, endpoint, expected_status=200, data=None):
        """Test a single API endpoint"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                try:
                    error_data = response.json()
                    details += f", Response: {error_data}"
                except:
                    details += f", Response: {response.text[:200]}"
            
            self.log_test(name, success, details)
            return success, response.json() if success and response.content else {}
            
        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_prayer_times_api(self):
        """Test prayer times calculation"""
        print("\n🕌 Testing Prayer Times API...")
        success, data = self.test_api_endpoint(
            "Get Prayer Times", 
            "GET", 
            "prayer-times"
        )
        
        if success:
            # Validate response structure
            required_fields = ['fajr', 'imsya', 'syuruq', 'dhuhr', 'asr', 'maghrib', 'isha', 
                             'gregorian_date', 'hijri_date', 'next_prayer', 'time_until_next', 'iqomah_times']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                self.log_test("Prayer Times Response Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Prayer Times Response Structure", True, "All required fields present")
                
                # Validate iqomah times structure
                if 'iqomah_times' in data and isinstance(data['iqomah_times'], dict):
                    expected_prayers = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
                    missing_iqomah = [p for p in expected_prayers if p not in data['iqomah_times']]
                    if missing_iqomah:
                        self.log_test("Iqomah Times Structure", False, f"Missing iqomah times: {missing_iqomah}")
                    else:
                        self.log_test("Iqomah Times Structure", True, "All iqomah times present")

    def test_settings_api(self):
        """Test settings CRUD operations"""
        print("\n⚙️ Testing Settings API...")
        
        # Test GET settings
        success, settings_data = self.test_api_endpoint(
            "Get Settings",
            "GET",
            "settings"
        )
        
        if success:
            # Test PUT settings update
            update_data = {
                "mosque_name": "Test Mosque Updated",
                "latitude": 3.1390,
                "longitude": 101.6869,
                "timezone": "Asia/Kuala_Lumpur"
            }
            
            self.test_api_endpoint(
                "Update Settings",
                "PUT",
                "settings",
                expected_status=200,
                data=update_data
            )

    def test_announcements_api(self):
        """Test announcements CRUD operations"""
        print("\n📢 Testing Announcements API...")
        
        # Test GET announcements
        success, announcements = self.test_api_endpoint(
            "Get Announcements",
            "GET",
            "announcements"
        )
        
        # Test POST new announcement
        new_announcement = {
            "text": "Test announcement for API testing",
            "priority": 3,
            "active": True
        }
        
        success, created_ann = self.test_api_endpoint(
            "Create Announcement",
            "POST",
            "announcements",
            expected_status=200,
            data=new_announcement
        )
        
        # Test DELETE announcement if created successfully
        if success and 'id' in created_ann:
            self.test_api_endpoint(
                "Delete Announcement",
                "DELETE",
                f"announcements/{created_ann['id']}"
            )

    def test_quran_verses_api(self):
        """Test Quran verses CRUD operations"""
        print("\n📖 Testing Quran Verses API...")
        
        # Test GET verses
        success, verses = self.test_api_endpoint(
            "Get Quran Verses",
            "GET",
            "quran-verses"
        )
        
        # Test POST new verse
        new_verse = {
            "arabic": "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ",
            "translation": "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
            "reference": "Surah Al-Fatiha 1:1",
            "active": True
        }
        
        success, created_verse = self.test_api_endpoint(
            "Create Quran Verse",
            "POST",
            "quran-verses",
            expected_status=200,
            data=new_verse
        )
        
        # Test DELETE verse if created successfully
        if success and 'id' in created_verse:
            self.test_api_endpoint(
                "Delete Quran Verse",
                "DELETE",
                f"quran-verses/{created_verse['id']}"
            )

    def test_financial_reports_api(self):
        """Test financial reports CRUD operations"""
        print("\n💰 Testing Financial Reports API...")
        
        # Test GET reports
        success, reports = self.test_api_endpoint(
            "Get Financial Reports",
            "GET",
            "financial-reports"
        )
        
        # Test POST new report
        new_report = {
            "title": "Test Donation",
            "amount": 1500.50,
            "period": "January 2025",
            "description": "Test financial report for API testing"
        }
        
        success, created_report = self.test_api_endpoint(
            "Create Financial Report",
            "POST",
            "financial-reports",
            expected_status=200,
            data=new_report
        )
        
        # Test DELETE report if created successfully
        if success and 'id' in created_report:
            self.test_api_endpoint(
                "Delete Financial Report",
                "DELETE",
                f"financial-reports/{created_report['id']}"
            )

    def run_all_tests(self):
        """Run all API tests"""
        print(f"🚀 Starting Mosque Display API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test all API endpoints
        self.test_prayer_times_api()
        self.test_settings_api()
        self.test_announcements_api()
        self.test_quran_verses_api()
        self.test_financial_reports_api()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for failed in self.failed_tests:
                print(f"  - {failed['test']}: {failed['error']}")
        
        return self.tests_passed == self.tests_run

def main():
    tester = MosqueAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "failed_tests": len(tester.failed_tests),
        "success_rate": (tester.tests_passed/tester.tests_run*100) if tester.tests_run > 0 else 0,
        "test_details": tester.test_results,
        "failed_tests_details": tester.failed_tests
    }
    
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())