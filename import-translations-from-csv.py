#!/usr/bin/env python3
"""
Import French translations from CSV and create Translation records
"""
import subprocess
import json
import csv
import requests
from typing import List, Dict
import sys

# Configuration - UPDATE THESE FOR YOUR ORG
ORG_ALIAS = "your-org-alias"
INSTANCE_URL = "https://your-instance.salesforce.com"

# Translation object mappings - ADD MORE AS NEEDED
TRANSLATION_OBJECTS = {
    "FundingAwardRequirementSection": "FundingAwardRqmtSectionTranslation",
    "IndividualApplicationTask": "IndividualApplicationTaskTranslation"
}

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
        print(f"❌ Error: {e}")
        sys.exit(1)

def read_translations_from_csv(filename: str) -> List[Dict]:
    """Read translations from CSV file"""
    translations = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["FrenchName"].strip():  # Only include rows with French translation
                translation_object = TRANSLATION_OBJECTS.get(row["ObjectType"])
                if translation_object:
                    translations.append({
                        "attributes": {"type": translation_object},
                        "ParentId": row["RecordId"],
                        "Language": "fr",
                        "Name": row["FrenchName"]
                    })
    return translations

def insert_translations(access_token: str, translations: List[Dict]):
    """Insert translation records"""
    if not translations:
        print("⚠️  No translations to insert")
        return

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Batch in groups of 200 (Salesforce composite API limit)
    batch_size = 200
    total_success = 0

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

        if response.status_code == 200:
            results = response.json()
            success_count = sum(1 for r in results if r.get("success"))
            total_success += success_count
            print(f"✅ Batch {i // batch_size + 1}: {success_count}/{len(batch)} succeeded")

            # Show failures
            failures = [r for r in results if not r.get("success")]
            for f in failures:
                print(f"  ⚠️  {f.get('errors', [{}])[0].get('message')}")
        else:
            print(f"❌ Batch {i // batch_size + 1} failed: {response.text}")

    print(f"\n✅ Total: {total_success}/{len(translations)} translations inserted")

def main():
    # Validate configuration
    if ORG_ALIAS == "your-org-alias" or INSTANCE_URL == "https://your-instance.salesforce.com":
        print("\n❌ ERROR: Please update ORG_ALIAS and INSTANCE_URL in the script")
        print("   Edit lines 13-14 with your org details")
        sys.exit(1)

    csv_file = "records-for-translation.csv"

    print("=" * 60)
    print("Importing French Translations")
    print("=" * 60)

    # Read CSV
    print(f"\n1. Reading {csv_file}...")
    try:
        translations = read_translations_from_csv(csv_file)
        print(f"✅ Found {len(translations)} translations to import")
    except FileNotFoundError:
        print(f"❌ File not found: {csv_file}")
        print("Please run: python3 export-for-translation.py first")
        return
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    if not translations:
        print("⚠️  No translations found in CSV. Make sure FrenchName column is filled.")
        return

    # Get access token
    print("\n2. Authenticating...")
    access_token = get_access_token()

    # Insert translations
    print("\n3. Inserting translations...")
    insert_translations(access_token, translations)

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == "__main__":
    main()
