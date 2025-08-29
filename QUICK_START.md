# Quick Start Guide

## 🚀 Start the Django Expense Claim System

### 1. Navigate to Project Directory
```bash
cd /Users/wongivan/ai_tools/business_tools/company_expense_claim_system
```

### 2. Start the Server (Port 8084)
```bash
# Background process (recommended)
nohup python manage.py runserver 8084 > server.log 2>&1 &

# Or standard process
python manage.py runserver 8084
```

### 3. Access the Application
- **Main App**: http://127.0.0.1:8084/
- **Admin**: http://127.0.0.1:8084/admin/

### 4. Check Server Status
```bash
# Verify server is running
ps aux | grep "runserver 8084" | grep -v grep

# Test connectivity
curl -I http://127.0.0.1:8084/
```

### 5. Stop Server (if needed)
```bash
pkill -f "runserver 8084"
```

---

## ✅ Recent Fixes Applied
- ✅ UNIQUE constraint resolved
- ✅ Dynamic categories in print functionality
- ✅ Print layout improvements
- ✅ Server stability enhanced

## 📊 Key Features
- Expense claim CRUD operations
- Combined claims printing
- Dynamic category detection
- Admin interface
- Bootstrap responsive UI

---

*For detailed lessons learned and troubleshooting, see: LESSONS_LEARNED.md*
