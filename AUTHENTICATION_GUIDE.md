# Budget Creation Scripts - Authentication Guide

## Two Authentication Methods Available

All budget creation scripts now come in **two versions** to support different authentication methods:

### 1. Salesforce CLI Authentication (Original)
- Uses `sf org login` command
- Recommended for developers with Salesforce CLI installed
- No credentials in script files
- More secure for team environments

### 2. Username/Password Authentication (New)
- Direct username/password login via SOAP API
- Works without Salesforce CLI
- Good for automated scripts and CI/CD
- Can prompt for credentials at runtime

---

## 📋 Available Scripts

| Script | Authentication | Best For |
|--------|---------------|----------|
| `create-budget-with-categories-periods.py` | SF CLI | Developers with CLI setup |
| `create-budget-with-categories-periods-username-password.py` | Username/Password | Automation, no CLI needed |
| `create-budget-enhanced-csv.py` | SF CLI | Full CSV import with CLI |
| `create-budget-enhanced-csv-username-password.py` | Username/Password | Full CSV import, no CLI |

---

## 🔐 Method 1: Salesforce CLI Authentication

### Prerequisites
```bash
# Install Salesforce CLI
npm install -g @salesforce/cli

# Verify installation
sf --version
```

### Setup (One Time)
```bash
# Login to your org
sf org login web --instance-url https://your-instance.salesforce.com --alias myorg

# Verify login
sf org display --target-org myorg
```

### Configure Script
```python
# Edit the script
vi create-budget-with-categories-periods.py

# Update these lines:
ORG_ALIAS = "myorg"  # Your org alias from sf login
INSTANCE_URL = "https://your-instance.salesforce.com"
```

### Run
```bash
python3 create-budget-with-categories-periods.py
```

### ✅ Advantages
- No passwords in script files
- OAuth-based authentication
- Supports MFA/SSO
- Automatic token refresh
- Best for developers

### ⚠️ Disadvantages
- Requires Salesforce CLI installation
- Manual login setup needed
- Not ideal for headless automation

---

## 🔑 Method 2: Username/Password Authentication

### Prerequisites
```bash
# Just Python with requests library
pip3 install requests
```

### Option A: Interactive Credentials (Recommended)
Leave credentials empty in the script - you'll be prompted at runtime:

```python
# In the script, leave these blank:
INSTANCE_URL = ""
USERNAME = ""
PASSWORD = ""
SECURITY_TOKEN = ""
```

When you run the script:
```bash
python3 create-budget-with-categories-periods-username-password.py

# You'll be prompted:
# Instance URL: https://your-instance.salesforce.com
# Username: your.name@company.com
# Password: ********
# Use security token? (y/N): n
```

### Option B: Hardcoded Credentials
Set credentials directly in the script:

```python
# Edit the script
vi create-budget-with-categories-periods-username-password.py

# Update these lines:
INSTANCE_URL = "https://your-instance.salesforce.com"
USERNAME = "your.name@company.com"
PASSWORD = "YourPassword123"
SECURITY_TOKEN = ""  # If needed
```

**⚠️ SECURITY WARNING**: Never commit scripts with hardcoded passwords to version control!

### Run
```bash
python3 create-budget-with-categories-periods-username-password.py
```

### ✅ Advantages
- No CLI installation needed
- Works in any Python environment
- Good for automation/scripts
- Can prompt for credentials at runtime

### ⚠️ Disadvantages
- Less secure if credentials hardcoded
- Security token may be required
- No MFA support
- Password exposed in memory

---

## 🔒 Security Token Guide

### Do I Need a Security Token?

**YES, if**:
- Logging in from an untrusted IP address
- Your org has IP restrictions enabled
- You see login errors about trusted IPs

**NO, if**:
- Your IP is in the org's trusted IP ranges
- You're using Salesforce CLI (handles this automatically)

### How to Get Your Security Token

1. **Login to Salesforce** (web browser)

2. **Navigate to Settings**:
   - Click your profile picture (top right)
   - Select **Settings**

3. **Reset Security Token**:
   - Go to: **My Personal Information** → **Reset My Security Token**
   - Click **Reset Security Token**

4. **Check Your Email**:
   - Salesforce sends the token to your email
   - Copy the token (it's a long alphanumeric string)

5. **Use the Token**:
   ```python
   PASSWORD = "YourPassword123"
   SECURITY_TOKEN = "AbCdEfGhIjKlMnOpQrStUv"
   
   # In the code, they're combined:
   # password_with_token = "YourPassword123AbCdEfGhIjKlMnOpQrStUv"
   ```

---

## 🎯 Which Method Should I Use?

### Use Salesforce CLI Authentication If:
- ✅ You're a developer with CLI already installed
- ✅ You have SSO or MFA enabled
- ✅ You work in a team environment
- ✅ You want the most secure option
- ✅ You run scripts manually/interactively

### Use Username/Password Authentication If:
- ✅ You can't install Salesforce CLI
- ✅ You need automation/scheduled scripts
- ✅ You're in a CI/CD pipeline
- ✅ You prefer not to deal with OAuth flows
- ✅ Your org allows username/password login

---

## 🔄 Switching Between Methods

You can easily switch between authentication methods:

### From CLI to Username/Password
```bash
# Instead of this:
python3 create-budget-with-categories-periods.py

# Use this:
python3 create-budget-with-categories-periods-username-password.py
```

### From Username/Password to CLI
```bash
# First, setup CLI auth
sf org login web --instance-url https://your-instance.salesforce.com --alias myorg

# Then use CLI version
python3 create-budget-with-categories-periods.py
```

---

## 🛠️ Configuration Comparison

### CLI Version
```python
# Only need 2 things:
ORG_ALIAS = "myorg"
INSTANCE_URL = "https://your-instance.salesforce.com"
```

### Username/Password Version
```python
# Need 3-4 things:
INSTANCE_URL = "https://your-instance.salesforce.com"
USERNAME = "your.name@company.com"
PASSWORD = "YourPassword123"
SECURITY_TOKEN = ""  # Optional, if needed
```

---

## 🔍 Troubleshooting

### CLI Authentication Issues

**Error: "Error getting access token"**
```bash
# Re-authenticate
sf org login web --instance-url https://your-instance.salesforce.com --alias myorg

# Verify
sf org display --target-org myorg
```

**Error: "Org not found"**
- Check `ORG_ALIAS` matches your login alias
- Run `sf org list` to see available orgs

### Username/Password Issues

**Error: "Login failed: INVALID_LOGIN"**
- Check username and password are correct
- Try adding security token if needed
- Verify IP address is allowed

**Error: "Login failed: 401"**
- Password may have changed
- Security token may be required
- Account may be locked

**Error: "Could not parse login response"**
- Check `INSTANCE_URL` is correct
- Ensure it includes `https://`
- Verify you're not using a My Domain URL incorrectly

### Security Token Issues

**Error: "Login failed" from untrusted IP**
```bash
# Get security token:
# 1. Login to Salesforce web
# 2. Settings → Reset Security Token
# 3. Check your email for the token
# 4. Add to script:
SECURITY_TOKEN = "your-token-here"
```

**Error: "Invalid username, password, security token"**
- Token may have been reset - get a new one
- Password + token must be concatenated correctly
- Check for extra spaces in token

---

## 💡 Best Practices

### Security

1. **Never commit credentials** to version control
   ```bash
   # Add to .gitignore:
   *-with-credentials.py
   *-password.py
   ```

2. **Use environment variables** for automation
   ```python
   import os
   USERNAME = os.getenv('SF_USERNAME')
   PASSWORD = os.getenv('SF_PASSWORD')
   ```

3. **Use interactive prompts** when possible
   ```python
   # Leave credentials blank in script
   USERNAME = ""
   PASSWORD = ""
   # Script will prompt at runtime
   ```

4. **Rotate passwords regularly**
   - Change password every 90 days
   - Reset security token when password changes

### For Teams

1. **CLI auth** for developers
2. **Username/password** for automation accounts
3. **Document** which method each script uses
4. **Never share** credentials in chat/email

### For Production

1. Use **dedicated integration user**
2. Store credentials in **secrets manager**
3. Use **connected app** with OAuth when possible
4. Monitor **login history** in Salesforce

---

## 📝 Quick Reference

### Run with CLI Auth
```bash
sf org login web --alias myorg
python3 create-budget-with-categories-periods.py
```

### Run with Username/Password (Interactive)
```bash
python3 create-budget-with-categories-periods-username-password.py
# Enter credentials when prompted
```

### Run with Username/Password (Environment Variables)
```bash
export SF_USERNAME="your.name@company.com"
export SF_PASSWORD="YourPassword123"
export SF_TOKEN=""
python3 create-budget-with-categories-periods-username-password.py
```

---

## 🆘 Still Having Issues?

1. **Check the script output** - errors are usually descriptive
2. **Verify credentials** - try logging in via web browser
3. **Check IP restrictions** - Settings → Security → Network Access
4. **Review login history** - Setup → Login History
5. **Test with simple query** - Use Workbench to test credentials

---

## 📚 Related Documentation

- [GET_STARTED.md](./GET_STARTED.md) - General setup guide
- [BUDGET_CREATION_README.md](./BUDGET_CREATION_README.md) - Full documentation
- [QUICK_START_BUDGET.md](./QUICK_START_BUDGET.md) - Quick commands

---

**Updated:** June 15, 2026  
**Scripts:** 4 total (2 CLI + 2 Username/Password versions)
