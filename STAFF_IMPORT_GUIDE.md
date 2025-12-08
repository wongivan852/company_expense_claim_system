# Staff Import and Login Guide

## Krystal Group - Integrated Business Platform

This guide explains how to import staff from CSV and manage user access to the integrated business platform.

---

## Overview

The Integrated Business Platform provides a unified login system for all business applications:
- **Expense Claims Management**
- **Document Management**
- **Reports & Analytics**
- **User Profile Management**

All users authenticate once and gain access to all applications they have permissions for.

---

## Importing Staff from CSV

### CSV Format

Your CSV file should have the following columns:

```csv
username,email,first_name,last_name,date_joined,region,is_staff,annual_leave_balance,sick_leave_balance
```

**Example:**
```csv
username,email,first_name,last_name,date_joined,region,is_staff,annual_leave_balance,sick_leave_balance
john.doe,john.doe@krystal.institute,John,Doe,2020-08-01,HK,TRUE,10,0
jane.smith,jane.smith@krystal.institute,Jane,Smith,2020-08-01,CN,TRUE,10,0
```

### Running the Import

#### Basic Import

Import users from the default location (`~/Downloads/staff_list.csv`):

```bash
python manage.py import_staff
```

#### Custom File Location

Import from a specific file:

```bash
python manage.py import_staff --file /path/to/your/staff_list.csv
```

#### Import with Custom Password

Set a custom default password for all new users:

```bash
python manage.py import_staff --default-password "YourSecurePassword2025!"
```

#### Update Existing Users

Update existing user information instead of skipping:

```bash
python manage.py import_staff --update-existing
```

#### Complete Example

```bash
python manage.py import_staff \
  --file ~/Downloads/staff_list.csv \
  --default-password "Krystal2025!" \
  --update-existing
```

### Import Results

After running the import, you'll see a summary:

```
============================================================
IMPORT SUMMARY
============================================================
Users created:  16
Users updated:  0
Users skipped:  0
Errors:         0
============================================================

Default password for new users: Krystal2025!
IMPORTANT: Users should change their password on first login!
```

---

## User Information

### Default Settings for Imported Users

- **Username**: From CSV (e.g., `john.doe`)
- **Email**: From CSV
- **Password**: Default password specified (default: `Krystal2025!`)
- **Employee ID**: Auto-generated (e.g., `EMP0001`)
- **Role**: `staff` (can be changed via admin panel)
- **Location**: Based on region (HK/CN/Other)
- **Status**: Active

### User Roles

The platform supports three role levels:

1. **Staff** - Regular employees
   - Submit expense claims
   - View own documents
   - Access personal reports

2. **Manager** - Department managers
   - All staff permissions
   - Approve expense claims
   - View team reports

3. **Admin** - System administrators
   - All manager permissions
   - User management
   - System configuration

---

## First Login

### For Users

1. Navigate to the platform URL
2. Click "Login"
3. Enter your username (e.g., `john.doe`)
4. Enter the default password provided by your administrator
5. **Important**: Change your password immediately after first login

### Changing Password

1. Log in to the platform
2. Click on your name in the top right
3. Select "Profile"
4. Click "Change Password"
5. Enter current password and new password

---

## Admin Tasks

### Viewing Imported Users

```bash
python manage.py shell
```

```python
from apps.accounts.models import User

# List all users
for user in User.objects.all():
    print(f"{user.username} - {user.email} - {user.employee_id}")

# Count users
print(f"Total users: {User.objects.count()}")
```

### Setting User Roles

Via Django admin:
1. Go to `/admin/`
2. Navigate to Accounts → Users
3. Select the user
4. Change the "Role" field to `manager` or `admin`
5. Save

Via command line:
```bash
python manage.py shell
```

```python
from apps.accounts.models import User

# Make user a manager
user = User.objects.get(username='john.doe')
user.role = 'manager'
user.save()

# Make user an admin
user = User.objects.get(username='jane.smith')
user.role = 'admin'
user.is_superuser = True
user.save()
```

### Assigning Managers

```python
from apps.accounts.models import User

# Set manager relationship
employee = User.objects.get(username='john.doe')
manager = User.objects.get(username='jane.smith')
employee.manager = manager
employee.save()
```

---

## Platform Access

### Available Applications

After logging in, users can access:

1. **Expense Claims**
   - Submit new expense claims
   - Track claim status
   - Upload receipts
   - View history

2. **Documents**
   - Upload business documents
   - Organize files
   - Share documents
   - Version control

3. **Reports**
   - Personal expense reports
   - Team analytics (managers)
   - Company-wide reports (admins)
   - Export data

4. **Profile Management**
   - Update personal information
   - Change password
   - Set preferences
   - View login history

### Navigation

- **Dashboard**: Main platform home (`/`)
- **Expense Claims**: `/expense-claims/`
- **Documents**: `/documents/`
- **Reports**: `/reports/`
- **Profile**: `/accounts/profile/`
- **Admin Panel**: `/admin/` (staff/admin only)

---

## Security

### Password Requirements

- Minimum 8 characters
- Must contain letters and numbers (recommended)
- Cannot be too similar to username

### Account Security

- Failed login attempts are tracked
- Accounts can be locked after multiple failed attempts
- Two-factor authentication available (optional)
- Login history is recorded

### Best Practices

1. Change default password immediately
2. Use strong, unique passwords
3. Don't share login credentials
4. Log out when finished
5. Report suspicious activity

---

## Troubleshooting

### Import Issues

**Problem**: CSV file not found
```
Solution: Check file path and ensure file exists
python manage.py import_staff --file ~/Downloads/staff_list.csv
```

**Problem**: Duplicate username errors
```
Solution: Use --update-existing flag to update instead of creating new users
python manage.py import_staff --update-existing
```

**Problem**: CSV formatting errors
```
Solution: Ensure CSV has proper headers and no extra newlines
Open CSV in text editor and verify format
```

### Login Issues

**Problem**: Cannot log in with username
```
Solution:
1. Verify username is correct (case-sensitive)
2. Try using email address instead
3. Contact administrator to reset password
```

**Problem**: Account locked
```
Solution: Contact administrator to unlock account via admin panel
```

**Problem**: Cannot access certain features
```
Solution: Check user role - may need manager/admin permissions
```

---

## Database Management

### Backup Before Import

```bash
# SQLite
cp db.sqlite3 db.sqlite3.backup

# PostgreSQL
pg_dump expense_claim_db > backup_$(date +%Y%m%d).sql
```

### Verify Import

```bash
python manage.py shell
```

```python
from apps.accounts.models import User

# Check specific user
user = User.objects.get(username='john.doe')
print(f"Username: {user.username}")
print(f"Email: {user.email}")
print(f"Name: {user.get_full_name()}")
print(f"Employee ID: {user.employee_id}")
print(f"Role: {user.role}")
print(f"Location: {user.location}")
print(f"Is Active: {user.is_active}")
```

---

## Support

For technical issues or questions:
- Contact: IT Support
- Email: support@krystal.institute
- Admin Panel: `/admin/`

---

## Appendix: Full Import Example

```bash
# 1. Navigate to project directory
cd /Users/wongivan/ai_tools/business_tools/company_expense_claim_system

# 2. Activate virtual environment (if using one)
source venv/bin/activate  # or: . venv/bin/activate

# 3. Run migrations (if not done)
python manage.py migrate

# 4. Import staff
python manage.py import_staff --file ~/Downloads/staff_list.csv

# 5. Verify import
python manage.py shell
>>> from apps.accounts.models import User
>>> print(f"Total users: {User.objects.count()}")
>>> exit()

# 6. Create superuser (if needed)
python manage.py createsuperuser

# 7. Run server
python manage.py runserver

# 8. Access platform
# Open browser: http://localhost:8000
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Platform**: Krystal Group Integrated Business Platform
