# 🔐 Django SECRET_KEY Guide

## What is SECRET_KEY?

The Django SECRET_KEY is a cryptographic key used for:
- Session security
- Password reset tokens
- CSRF protection
- Cryptographic signing

**⚠️ CRITICAL**: Never share or commit your SECRET_KEY to Git!

---

## Your Generated SECRET_KEY

```
zrn&#6&nh!0cna$lo120#9g6li*s7ilx4=8*a&0wa%1+ekx38b
```

**Copy this key for your Render deployment!**

---

## How to Use in Render

### When Deploying to Render:

1. Go to your service on Render
2. Click "Environment" tab
3. Add environment variable:
   ```
   Key: SECRET_KEY
   Value: zrn&#6&nh!0cna$lo120#9g6li*s7ilx4=8*a&0wa%1+ekx38b
   ```
4. Save

---

## Generate New SECRET_KEY

### Method 1: Using Python Script (Easiest)

```bash
python generate_secret_key.py
```

### Method 2: Using Django Command

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Method 3: Using Python Interactive Shell

```python
python
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
```

### Method 4: Online Generator

Visit: https://djecrety.ir/
(Use only for development, not production)

---

## Security Best Practices

### ✅ DO:
- Use a unique SECRET_KEY for each environment (dev, staging, prod)
- Store SECRET_KEY in environment variables
- Keep SECRET_KEY at least 50 characters long
- Use random, unpredictable characters
- Rotate SECRET_KEY periodically

### ❌ DON'T:
- Commit SECRET_KEY to Git
- Share SECRET_KEY publicly
- Use the same key across multiple projects
- Use simple or predictable keys
- Store in code files

---

## Environment Variables Setup

### Local Development (.env file)

Create `.env` file (already in .gitignore):
```env
SECRET_KEY=zrn&#6&nh!0cna$lo120#9g6li*s7ilx4=8*a&0wa%1+ekx38b
DEBUG=True
```

### Production (Render)

Add in Render dashboard:
```
SECRET_KEY=zrn&#6&nh!0cna$lo120#9g6li*s7ilx4=8*a&0wa%1+ekx38b
DEBUG=False
```

---

## Checking Your Current SECRET_KEY

### In Django Shell:

```bash
python manage.py shell
```

```python
from django.conf import settings
print(settings.SECRET_KEY)
```

---

## What Happens if SECRET_KEY is Compromised?

If your SECRET_KEY is exposed:

1. **Generate a new key immediately**
2. **Update environment variables**
3. **Redeploy your application**
4. **All users will be logged out** (sessions invalidated)
5. **Password reset tokens will be invalid**

---

## Multiple SECRET_KEYs for Different Environments

### Development
```python
SECRET_KEY = 'dev-key-not-for-production-12345'
```

### Staging
```python
SECRET_KEY = 'staging-zrn&#6&nh!0cna$lo120#9g6li*s7ilx4'
```

### Production
```python
SECRET_KEY = 'zrn&#6&nh!0cna$lo120#9g6li*s7ilx4=8*a&0wa%1+ekx38b'
```

---

## Troubleshooting

### Error: "SECRET_KEY must not be empty"

**Solution**: Make sure SECRET_KEY is set in environment variables

### Error: "Invalid SECRET_KEY"

**Solution**: Check for special characters that might need escaping

### Sessions not working

**Solution**: Verify SECRET_KEY hasn't changed between deployments

---

## Quick Reference

### Generate New Key:
```bash
python generate_secret_key.py
```

### Your Current Key:
```
zrn&#6&nh!0cna$lo120#9g6li*s7ilx4=8*a&0wa%1+ekx38b
```

### Add to Render:
```
Environment → Add Variable
Key: SECRET_KEY
Value: [paste your key]
```

---

## Additional Security Tips

1. **Use environment variables** for all secrets
2. **Enable HTTPS** (automatic on Render)
3. **Set DEBUG=False** in production
4. **Use strong passwords** for admin accounts
5. **Keep Django updated** to latest security patches
6. **Enable CSRF protection** (enabled by default)
7. **Use secure cookies** in production

---

## Resources

- [Django Security Settings](https://docs.djangoproject.com/en/5.0/topics/security/)
- [Django SECRET_KEY Documentation](https://docs.djangoproject.com/en/5.0/ref/settings/#secret-key)
- [OWASP Security Guidelines](https://owasp.org/www-project-web-security-testing-guide/)

---

**Remember: Keep your SECRET_KEY secret! 🔐**
