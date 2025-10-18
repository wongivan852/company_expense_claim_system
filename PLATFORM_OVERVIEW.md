# Krystal Group - Integrated Business Platform

## Platform Overview

A unified business management platform providing single sign-on (SSO) access to multiple business applications.

---

## Quick Start

### For Users

1. **Access the Platform**
   - URL: `http://localhost:8000` (or your deployment URL)
   - Login with your username and password

2. **First Login**
   - Username: Your email prefix (e.g., `john.doe`)
   - Default Password: `Krystal2025!` (change immediately!)

3. **Available Apps**
   - Expense Claims Management
   - Document Management
   - Reports & Analytics
   - Profile Management

### For Administrators

1. **Import Staff**
   ```bash
   python manage.py import_staff --file ~/Downloads/staff_list.csv
   ```

2. **Access Admin Panel**
   - URL: `/admin/`
   - Manage users, roles, and permissions

3. **View User Statistics**
   ```bash
   python manage.py shell -c "from apps.accounts.models import User; print(f'Total users: {User.objects.count()}')"
   ```

---

## Platform Architecture

### Applications

#### 1. **Accounts App** (`apps.accounts`)
- User authentication and authorization
- Profile management
- Role-based access control (RBAC)
- Login history tracking

**Features:**
- Custom User model with employee_id, department, position
- Manager hierarchy support
- Location-based user organization (HK/CN/Other)
- Password change functionality
- Profile editing

#### 2. **Expense Claims App** (`apps.expense_claims`)
- Submit and manage expense claims
- Receipt upload and management
- Approval workflow
- Multi-currency support

**Features:**
- Create/edit/delete claims
- Upload receipt images
- Track claim status (draft, pending, approved, rejected)
- Manager approval system
- Print claim reports

#### 3. **Documents App** (`apps.documents`)
- Upload and organize business documents
- Document sharing and permissions
- Version control

**Features:**
- File upload
- Document categorization
- Access control
- Search and filter

#### 4. **Reports App** (`apps.reports`)
- Generate expense reports
- View analytics
- Export data

**Features:**
- Personal expense reports
- Team reports (managers)
- Company-wide analytics (admins)
- Export to CSV/PDF

#### 5. **Core App** (`apps.core`)
- Shared utilities and services
- System monitoring
- Caching utilities

**Features:**
- Health checks
- Performance metrics
- System information endpoints

---

## User Roles and Permissions

### Staff (Default)
- Submit own expense claims
- View own documents
- Access personal reports
- Update own profile

### Manager
- All staff permissions
- Approve team expense claims
- View team reports
- Manage team members

### Admin
- All manager permissions
- User management
- System configuration
- Platform-wide analytics
- Access admin panel

---

## Authentication System

### Login Flow

```
User visits platform →
Redirects to /accounts/login/ →
Enter credentials →
Authenticate →
Redirect to dashboard →
Access all apps with single session
```

### Session Management

- **Session Duration**: 24 hours (configurable)
- **Session Storage**: Cached database
- **Remember Me**: Optional
- **Logout**: Clears session and redirects to login

### Security Features

- Password validation
- Failed login tracking
- Account locking (after multiple failures)
- Login history
- IP address logging
- Two-factor authentication support (optional)

---

## Database Schema

### User Model Fields

```python
- username (unique)
- email
- first_name
- last_name
- employee_id (unique, auto-generated)
- department
- position
- manager (ForeignKey to User)
- role (staff/manager/admin)
- location (hk/cn/other)
- phone
- preferred_language (en/zh-hans)
- is_active
- is_staff
- date_joined
- last_login
```

### Additional Models

- **UserProfile**: Extended profile information
- **LoginHistory**: Track login attempts
- **ExpenseClaim**: Expense claim records
- **Document**: Document storage
- **Report**: Generated reports

---

## API Endpoints

### Authentication
- `POST /accounts/login/` - User login
- `POST /accounts/logout/` - User logout
- `GET /accounts/profile/` - View profile
- `POST /accounts/profile/` - Update profile

### Dashboard
- `GET /` - Platform home (shows available apps)
- `GET /dashboard/` - User dashboard with stats

### Monitoring
- `GET /monitoring/health/` - System health check
- `GET /monitoring/performance/` - Performance metrics
- `GET /monitoring/system/` - System information

---

## Configuration

### Settings

Located in: `business_platform/settings.py`

Key configurations:
```python
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'
SESSION_COOKIE_AGE = 86400  # 24 hours
```

### Environment Variables

Create `.env` file:
```bash
# Security
SECRET_KEY=your-secret-key
DEBUG=True

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=expense_claim_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Or use SQLite for development
USE_SQLITE=True

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True

# Session
SESSION_COOKIE_AGE=86400
```

---

## Deployment

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Import staff
python manage.py import_staff

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server
python manage.py runserver
```

### Production

```bash
# Set environment variables
export DEBUG=False
export SECRET_KEY='your-production-secret-key'

# Use production database (PostgreSQL)
export USE_SQLITE=False
export DB_NAME=expense_claim_db
export DB_USER=postgres
export DB_PASSWORD=secure-password

# Collect static files
python manage.py collectstatic --noinput

# Run with gunicorn
gunicorn business_platform.wsgi:application --bind 0.0.0.0:8000
```

---

## Management Commands

### Import Staff
```bash
python manage.py import_staff [--file PATH] [--default-password PWD] [--update-existing]
```

### Create Superuser
```bash
python manage.py createsuperuser
```

### Migrate Database
```bash
python manage.py migrate
```

### Collect Static Files
```bash
python manage.py collectstatic
```

### Shell Access
```bash
python manage.py shell
```

---

## Monitoring and Maintenance

### Health Checks

```bash
# Check system health
curl http://localhost:8000/monitoring/health/

# Check performance
curl http://localhost:8000/monitoring/performance/

# System info
curl http://localhost:8000/monitoring/system/
```

### Logs

Log file location: `logs/business_platform.log`

```bash
# View logs
tail -f logs/business_platform.log

# Filter errors
grep ERROR logs/business_platform.log
```

### Database Backup

```bash
# SQLite
cp db.sqlite3 backups/db_$(date +%Y%m%d).sqlite3

# PostgreSQL
pg_dump expense_claim_db > backups/backup_$(date +%Y%m%d).sql
```

---

## Customization

### Adding New Apps

1. Create app directory in `apps/`
2. Add to `INSTALLED_APPS` in settings
3. Create models, views, templates
4. Add URL patterns to `business_platform/urls.py`
5. Update platform home to show new app

### Modifying User Model

```python
# In apps/accounts/models.py
class User(AbstractUser):
    # Add new fields
    new_field = models.CharField(max_length=100)
```

Then run:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Customizing Templates

Templates are in `templates/` directory:
- `base.html` - Main layout
- `platform_home.html` - Dashboard
- `accounts/login.html` - Login page
- `accounts/profile.html` - Profile page

---

## Troubleshooting

### Common Issues

**Issue**: Cannot import staff
```bash
# Check file exists
ls -la ~/Downloads/staff_list.csv

# Check file format
head -5 ~/Downloads/staff_list.csv

# Run with verbose output
python manage.py import_staff --file ~/Downloads/staff_list.csv
```

**Issue**: Login not working
```python
# Check user exists
python manage.py shell
>>> from apps.accounts.models import User
>>> User.objects.filter(username='john.doe').exists()
```

**Issue**: Static files not loading
```bash
python manage.py collectstatic --noinput
```

---

## Support and Documentation

- **Project**: Krystal Group Integrated Business Platform
- **Framework**: Django 4.2+
- **Python**: 3.8+
- **Database**: PostgreSQL (recommended) / SQLite (development)

**Additional Documentation:**
- [Staff Import Guide](STAFF_IMPORT_GUIDE.md)
- [Django Documentation](https://docs.djangoproject.com/)
- [Bootstrap Documentation](https://getbootstrap.com/)

---

## File Structure

```
company_expense_claim_system/
├── apps/
│   ├── accounts/          # User authentication
│   ├── expense_claims/    # Expense management
│   ├── documents/         # Document management
│   ├── reports/           # Analytics & reports
│   └── core/              # Shared utilities
├── business_platform/     # Main project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/             # HTML templates
│   ├── base.html
│   ├── platform_home.html
│   └── accounts/
├── static/                # Static files (CSS, JS)
├── media/                 # User uploads
├── logs/                  # Application logs
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

---

## Version Information

- **Platform Version**: 1.0
- **Last Updated**: 2025-10-14
- **Django Version**: 4.2+
- **Python Version**: 3.8+
- **Database**: PostgreSQL 12+ / SQLite 3

---

## License

Proprietary - Krystal Group
All rights reserved.
