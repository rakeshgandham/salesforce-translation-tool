#!/usr/bin/env python3
"""
Query Salesforce BPO records, translate their names to French using Google Translate API,
and insert corresponding Translation records.

Supports: FundingAwardRequirementSection, IndividualApplicationTask
"""
import subprocess
import json
import requests
from typing import List, Dict
import time
import sys

# Configuration - UPDATE THESE FOR YOUR ORG
ORG_ALIAS = "your-org-alias"  # Your Salesforce org alias (set via `sf org login`)
INSTANCE_URL = "https://your-instance.salesforce.com"  # Your Salesforce instance URL

# Translation object mappings - ADD MORE AS NEEDED
TRANSLATION_OBJECTS = {
    "FundingAwardRequirementSection": "FundingAwardRqmtSectionTranslation",
    "IndividualApplicationTask": "IndividualApplicationTaskTranslation"
}

# Choose translation method: 'googletrans', 'deep-translator', or 'manual'
TRANSLATION_METHOD = 'googletrans'  # Change to 'deep-translator' if you prefer

def get_access_token():
    """Get access token from SF CLI"""
    try:
        result = subprocess.run(
            ["sf", "org", "display", "--target-org", ORG_ALIAS, "--json"],
            capture_output=True,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        return data["result"]["accessToken"]
    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        print(f"Please run: sf org login web --instance-url {INSTANCE_URL} --alias {ORG_ALIAS}")
        sys.exit(1)

def query_records(access_token: str, object_name: str) -> List[Dict]:
    """Query all records for a given object"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    query = f"SELECT Id, Name FROM {object_name} ORDER BY Name"

    response = requests.get(
        f"{INSTANCE_URL}/services/data/v62.0/query",
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
    """
    Translate text to French using googletrans library
    """
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
    """
    Translate text to French using deep-translator library
    """
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
    """
    Simple French translation helper (fallback).
    Basic word-by-word replacement.
    """
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
    """
    Translate text to French using specified method
    """
    if method == 'googletrans':
        return translate_to_french_googletrans(text)
    elif method == 'deep-translator':
        return translate_to_french_deep_translator(text)
    else:
        return translate_to_french_manual(text)

def insert_translation_records(access_token: str, translations: List[Dict]) -> Dict:
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
            f"{INSTANCE_URL}/services/data/v62.0/composite/sobjects",
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
    print(f"Translation Method: {TRANSLATION_METHOD}")
    print("=" * 60)

    # Validate configuration
    if ORG_ALIAS == "your-org-alias" or INSTANCE_URL == "https://your-instance.salesforce.com":
        print("\n❌ ERROR: Please update ORG_ALIAS and INSTANCE_URL in the script")
        print("   Edit lines 13-14 with your org details")
        sys.exit(1)

    # Get access token
    print("\n1. Authenticating...")
    access_token = get_access_token()
    print("✅ Authenticated successfully")

    all_translations = []

    # Process each object type
    for object_name, translation_object in TRANSLATION_OBJECTS.items():
        print(f"\n2. Processing {object_name}...")

        # Query records
        records = query_records(access_token, object_name)

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
    result = insert_translation_records(access_token, all_translations)

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
