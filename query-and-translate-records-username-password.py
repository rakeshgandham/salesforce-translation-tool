#!/usr/bin/env python3
"""
Query and translate records - Username/Password authentication
Uses Salesforce SOAP API for login
"""
import json
import requests
from typing import List, Dict
import time
import xml.etree.ElementTree as ET

# Configuration - UPDATE THESE
INSTANCE_URL = "" 
USERNAME = "***********"  # Your Salesforce username
PASSWORD = "Test1234"  # Your password
SECURITY_TOKEN = ""  # Your security token (leave empty if not required)
API_VERSION = "67.0"  # Salesforce API version (change if needed: 61.0, 62.0, 68.0, etc.)

# Translation object mappings
TRANSLATION_OBJECTS = {
    "ActionPlan": "ActionPlanDataTranslation",
    "FundingAwardRqmtSection": "FundingAwardRqmtSectionDataTranslation",
    "IndividualApplicationTask": "IndividualApplicationTaskDataTranslation",
    "IntakeFormSection": "IntakeFormSectionDataTranslation"
}

TRANSLATION_METHOD = 'googletrans'

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
    global USERNAME, PASSWORD, SECURITY_TOKEN

    if not USERNAME:
        print("=" * 60)
        print("Salesforce Login")
        print("=" * 60)
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

def check_object_exists(access_token: str, instance_url: str, object_name: str) -> bool:
    """Check if an object exists in the org"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(
            f"{instance_url}/services/data/v{API_VERSION}/sobjects/{object_name}/describe",
            headers=headers
        )
        return response.status_code == 200
    except:
        return False

def query_records(access_token: str, instance_url: str, object_name: str) -> List[Dict]:
    """Query all records for a given object"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    query = f"SELECT Id, Name FROM {object_name} ORDER BY Name"

    response = requests.get(
        f"{instance_url}/services/data/v{API_VERSION}/query",
        headers=headers,
        params={"q": query}
    )

    if response.status_code != 200:
        error_data = response.json()
        error_code = error_data[0].get("errorCode") if error_data else "UNKNOWN"

        if error_code == "INVALID_TYPE":
            print(f"⚠️  {object_name} does not exist in this org (skipping)")
        else:
            print(f"❌ Error querying {object_name}: {response.text}")
        return []

    records = response.json().get("records", [])
    print(f"✅ Found {len(records)} {object_name} records")
    return records

def translate_to_french_googletrans(text: str) -> str:
    """Translate using googletrans"""
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, src='en', dest='fr')
        return result.text
    except ImportError:
        print("❌ googletrans not installed. Run: pip3 install googletrans==4.0.0-rc1")
        return text
    except Exception as e:
        print(f"⚠️  Translation error: {e}")
        return text

def translate_to_french_deep_translator(text: str) -> str:
    """Translate using deep-translator"""
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='fr')
        return translator.translate(text)
    except ImportError:
        print("❌ deep-translator not installed. Run: pip3 install deep-translator")
        return text
    except Exception as e:
        print(f"⚠️  Translation error: {e}")
        return text

def translate_to_french(text: str, method: str = 'googletrans') -> str:
    """Translate text to French"""
    if method == 'googletrans':
        return translate_to_french_googletrans(text)
    elif method == 'deep-translator':
        return translate_to_french_deep_translator(text)
    else:
        return text

def check_existing_translations(access_token: str, instance_url: str, parent_ids: List[str], translation_object: str, language: str = 'fr') -> set:
    """
    Check which parent IDs already have translation records
    Returns: set of parent IDs that already have translations
    """
    if not parent_ids:
        return set()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Build query to check existing translations
    parent_ids_str = "','".join(parent_ids)
    query = f"SELECT ParentId FROM {translation_object} WHERE ParentId IN ('{parent_ids_str}') AND Language = '{language}'"

    try:
        response = requests.get(
            f"{instance_url}/services/data/v{API_VERSION}/query",
            headers=headers,
            params={"q": query}
        )

        if response.status_code != 200:
            print(f"⚠️  Could not check existing translations for {translation_object}: {response.text}")
            return set()

        records = response.json().get("records", [])
        existing_parent_ids = {record["ParentId"] for record in records}

        if existing_parent_ids:
            print(f"   ℹ️  Found {len(existing_parent_ids)} existing translations, will skip those")

        return existing_parent_ids

    except Exception as e:
        print(f"⚠️  Error checking existing translations: {e}")
        return set()

def insert_translation_records(access_token: str, instance_url: str, translations: List[Dict]) -> Dict:
    """Insert translation records (skipping those that already exist)"""
    if not translations:
        return {"success": True, "count": 0, "skipped": 0}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Group translations by object type to check existing records
    translations_by_type = {}
    for trans in translations:
        obj_type = trans["attributes"]["type"]
        if obj_type not in translations_by_type:
            translations_by_type[obj_type] = []
        translations_by_type[obj_type].append(trans)

    # Check existing translations for each object type
    filtered_translations = []
    total_skipped = 0

    for obj_type, trans_list in translations_by_type.items():
        parent_ids = [t["ParentId"] for t in trans_list]
        language = trans_list[0].get("Language", "fr")

        existing_parent_ids = check_existing_translations(access_token, instance_url, parent_ids, obj_type, language)

        # Filter out translations that already exist
        for trans in trans_list:
            if trans["ParentId"] in existing_parent_ids:
                total_skipped += 1
            else:
                filtered_translations.append(trans)

    if total_skipped > 0:
        print(f"\n⏭️  Skipping {total_skipped} records that already have translations")

    if not filtered_translations:
        print("✅ All records already have translations, nothing to insert")
        return {"success": True, "count": 0, "skipped": total_skipped, "total": len(translations)}

    # Insert only the new translations
    batch_size = 200
    all_results = []

    for i in range(0, len(filtered_translations), batch_size):
        batch = filtered_translations[i:i + batch_size]
        payload = {"allOrNone": False, "records": batch}

        response = requests.post(
            f"{instance_url}/services/data/v{API_VERSION}/composite/sobjects",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            all_results.extend(response.json())
        else:
            print(f"❌ Batch {i // batch_size + 1} failed: {response.text}")

    success_count = sum(1 for r in all_results if r.get("success"))
    return {
        "success": True,
        "count": success_count,
        "total": len(translations),
        "skipped": total_skipped,
        "results": all_results
    }

def main():
    print("=" * 60)
    print("French Translation Generator")
    print("Username/Password Authentication")
    print("=" * 60)

    # Get credentials
    username, password, security_token = get_credentials()

    # Login
    print("\n1. Logging in...")
    auth_result = login_with_password(username, password, security_token)

    if not auth_result:
        print("\n❌ Login failed. Please check:")
        print("  - Username is correct")
        print("  - Password is correct")
        print("  - Security token is required and correct (if needed)")
        print("  - Your IP is trusted, or you're using security token")
        return

    access_token = auth_result['access_token']
    instance_url = auth_result['instance_url']

    print(f"✅ Logged in successfully")
    print(f"   Instance URL: {instance_url}")
    print(f"   API Version: v{API_VERSION}")
    print(f"\n   Note: If you see 'object not supported' errors, try changing")
    print(f"         the API_VERSION setting at the top of the script.")

    all_translations = []

    # Process each object
    for object_name, translation_object in TRANSLATION_OBJECTS.items():
        print(f"\n2. Processing {object_name}...")

        # Check if object exists first
        if not check_object_exists(access_token, instance_url, object_name):
            print(f"   ⚠️  {object_name} does not exist in this org (skipping)")
            continue

        records = query_records(access_token, instance_url, object_name)

        if not records:
            print(f"   ℹ️  No records found for {object_name}")
            continue

        print(f"\nTranslating {len(records)} records:")
        for idx, record in enumerate(records, 1):
            french_name = translate_to_french(record["Name"], TRANSLATION_METHOD)
            print(f"  {idx}. {record['Name']:<40} → {french_name}")

            all_translations.append({
                "attributes": {"type": translation_object},
                "ParentId": record["Id"],
                "Language": "fr",
                "Name": french_name
            })
            time.sleep(0.1)

    if not all_translations:
        print("\n⚠️  No translations to insert")
        return

    # Confirm
    print(f"\n{'='*60}")
    confirm = input(f"Insert {len(all_translations)} translation records? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Aborted")
        return

    # Insert
    print(f"\n3. Inserting translations...")
    result = insert_translation_records(access_token, instance_url, all_translations)

    # Summary
    skipped = result.get('skipped', 0)
    if skipped > 0:
        print(f"\n⏭️  Skipped {skipped} records (already have translations)")

    print(f"✅ Successfully inserted {result['count']} new translation records")

    if result['count'] > 0 or skipped > 0:
        print(f"   Total processed: {result.get('total', 0)} records")

    # Show failures
    failures = [r for r in result.get("results", []) if not r.get("success")]
    if failures:
        print(f"\n⚠️  {len(failures)} translations failed:")
        for f in failures:
            error_msg = f.get('errors', [{}])[0].get('message', 'Unknown error')
            print(f"  • {error_msg}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
