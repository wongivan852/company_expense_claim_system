# Leave Management System - Integration Complete

## Summary

The **Annual Leave Management System** has been successfully integrated into the Krystal Group Integrated Business Platform. Users can now manage their leave requests, view balances, and track leave history through a unified interface.

---

## What Was Integrated

### 1. Leave Management App ✓

**Location**: `apps/leave_management/`

**Models**:
- `LeaveType` - Types of leave (Annual, Sick, Special, etc.)
- `LeaveApplication` - Leave requests submitted by users
- `LeaveBalance` - Leave balances for each user by type and year
- `SpecialWorkClaim` - Claims for working on rest days/holidays to earn credits
- `SpecialLeaveApplication` - Leave applications using earned special credits
- `SpecialLeaveBalance` - Special leave credits earned and used

### 2. Database Setup ✓

**Migrations**: Ran successfully
- Created 6 new tables for leave management
- All tables use the integrated platform's User model (no separate Employee table)

**Initial Data**:
- **7 Leave Types** created:
  - Annual Leave (14 days/year)
  - Sick Leave (10 days/year)
  - Special Leave (earned through special work)
  - Maternity Leave (90 days)
  - Paternity Leave (5 days)
  - Compassionate Leave (5 days)
  - Unpaid Leave

- **32 Leave Balances** created:
  - 16 users × 2 leave types (Annual + Sick)
  - Imported from staff_list.csv
  - Annual Leave: 10 days per user
  - Sick Leave: 0 days per user (as per CSV)

### 3. Platform Integration ✓

**URLs**: `/leave/`
- Integrated into main platform URL configuration
- App namespace: `leave_management`

**Navigation**:
- Added "Leave Management" card to platform home
- Icon: Calendar check (fa-calendar-check)
- Color: Success (green)
- Description: "Apply for leave and manage your annual leave balance"

### 4. Admin Interface ✓

All leave models registered in Django admin:
- Leave Types management
- Leave Applications (view, filter, search)
- Leave Balances (view balances by user/type)
- Special Work Claims
- Special Leave Applications
- Special Leave Balances

---

## Features Available

### Current Features (v1.0)

1. **Leave Types Management**
   - Predefined leave types with entitlements
   - Configurable approval requirements
   - Active/inactive status

2. **Leave Balance Tracking**
   - Opening balance
   - Carried forward from previous year
   - Current year entitlement
   - Taken leave
   - Real-time balance calculation

3. **Special Leave System**
   - Earn credits by working on rest days/holidays
   - Use earned credits for additional leave
   - Session-based tracking (AM/PM/Full Day)
   - Priority levels for special work claims

4. **Smart Calculations**
   - Business days calculation (excludes weekends)
   - Half-day leave support (AM/PM sessions)
   - Multi-day leave spanning
   - Back-to-office date calculation

### Coming Soon (Next Phase)

The following features exist in the codebase but views need to be fully implemented:

1. **Leave Application System**
   - Submit leave requests
   - View leave history
   - Cancel pending requests
   - Print leave forms

2. **Approval Workflow**
   - Manager dashboard for approvals
   - Approve/reject leave requests
   - Approval notifications
   - Approval history

3. **Leave Calendar**
   - Team leave calendar
   - View who's on leave
   - Plan leave around team availability

4. **Holiday Management**
   - Define public holidays
   - Import holidays from file
   - Region-specific holidays (HK/CN)

---

## How to Use

### For Users

#### View Leave Balance

```bash
# Via Admin Panel
1. Login to /admin/
2. Go to Leave Management → Leave Balances
3. Search for your name
```

#### Apply for Leave (Coming Soon)

Once views are fully implemented:
1. Login to platform
2. Click "Leave Management" card
3. Click "Apply for Leave"
4. Select dates and leave type
5. Submit for approval

### For Administrators

#### Setup Leave Types

```bash
python manage.py setup_leave_types
```

This creates/updates the 7 standard leave types.

####  Import Leave Balances

```bash
# From default location (~/Downloads/staff_list.csv)
python manage.py import_leave_balances

# From custom location
python manage.py import_leave_balances --file /path/to/staff.csv

# For a specific year
python manage.py import_leave_balances --year 2026
```

#### Manage via Admin Panel

1. Go to `/admin/`
2. Navigate to **Leave Management** section
3. You can:
   - Add/edit leave types
   - View all leave applications
   - Manually adjust leave balances
   - Approve special work claims
   - View special leave balances

---

## Database Schema

### LeaveType
```
- id
- name (e.g., "Annual Leave")
- description
- max_days_per_year
- requires_approval
- is_active
```

### LeaveApplication
```
- id
- user (FK to User)
- leave_type (FK to LeaveType)
- date_from (DateTime)
- date_to (DateTime)
- reason
- status (pending/approved/rejected/cancelled)
- created_at, updated_at
- approved_by (FK to User)
- approved_at
- rejection_reason
```

### LeaveBalance
```
- id
- user (FK to User)
- leave_type (FK to LeaveType)
- year
- opening_balance
- carried_forward
- current_year_entitlement
- taken
- balance (calculated property)
```

### SpecialWorkClaim
```
- id
- user (FK to User)
- work_date
- work_end_date
- session (AM/PM/FULL)
- event_name
- description
- priority
- status
- credits_earned (auto-calculated)
- manager_comment
```

### SpecialLeaveApplication
```
- id
- user (FK to User)
- date_from, date_to
- reason
- status
- credits_used (auto-calculated)
- approved_by, approved_at
```

### SpecialLeaveBalance
```
- id
- user (OneToOne with User)
- earned (from SpecialWorkClaims)
- used (from SpecialLeaveApplications)
- year
- balance (calculated property)
```

---

## API Endpoints (Future)

Once REST API is implemented:

```
GET    /api/leave/types/                 - List leave types
GET    /api/leave/balances/              - Get my leave balances
GET    /api/leave/applications/          - List my leave applications
POST   /api/leave/applications/          - Create leave application
GET    /api/leave/applications/{id}/     - Get leave application details
PATCH  /api/leave/applications/{id}/     - Update leave application
DELETE /api/leave/applications/{id}/     - Cancel leave application

# Manager endpoints
GET    /api/leave/pending/               - List pending approvals
POST   /api/leave/applications/{id}/approve/  - Approve leave
POST   /api/leave/applications/{id}/reject/   - Reject leave

# Special leave
GET    /api/leave/special-work/          - List special work claims
POST   /api/leave/special-work/          - Create special work claim
GET    /api/leave/special-leave/         - List special leave applications
POST   /api/leave/special-leave/         - Apply for special leave
```

---

## Management Commands

### setup_leave_types

Creates/updates the standard leave types.

```bash
python manage.py setup_leave_types
```

**Output**:
```
Setting up leave types...
  ✓ Created: Annual Leave
  ✓ Created: Sick Leave
  ✓ Created: Special Leave
  ...
Summary:
  Created: 7
  Updated: 0
  Total: 7
```

### import_leave_balances

Imports leave balances from staff CSV file.

```bash
python manage.py import_leave_balances [OPTIONS]
```

**Options**:
- `--file PATH` - Path to CSV file (default: ~/Downloads/staff_list.csv)
- `--year YEAR` - Year for balances (default: 2025)

**CSV Format**:
```csv
username,email,first_name,last_name,date_joined,region,is_staff,annual_leave_balance,sick_leave_balance
eugene.choy,eugene.choy@krystal.institute,Eugene,Choy,2020-08-01,HK,TRUE,10,0
```

**Output**:
```
Importing leave balances from: /Users/wongivan/Downloads/staff_list.csv
Row 2: Created balances for Eugene Choy (Annual: 10, Sick: 0)
...
============================================================
IMPORT SUMMARY
============================================================
Balances created:  16
Balances updated:  0
Skipped:           0
Errors:            0
============================================================
```

---

## Integration Status

### ✅ Completed

- [x] Leave management app copied and adapted
- [x] Models updated to use platform User model
- [x] Database migrations created and applied
- [x] Admin interface configured
- [x] URL routing setup
- [x] Platform home integration (Leave Management card)
- [x] Management commands created
- [x] Leave types setup (7 types)
- [x] Leave balances imported (16 users, 32 balances)

### 🚧 In Progress / Coming Soon

- [ ] Full view implementation (currently placeholder views)
- [ ] Leave application forms
- [ ] Manager approval interface
- [ ] Leave calendar view
- [ ] Holiday management
- [ ] Email notifications
- [ ] PDF generation for leave forms
- [ ] Mobile-responsive templates
- [ ] REST API endpoints

---

## File Structure

```
apps/leave_management/
├── __init__.py
├── admin.py                          # Admin interface ✓
├── apps.py                           # App configuration ✓
├── models.py                         # Database models ✓
├── views.py                          # Placeholder views ✓
├── views_auth.py                     # Auth views placeholder ✓
├── views_original.py                 # Original views (backup)
├── views_auth_original.py            # Original auth views (backup)
├── urls.py                           # URL patterns ✓
├── forms.py                          # Forms (from original)
├── templates/                        # Templates (from original)
│   └── leave_management/
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py              # Initial migration ✓
└── management/
    └── commands/
        ├── __init__.py
        ├── setup_leave_types.py     # Setup command ✓
        └── import_leave_balances.py # Import command ✓
```

---

## Testing

### Verify Installation

```bash
# Check Django configuration
python manage.py check
# Should show: System check identified no issues (0 silenced).

# Check database
python manage.py shell -c "from apps.leave_management.models import LeaveType, LeaveBalance; print(f'Leave Types: {LeaveType.objects.count()}'); print(f'Leave Balances: {LeaveBalance.objects.count()}')"
# Should show: Leave Types: 7, Leave Balances: 32

# Check URLs resolve
python manage.py shell -c "from django.urls import reverse; print(reverse('leave_management:dashboard'))"
# Should show: /leave/dashboard/
```

### Test in Browser

1. **Start server**:
   ```bash
   python manage.py runserver
   ```

2. **Access platform**:
   - Go to `http://localhost:8000`
   - Login with any user (e.g., `eugene.choy` / `Krystal2025!`)
   - You should see 5 app cards including "Leave Management"

3. **Click Leave Management**:
   - Should redirect to `/leave/dashboard/`
   - Currently shows placeholder message: "Leave Management - Coming Soon"

4. **Access admin**:
   - Go to `http://localhost:8000/admin/`
   - Navigate to Leave Management section
   - View leave types and balances

---

## Next Steps

### Phase 2: View Implementation

1. **Dashboard View**
   - Show leave balance summary
   - Recent leave applications
   - Quick apply button
   - Pending approvals (for managers)

2. **Leave Application Form**
   - Date picker with session selection (AM/PM/Full Day)
   - Leave type selector
   - Reason textarea
   - Balance check before submission

3. **My Leaves List**
   - Table of all leave applications
   - Filter by status/year
   - Actions: view, cancel (if pending)

4. **Manager Approval Interface**
   - List of pending leave requests
   - Approve/reject with comments
   - Email notifications

5. **Leave Calendar**
   - Monthly calendar view
   - Show who's on leave
   - Color-coded by leave type
   - Team view for managers

### Phase 3: Advanced Features

1. **Holiday Management**
   - Public holiday setup
   - Region-specific holidays
   - Auto-exclude from leave calculations

2. **Notifications**
   - Email on leave submission
   - Email on approval/rejection
   - Reminder for unused leave
   - Manager notifications

3. **Reports**
   - Leave utilization reports
   - Team leave patterns
   - Export to Excel/PDF

4. **Mobile App**
   - REST API implementation
   - Mobile-responsive views
   - Push notifications

---

## Support

### Documentation
- [PLATFORM_OVERVIEW.md](PLATFORM_OVERVIEW.md) - Platform documentation
- [STAFF_IMPORT_GUIDE.md](STAFF_IMPORT_GUIDE.md) - Staff import guide
- [SETUP_COMPLETE.md](SETUP_COMPLETE.md) - Platform setup

### Commands Help
```bash
python manage.py setup_leave_types --help
python manage.py import_leave_balances --help
```

### Django Admin
- URL: `/admin/`
- Section: Leave Management
- View and manage all leave data

---

## Version Information

- **Integration Date**: 2025-10-14
- **Platform Version**: 1.0
- **Leave System Version**: 1.0 (Basic Integration)
- **Django Version**: 4.2+
- **Python Version**: 3.8+
- **Database**: SQLite 3 (Development) / PostgreSQL (Production)

---

## Summary

✅ **Leave Management System Successfully Integrated!**

- 7 leave types configured
- 16 staff members with leave balances
- Database tables created
- Admin interface ready
- Platform navigation updated
- Management commands functional

**Status**: Ready for Phase 2 (View Implementation)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-14
**Author**: Integration Team
