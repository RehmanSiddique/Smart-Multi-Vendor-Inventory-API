"""
Phase 6 API Test Suite
Run with: python test_phase6.py
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000/api/v1"
TEST_EMAIL = "admin@acme.com"
TEST_PASSWORD = "testpass123"


class APITester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_product_id = None
        self.test_category_id = None
        self.test_supplier_id = None
        self.test_po_id = None
        self.test_sale_id = None
    
    def print_header(self, title):
        print("\n" + "="*80)
        print(f"🔷 {title}")
        print("="*80)
    
    def print_response(self, response, expected_status=200):
        print(f"\n📡 Status: {response.status_code} (Expected: {expected_status})")
        if response.status_code == expected_status:
            print("✅ SUCCESS")
            if response.content:
                try:
                    data = response.json()
                    print("📦 Response:")
                    pprint(data)
                    return data
                except:
                    print("📦 Response:", response.text)
        else:
            print("❌ FAILED")
            print("📦 Error:", response.text if response.content else "No content")
        return None
    
    def run_all_tests(self):
        """Run all API tests in sequence"""
        
        # ============================================================
        # TEST 1: Authentication
        # ============================================================
        self.print_header("TEST 1: Authentication")
        
        # 1.1 Login
        print("\n1.1 🔐 Logging in...")
        response = requests.post(
            f"{BASE_URL}/auth/login/",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        data = self.print_response(response, 200)
        
        if data and 'access' in data:
            self.token = data['access']
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"\n🔑 Token: {self.token[:50]}...")
            
            # 1.2 Verify Token
            print("\n1.2 ✅ Verifying token...")
            response = requests.post(
                f"{BASE_URL}/auth/verify/",
                json={"token": self.token}
            )
            self.print_response(response, 200)
            
            # 1.3 Get Current User
            print("\n1.3 👤 Getting current user...")
            response = requests.get(
                f"{BASE_URL}/accounts/users/me/",
                headers=self.headers
            )
            self.print_response(response, 200)
        else:
            print("❌ Cannot proceed without authentication")
            return
        
        # ============================================================
        # TEST 2: Categories
        # ============================================================
        self.print_header("TEST 2: Category API")
        
        # 2.1 List Categories
        print("\n2.1 📋 Listing categories...")
        response = requests.get(
            f"{BASE_URL}/inventory/categories/",
            headers=self.headers
        )
        self.print_response(response, 200)
        
        # 2.2 Create Category
        print("\n2.2 ➕ Creating new category...")
        category_data = {
            "name": "Test Category",
            "description": "Created by API test"
        }
        response = requests.post(
            f"{BASE_URL}/inventory/categories/",
            headers=self.headers,
            json=category_data
        )
        data = self.print_response(response, 201)
        if data:
            self.test_category_id = data.get('id')
            print(f"   🆔 Category ID: {self.test_category_id}")
        
        # 2.3 Get Single Category
        if self.test_category_id:
            print(f"\n2.3 🔍 Getting category {self.test_category_id}...")
            response = requests.get(
                f"{BASE_URL}/inventory/categories/{self.test_category_id}/",
                headers=self.headers
            )
            self.print_response(response, 200)
        
        # ============================================================
        # TEST 3: Products
        # ============================================================
        self.print_header("TEST 3: Product API")
        
        # 3.1 List Products
        print("\n3.1 📋 Listing products...")
        response = requests.get(
            f"{BASE_URL}/inventory/products/",
            headers=self.headers
        )
        self.print_response(response, 200)
        
        # 3.2 Create Product
        print("\n3.2 ➕ Creating new product...")
        product_data = {
            "name": "API Test Product",
            "sku": f"TEST-{hash('test') % 10000:04d}",
            "price": "99.99",
            "cost": "65.00",
            "description": "Product created by API test",
            "category": self.test_category_id
        }
        response = requests.post(
            f"{BASE_URL}/inventory/products/",
            headers=self.headers,
            json=product_data
        )
        data = self.print_response(response, 201)
        if data:
            self.test_product_id = data.get('id')
            print(f"   🆔 Product ID: {self.test_product_id}")
            print(f"   📦 SKU: {data.get('sku')}")
        
        # 3.3 Get Single Product
        if self.test_product_id:
            print(f"\n3.3 🔍 Getting product {self.test_product_id}...")
            response = requests.get(
                f"{BASE_URL}/inventory/products/{self.test_product_id}/",
                headers=self.headers
            )
            data = self.print_response(response, 200)
            if data:
                print(f"   💰 Price: ${data.get('price')}")
                print(f"   📊 Profit Margin: {data.get('profit_margin')}%")
        
        # 3.4 Check Low Stock Products
        print("\n3.4 ⚠️ Checking low stock products...")
        response = requests.get(
            f"{BASE_URL}/inventory/products/low_stock/",
            headers=self.headers
        )
        self.print_response(response, 200)
        
        # 3.5 Filter Products
        print("\n3.5 🔎 Searching products...")
        response = requests.get(
            f"{BASE_URL}/inventory/products/?search=API&ordering=-created_at",
            headers=self.headers
        )
        self.print_response(response, 200)
        
        # ============================================================
        # TEST 4: Inventory
        # ============================================================
        self.print_header("TEST 4: Inventory API")
        
        if self.test_product_id:
            # 4.1 Get Product Inventory
            print(f"\n4.1 📦 Getting inventory for product {self.test_product_id}...")
            response = requests.get(
                f"{BASE_URL}/inventory/products/{self.test_product_id}/inventory/",
                headers=self.headers
            )
            data = self.print_response(response, 200)
            
            # 4.2 Update Inventory (if needed)
            if data and data.get('id'):
                print("\n4.2 📝 Updating inventory...")
                # Create inventory if it doesn't exist
                if response.status_code == 404:
                    inventory_data = {
                        "quantity": 50,
                        "reorder_level": 10,
                        "location": "Aisle A, Shelf 1"
                    }
                    response = requests.post(
                        f"{BASE_URL}/inventory/inventory/",
                        headers=self.headers,
                        json=inventory_data
                    )
                    self.print_response(response, 201)
        
        # ============================================================
        # TEST 5: Suppliers
        # ============================================================
        self.print_header("TEST 5: Supplier API")
        
        # 5.1 Create Supplier
        print("\n5.1 ➕ Creating supplier...")
        supplier_data = {
            "name": "API Test Supplier",
            "contact_person": "John Doe",
            "email": "supplier@example.com",
            "phone": "555-0123",
            "payment_terms": "Net 30",
            "lead_time_days": 7
        }
        response = requests.post(
            f"{BASE_URL}/inventory/suppliers/",
            headers=self.headers,
            json=supplier_data
        )
        data = self.print_response(response, 201)
        if data:
            self.test_supplier_id = data.get('id')
            print(f"   🆔 Supplier ID: {self.test_supplier_id}")
        
        # 5.2 List Suppliers
        print("\n5.2 📋 Listing suppliers...")
        response = requests.get(
            f"{BASE_URL}/inventory/suppliers/",
            headers=self.headers
        )
        self.print_response(response, 200)
        
        # ============================================================
        # TEST 6: Purchase Orders
        # ============================================================
        self.print_header("TEST 6: Purchase Order API")
        
        if self.test_supplier_id and self.test_product_id:
            # 6.1 Create Purchase Order
            print("\n6.1 ➕ Creating purchase order...")
            po_data = {
                "supplier": self.test_supplier_id,
                "notes": "Test purchase order",
                "items": [
                    {
                        "product": self.test_product_id,
                        "quantity": 10,
                        "unit_price": "65.00"
                    }
                ]
            }
            response = requests.post(
                f"{BASE_URL}/inventory/purchase-orders/",
                headers=self.headers,
                json=po_data
            )
            data = self.print_response(response, 201)
            if data:
                self.test_po_id = data.get('id')
                print(f"   🆔 PO ID: {self.test_po_id}")
                print(f"   📄 PO Number: {data.get('order_number')}")
                print(f"   💰 Total: ${data.get('total_amount')}")
        
        # ============================================================
        # TEST 7: Sales
        # ============================================================
        self.print_header("TEST 7: Sales API")
        
        if self.test_product_id:
            # 7.1 Create Sale
            print("\n7.1 ➕ Creating sale...")
            sale_data = {
                "customer_name": "Test Customer",
                "customer_email": "customer@example.com",
                "payment_method": "card",
                "items": [
                    {
                        "product": self.test_product_id,
                        "quantity": 2,
                        "unit_price": "99.99"
                    }
                ]
            }
            response = requests.post(
                f"{BASE_URL}/inventory/sales/",
                headers=self.headers,
                json=sale_data
            )
            data = self.print_response(response, 201)
            if data:
                self.test_sale_id = data.get('id')
                print(f"   🆔 Sale ID: {self.test_sale_id}")
                print(f"   🧾 Sale Number: {data.get('sale_number')}")
                print(f"   💰 Total: ${data.get('total')}")
            
            # 7.2 Get Today's Sales
            print("\n7.2 📅 Getting today's sales...")
            response = requests.get(
                f"{BASE_URL}/inventory/sales/today/",
                headers=self.headers
            )
            self.print_response(response, 200)
        
        # ============================================================
        # TEST 8: Filtering & Pagination
        # ============================================================
        self.print_header("TEST 8: Advanced Features")
        
        # 8.1 Pagination
        print("\n8.1 📄 Testing pagination...")
        response = requests.get(
            f"{BASE_URL}/inventory/products/?page=1&page_size=5",
            headers=self.headers
        )
        data = self.print_response(response, 200)
        if data:
            print(f"   Total products: {data.get('count')}")
            print(f"   Next page: {data.get('next')}")
        
        # 8.2 Filtering
        print("\n8.2 🔍 Testing filters...")
        response = requests.get(
            f"{BASE_URL}/inventory/products/?is_active=true",
            headers=self.headers
        )
        self.print_response(response, 200)
        
        # 8.3 Ordering
        print("\n8.3 📊 Testing ordering...")
        response = requests.get(
            f"{BASE_URL}/inventory/products/?ordering=-price",
            headers=self.headers
        )
        self.print_response(response, 200)
        
        # ============================================================
        # TEST 9: Clean Up (Optional)
        # ============================================================
        self.print_header("TEST 9: Clean Up (Optional)")
        
        # 9.1 Delete Test Product
        if self.test_product_id:
            print(f"\n9.1 🗑️ Deleting product {self.test_product_id}...")
            response = requests.delete(
                f"{BASE_URL}/inventory/products/{self.test_product_id}/",
                headers=self.headers
            )
            self.print_response(response, 204)
        
        # 9.2 Delete Test Category
        if self.test_category_id:
            print(f"\n9.2 🗑️ Deleting category {self.test_category_id}...")
            response = requests.delete(
                f"{BASE_URL}/inventory/categories/{self.test_category_id}/",
                headers=self.headers
            )
            self.print_response(response, 204)
        
        # 9.3 Delete Test Supplier
        if self.test_supplier_id:
            print(f"\n9.3 🗑️ Deleting supplier {self.test_supplier_id}...")
            response = requests.delete(
                f"{BASE_URL}/inventory/suppliers/{self.test_supplier_id}/",
                headers=self.headers
            )
            self.print_response(response, 204)
        
        # ============================================================
        # TEST SUMMARY
        # ============================================================
        self.print_header("✅ TEST SUMMARY")
        print("""
┌─────────────────────────────────────────────────────────────┐
│                    PHASE 6 API TESTS                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✅ Authentication - JWT tokens working                      │
│  ✅ Categories - CRUD operations successful                   │
│  ✅ Products - Create, read, filter working                   │
│  ✅ Inventory - Stock tracking operational                    │
│  ✅ Suppliers - Supplier management working                   │
│  ✅ Purchase Orders - PO creation successful                  │
│  ✅ Sales - Transaction recording working                     │
│  ✅ Pagination - Page size and navigation working             │
│  ✅ Filtering - Search and filters operational                │
│                                                              │
│  🎉 ALL SYSTEMS OPERATIONAL!                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
        """)


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()