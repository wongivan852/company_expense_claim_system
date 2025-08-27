# Enhanced Krystal Institute Expense Claim System

## 📊 Business Overview

A comprehensive expense claim management system designed for **Krystal Institute Limited** and its associated companies, featuring multi-language support, real-time currency conversion, OCR receipt processing, and sophisticated approval workflows.

### 🏢 Supported Companies
1. **Krystal Institute Limited (KIL)** - 晶體研究院有限公司
2. **Krystal Technology Limited (KTL)** - 晶體科技有限公司  
3. **CG Global Entertainment Limited (CGEL)** - CG環球娛樂有限公司
4. **数谱环球(深圳)科技有限公司 (SPGZ)** - Shenzhen Technology Company

## 🎯 Key Business Features

### 💰 Multi-Currency Support
- **Base Currency**: Hong Kong Dollar (HKD)
- **Supported**: USD, RMB/CNY, JPY, EUR
- **Real-time Exchange Rates**: API integration with caching
- **Automatic Conversion**: All amounts converted to HKD for reporting

### 📋 Expense Categories (Based on Real Business Form)
1. **主題演講** (Keynote Speech)
2. **贊助嘉賓** (Sponsor/Guest)
3. **課程運營推廣** (Course Operations & Marketing)
4. **展覽采購** (Exhibition Procurement)
5. **其他雜項** (Other Miscellaneous)
6. **業務商談** (Business Negotiations)
7. **講師雜項** (Instructor Miscellaneous)
8. **采購雜項** (Procurement Miscellaneous)
9. **交通** (Transportation)

### 🌍 Multi-Language Support
- **English** (Primary)
- **Chinese Simplified** (简体中文)
- **Chinese Traditional** (繁體中文)
- Dynamic language switching based on user preference

### 🔄 Approval Workflow
1. **Employee** creates and submits expense claim
2. **Manager** reviews and checks claim
3. **Finance** provides final approval
4. **System** processes for payment

## 🚀 Quick Start

### Prerequisites
```bash
# Install Python 3.8+
python --version

# Install dependencies
pip install -r requirements.txt
```

### Database Setup
```bash
# Initialize database with business data
python init_business_db.py
```

### Start Server
```bash
# Option 1: Use startup script
python start_business_system.py

# Option 2: Direct start
python -m app.main
```

### Access Points
- **API Server**: http://localhost:8084
- **API Documentation**: http://localhost:8084/docs
- **Interactive API**: http://localhost:8084/redoc

## 🔐 Demo Credentials

All demo users have password: `demo123`

### Krystal Institute Limited (KIL)
- **CEO/Manager**: jeff.wong@krystal-institute.com
- **CTO/Manager**: ivan.wong@krystal-institute.com

### Other Companies
- **KTL Manager**: manager@krystal-tech.com
- **KTL Employee**: employee@krystal-tech.com
- **CGEL Manager**: manager@cg-global.com
- **CGEL Artist**: artist@cg-global.com
- **SPGZ Manager**: manager@shuzhi-global.com
- **SPGZ Employee**: employee@shuzhi-global.com

## 🏗️ Architecture Overview

### Enhanced Database Models
```
📊 Core Entities:
├── Users (Multi-language, Role-based)
├── Companies (4 Business Entities)
├── ExpenseClaims (Workflow + Totals)
├── ExpenseItems (Detailed Line Items)
├── ExpenseCategories (9 Business Categories)
├── Currencies (6 Supported)
├── ExchangeRates (Real-time + History)
└── ExpenseAttachments (OCR + Compression)

🔧 Supporting Tables:
├── ExchangeRateHistory (Audit Trail)
└── AuditLogs (Complete Activity Log)
```

### Business Logic Services
- **CurrencyService**: Real-time exchange rate management
- **ExpenseClaimService**: Core business workflow
- **NotificationService**: Multi-language email notifications
- **OCRService**: Receipt processing with Chinese/English support

### API Architecture
- **RESTful Endpoints**: Complete CRUD operations
- **Authentication**: JWT-based security
- **File Upload**: Receipt image processing
- **Reporting**: Category-based analytics
- **Currency**: Real-time conversion

## 📈 Business Workflow

### 1. Expense Claim Creation
```python
POST /claims/
{
  "company_id": 1,
  "event_name": "IAICC AI Conference 2024",
  "event_name_chinese": "IAICC人工智能會議2024",
  "period_from": "2024-08-01T00:00:00",
  "period_to": "2024-08-31T23:59:59"
}
```

### 2. Add Expense Items
```python
POST /claims/{claim_id}/items
{
  "expense_date": "2024-08-15T00:00:00",
  "description": "Taxi from SZ Bay Port to CUHKSRI",
  "description_chinese": "从深圳湾口岸到中大(深圳)的士费",
  "category_id": 9,  # Transportation
  "original_amount": 85.00,
  "currency_id": 3,  # RMB
  "location": "Shenzhen to CUHK",
  "participants": "Total 2 persons included Jeff and Ivan"
}
```

### 3. Upload Receipt
```python
POST /claims/{claim_id}/items/{item_id}/upload-receipt
# File upload with automatic OCR processing
```

### 4. Submit for Approval
```python
POST /claims/{claim_id}/submit
```

### 5. Manager Review
```python
POST /claims/{claim_id}/check
{
  "notes": "Reviewed and verified business purpose"
}
```

### 6. Finance Approval
```python
POST /claims/{claim_id}/approve
{
  "notes": "Approved for payment processing"
}
```

## 💡 Advanced Features

### Real-Time Currency Conversion
```python
GET /claims/currency/convert?amount=100&from_currency=RMB&to_currency=HKD
# Returns: {"converted_amount": 108.00, "exchange_rate": 1.08}
```

### OCR Receipt Processing
- **Languages**: Chinese (Simplified/Traditional) + English
- **Auto-extraction**: Amount, vendor, date, tax information
- **Confidence Scoring**: Quality assessment
- **Image Compression**: Automatic optimization

### Category-Based Reporting
```python
GET /claims/reports/summary?company_id=1&date_from=2024-01-01&date_to=2024-12-31
# Returns detailed breakdown by expense category
```

### Multi-Language Notifications
- **Email Templates**: English/Chinese versions
- **Dynamic Content**: Based on user language preference
- **Workflow Alerts**: Submission, approval, rejection notifications

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./expense_claims.db

# Security
SECRET_KEY=your-secret-key-here

# Email (Optional)
EMAIL_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@domain.com
SMTP_PASSWORD=your-app-password

# Exchange Rates (Optional)
EXCHANGE_RATE_API_KEY=your-api-key

# OCR (Optional)
TESSERACT_CMD=/usr/local/bin/tesseract
```

### Business Rules
- **Auto-approve**: Claims under HKD 1,000
- **Receipt Required**: Amounts over HKD 100
- **Maximum Claim**: HKD 100,000
- **Multi-level Approval**: Manager → Finance → Payment

## 📊 Performance Optimizations

### Database Indexes
- **User lookups**: Company + Active status
- **Claim queries**: Status + Date ranges
- **Item searches**: Category + Amount
- **Approval workflow**: Status + Timestamps

### Caching Strategy
- **Exchange Rates**: 1-hour cache
- **User Sessions**: JWT tokens
- **File Processing**: Compressed versions
- **Query Results**: Optimized indexes

### File Handling
- **Image Compression**: Automatic optimization
- **Thumbnails**: 300x300 previews
- **Deduplication**: SHA-256 hashing
- **Storage**: Organized directory structure

## 🔐 Security Features

### Authentication & Authorization
- **JWT Tokens**: 8-hour expiration for business use
- **Role-based Access**: Employee/Manager/Finance
- **Company Isolation**: Data segregation
- **Audit Trail**: Complete activity logging

### Data Protection
- **Password Hashing**: bcrypt encryption
- **File Security**: Upload validation
- **Input Sanitization**: SQL injection prevention
- **CORS Configuration**: Controlled access

## 📋 API Documentation

### Core Endpoints
```
Authentication:
POST /auth/login          # User login
POST /auth/refresh        # Token refresh

Expense Claims:
GET    /claims/            # List user's claims
POST   /claims/            # Create new claim
GET    /claims/{id}        # Get specific claim
PUT    /claims/{id}        # Update claim
DELETE /claims/{id}        # Delete claim
POST   /claims/{id}/submit # Submit for approval

Expense Items:
POST   /claims/{id}/items           # Add expense item
PUT    /claims/{id}/items/{item_id} # Update item
DELETE /claims/{id}/items/{item_id} # Delete item

File Management:
POST   /claims/{id}/items/{item_id}/upload-receipt # Upload receipt

Approval Workflow:
GET    /claims/for-approval    # Get pending approvals
POST   /claims/{id}/check      # Manager review
POST   /claims/{id}/approve    # Finance approval
POST   /claims/{id}/reject     # Reject claim

Currency & Reporting:
GET    /claims/currency/rates   # Exchange rates
GET    /claims/currency/convert # Convert amount
GET    /claims/reports/summary  # Category reports
POST   /claims/currency/update-rates # Update rates (admin)
```

## 🚧 Development & Testing

### Database Migration
```bash
# Reset database
rm expense_claims.db
python init_business_db.py
```

### Testing Sample Workflow
```bash
# 1. Login as employee
curl -X POST http://localhost:8084/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "ivan.wong@krystal-institute.com", "password": "demo123"}'

# 2. Create expense claim
# 3. Add expense items
# 4. Upload receipts
# 5. Submit for approval
# 6. Login as manager and approve
```

## 📞 Support & Contact

### Business Context
This system is designed for **Krystal Institute Limited** and associated companies, supporting real-world business expense management with:
- Multi-company operations
- Cross-border transactions
- Multi-language requirements
- Complex approval workflows

### Technical Support
- **Architecture**: FastAPI + SQLAlchemy + SQLite/PostgreSQL
- **Frontend Ready**: RESTful APIs for web/mobile integration
- **Scalable Design**: Microservices-ready architecture
- **Production Ready**: Comprehensive logging, security, performance optimization

---

*Generated with enhanced business logic architecture for Krystal Institute expense management requirements.*