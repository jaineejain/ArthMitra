#!/usr/bin/env python3
"""
Test script for ArthMitra Finance APIs
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_finance_health():
    """Test finance API health"""
    try:
        response = requests.get(f"{BASE_URL}/api/finance/health")
        print(f"Finance Health: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except Exception as e:
        print(f"Finance Health Error: {e}")
        return False

def test_mhs_calculation():
    """Test MHS calculation"""
    test_data = {
        "age": 30,
        "monthly_income": 5000000,  # 50,000 INR in paise
        "monthly_expenses": 3000000,  # 30,000 INR in paise
        "monthly_emi": 1500000,  # 15,000 INR in paise
        "emergency_fund": 60000000,  # 6,00,000 INR in paise
        "monthly_sip": 1000000,  # 10,000 INR in paise
        "term_cover": 50000000,  # 5,00,000 INR in paise
        "health_cover": 30000000  # 3,00,000 INR in paise
    }

    try:
        response = requests.post(f"{BASE_URL}/api/finance/mhs", json=test_data)
        print(f"MHS Calculation: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"MHS Score: {result['data']['total']}")
            print(f"Band: {result['data']['band']}")
            print(f"Weakest Area: {result['data']['weakest']}")
        return response.status_code == 200
    except Exception as e:
        print(f"MHS Calculation Error: {e}")
        return False

def test_tax_calculation():
    """Test tax calculation"""
    test_data = {
        "age": 30,
        "monthly_income": 5000000,
        "monthly_expenses": 3000000,
        "annual_gross": 60000000,  # 6,00,000 INR in paise
        "basic_salary": 40000000,  # 4,00,000 INR in paise
        "hra_received": 12000000,  # 1,20,000 INR in paise
        "rent_paid": 15000000,  # 1,50,000 INR in paise
        "city_type": "metro",
        "used_80c": 15000000,  # 1,50,000 INR in paise
        "health_premium": 2500000,  # 25,000 INR in paise
        "nps_tier1": 5000000  # 50,000 INR in paise
    }

    try:
        response = requests.post(f"{BASE_URL}/api/finance/tax", json=test_data)
        print(f"Tax Calculation: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Old Regime Tax: ₹{result['data']['old_tax'] / 100:.2f}")
            print(f"New Regime Tax: ₹{result['data']['new_tax'] / 100:.2f}")
            print(f"Recommended: {result['data']['recommended']}")
            print(f"Savings: ₹{result['data']['savings'] / 100:.2f}")
        return response.status_code == 200
    except Exception as e:
        print(f"Tax Calculation Error: {e}")
        return False

def test_portfolio_analysis():
    """Test portfolio analysis"""
    test_data = [
        {"name": "HDFC Equity Fund", "type": "equity", "invested": 10000000, "current": 12000000},
        {"name": "SBI Debt Fund", "type": "debt", "invested": 5000000, "current": 5100000},
        {"name": "ICICI Hybrid Fund", "type": "hybrid", "invested": 8000000, "current": 8500000}
    ]

    try:
        response = requests.post(f"{BASE_URL}/api/finance/portfolio", json=test_data)
        print(f"Portfolio Analysis: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Total Invested: ₹{result['data']['total_invested'] / 100:.2f}")
            print(f"Total Current: ₹{result['data']['total_current'] / 100:.2f}")
            print(f"Total Return: ₹{result['data']['total_return'] / 100:.2f}")
            print(f"Risk Level: {result['data']['risk_level']}")
        return response.status_code == 200
    except Exception as e:
        print(f"Portfolio Analysis Error: {e}")
        return False

if __name__ == "__main__":
    print("Testing ArthMitra Finance APIs...")
    print("=" * 50)

    # Test health
    health_ok = test_finance_health()
    print()

    if health_ok:
        # Test calculations
        test_mhs_calculation()
        print()
        test_tax_calculation()
        print()
        test_portfolio_analysis()
        print()

        print("All tests completed!")
    else:
        print("Finance API not available")