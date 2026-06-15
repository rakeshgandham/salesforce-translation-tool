# Budget Creation Script

This script creates a Budget sObject along with related BudgetCategory and BudgetPeriod records in Salesforce using the Composite Graph API.

## Features

- ✅ Creates Budget parent record with child BudgetCategory and BudgetPeriod records in a single API call
- ✅ Uses Composite Graph API for efficient bulk creation
- ✅ Reads categories and periods from text files or CSV files
- ✅ Automatic reference resolution between parent and child records
- ✅ Interactive prompts for budget details
- ✅ Detailed result reporting

## Prerequisites

1. **Salesforce CLI** installed and authenticated:
   ```bash
   sf org login web --instance-url https://your-instance.salesforce.com --alias your-org-alias
   ```

2. **Python 3.7+** with requests library:
   ```bash
   pip3 install requests
   ```

3. **Custom Objects** in your Salesforce org:
   - `Budget__c` (parent)
   - `BudgetCategory__c` (child with lookup to Budget__c)
   - `BudgetPeriod__c` (child with lookup to Budget__c)

## Configuration

Edit `create-budget-with-categories-periods.py` and update:

```python
ORG_ALIAS = "your-org-alias"  # Your SF org alias
INSTANCE_URL = "https://your-instance.salesforce.com"  # Your SF instance URL
```

## Input Files

### Option 1: Text Files (Simple)

**budget_categories.txt** - One category per line:
```
Personnel
Equipment
Travel
Supplies
```

**budget_periods.txt** - One period per line:
```
Q1 FY2026
Q2 FY2026
Q3 FY2026
Q4 FY2026
```

### Option 2: CSV Files (With Additional Fields)

**budget_categories.csv**:
```csv
Name,Description
Personnel,Salaries and wages
Equipment,Hardware and software
Travel,Business travel expenses
```

**budget_periods.csv**:
```csv
Name,StartDate,EndDate
Q1 FY2026,2025-10-01,2025-12-31
Q2 FY2026,2026-01-01,2026-03-31
```

> **Note**: Currently, the script only uses the `Name` column from CSV files. You can extend the script to use additional columns.

## Usage

1. **Prepare input files**:
   ```bash
   # Edit the files with your categories and periods
   vi budget_categories.txt
   vi budget_periods.txt
   ```

2. **Run the script**:
   ```bash
   python3 create-budget-with-categories-periods.py
   ```

3. **Enter budget details** when prompted:
   - Budget Name (required)
   - Total Budget Amount (optional)
   - Start Date (optional, YYYY-MM-DD format)
   - End Date (optional, YYYY-MM-DD format)
   - Description (optional)

4. **Review and confirm** the records to be created

5. **View results** including:
   - Budget record ID and URL
   - Number of categories created
   - Number of periods created
   - Any errors encountered

## Example Session

```
==============================================================
Salesforce Budget Creation Tool
Creates Budget + BudgetCategory + BudgetPeriod records
==============================================================

1. Reading input files...
   • Categories: 8
   • Periods: 4

   Budget Categories:
      • Personnel
      • Equipment
      • Travel
      • Supplies
      • Consulting Services
      • Training and Development
      • Marketing
      • Other Direct Costs

   Budget Periods:
      • Q1 FY2026
      • Q2 FY2026
      • Q3 FY2026
      • Q4 FY2026

==============================================================
Enter Budget Details
==============================================================
Budget Name: FY2026 Operations Budget
Total Budget Amount (optional): 500000
Start Date (YYYY-MM-DD) (optional): 2025-10-01
End Date (YYYY-MM-DD) (optional): 2026-09-30
Description (optional): Annual operations budget for FY2026

==============================================================
Ready to create:
   • 1 Budget: FY2026 Operations Budget
   • 8 Categories
   • 4 Periods

Continue? (y/N): y

2. Authenticating...
✅ Authenticated successfully

3. Creating records...

📤 Sending composite request...
   • 1 Budget
   • 8 Categories
   • 4 Periods
   • Total: 13 records

==============================================================
RESULTS
==============================================================

✅ Budget Created
   ID: a0x5e000001AbCdEAK
   URL: https://your-instance.salesforce.com/lightning/r/Budget__c/a0x5e000001AbCdEAK/view

✅ Created 8 Budget Categories:
   • a0y5e000001XyZ1AAK
   • a0y5e000001XyZ2AAK
   • a0y5e000001XyZ3AAK
   • a0y5e000001XyZ4AAK
   • a0y5e000001XyZ5AAK
   • a0y5e000001XyZ6AAK
   • a0y5e000001XyZ7AAK
   • a0y5e000001XyZ8AAK

✅ Created 4 Budget Periods:
   • a0z5e000001Pqr1AAC
   • a0z5e000001Pqr2AAC
   • a0z5e000001Pqr3AAC
   • a0z5e000001Pqr4AAC

==============================================================
Summary: 13 created, 0 failed
==============================================================
```

## How It Works

### Composite Graph API

The script uses Salesforce's Composite Graph API to create all records in a single HTTP request:

1. **Creates parent Budget** record first
2. **References the Budget ID** using `@{Budget1.id}` syntax
3. **Creates child records** (Categories and Periods) that reference the parent

This approach:
- ✅ Reduces API calls (1 call instead of 13 separate calls)
- ✅ Maintains referential integrity
- ✅ Provides atomic transaction-like behavior
- ✅ Faster execution

### Request Structure

```json
{
  "graphs": [{
    "graphId": "BudgetCreation",
    "compositeRequest": [
      {
        "method": "POST",
        "url": "/services/data/v62.0/sobjects/Budget__c",
        "referenceId": "Budget1",
        "body": {"Name": "FY2026 Budget"}
      },
      {
        "method": "POST",
        "url": "/services/data/v62.0/sobjects/BudgetCategory__c",
        "referenceId": "Category1",
        "body": {
          "Name": "Personnel",
          "Budget__c": "@{Budget1.id}"
        }
      }
      // ... more categories and periods
    ]
  }]
}
```

## Extending the Script

### Add More Budget Fields

Edit the `get_budget_details()` function to prompt for additional fields:

```python
fiscal_year = input("Fiscal Year (optional): ").strip()
if fiscal_year:
    budget["FiscalYear__c"] = fiscal_year
```

### Use CSV Additional Columns

Modify the `read_items_from_file()` function to return dictionaries with all fields:

```python
def read_items_from_csv(file_path: str) -> List[Dict]:
    items = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        items = [row for row in reader]
    return items
```

Then update the composite request to include additional fields:

```python
graphs.append({
    "method": "POST",
    "url": "/services/data/v62.0/sobjects/BudgetCategory__c",
    "referenceId": f"Category{idx}",
    "body": {
        "Name": category["Name"],
        "Description__c": category.get("Description", ""),
        "Budget__c": f"@{{{budget_ref_id}.id}}"
    }
})
```

### Create Multiple Budgets

Wrap the main logic in a loop to read multiple budgets from a CSV file.

## Troubleshooting

### Authentication Issues

```
❌ Error getting access token
```

**Solution**: Authenticate with Salesforce CLI:
```bash
sf org login web --instance-url https://your-instance.salesforce.com --alias your-org-alias
```

### Field Validation Errors

```
⚠️  1 Categories Failed:
   • Required field missing: Budget__c
```

**Solution**: Check that your custom objects have the correct field API names and required fields.

### API Version Issues

If using an older Salesforce org, update the API version in the script:
```python
# Change from v62.0 to your org's API version
url = "/services/data/v61.0/sobjects/Budget__c"
```

### File Not Found

```
⚠️  File not found: budget_categories.txt
```

**Solution**: The script will auto-create sample files on first run, or create them manually as shown in the Input Files section.

## API Limits

- **Composite Graph API**: Maximum 500 requests per graph
- **This script**: Creates 1 Budget + N Categories + M Periods per execution
- **Example**: 1 Budget + 50 Categories + 12 Periods = 63 requests (well within limit)

## Related Scripts

- `query-and-translate-records.py` - Query and translate BPO records
- `export-for-translation.py` - Export records for translation
- `import-translations-from-csv.py` - Import translations from CSV

## License

This script is provided as-is for use with Salesforce orgs.
