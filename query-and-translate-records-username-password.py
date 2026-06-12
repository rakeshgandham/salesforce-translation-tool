#!/usr/bin/env python3
"""
Query Salesforce BPO records, translate their names to French using Google Translate API,
and insert corresponding Translation records.

Authentication: Username + Password + Security Token

Supports: FundingAwardRequirementSection, IndividualApplicationTask
"""
import json
import requests
from typing import List, Dict
import time
import sys

# ============================================================================
# CONFIGURATION - UPDATE THESE FOR YOUR ORG
# ============================================================================

# Salesforce Credentials
SALESFORCE_USERNAME = "your-username@example.com"
SALESFORCE_PASSWORD = "your-password"
SALESFORCE_SECURITY_TOKEN = "your-security-token"  # Get from Setup > My Personal Information > Reset Security Token

# Salesforce Instance (usually 'login' for production, 'test' for sandbox)
SALESFORCE_DOMAIN = "login.salesforce.com"  # or "test.salesforce.com" for sandbox

# Translation object mappings - ADD MORE AS NEEDED
TRANSLATION_OBJECTS = {
    "FundingAwardRequirementSection": "FundingAwardRqmtSectionTranslation",
    "IndividualApplicationTask": "IndividualApplicationTaskTranslation"
}

# Choose translation method: 'googletrans', 'deep-translator', or 'manual'
TRANSLATION_METHOD = 'googletrans'

# ============================================================================
# DO NOT EDIT BELOW THIS LINE
# ============================================================================

def salesforce_login(username: str, password: str, security_token: str, domain: str) -> Dict:
    """
    Login to Salesforce using username/password/security token
    Returns: dict with 'access_token' and 'instance_url'
    """
    login_url = f"https://{domain}/services/oauth2/token"

    payload = {
        "grant_type": "password",
        "client_id": "3MVG9_XwsqeYoue6F7LxOe.qYQF0dNJOhGLxaQQU_y7h8vCN7xKYPq1a8wv_Jq0cJqH8_qYh2qYQF0dNJOhGLx",  # Generic Connected App
        "client_secret": "1234567890123456789",  # Generic Connected App
        "username": username,
        "password": password + security_token  # Concatenate password and security token
    }

    try:
        response = requests.post(login_url, data=payload)
        response.raise_for_status()
        data = response.json()

        return {
            "access_token": data["access_token"],
            "instance_url": data["instance_url"]
        }
    except requests.exceptions.HTTPError as e:
        print(f"❌ Login failed: {e}")
        if response.status_code == 400:
            error_data = response.json()
            print(f"   Error: {error_data.get('error_description', 'Invalid credentials')}")
            print("\n   Common issues:")
            print("   1. Password + Security Token must be concatenated (no space)")
            print("   2. Security Token may have expired - reset it in Salesforce Setup")
            print("   3. IP address may be restricted - check Salesforce Login History")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during login: {e}")
        sys.exit(1)

def query_records(access_token: str, instance_url: str, object_name: str) -> List[Dict]:
    """Query all records for a given object"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    query = f"SELECT Id, Name FROM {object_name} ORDER BY Name"

    response = requests.get(
        f"{instance_url}/services/data/v62.0/query",
        headers=headers,
        params={"q": query}
    )

    if response.status_code != 200:
        print(f"❌ Error querying {object_name}: {response.text}")
        return []

    records = response.json().get("records", [])
    print(f"✅ Found {len(records)} {object_name} records")
    return records

def translate_to_french_googletrans(text: str) -> str:
    """Translate text to French using googletrans library"""
    try:
        from googletrans import Translator
        translator = Translator()
        result = translator.translate(text, src='en', dest='fr')
        return result.text
    except ImportError:
        print("❌ googletrans library not installed.")
        print("   Run: pip3 install googletrans==4.0.0-rc1")
        print("   Falling back to manual translation...")
        return translate_to_french_manual(text)
    except Exception as e:
        print(f"⚠️  Translation error: {e}. Using original text.")
        return text

def translate_to_french_deep_translator(text: str) -> str:
    """Translate text to French using deep-translator library"""
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source='en', target='fr')
        return translator.translate(text)
    except ImportError:
        print("❌ deep-translator library not installed.")
        print("   Run: pip3 install deep-translator")
        print("   Falling back to manual translation...")
        return translate_to_french_manual(text)
    except Exception as e:
        print(f"⚠️  Translation error: {e}. Using original text.")
        return text

def translate_to_french_manual(text: str) -> str:
    """Simple French translation helper (fallback)"""
    translations = {
        "Section": "Section",
        "Task": "Tâche",
        "Application": "Demande",
        "Individual": "Individuel",
        "Funding": "Financement",
        "Award": "Attribution",
        "Requirement": "Exigence",
        "Review": "Révision",
        "Eligibility": "Éligibilité"
    }

    result = text
    for en, fr in translations.items():
        result = result.replace(en, fr)

    return result

def translate_to_french(text: str, method: str = 'googletrans') -> str:
    """Translate text to French using specified method"""
    if method == 'googletrans':
        return translate_to_french_googletrans(text)
    elif method == 'deep-translator':
        return translate_to_french_deep_translator(text)
    else:
        return translate_to_french_manual(text)

def insert_translation_records(access_token: str, instance_url: str, translations: List[Dict]) -> Dict:
    """Insert translation records using Composite API"""
    if not translations:
        return {"success": True, "count": 0}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Batch in groups of 200 (Salesforce composite API limit)
    batch_size = 200
    all_results = []

    for i in range(0, len(translations), batch_size):
        batch = translations[i:i + batch_size]

        payload = {
            "allOrNone": False,
            "records": batch
        }

        response = requests.post(
            f"{instance_url}/services/data/v62.0/composite/sobjects",
            headers=headers,
            json=payload
        )

        if response.status_code != 200:
            print(f"❌ Error inserting batch {i // batch_size + 1}: {response.text}")
            continue

        results = response.json()
        all_results.extend(results)

    success_count = sum(1 for r in all_results if r.get("success"))

    return {
        "success": True,
        "count": success_count,
        "total": len(translations),
        "results": all_results
    }

def main():
    print("=" * 60)
    print("Salesforce BPO Record French Translation Tool")
    print("Authentication: Username/Password/Security Token")
    print(f"Translation Method: {TRANSLATION_METHOD}")
    print("=" * 60)

    # Validate configuration
    if SALESFORCE_USERNAME == "your-username@example.com":
        print("\n❌ ERROR: Please update credentials in the script")
        print("   Edit lines 19-21:")
        print("   - SALESFORCE_USERNAME")
        print("   - SALESFORCE_PASSWORD")
        print("   - SALESFORCE_SECURITY_TOKEN")
        print("\n   To get your security token:")
        print("   Setup > My Personal Information > Reset My Security Token")
        sys.exit(1)

    # Login to Salesforce
    print("\n1. Authenticating with Salesforce...")
    print(f"   Domain: {SALESFORCE_DOMAIN}")
    print(f"   Username: {SALESFORCE_USERNAME}")

    auth = salesforce_login(
        SALESFORCE_USERNAME,
        SALESFORCE_PASSWORD,
        SALESFORCE_SECURITY_TOKEN,
        SALESFORCE_DOMAIN
    )

    access_token = auth["access_token"]
    instance_url = auth["instance_url"]

    print(f"✅ Authenticated successfully")
    print(f"   Instance: {instance_url}")

    all_translations = []

    # Process each object type
    for object_name, translation_object in TRANSLATION_OBJECTS.items():
        print(f"\n2. Processing {object_name}...")

        # Query records
        records = query_records(access_token, instance_url, object_name)

        if not records:
            print(f"⚠️  No records found for {object_name}")
            continue

        # Display records and prepare translations
        print(f"\nTranslating {len(records)} records:")
        for idx, record in enumerate(records, 1):
            # Translate to French
            french_name = translate_to_french(record["Name"], TRANSLATION_METHOD)

            print(f"  {idx}. {record['Name']:<40} → {french_name}")

            # Prepare translation record
            all_translations.append({
                "attributes": {"type": translation_object},
                "ParentId": record["Id"],
                "Language": "fr",
                "Name": french_name
            })

            # Small delay to avoid rate limiting
            if TRANSLATION_METHOD in ['googletrans', 'deep-translator']:
                time.sleep(0.1)

    if not all_translations:
        print("\n⚠️  No translations to insert")
        return

    # Ask for confirmation
    print(f"\n{'='*60}")
    print(f"Ready to insert {len(all_translations)} translation records.")
    response = input("Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Aborted by user")
        return

    # Insert translations
    print(f"\n3. Inserting {len(all_translations)} translation records...")
    result = insert_translation_records(access_token, instance_url, all_translations)

    if result.get("success"):
        print(f"\n✅ Successfully inserted {result['count']}/{result['total']} translations")

        # Show any failures
        failures = [r for r in result.get("results", []) if not r.get("success")]
        if failures:
            print(f"\n⚠️  {len(failures)} translations failed:")
            for f in failures:
                error_msg = f.get('errors', [{}])[0].get('message', 'Unknown error')
                print(f"  • {error_msg}")
    else:
        print(f"\n❌ Failed to insert translations: {result.get('error')}")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
