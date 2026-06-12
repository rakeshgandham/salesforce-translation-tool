#!/usr/bin/env python3
"""
Export Salesforce BPO records to CSV for manual French translation review.
"""
import subprocess
import json
import csv
import requests
import sys

# Configuration - UPDATE THESE FOR YOUR ORG
ORG_ALIAS = "your-org-alias"
INSTANCE_URL = "https://your-instance.salesforce.com"

# Objects to export - ADD MORE AS NEEDED
OBJECTS_TO_EXPORT = [
    "FundingAwardRequirementSection",
    "IndividualApplicationTask"
]

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
        print(f"Please run: sf org login web --instance-url {INSTANCE_URL} --alias {ORG_ALIAS}")
        sys.exit(1)

def main():
    # Validate configuration
    if ORG_ALIAS == "your-org-alias" or INSTANCE_URL == "https://your-instance.salesforce.com":
        print("\n❌ ERROR: Please update ORG_ALIAS and INSTANCE_URL in the script")
        print("   Edit lines 12-13 with your org details")
        sys.exit(1)

    print("Exporting records for translation...")
    access_token = get_access_token()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    all_records = []

    for object_name in OBJECTS_TO_EXPORT:
        query = f"SELECT Id, Name FROM {object_name} ORDER BY Name"
        response = requests.get(
            f"{INSTANCE_URL}/services/data/v62.0/query",
            headers=headers,
            params={"q": query}
        )

        if response.status_code == 200:
            records = response.json().get("records", [])
            for record in records:
                all_records.append({
                    "ObjectType": object_name,
                    "RecordId": record["Id"],
                    "EnglishName": record["Name"],
                    "FrenchName": ""  # To be filled manually
                })
            print(f"✅ Exported {len(records)} {object_name} records")
        else:
            print(f"❌ Error querying {object_name}: {response.text}")

    # Write to CSV
    csv_file = "records-for-translation.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["ObjectType", "RecordId", "EnglishName", "FrenchName"])
        writer.writeheader()
        writer.writerows(all_records)

    print(f"\n✅ Exported {len(all_records)} records to {csv_file}")
    print("\nNext steps:")
    print("1. Open records-for-translation.csv")
    print("2. Fill in the FrenchName column")
    print("3. Run: python3 import-translations-from-csv.py")

if __name__ == "__main__":
    main()
