#!/usr/bin/env python3
"""
Quick script to check Budget object fields and relationships
"""
import json
import requests
import sys
import xml.etree.ElementTree as ET

# Configuration
INSTANCE_URL = "https://gandham.my.salesforce-com.ut5fm8x39smv0pzcasy21xozj16.wc.crm.dev:6101"
USERNAME = "rgandham_gmtesting@salesforce.com"
PASSWORD = "Test1234"
SECURITY_TOKEN = ""
API_VERSION = "66.0"

def login_with_password(username: str, password: str, security_token: str = ""):
    """Login to Salesforce using SOAP API"""
    password_with_token = password + security_token
    soap_url = f"{INSTANCE_URL}/services/Soap/u/64.0"

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
        response = requests.post(soap_url, data=soap_body, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            return None

        root = ET.fromstring(response.text)
        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'urn': 'urn:partner.soap.sforce.com'
        }

        session_id = root.find('.//urn:sessionId', namespaces)
        server_url = root.find('.//urn:serverUrl', namespaces)

        if session_id is None or server_url is None:
            print("❌ Could not parse login response")
            return None

        instance_url = server_url.text.split('/services')[0]

        return {
            'access_token': session_id.text,
            'instance_url': instance_url
        }
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def describe_object(access_token: str, instance_url: str, object_name: str):
    """Get object metadata"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    url = f"{instance_url}/services/data/v{API_VERSION}/sobjects/{object_name}/describe"

    print(f"\n🔍 Describing {object_name}...")
    print(f"   URL: {url}")

    response = requests.get(url, headers=headers)

    print(f"   Status: {response.status_code}")

    if response.status_code == 200:
        return response.json()
    else:
        print(f"   Error: {response.text}")
        return None

def main():
    print("="*60)
    print("Budget Object Field Checker")
    print("="*60)

    # Login
    print("\n1. Authenticating...")
    auth_result = login_with_password(USERNAME, PASSWORD, SECURITY_TOKEN)

    if not auth_result:
        print("❌ Authentication failed")
        sys.exit(1)

    access_token = auth_result['access_token']
    instance_url = auth_result['instance_url']
    print(f"✅ Authenticated!")

    # Check each object - These are standard BPO objects (no __c suffix)
    objects_to_check = [
        "Budget",
        "BudgetCategory",
        "BudgetPeriod"
    ]

    for obj_name in objects_to_check:
        metadata = describe_object(access_token, instance_url, obj_name)

        if metadata:
            print(f"\n{'='*60}")
            print(f"Object: {metadata.get('name')}")
            print(f"Label: {metadata.get('label')}")
            print(f"{'='*60}")

            # Show all fields
            print(f"\nAll Fields:")
            for field in metadata.get('fields', []):
                print(f"  • {field.get('name')} ({field.get('type')}) - {field.get('label')}")

            # Show lookup/master-detail relationships
            print(f"\nRelationship Fields:")
            for field in metadata.get('fields', []):
                if field.get('type') in ['reference', 'masterdetail']:
                    print(f"  • {field.get('name')} ({field.get('type')})")
                    print(f"    - Label: {field.get('label')}")
                    print(f"    - Reference To: {field.get('referenceTo')}")
                    print(f"    - Relationship Name: {field.get('relationshipName')}")

            # Show child relationships
            if metadata.get('childRelationships'):
                print(f"\nChild Relationships:")
                for child in metadata.get('childRelationships', []):
                    if child.get('relationshipName'):
                        print(f"  • {child.get('relationshipName')}")
                        print(f"    - Child Object: {child.get('childSObject')}")
                        print(f"    - Field: {child.get('field')}")

        print("\n")

if __name__ == "__main__":
    main()
