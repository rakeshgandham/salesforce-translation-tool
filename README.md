# Salesforce Automation Scripts

Collection of Python scripts for Salesforce data management and automation.

## Scripts

1. **[Budget Creation Tool](#budget-creation-tool)** - Create Budget records with related Categories and Periods
2. **[BPO Record Translation Tool](#bpo-record-translation-tool)** - Translate BPO record names to French

---

## Budget Creation Tool

Create Budget sObjects with related BudgetCategory and BudgetPeriod records using Salesforce Composite Graph API.

### Available Scripts

| Script | Authentication | Best For |
|--------|---------------|----------|
| `create-budget-with-categories-periods.py` | Salesforce CLI | Developers with CLI |
| `create-budget-with-categories-periods-username-password.py` | Username/Password | Automation, no CLI needed |
| `create-budget-enhanced-csv.py` | Salesforce CLI | Full CSV import with CLI |
| `create-budget-enhanced-csv-username-password.py` | Username/Password | Full CSV import, no CLI |

### Quick Start (Salesforce CLI)

```bash
# 1. Install dependencies & authenticate
pip3 install requests
sf org login web --alias myorg

# 2. Configure the script
vi create-budget-with-categories-periods.py
# Update ORG_ALIAS and INSTANCE_URL

# 3. Prepare input files
cat > budget_categories.txt << EOF
Personnel
Equipment
Travel
Supplies
EOF

cat > budget_periods.txt << EOF
Q1 FY2026
Q2 FY2026
Q3 FY2026
Q4 FY2026
EOF

# 4. Run the script
python3 create-budget-with-categories-periods.py
```

### Quick Start (Username/Password)

```bash
# 1. Install dependencies
pip3 install requests

# 2. Run script (will prompt for credentials)
python3 create-budget-with-categories-periods-username-password.py
# Enter: Instance URL, Username, Password, Security Token (if needed)
```

### Features

- ✅ **Single API call** - Creates Budget + all child records in one Composite Graph request
- ✅ **Two authentication methods** - Salesforce CLI or Username/Password
- ✅ **Flexible input** - Supports both text files and CSV files
- ✅ **Automatic relationships** - Parent-child references resolved automatically
- ✅ **Interactive** - Prompts for budget details and credentials
- ✅ **Detailed results** - Reports success/failure with direct record links

### Documentation

- 📖 [Full Documentation](./BUDGET_CREATION_README.md)
- 🚀 [Quick Start Guide](./QUICK_START_BUDGET.md)
- 🔐 [Authentication Guide](./AUTHENTICATION_GUIDE.md) - Choose your auth method

### Sample Files Included

- `budget_categories.txt` - Simple text format
- `budget_periods.txt` - Simple text format  
- `budget_categories.csv` - CSV with additional fields
- `budget_periods.csv` - CSV with date ranges

---

## BPO Record Translation Tool

Automated tool to translate Salesforce BPO record names to multiple languages and create corresponding Translation records.

### Supported Objects

- `ActionPlan` → `ActionPlanDataTranslation`
- `FundingAwardRqmtSection` → `FundingAwardRqmtSectionDataTranslation`
- `IndividualApplicationTask` → `IndividualApplicationTaskDataTranslation`
- `IntakeFormSection` → `IntakeFormSectionDataTranslation`
- `BudgetCategory` → `BudgetCategoryDataTranslation`
- `BudgetPeriod` → `BudgetPeriodDataTranslation`

Easily extensible to support additional objects.

### Supported Languages

**Popular**: French, Spanish, German, Italian, Portuguese, Japanese, Chinese (Simplified)

**All Languages**: French (fr), Spanish (es), German (de), Italian (it), Portuguese (pt), Japanese (ja), Chinese Simplified (zh-cn), Chinese Traditional (zh-tw), Korean (ko), Arabic (ar), Hindi (hi), Russian (ru), Dutch (nl), Polish (pl), Turkish (tr), Swedish (sv), Norwegian (no), Danish (da), Finnish (fi), Thai (th), Vietnamese (vi), Indonesian (id)

## Features

- ✅ **Multi-language support** - Translate to 22+ languages
- ✅ **Interactive language selection** - Choose target language at runtime
- ✅ Automatic translation using Google Translate API
- ✅ Manual CSV workflow for review and editing
- ✅ Batch processing with Salesforce Composite API
- ✅ Support for multiple translation libraries (googletrans, deep-translator)
- ✅ Two authentication methods: Salesforce CLI or Username/Password
- ✅ Duplicate detection - automatically skips records that already have translations
- ✅ Interactive credential prompting (no hardcoding required)
- ✅ Rate limiting and error handling

---

## Prerequisites

### 1. Python 3.7+
```bash
python3 --version
```

### 2. Python Dependencies
```bash
pip3 install requests googletrans==4.0.0-rc1
```

**Alternative translation library:**
```bash
pip3 install deep-translator
```

### 3. Authentication (Choose One)

#### Option A: Salesforce CLI (Recommended)
```bash
sf --version
```
If not installed, get it from: https://developer.salesforce.com/tools/salesforcecli

#### Option B: Username/Password/Security Token
No CLI needed - just your Salesforce credentials.

---

## Setup

Choose your authentication method:

### Option A: Using Salesforce CLI

#### 1. Configure Your Org

Edit `query-and-translate-records.py` and update:

```python
ORG_ALIAS = "your-org-alias"  # Your Salesforce org alias
INSTANCE_URL = "https://your-instance.salesforce.com"  # Your instance URL
```

#### 2. Login to Salesforce

```bash
sf org login web --instance-url https://your-instance.salesforce.com --alias your-org-alias
```

### Option B: Using Username/Password

#### 1. Configure Instance URL

Edit `query-and-translate-records-username-password.py` and update the configuration (lines 13-17):

```python
INSTANCE_URL = "https://your-instance.salesforce.com"  # Your Salesforce instance URL
USERNAME = ""  # Leave empty to be prompted, or hardcode your username
PASSWORD = ""  # Leave empty to be prompted, or hardcode your password
SECURITY_TOKEN = ""  # Leave empty if not needed (trusted IP), or add your token
API_VERSION = "67.0"  # Change if needed (61.0, 62.0, 68.0, etc.)
```

#### 2. Get Your Security Token (if needed)

Security tokens are **only required if logging in from an untrusted IP address**.

To get your security token:
1. Login to Salesforce
2. Go to **Setup → My Personal Information → Reset My Security Token**
3. Click "Reset Security Token" - it will be emailed to you

#### 3. Run the Script

The script will **prompt you for credentials** if they're not hardcoded:
- Username
- Password
- Whether you need a security token (y/N)
- Security token (if needed)

**⚠️ Security Note:** 
- Credentials can be entered interactively (recommended) or hardcoded
- Never commit hardcoded credentials to Git!

---

## Usage

### Option 1: Automated Translation (Recommended)

Automatically query records, translate using Google Translate, and insert Translation records.

**Using Salesforce CLI:**
```bash
python3 query-and-translate-records.py
```

**Using Username/Password:**
```bash
python3 query-and-translate-records-username-password.py
```

**Example output:**
```
============================================================
French Translation Generator
Username/Password Authentication
============================================================

1. Logging in...
✅ Logged in successfully
   Instance URL: https://your-instance.salesforce.com
   API Version: v67.0

2. Processing ActionPlan...
✅ Found 5 ActionPlan records

Translating 5 records:
  1. Application Review Task          → Tâche de révision de la demande
  2. Eligibility Section               → Section d'éligibilité
  3. Funding Award Requirements        → Exigences d'attribution de financement
  
3. Inserting translations...
   ℹ️  Found 2 existing translations, will skip those
⏭️  Skipped 2 records (already have translations)
✅ Successfully inserted 3 new translation records
   Total processed: 5 records
```

---

### Option 2: Manual Translation (Full Control)

For cases where you want to review and edit translations manually:

#### Step 1: Export Records
```bash
python3 export-for-translation.py
```

This creates `records-for-translation.csv`:
```csv
ObjectType,RecordId,EnglishName,FrenchName
IndividualApplicationTask,a1X5g000000ABC1,Application Review,
FundingAwardRequirementSection,a2Y5g000000DEF2,Eligibility Section,
```

#### Step 2: Fill French Translations

Open the CSV and fill the `FrenchName` column:
```csv
ObjectType,RecordId,EnglishName,FrenchName
IndividualApplicationTask,a1X5g000000ABC1,Application Review,Révision de la demande
FundingAwardRequirementSection,a2Y5g000000DEF2,Eligibility Section,Section d'éligibilité
```

#### Step 3: Import Translations
```bash
python3 import-translations-from-csv.py
```

---

## Translation Methods

The automated script supports multiple translation backends:

| Method | Pros | Cons | Setup |
|---|---|---|---|
| **googletrans** (default) | Free, no API key needed | Occasional rate limits | `pip3 install googletrans==4.0.0-rc1` |
| **deep-translator** | More reliable | Slightly slower | `pip3 install deep-translator` |
| **manual** (fallback) | No dependencies | Basic word replacement | Built-in |

To switch methods, edit the script (line 27 in username-password version, line 19 in CLI version):
```python
TRANSLATION_METHOD = 'googletrans'      # or 'deep-translator'
```

---

## Adding New Objects

To support additional BPO objects:

### 1. Update `TRANSLATION_OBJECTS` mapping:

```python
TRANSLATION_OBJECTS = {
    "ActionPlan": "ActionPlanDataTranslation",
    "FundingAwardRqmtSection": "FundingAwardRqmtSectionDataTranslation",
    "IndividualApplicationTask": "IndividualApplicationTaskDataTranslation",
    "IntakeFormSection": "IntakeFormSectionDataTranslation",
    "YourNewObject": "YourNewObjectDataTranslation",  # Add this
}
```

### 2. Update `OBJECTS_TO_EXPORT` in `export-for-translation.py`:

```python
OBJECTS_TO_EXPORT = [
    "ActionPlan",
    "FundingAwardRqmtSection",
    "IndividualApplicationTask",
    "IntakeFormSection",
    "YourNewObject",  # Add this
]
```

---

## Troubleshooting

### Error: "No default environment found"
Run the login command:
```bash
sf org login web --instance-url https://your-instance.salesforce.com --alias your-org-alias
```

### Error: "googletrans library not installed"
Install it:
```bash
pip3 install googletrans==4.0.0-rc1
```

Or switch to deep-translator:
```bash
pip3 install deep-translator
```

### Error: "FIELD_INTEGRITY_EXCEPTION: Duplicate Name"
**This should no longer occur** - the script automatically detects and skips records that already have translations. If you still encounter this error, there may be an issue with the duplicate detection logic.

### Translation API Rate Limiting
- The script includes a 0.1s delay between translations
- Try switching to `deep-translator` method
- Or use the manual CSV workflow

### Error: "INVALID_TYPE" or "Object not supported"
The object doesn't exist in your org, or the API version is too old/new. Try:
1. Verify the object exists in your org
2. Adjust the `API_VERSION` setting at the top of the script (e.g., 61.0, 62.0, 67.0, 68.0)

### Login Failures (Username/Password method)
If login fails, check:
- Username is correct (usually your email)
- Password is correct
- Security token is appended to password (if required)
- Your IP is trusted OR you're using the security token
- INSTANCE_URL is set correctly
- The SOAP API endpoint is accessible (uses v64.0 for login)

---

## How It Works

### Translation Record Structure

For each source record, a corresponding Translation record is created:

```json
{
  "attributes": {"type": "IndividualApplicationTaskDataTranslation"},
  "ParentId": "a1X5g000000ABC1",  // Lookup to source record
  "Language": "fr",                // French
  "Name": "Révision de la demande" // Translated name
}
```

### Authentication Methods

**Username/Password (SOAP API):**
- Uses Salesforce SOAP API v64.0 for login
- Returns a session ID used as Bearer token for REST API calls
- Queries and data operations use the configured API version (e.g., v67.0)
- Security token may be required depending on your IP trust settings

**Salesforce CLI:**
- Uses the SF CLI's stored OAuth credentials
- More secure - no password handling in the script
- Recommended for development environments

This is exactly how Salesforce Translation Workbench stores translations internally.

---

## Files

| File | Purpose |
|---|---|
| `query-and-translate-records.py` | Automated translation (Salesforce CLI auth) |
| `query-and-translate-records-username-password.py` | Automated translation (Username/Password auth) |
| `export-for-translation.py` | Export records to CSV for manual translation |
| `import-translations-from-csv.py` | Import translations from edited CSV |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Prevents committing sensitive files |
| `README.md` | This documentation |
| `PUSH_TO_GITHUB.md` | Instructions for creating GitHub repo |

---

## Recent Improvements

### Username/Password Script Updates
- ✅ **Duplicate Detection**: Automatically checks for existing translations and skips them
- ✅ **Interactive Prompts**: No need to hardcode credentials - script prompts for them
- ✅ **Smart Security Token Handling**: Only prompts for token if needed
- ✅ **Object Existence Checks**: Verifies objects exist before querying
- ✅ **Better Error Messages**: Clear guidance on what to check if login fails
- ✅ **Batch Processing**: Handles large datasets with 200-record batches
- ✅ **API Version Flexibility**: Easy to adjust API version for different org configurations

---

## Contributing

To extend this tool:

1. Add new object mappings to `TRANSLATION_OBJECTS`
2. Add custom translation backends (OpenAI, AWS Translate, etc.)
3. Add support for additional languages (update `Language` field)

---

## License

MIT License - feel free to use and modify for your needs.

---

## Questions?

For issues or questions, please open a GitHub issue or contact your Salesforce admin.
