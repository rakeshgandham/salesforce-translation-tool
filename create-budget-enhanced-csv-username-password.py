#!/usr/bin/env python3
"""
Enhanced Budget Creation with Full CSV Support - Username/Password Authentication

This version reads ALL columns from CSV files and maps them to Salesforce fields.
Great for importing comprehensive budget data with categories and periods that have
additional attributes like descriptions, amounts, dates, etc.
"""
import json
import requests
import csv
import sys
import xml.etree.ElementTree as ET
from typing import List, Dict

# Configuration - UPDATE THESE FOR YOUR ORG
INSTANCE_URL = ""  # e.g., "https://your-instance.salesforce.com"
USERNAME = ""  # Your Salesforce username
PASSWORD = ""  # Your password
SECURITY_TOKEN = ""  # Your security token (leave empty if not required)
API_VERSION = "62.0"  # Salesforce API version

# Input files
CATEGORIES_FILE = "budget_categories_enhanced.csv"
PERIODS_FILE = "budget_periods_enhanced.csv"

# Field mappings: CSV column name → Salesforce field API name
CATEGORY_FIELD_MAP = {
    "Name": "Name",
    "Description": "Description__c",
    "Amount": "Amount__c",
    "Code": "CategoryCode__c"
}

PERIOD_FIELD_MAP = {
    "Name": "Name",
    "StartDate": "StartDate__c",
    "EndDate": "EndDate__c",
    "Quarter": "Quarter__c",
    "FiscalYear": "FiscalYear__c"
}

def login_with_password(username: str, password: str, security_token: str = "") -> Dict:
    """
    Login to Salesforce using SOAP API with username/password
    Returns: dict with 'access_token' and 'instance_url'
    """
    # Concatenate password with security token if provided
    password_with_token = password + security_token

    # SOAP login endpoint (SOAP API only supports up to v64.0)
    soap_url = f"{INSTANCE_URL}/services/Soap/u/64.0"

    # SOAP login request body
    soap_body = f"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:urn="urn:partner.soap.sforce.com">
    <soapenv:Body>
        <urn:login>
            <urn:username>{username}</urn:username>
            <urn:password>{password_with_token}</urn:password>
        </urn:login>
    </soapenv:Body>
</soapenv:Envelope>"""

    headers = {
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": "login"
    }

    try:
        response = requests.post(soap_url, data=soap_body, headers=headers)

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return None

        # Parse SOAP response
        root = ET.fromstring(response.text)

        # Find sessionId and serverUrl in the response
        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'urn': 'urn:partner.soap.sforce.com'
        }

        session_id = root.find('.//urn:sessionId', namespaces)
        server_url = root.find('.//urn:serverUrl', namespaces)

        if session_id is None or server_url is None:
            print("❌ Could not parse login response")
            print(response.text)
            return None

        # Extract instance URL from serverUrl
        instance_url = server_url.text.split('/services')[0]

        return {
            'access_token': session_id.text,
            'instance_url': instance_url
        }

    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def get_credentials():
    """Get credentials from user if not set in script"""
    global USERNAME, PASSWORD, SECURITY_TOKEN, INSTANCE_URL

    if not USERNAME or not INSTANCE_URL:
        print("=" * 60)
        print("Salesforce Login")
        print("=" * 60)

        if not INSTANCE_URL:
            INSTANCE_URL = input("Instance URL (e.g., https://your-instance.salesforce.com): ").strip()

        USERNAME = input("Username: ").strip()
        PASSWORD = input("Password: ").strip()

        print("\nDo you need a security token?")
        print("(Required if logging in from untrusted IP)")
        use_token = input("Use security token? (y/N): ").strip().lower()

        if use_token == 'y':
            print("\nTo get your security token:")
            print("1. Login to Salesforce")
            print("2. Go to: Your Name → Settings → My Personal Information → Reset Security Token")
            print("3. Click 'Reset Security Token' - it will be emailed to you")
            SECURITY_TOKEN = input("Security Token: ").strip()

    return USERNAME, PASSWORD, SECURITY_TOKEN

def read_csv_with_mapping(file_path: str, field_map: Dict[str, str]) -> List[Dict]:
    """
    Read CSV file and map columns to Salesforce field names
    Returns list of dicts with Salesforce field API names
    """
    items = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                item = {}
                for csv_col, sf_field in field_map.items():
                    if csv_col in row and row[csv_col].strip():
                        value = row[csv_col].strip()

                        # Type conversion for numeric fields
                        if "Amount" in sf_field:
                            try:
                                item[sf_field] = float(value)
                            except ValueError:
                                print(f"⚠️  Invalid amount value: {value}, skipping")
                                continue
                        else:
                            item[sf_field] = value

                if item.get("Name"):  # Only add if Name is present
                    items.append(item)

    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return []

    return items

def create_sample_csv_files():
    """Create sample CSV files with all supported columns"""
    import os

    if not os.path.exists(CATEGORIES_FILE):
        print(f"\n📝 Creating sample {CATEGORIES_FILE}...")
        with open(CATEGORIES_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(CATEGORY_FIELD_MAP.keys()))
            writer.writeheader()
            writer.writerows([
                {"Name": "Personnel", "Description": "Salaries, wages, and benefits", "Amount": "300000", "Code": "CAT-001"},
                {"Name": "Equipment", "Description": "Hardware, software, and tools", "Amount": "75000", "Code": "CAT-002"},
                {"Name": "Travel", "Description": "Business travel and transportation", "Amount": "50000", "Code": "CAT-003"},
                {"Name": "Supplies", "Description": "Office and operational supplies", "Amount": "25000", "Code": "CAT-004"},
                {"Name": "Consulting", "Description": "External consultants and contractors", "Amount": "100000", "Code": "CAT-005"},
            ])
        print(f"✅ Created {CATEGORIES_FILE}")

    if not os.path.exists(PERIODS_FILE):
        print(f"\n📝 Creating sample {PERIODS_FILE}...")
        with open(PERIODS_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(PERIOD_FIELD_MAP.keys()))
            writer.writeheader()
            writer.writerows([
                {"Name": "Q1 FY2026", "StartDate": "2025-10-01", "EndDate": "2025-12-31", "Quarter": "Q1", "FiscalYear": "2026"},
                {"Name": "Q2 FY2026", "StartDate": "2026-01-01", "EndDate": "2026-03-31", "Quarter": "Q2", "FiscalYear": "2026"},
                {"Name": "Q3 FY2026", "StartDate": "2026-04-01", "EndDate": "2026-06-30", "Quarter": "Q3", "FiscalYear": "2026"},
                {"Name": "Q4 FY2026", "StartDate": "2026-07-01", "EndDate": "2026-09-30", "Quarter": "Q4", "FiscalYear": "2026"},
            ])
        print(f"✅ Created {PERIODS_FILE}")

def get_budget_details():
    """Prompt user for budget details"""
    print("\n" + "="*60)
    print("Enter Budget Details")
    print("="*60)

    budget_name = input("Budget Name: ").strip()
    if not budget_name:
        print("❌ Budget name is required")
        sys.exit(1)

    budget_amount = input("Total Budget Amount (optional): ").strip()
    start_date = input("Start Date (YYYY-MM-DD) (optional): ").strip()
    end_date = input("End Date (YYYY-MM-DD) (optional): ").strip()
    fiscal_year = input("Fiscal Year (optional): ").strip()
    status = input("Status (Draft/Approved/Active) (optional): ").strip()
    description = input("Description (optional): ").strip()

    budget = {
        "Name": budget_name
    }

    if budget_amount:
        try:
            budget["TotalAmount__c"] = float(budget_amount)
        except ValueError:
            print("⚠️  Invalid amount, skipping...")

    if start_date:
        budget["StartDate__c"] = start_date

    if end_date:
        budget["EndDate__c"] = end_date

    if fiscal_year:
        budget["FiscalYear__c"] = fiscal_year

    if status:
        budget["Status__c"] = status

    if description:
        budget["Description__c"] = description

    return budget

def create_budget_composite(access_token: str, instance_url: str, budget_data: Dict,
                           categories: List[Dict], periods: List[Dict]) -> Dict:
    """Create Budget with categories and periods using Composite Graph API"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    graphs = []
    budget_ref_id = "Budget1"

    # 1. Create Budget
    graphs.append({
        "method": "POST",
        "url": f"/services/data/v{API_VERSION}/sobjects/Budget__c",
        "referenceId": budget_ref_id,
        "body": budget_data
    })

    # 2. Create BudgetCategory records with all fields
    for idx, category in enumerate(categories, 1):
        category_body = dict(category)  # Copy all fields
        category_body["Budget__c"] = f"@{{{budget_ref_id}.id}}"

        graphs.append({
            "method": "POST",
            "url": f"/services/data/v{API_VERSION}/sobjects/BudgetCategory__c",
            "referenceId": f"Category{idx}",
            "body": category_body
        })

    # 3. Create BudgetPeriod records with all fields
    for idx, period in enumerate(periods, 1):
        period_body = dict(period)  # Copy all fields
        period_body["Budget__c"] = f"@{{{budget_ref_id}.id}}"

        graphs.append({
            "method": "POST",
            "url": f"/services/data/v{API_VERSION}/sobjects/BudgetPeriod__c",
            "referenceId": f"Period{idx}",
            "body": period_body
        })

    payload = {
        "graphs": [
            {
                "graphId": "BudgetCreation",
                "compositeRequest": graphs
            }
        ]
    }

    print(f"\n📤 Sending composite request...")
    print(f"   • 1 Budget")
    print(f"   • {len(categories)} Categories (with {len(CATEGORY_FIELD_MAP)} fields each)")
    print(f"   • {len(periods)} Periods (with {len(PERIOD_FIELD_MAP)} fields each)")
    print(f"   • Total: {1 + len(categories) + len(periods)} records")

    response = requests.post(
        f"{instance_url}/services/data/v{API_VERSION}/composite/graph",
        headers=headers,
        json=payload
    )

    if response.status_code not in [200, 201]:
        return {
            "success": False,
            "error": f"HTTP {response.status_code}: {response.text}"
        }

    result = response.json()
    return {
        "success": True,
        "result": result
    }

def print_results(result: Dict, instance_url: str):
    """Print creation results"""
    if not result.get("success"):
        print(f"\n❌ Error: {result.get('error')}")
        return

    graphs_result = result.get("result", {}).get("graphs", [])
    if not graphs_result:
        print("\n⚠️  No results returned")
        return

    composite_response = graphs_result[0].get("compositeResponse", [])

    # Separate results
    budget_result = None
    category_results = []
    period_results = []

    for item in composite_response:
        ref_id = item.get("referenceId", "")
        if ref_id.startswith("Budget"):
            budget_result = item
        elif ref_id.startswith("Category"):
            category_results.append(item)
        elif ref_id.startswith("Period"):
            period_results.append(item)

    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    # Budget result
    if budget_result:
        if budget_result.get("httpStatusCode") in [200, 201]:
            budget_id = budget_result.get("body", {}).get("id")
            print(f"\n✅ Budget Created")
            print(f"   ID: {budget_id}")
            print(f"   URL: {instance_url}/lightning/r/Budget__c/{budget_id}/view")
        else:
            errors = budget_result.get("body", [])
            print(f"\n❌ Budget Creation Failed")
            for error in errors:
                print(f"   • {error.get('message', 'Unknown error')}")

    # Category results
    success_categories = [c for c in category_results if c.get("httpStatusCode") in [200, 201]]
    if success_categories:
        print(f"\n✅ Created {len(success_categories)} Budget Categories")

    failed_categories = [c for c in category_results if c.get("httpStatusCode") not in [200, 201]]
    if failed_categories:
        print(f"\n⚠️  {len(failed_categories)} Categories Failed:")
        for cat in failed_categories:
            errors = cat.get("body", [])
            for error in errors:
                print(f"   • {error.get('message', 'Unknown error')}")

    # Period results
    success_periods = [p for p in period_results if p.get("httpStatusCode") in [200, 201]]
    if success_periods:
        print(f"\n✅ Created {len(success_periods)} Budget Periods")

    failed_periods = [p for p in period_results if p.get("httpStatusCode") not in [200, 201]]
    if failed_periods:
        print(f"\n⚠️  {len(failed_periods)} Periods Failed:")
        for period in failed_periods:
            errors = period.get("body", [])
            for error in errors:
                print(f"   • {error.get('message', 'Unknown error')}")

    # Summary
    total_success = len(success_categories) + len(success_periods)
    total_fail = len(failed_categories) + len(failed_periods)
    if budget_result and budget_result.get("httpStatusCode") in [200, 201]:
        total_success += 1
    else:
        total_fail += 1

    print(f"\n{'='*60}")
    print(f"Summary: {total_success} created, {total_fail} failed")
    print(f"{'='*60}")

def main():
    print("="*60)
    print("Enhanced Budget Creation Tool (Full CSV Support)")
    print("Username/Password Authentication")
    print("="*60)

    # Get credentials
    username, password, security_token = get_credentials()

    # Create sample files if needed
    create_sample_csv_files()

    # Read CSV files with field mappings
    print(f"\n1. Reading CSV files...")
    categories = read_csv_with_mapping(CATEGORIES_FILE, CATEGORY_FIELD_MAP)
    periods = read_csv_with_mapping(PERIODS_FILE, PERIOD_FIELD_MAP)

    print(f"   • Categories: {len(categories)}")
    print(f"   • Periods: {len(periods)}")

    if not categories and not periods:
        print("\n⚠️  No categories or periods found. Please check CSV files.")
        sys.exit(1)

    # Display preview
    if categories:
        print(f"\n   Category Preview:")
        for cat in categories[:3]:
            print(f"      • {cat.get('Name')} - {cat.get('Description__c', 'N/A')}")
        if len(categories) > 3:
            print(f"      ... and {len(categories) - 3} more")

    if periods:
        print(f"\n   Period Preview:")
        for period in periods[:3]:
            print(f"      • {period.get('Name')} ({period.get('StartDate__c', 'N/A')} to {period.get('EndDate__c', 'N/A')})")
        if len(periods) > 3:
            print(f"      ... and {len(periods) - 3} more")

    # Get budget details
    budget_data = get_budget_details()

    # Confirm
    print(f"\n{'='*60}")
    print("Ready to create:")
    print(f"   • 1 Budget: {budget_data.get('Name')}")
    print(f"   • {len(categories)} Categories")
    print(f"   • {len(periods)} Periods")
    response = input("\nContinue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Aborted by user")
        return

    # Authenticate
    print("\n2. Authenticating...")
    auth_result = login_with_password(username, password, security_token)

    if not auth_result:
        print("❌ Authentication failed")
        sys.exit(1)

    access_token = auth_result['access_token']
    instance_url = auth_result['instance_url']
    print(f"✅ Authenticated successfully")
    print(f"   Instance: {instance_url}")

    # Create records
    print("\n3. Creating records...")
    result = create_budget_composite(access_token, instance_url, budget_data, categories, periods)

    # Print results
    print_results(result, instance_url)

if __name__ == "__main__":
    main()
