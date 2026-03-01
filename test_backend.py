#!/usr/bin/env python3
"""
Comprehensive Backend Functionality Test
Tests all CRUD operations for all models
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def get_auth_token():
    """Get authentication token"""
    login_data = {"email": "admin@acme.com", "password": "admin123"}
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if response.status_code == 200:
        return response.json().get('access')
    return None

def test_endpoint(name, method, url, headers, data=None):
    """Test an API endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers)
        
        status = "PASS" if response.status_code < 400 else "FAIL"
        result_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        
        print(f"{status} {name}: {response.status_code}")
        if response.status_code >= 400:
            print(f"   Error: {result_data}")
        elif isinstance(result_data, dict):
            if 'results' in result_data:
                print(f"   Found: {len(result_data['results'])} items")
            elif 'id' in result_data:
                print(f"   ID: {result_data['id']}")
        
        return response.status_code < 400, result_data
    except Exception as e:
        print(f"FAIL {name}: Exception - {e}")
        return False, str(e)

def main():
    print("COMPREHENSIVE BACKEND FUNCTIONALITY TEST")
    print("=" * 60)
    
    # Get auth token
    token = get_auth_token()
    if not token:
        print("AUTHENTICATION FAILED - Cannot proceed")
        return
    
    print("AUTHENTICATION SUCCESS")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Test Categories
    print("\nTESTING CATEGORIES")
    test_endpoint("List Categories", "GET", f"{BASE_URL}/inventory/categories/", headers)
    
    # Create category
    category_data = {"name": "Test Category", "description": "Test description"}
    success, result = test_endpoint("Create Category", "POST", f"{BASE_URL}/inventory/categories/", headers, category_data)
    category_id = result.get('id') if success and isinstance(result, dict) else None
    
    if category_id:
        test_endpoint("Get Category", "GET", f"{BASE_URL}/inventory/categories/{category_id}/", headers)
        update_data = {"name": "Updated Test Category"}
        test_endpoint("Update Category", "PUT", f"{BASE_URL}/inventory/categories/{category_id}/", headers, update_data)
    
    # Test Products
    print("\nTESTING PRODUCTS")
    test_endpoint("List Products", "GET", f"{BASE_URL}/inventory/products/", headers)
    
    # Create product
    product_data = {
        "name": "Test Product",
        "sku": "TEST-001",
        "price": "99.99",
        "category": category_id
    }
    success, result = test_endpoint("Create Product", "POST", f"{BASE_URL}/inventory/products/", headers, product_data)
    product_id = result.get('id') if success and isinstance(result, dict) else None
    
    if product_id:
        test_endpoint("Get Product", "GET", f"{BASE_URL}/inventory/products/{product_id}/", headers)
        test_endpoint("Get Product Inventory", "GET", f"{BASE_URL}/inventory/products/{product_id}/inventory/", headers)
    
    # Test Suppliers
    print("\nTESTING SUPPLIERS")
    test_endpoint("List Suppliers", "GET", f"{BASE_URL}/inventory/suppliers/", headers)
    
    # Create supplier
    supplier_data = {
        "name": "Test Supplier Co",
        "contact_person": "John Doe",
        "email": "john@testsupplier.com",
        "payment_terms": "Net 30",
        "lead_time_days": 7
    }
    success, result = test_endpoint("Create Supplier", "POST", f"{BASE_URL}/inventory/suppliers/", headers, supplier_data)
    supplier_id = result.get('id') if success and isinstance(result, dict) else None
    
    if supplier_id:
        test_endpoint("Get Supplier", "GET", f"{BASE_URL}/inventory/suppliers/{supplier_id}/", headers)
        update_data = {"name": "Updated Test Supplier Co"}
        test_endpoint("Update Supplier", "PUT", f"{BASE_URL}/inventory/suppliers/{supplier_id}/", headers, update_data)
    
    # Test Purchase Orders
    print("\nTESTING PURCHASE ORDERS")
    test_endpoint("List Purchase Orders", "GET", f"{BASE_URL}/inventory/purchase-orders/", headers)
    
    if supplier_id:
        po_data = {
            "supplier": supplier_id,
            "expected_date": "2024-12-31",
            "notes": "Test purchase order"
        }
        success, result = test_endpoint("Create Purchase Order", "POST", f"{BASE_URL}/inventory/purchase-orders/", headers, po_data)
        po_id = result.get('id') if success and isinstance(result, dict) else None
        
        if po_id:
            test_endpoint("Get Purchase Order", "GET", f"{BASE_URL}/inventory/purchase-orders/{po_id}/", headers)
    
    # Test Sales
    print("\nTESTING SALES")
    test_endpoint("List Sales", "GET", f"{BASE_URL}/inventory/sales/", headers)
    test_endpoint("Today's Sales", "GET", f"{BASE_URL}/inventory/sales/today/", headers)
    
    # Create sale
    sale_data = {
        "customer_name": "Test Customer",
        "customer_email": "customer@test.com",
        "payment_method": "cash",
        "notes": "Test sale"
    }
    success, result = test_endpoint("Create Sale", "POST", f"{BASE_URL}/inventory/sales/", headers, sale_data)
    sale_id = result.get('id') if success and isinstance(result, dict) else None
    
    if sale_id:
        test_endpoint("Get Sale", "GET", f"{BASE_URL}/inventory/sales/{sale_id}/", headers)
    
    # Test Special Endpoints
    print("\nTESTING SPECIAL ENDPOINTS")
    test_endpoint("Test Vendor", "GET", f"{BASE_URL}/inventory/test-vendor/", headers)
    test_endpoint("Low Stock Products", "GET", f"{BASE_URL}/inventory/products/low_stock/", headers)
    
    # Cleanup - Delete created items
    print("\nCLEANUP")
    if sale_id:
        test_endpoint("Delete Sale", "DELETE", f"{BASE_URL}/inventory/sales/{sale_id}/", headers)
    if po_id:
        test_endpoint("Delete Purchase Order", "DELETE", f"{BASE_URL}/inventory/purchase-orders/{po_id}/", headers)
    if supplier_id:
        test_endpoint("Delete Supplier", "DELETE", f"{BASE_URL}/inventory/suppliers/{supplier_id}/", headers)
    if product_id:
        test_endpoint("Delete Product", "DELETE", f"{BASE_URL}/inventory/products/{product_id}/", headers)
    if category_id:
        test_endpoint("Delete Category", "DELETE", f"{BASE_URL}/inventory/categories/{category_id}/", headers)
    
    print("\nBACKEND FUNCTIONALITY TEST COMPLETE")

if __name__ == "__main__":
    main()