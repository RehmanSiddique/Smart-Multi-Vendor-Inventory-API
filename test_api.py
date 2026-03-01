#!/usr/bin/env python3
"""
Test script to verify API authentication and supplier retrieval
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_login():
    """Test login with existing user"""
    login_data = {
        "email": "admin@acme.com",
        "password": "admin123"  # You may need to adjust this
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    print(f"Login Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Login successful! Access token: {data.get('access', 'Not found')[:50]}...")
        return data.get('access')
    else:
        print(f"Login failed: {response.text}")
        return None

def test_suppliers(token):
    """Test supplier retrieval with authentication"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/inventory/suppliers/", headers=headers)
    print(f"Suppliers Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Suppliers found: {len(data.get('results', data))}")
        if isinstance(data, dict) and 'results' in data:
            suppliers = data['results']
        else:
            suppliers = data if isinstance(data, list) else []
        
        for supplier in suppliers[:3]:  # Show first 3
            print(f"  - {supplier.get('name', 'Unknown')}")
    else:
        print(f"Suppliers failed: {response.text}")

def test_vendor_info(token):
    """Test vendor info endpoint"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{BASE_URL}/inventory/test-vendor/", headers=headers)
    print(f"Vendor Info Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Current vendor: {data}")
    else:
        print(f"Vendor info failed: {response.text}")

if __name__ == "__main__":
    print("Testing API Authentication and Supplier Retrieval")
    print("=" * 50)
    
    # Test login
    token = test_login()
    
    if token:
        print("\n" + "=" * 50)
        # Test vendor info
        test_vendor_info(token)
        
        print("\n" + "=" * 50)
        # Test suppliers
        test_suppliers(token)
    else:
        print("Cannot proceed without valid token")