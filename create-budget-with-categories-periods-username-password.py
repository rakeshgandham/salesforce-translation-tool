#!/usr/bin/env python3
"""
Create Budget sObjects with related BudgetCategory and BudgetPeriod records
using Salesforce Composite API - Username/Password Authentication

Reads budget categories and periods from text/CSV files and creates:
1. Budget record (parent)
2. BudgetCategory records (children)
3. BudgetPeriod records (children)
"""
import json
import requests
import csv
import sys
import xml.etree.ElementTree as ET
from typing import List, Dict

# Configuration - UPDATE THESE FOR YOUR ORG
INSTANCE_URL = "https://gandham.my.salesforce-com.ut5fm8x39smv0pzcasy21xozj16.wc.crm.dev:6101"
USERNAME = "rgandham_gmtesting@salesforce.com"  # Your Salesforce username
PASSWORD = "Test1234"  # Your password
SECURITY_TOKEN = ""  # Your security token (leave empty if not required)
API_VERSION = "66.0"  # Salesforce API version

# Input files
CATEGORIES_FILE = "budget_categories.txt"  # One category per line (or .csv with "Name" column)
PERIODS_FILE = "budget_periods.txt"  # One period per line (or .csv with "Name" column)

def login_with_password(username: str, password: str, security_token: str = "") -> Dict:
    """
    Login to Salesforce using SOAP API with username/password
    Returns: dict with 'access_token' and 'instance_url'
    """
    print(f"\n🔍 DEBUG: Attempting login...")
    print(f"   Username: {username}")
    print(f"   Instance: {INSTANCE_URL}")
    print(f"   Security Token: {'[SET]' if security_token else '[NOT SET]'}")

    # Concatenate password with security token if provided
    password_with_token = password + security_token

    # SOAP login endpoint (SOAP API only supports up to v64.0)
    soap_url = f"{INSTANCE_URL}/services/Soap/u/64.0"
    print(f"   SOAP URL: {soap_url}")

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
        print(f"\n📤 Sending SOAP login request...")
        response = requests.post(soap_url, data=soap_body, headers=headers, timeout=30)

        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")

        if response.status_code != 200:
            print(f"\n❌ Login failed with status code: {response.status_code}")
            print(f"❌ Response body:")
            print(response.text)

            # Try to parse error from SOAP fault
            try:
                error_root = ET.fromstring(response.text)
                fault = error_root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault')
                if fault is not None:
                    fault_string = fault.find('.//faultstring')
                    if fault_string is not None:
                        print(f"❌ SOAP Fault: {fault_string.text}")
            except:
                pass

            return None

        # Parse SOAP response
        print(f"\n🔍 Parsing SOAP response...")
        root = ET.fromstring(response.text)

        # Find sessionId and serverUrl in the response
        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'urn': 'urn:partner.soap.sforce.com'
        }

        session_id = root.find('.//urn:sessionId', namespaces)
        server_url = root.find('.//urn:serverUrl', namespaces)

        if session_id is None or server_url is None:
            print("❌ Could not parse login response - sessionId or serverUrl missing")
            print("❌ Full response:")
            print(response.text)
            print("\n❌ Parsed elements:")
            print(f"   sessionId found: {session_id is not None}")
            print(f"   serverUrl found: {server_url is not None}")
            return None

        # Extract instance URL from serverUrl
        instance_url = server_url.text.split('/services')[0]

        print(f"\n✅ Login successful!")
        print(f"   Session ID: {session_id.text[:20]}...")
        print(f"   Server URL: {server_url.text}")
        print(f"   Instance URL: {instance_url}")

        return {
            'access_token': session_id.text,
            'instance_url': instance_url
        }

    except requests.exceptions.Timeout:
        print(f"❌ Login error: Request timed out after 30 seconds")
        print(f"   Check if {INSTANCE_URL} is reachable")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Login error: Connection failed")
        print(f"   Error: {e}")
        print(f"   Check if {INSTANCE_URL} is correct and reachable")
        return None
    except ET.ParseError as e:
        print(f"❌ Login error: Could not parse XML response")
        print(f"   Error: {e}")
        print(f"   Response text: {response.text if 'response' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"❌ Login error: {type(e).__name__}")
        print(f"   Error details: {e}")
        import traceback
        print(f"   Traceback:")
        traceback.print_exc()
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

def read_items_from_file(file_path: str) -> List[str]:
    """
    Read items from text or CSV file.
    - .txt files: one item per line
    - .csv files: reads from "Name" column
    """
    items = []

    try:
        if file_path.endswith('.csv'):
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                if 'Name' not in reader.fieldnames:
                    print(f"❌ CSV file {file_path} must have a 'Name' column")
                    return []
                items = [row['Name'].strip() for row in reader if row['Name'].strip()]
        else:
            # Plain text file - one item per line
            with open(file_path, 'r', encoding='utf-8') as f:
                items = [line.strip() for line in f if line.strip()]

    except FileNotFoundError:
        print(f"⚠️  File not found: {file_path}")
        return []
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return []

    return items

def create_sample_files():
    """Create sample input files if they don't exist"""
    import os

    if not os.path.exists(CATEGORIES_FILE):
        print(f"\n📝 Creating sample {CATEGORIES_FILE}...")
        with open(CATEGORIES_FILE, 'w') as f:
            f.write("Personnel\n")
            f.write("Equipment\n")
            f.write("Travel\n")
            f.write("Supplies\n")
            f.write("Other\n")
        print(f"✅ Created {CATEGORIES_FILE}")

    if not os.path.exists(PERIODS_FILE):
        print(f"\n📝 Creating sample {PERIODS_FILE}...")
        with open(PERIODS_FILE, 'w') as f:
            f.write("Q1 FY2026\n")
            f.write("Q2 FY2026\n")
            f.write("Q3 FY2026\n")
            f.write("Q4 FY2026\n")
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
    description = input("Description (optional): ").strip()

    budget = {
        "Name": budget_name
    }

    if budget_amount:
        try:
            budget["Amount__c"] = float(budget_amount)
        except ValueError:
            print("⚠️  Invalid amount, skipping...")

    if start_date:
        budget["StartDate__c"] = start_date

    if end_date:
        budget["EndDate__c"] = end_date

    if description:
        budget["Description__c"] = description

    return budget

def create_budget_with_children_composite(access_token: str, instance_url: str, budget_data: Dict,
                                         categories: List[str], periods: List[str]) -> Dict:
    """
    Create Budget with related BudgetCategory and BudgetPeriod records using Composite API.

    Uses composite graph to:
    1. Create parent Budget
    2. Create child BudgetCategory records referencing the Budget
    3. Create child BudgetPeriod records referencing the Budget
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Build composite request
    graphs = []

    # 1. Create Budget (parent) - Standard BPO object (no __c suffix)
    budget_ref_id = "Budget1"
    graphs.append({
        "method": "POST",
        "url": f"/services/data/v{API_VERSION}/sobjects/Budget",
        "referenceId": budget_ref_id,
        "body": budget_data
    })

    print(f"\n🔍 DEBUG: Budget request:")
    print(json.dumps(graphs[0], indent=2))

    # 2. Create BudgetCategory records - Standard BPO object (no __c suffix)
    for idx, category_name in enumerate(categories, 1):
        # For standard BPO objects, the lookup field is "BudgetId" not "Budget__c"
        category_body = {
            "Name": category_name,
            "BudgetId": f"@{{{budget_ref_id}.id}}"  # Reference to parent Budget
        }

        print(f"\n🔍 DEBUG: Category {idx} request:")
        print(json.dumps({
            "method": "POST",
            "url": f"/services/data/v{API_VERSION}/sobjects/BudgetCategory",
            "referenceId": f"Category{idx}",
            "body": category_body
        }, indent=2))

        graphs.append({
            "method": "POST",
            "url": f"/services/data/v{API_VERSION}/sobjects/BudgetCategory",
            "referenceId": f"Category{idx}",
            "body": category_body
        })

    # 3. Create BudgetPeriod records - Standard BPO object (no __c suffix)
    for idx, period_name in enumerate(periods, 1):
        # For standard BPO objects, the lookup field is "BudgetId" not "Budget__c"
        period_body = {
            "Name": period_name,
            "BudgetId": f"@{{{budget_ref_id}.id}}"  # Reference to parent Budget
        }

        if idx == 1:  # Only print first one to avoid clutter
            print(f"\n🔍 DEBUG: Period {idx} request:")
            print(json.dumps({
                "method": "POST",
                "url": f"/services/data/v{API_VERSION}/sobjects/BudgetPeriod",
                "referenceId": f"Period{idx}",
                "body": period_body
            }, indent=2))

        graphs.append({
            "method": "POST",
            "url": f"/services/data/v{API_VERSION}/sobjects/BudgetPeriod",
            "referenceId": f"Period{idx}",
            "body": period_body
        })

    # Composite Graph API request
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
    print(f"   • {len(categories)} Categories")
    print(f"   • {len(periods)} Periods")
    print(f"   • Total: {1 + len(categories) + len(periods)} records")

    api_url = f"{instance_url}/services/data/v{API_VERSION}/composite/graph"
    print(f"\n🔍 DEBUG: Composite API details")
    print(f"   URL: {api_url}")
    print(f"   API Version: v{API_VERSION}")
    print(f"   Access Token: {access_token[:20]}...{access_token[-10:]}")
    print(f"   Request payload (first budget):")
    print(f"   {json.dumps(graphs[0], indent=2)}")

    try:
        print(f"\n📤 Making API request...")
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)

        print(f"\n📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        print(f"📥 Response body (first 500 chars):")
        print(response.text[:500])

        if response.status_code not in [200, 201]:
            print(f"\n❌ Composite API request failed!")
            print(f"❌ Status code: {response.status_code}")
            print(f"❌ Full response:")
            print(response.text)

            # Try to parse error details
            try:
                error_data = response.json()
                print(f"\n❌ Parsed error details:")
                print(json.dumps(error_data, indent=2))
            except:
                pass

            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }

        result = response.json()
        print(f"\n✅ API request successful!")
        print(f"✅ Response summary:")
        print(json.dumps(result, indent=2)[:1000])

        return {
            "success": True,
            "result": result
        }

    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 60 seconds")
        return {
            "success": False,
            "error": "Request timeout"
        }
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {type(e).__name__}")
        print(f"   Error details: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}")
        print(f"   Error details: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }

def print_results(result: Dict, instance_url: str):
    """Print creation results"""
    print(f"\n🔍 DEBUG: Processing results...")
    print(f"   Success flag: {result.get('success')}")

    if not result.get("success"):
        print(f"\n❌ Error: {result.get('error')}")
        print(f"\n🔍 DEBUG: Full result object:")
        print(json.dumps(result, indent=2))
        return

    print(f"\n🔍 DEBUG: Result structure:")
    print(f"   Keys in result: {list(result.keys())}")

    graphs_result = result.get("result", {}).get("graphs", [])
    print(f"   graphs found: {len(graphs_result)}")

    if not graphs_result:
        print("\n⚠️  No results returned")
        print(f"\n🔍 DEBUG: Full result:")
        print(json.dumps(result, indent=2))
        return

    composite_response = graphs_result[0].get("compositeResponse", [])
    print(f"   composite responses: {len(composite_response)}")

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

    # Print Budget result
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    if budget_result:
        print(f"\n🔍 DEBUG: Budget result:")
        print(f"   HTTP Status: {budget_result.get('httpStatusCode')}")
        print(f"   Body type: {type(budget_result.get('body'))}")
        print(f"   Body: {json.dumps(budget_result.get('body'), indent=2)}")

        if budget_result.get("httpStatusCode") in [200, 201]:
            budget_id = budget_result.get("body", {}).get("id")
            print(f"\n✅ Budget Created")
            print(f"   ID: {budget_id}")
            print(f"   URL: {instance_url}/lightning/r/Budget__c/{budget_id}/view")
        else:
            errors = budget_result.get("body", [])
            print(f"\n❌ Budget Creation Failed")
            print(f"   HTTP Status: {budget_result.get('httpStatusCode')}")
            print(f"   Error details:")
            for error in errors:
                print(f"   • Message: {error.get('message', 'Unknown error')}")
                print(f"   • Status Code: {error.get('statusCode', 'N/A')}")
                print(f"   • Fields: {error.get('fields', [])}")
                print(f"   • Full error: {json.dumps(error, indent=2)}")

    # Print Category results
    success_categories = [c for c in category_results if c.get("httpStatusCode") in [200, 201]]
    if success_categories:
        print(f"\n✅ Created {len(success_categories)} Budget Categories:")
        for cat in success_categories:
            cat_id = cat.get("body", {}).get("id")
            print(f"   • {cat_id}")

    failed_categories = [c for c in category_results if c.get("httpStatusCode") not in [200, 201]]
    if failed_categories:
        print(f"\n⚠️  {len(failed_categories)} Categories Failed:")
        for idx, cat in enumerate(failed_categories, 1):
            print(f"\n   Category #{idx} (Ref: {cat.get('referenceId')}):")
            print(f"   HTTP Status: {cat.get('httpStatusCode')}")
            errors = cat.get("body", [])
            for error in errors:
                print(f"   • Message: {error.get('message', 'Unknown error')}")
                print(f"   • Status Code: {error.get('statusCode', 'N/A')}")
                print(f"   • Fields: {error.get('fields', [])}")
                if error.get('errorCode'):
                    print(f"   • Error Code: {error.get('errorCode')}")

    # Print Period results
    success_periods = [p for p in period_results if p.get("httpStatusCode") in [200, 201]]
    if success_periods:
        print(f"\n✅ Created {len(success_periods)} Budget Periods:")
        for period in success_periods:
            period_id = period.get("body", {}).get("id")
            print(f"   • {period_id}")

    failed_periods = [p for p in period_results if p.get("httpStatusCode") not in [200, 201]]
    if failed_periods:
        print(f"\n⚠️  {len(failed_periods)} Periods Failed:")
        for idx, period in enumerate(failed_periods, 1):
            print(f"\n   Period #{idx} (Ref: {period.get('referenceId')}):")
            print(f"   HTTP Status: {period.get('httpStatusCode')}")
            errors = period.get("body", [])
            for error in errors:
                print(f"   • Message: {error.get('message', 'Unknown error')}")
                print(f"   • Status Code: {error.get('statusCode', 'N/A')}")
                print(f"   • Fields: {error.get('fields', [])}")
                if error.get('errorCode'):
                    print(f"   • Error Code: {error.get('errorCode')}")

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
    print("Salesforce Budget Creation Tool")
    print("Username/Password Authentication")
    print("Creates Budget + BudgetCategory + BudgetPeriod records")
    print("="*60)

    # Get credentials
    username, password, security_token = get_credentials()

    # Create sample files if needed
    create_sample_files()

    # Read categories and periods
    print(f"\n1. Reading input files...")
    categories = read_items_from_file(CATEGORIES_FILE)
    periods = read_items_from_file(PERIODS_FILE)

    print(f"   • Categories: {len(categories)}")
    print(f"   • Periods: {len(periods)}")

    if not categories and not periods:
        print("\n⚠️  No categories or periods found. Please add them to input files.")
        sys.exit(1)

    # Display what will be created
    if categories:
        print(f"\n   Budget Categories:")
        for cat in categories:
            print(f"      • {cat}")

    if periods:
        print(f"\n   Budget Periods:")
        for period in periods:
            print(f"      • {period}")

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

    # Create records using composite API
    print("\n3. Creating records...")
    result = create_budget_with_children_composite(access_token, instance_url, budget_data, categories, periods)

    # Print results
    print_results(result, instance_url)

if __name__ == "__main__":
    main()
