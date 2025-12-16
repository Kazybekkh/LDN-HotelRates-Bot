# Security Best Practices

This document outlines the security measures implemented in the Flight Price Monitor Bot.

## 🔒 Environment Variable Security

### ✅ What We Do Right

1. **No Hardcoded Secrets**
   - All API keys stored in `.env` file
   - `.env` file is gitignored
   - Example file (`.env.example`) contains no real credentials

2. **Configuration Validation**
   - Bot validates all required variables on startup
   - Fails fast if credentials are missing
   - Clear error messages guide setup

3. **Separation of Concerns**
   - Configuration in `secure_config.py`
   - Never import credentials directly in business logic

### ❌ What NOT To Do

```python
# NEVER DO THIS:
API_KEY = "sk-ant-1234567890"  # Hardcoded API key

# NEVER DO THIS:
import con  # Importing a file with hardcoded credentials
```

### ✅ Correct Approach

```python
# ALWAYS DO THIS:
from secure_config import Config
api_key = Config.ANTHROPIC_API_KEY  # From environment
```

## 🛡️ Gitignore Protection

Our `.gitignore` protects:

- `.env` and all variants (`.env.local`, `.env.*.local`)
- `config.py` (in case someone creates one)
- `con.py` (old credential file)
- `secrets.json`, `credentials.json`
- Database files (`.db`, `.sqlite`)
- Session files

## 🚦 Rate Limiting

Protection against abuse:

- **Daily Limit**: 50 messages per user (configurable)
- **Session Timeout**: 10 minutes (configurable)
- **Per-user Tracking**: Database-backed rate limiting

## 🗄️ Database Security

- **Parameterized Queries**: Prevents SQL injection
- **No User Input in Schema**: Table structure is fixed
- **Local Storage**: SQLite database in gitignored `db/` folder

## 🌐 API Security

### Anthropic API

- API key stored in environment
- HTTPS-only connections
- Error messages don't leak API details

### Amadeus API

- OAuth2 token-based authentication
- Tokens are cached in-memory (never persisted)
- Automatic token refresh
- Test environment for development

## 📝 Logging Security

### ✅ Safe Logging

```python
logger.info("User 12345 created alert")
logger.error(f"API call failed: {error_type}")
```

### ❌ Dangerous Logging

```python
# NEVER DO THIS:
logger.debug(f"API key: {api_key}")  # Leaks credentials
logger.info(f"Request: {full_request_with_token}")  # Leaks tokens
```

## 🔐 Deployment Security Checklist

Before deploying, ensure:

- [ ] `.env` file is created with real credentials
- [ ] `.env` is in `.gitignore`
- [ ] No API keys in code or comments
- [ ] All credentials stored as environment variables
- [ ] Database path is writable and secure
- [ ] Log files don't contain sensitive data
- [ ] Rate limiting is enabled
- [ ] Session timeout is set appropriately

## 🚨 What To Do If Keys Are Leaked

If you accidentally commit API keys:

1. **Immediately Revoke** the exposed keys
   - Anthropic: Delete API key in console
   - Telegram: Revoke bot token via @BotFather
   - Amadeus: Regenerate credentials

2. **Remove from Git History**
   ```bash
   # Remove sensitive file from history
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (WARNING: Destructive)
   git push origin --force --all
   ```

3. **Generate New Keys** and update `.env`

4. **Notify Team** if in a team environment

## 📋 Security Audit Checklist

Regularly review:

- [ ] No API keys in code (`git grep -i "sk-ant"`)
- [ ] No API keys in commit history
- [ ] `.env.example` has placeholder values only
- [ ] All secure files in `.gitignore`
- [ ] Rate limiting working correctly
- [ ] Database queries use parameterization
- [ ] Error messages don't leak system details
- [ ] Dependencies are up to date (`pip list --outdated`)

## 🔍 Security Testing

### Test 1: Environment Validation

```bash
# Remove .env and run bot
rm .env
python flight_monitor_bot.py
# Should fail with clear error message
```

### Test 2: Gitignore Check

```bash
# These should return nothing:
git status | grep .env
git status | grep config.py
git status | grep *.db
```

### Test 3: Code Audit

```bash
# Search for hardcoded patterns (should return nothing):
git grep -i "api_key.*=.*['\"]sk-"
git grep -i "token.*=.*['\"]bot"
git grep -i "secret.*=.*['\"][^$]"
```

## 📚 Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [Anthropic Security Best Practices](https://docs.anthropic.com/security)
- [Telegram Bot Security](https://core.telegram.org/bots/security)

## 🆘 Support

If you discover a security vulnerability, please email: [your-email]

**DO NOT** open a public issue for security vulnerabilities.

---

Remember: **Security is not a feature, it's a requirement.** 🔒
