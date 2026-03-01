#!/usr/bin/env python
"""
Test script to verify product update functionality.
Run this after starting the Django server.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
LOGIN_URL = f"{BASE_URL}/auth/login/"
PRODUCTS_URL = f"{BASE_URL}/inventory/products/"

# Test credentials (adjust as needed)
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "admin123"

def test_product_update():
    """Test product update with category field."""
    
    # Step 1: Login
    print("1. Logging in...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code != 200:
        print(f"Login failed: {response.status_code} - {response.text}")
        return
    
    tokens = response.json()
    headers = {
        "Authorization": f"Bearer {tokens['access']}",
        "Content-Type": "application/json"
    }
    
    print("✅ Login successful")
    
    # Step 2: Get existing products
    print("2. Fetching products...")
    response = requests.get(PRODUCTS_URL, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch products: {response.status_code} - {response.text}")
        return
    
    products = response.json()
    if not products.get('results'):
        print("No products found")
        return
    
    product = products['results'][0]
    product_id = product['id']
    print(f"✅ Found product: {product['name']} (ID: {product_id})")
    
    # Step 3: Test different category formats
    test_cases = [
        {
            "name": "Valid category ID",
            "data": {
                "name": product['name'],
                "sku": product['sku'],
                "price": "99.99",
                "category": 1  # Simple integer
            }
        },
        {
            "name": "Category as string",
            "data": {
                "name": product['name'],
                "sku": product['sku'],
                "price": "99.99",
                "category": "1"  # String that can be converted
            }
        },
        {
            "name": "Category as array (problematic case)",
            "data": {
                "name": product['name'],
                "sku": product['sku'],
                "price": "99.99",
                "category": [1]  # Array with single element
            }
        },
        {
            "name": "No category",
            "data": {
                "name": product['name'],
                "sku": product['sku'],
                "price": "99.99"
                # No category field
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 3):
        print(f"{i}. Testing: {test_case['name']}")
        
        response = requests.put(
            f"{PRODUCTS_URL}{product_id}/",
            json=test_case['data'],
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"✅ {test_case['name']} - SUCCESS")
        else:
            print(f"❌ {test_case['name']} - FAILED: {response.status_code}")
            print(f"   Error: {response.text}")
        
        print()

if __name__ == "__main__":
    test_product_update()