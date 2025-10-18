# Quick Start Guide - Krystal Group Business Platform

## 🚀 Get Started in 5 Minutes

---

## For Users

### Login

1. **Open Browser**: `http://localhost:8000`

2. **Login Credentials**:
   - **Username**: Your email prefix (e.g., `eugene.choy`)
   - **Password**: `Krystal2025!`

3. **First Time?**
   - Click "Profile" → "Change Password" after login

### Available Apps

After login, click on any app card:

| App | What It Does |
|-----|--------------|
| 💰 **Expense Claims** | Submit and track expense claims |
| 📁 **Documents** | Upload and manage documents |
| 📊 **Reports** | View analytics and reports |
| 👤 **Profile** | Manage your account |

---

## For Administrators

### Start the Server

```bash
cd /Users/wongivan/ai_tools/business_tools/company_expense_claim_system
python manage.py runserver
```

Access at: `http://localhost:8000`

### Import Staff

```bash
# Basic import (default location)
python manage.py import_staff

# Custom location
python manage.py import_staff --file /path/to/staff_list.csv

# Update existing users
python manage.py import_staff --update-existing
```

### Make Someone a Manager

```bash
python manage.py shell
```

```python
from apps.accounts.models import User
user = User.objects.get(username='eugene.choy')
user.role = 'manager'
user.save()
```

### Make Someone an Admin

```bash
python manage.py shell
```

```python
from apps.accounts.models import User
user = User.objects.get(username='swing.wong')
user.role = 'admin'
user.is_superuser = True
user.is_staff = True
user.save()
```

### Access Admin Panel

1. Go to: `http://localhost:8000/admin/`
2. Login with admin credentials
3. Manage users, roles, and settings

---

## Common Commands

```bash
# Start server
python manage.py runserver

# Import staff
python manage.py import_staff

# Create admin user
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Check for issues
python manage.py check

# View all users
python manage.py shell -c "from apps.accounts.models import User; print(f'Total: {User.objects.count()}')"
```

---

## Current Users

**Total Users**: 16

**Default Password**: `Krystal2025!`

Sample usernames:
- `eugene.choy`
- `swing.wong`
- `adrian.chow`
- `cat.tan`
- `ivan.wong`
- (and 11 more...)

---

## URLs

| Page | URL |
|------|-----|
| Home | `/` |
| Login | `/accounts/login/` |
| Dashboard | `/dashboard/` |
| Expense Claims | `/expense-claims/` |
| Documents | `/documents/` |
| Reports | `/reports/` |
| Profile | `/accounts/profile/` |
| Admin | `/admin/` |

---

## Need Help?

- 📖 **Detailed Guide**: [STAFF_IMPORT_GUIDE.md](STAFF_IMPORT_GUIDE.md)
- 📚 **Full Documentation**: [PLATFORM_OVERVIEW.md](PLATFORM_OVERVIEW.md)
- ✅ **Setup Details**: [SETUP_COMPLETE.md](SETUP_COMPLETE.md)

---

## Quick Troubleshooting

**Can't login?**
```bash
# Check if user exists
python manage.py shell
>>> from apps.accounts.models import User
>>> User.objects.filter(username='eugene.choy').exists()
```

**Server not starting?**
```bash
# Check for errors
python manage.py check

# Check if port is in use
lsof -i :8000
```

**Need to reset password?**
- Go to `/admin/`
- Find user
- Click "Change password"

---

## That's It!

You're ready to use the Krystal Group Integrated Business Platform! 🎉

**Version**: 1.0
**Date**: 2025-10-14
