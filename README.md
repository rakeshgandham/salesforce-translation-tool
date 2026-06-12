# Salesforce BPO Record Translation Tool

Automated tool to translate Salesforce BPO record names to French and create corresponding Translation records.

## Supported Objects

- `FundingAwardRequirementSection` → `FundingAwardRqmtSectionTranslation`
- `IndividualApplicationTask` → `IndividualApplicationTaskTranslation`

Easily extensible to support additional objects.

---

## Features

- ✅ Automatic translation using Google Translate API
- ✅ Manual CSV workflow for review and editing
- ✅ Batch processing with Salesforce Composite API
- ✅ Support for multiple translation libraries (googletrans, deep-translator)
- ✅ Two authentication methods: Salesforce CLI or Username/Password
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

#### 1. Get Your Security Token

1. Login to Salesforce
2. Go to **Setup → My Personal Information → Reset My Security Token**
3. Check your email for the security token

#### 2. Configure Credentials

Edit `query-and-translate-records-username-password.py` and update lines 19-24:

```python
SALESFORCE_USERNAME = "your-username@example.com"
SALESFORCE_PASSWORD = "your-password"
SALESFORCE_SECURITY_TOKEN = "your-security-token"
SALESFORCE_DOMAIN = "login.salesforce.com"  # or "test.salesforce.com" for sandbox
```

**⚠️ Security Note:** Never commit this file with real credentials to Git!

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
Translating 3 records:
  1. Application Review Task          → Tâche de révision de la demande
  2. Eligibility Section               → Section d'éligibilité
  3. Funding Award Requirements        → Exigences d'attribution de financement

Ready to insert 3 translation records.
Continue? (y/N):
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

To switch methods, edit `query-and-translate-records.py` line 19:
```python
TRANSLATION_METHOD = 'googletrans'      # or 'deep-translator' or 'manual'
```

---

## Adding New Objects

To support additional BPO objects:

### 1. Update `TRANSLATION_OBJECTS` mapping:

```python
TRANSLATION_OBJECTS = {
    "FundingAwardRequirementSection": "FundingAwardRqmtSectionTranslation",
    "IndividualApplicationTask": "IndividualApplicationTaskTranslation",
    "YourNewObject": "YourNewObjectTranslation",  # Add this
}
```

### 2. Update `OBJECTS_TO_EXPORT` in `export-for-translation.py`:

```python
OBJECTS_TO_EXPORT = [
    "FundingAwardRequirementSection",
    "IndividualApplicationTask",
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
Translation records already exist. Either:
1. Delete existing translations first
2. Modify the script to check for existing records before inserting

### Translation API Rate Limiting
- The script includes a 0.1s delay between translations
- Try switching to `deep-translator` method
- Or use the manual CSV workflow

---

## How It Works

### Translation Record Structure

For each source record, a corresponding Translation record is created:

```json
{
  "attributes": {"type": "IndividualApplicationTaskTranslation"},
  "ParentId": "a1X5g000000ABC1",  // Lookup to source record
  "Language": "fr",                // French
  "Name": "Révision de la demande" // Translated name
}
```

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
