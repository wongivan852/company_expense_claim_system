# Company Expense Claim System

A Django-based web application for managing company expense claims with comprehensive print functionality, receipt image handling, and approval workflows.

## Features

- **User Authentication**: Secure login and user management
- **Expense Claims**: Submit and manage expense claims with receipt uploads
- **Print System**: Professional print formats with receipt images in landscape orientation
- **Dynamic Categories**: Flexible expense categorization system
- **Approval Workflows**: Multi-level approval processes
- **Receipt Management**: Upload and display receipt images with error handling
- **Combined Printing**: Print multiple claims together with optimized layout

## Tech Stack

- **Backend**: Django 4.x, Python 3.8+
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5, JavaScript
- **File Storage**: Local file system with media handling
- **Print System**: CSS print media queries with landscape orientation

## Setup

### Prerequisites

- Python 3.8+
- Virtual environment
- Git

### Installation

1. Clone the repository:
```bash
git clone https://gitlab.kryedu.org/company_apps/company_expense_claim_system.git
cd company_expense_claim_system
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Database setup:
```bash
python manage.py migrate
python manage.py createsuperuser
```

5. Run the application:
```bash
python manage.py runserver 0.0.0.0:8081
```

The application will be available at:
- Local: `http://localhost:8081`
- Network: `http://[your-ip]:8081`

## Key Features

### Enhanced Print System
- **Professional Layout**: Summary on page 1, receipts on following pages
- **Landscape Orientation**: Optimized for A4 landscape printing
- **Multiple Receipts**: Up to 2 receipts per page with intelligent layout
- **Error Handling**: Clean display for missing receipt images
- **Dynamic Categories**: Proper expense claim format with category columns

### Input Improvements
- **Decimal Input Fix**: Resolved cursor jumping issues when entering amounts
- **User-Friendly Interface**: Improved form handling and validation
- **Receipt Upload**: Drag-and-drop file uploads with preview

### Print Options
- **Summary Only**: Basic claim summary without images
- **With Receipt Images**: Complete claims with all receipt images
- **Combined Claims**: Print multiple claims in one document
- **Professional Signatures**: "Prepared by" and "Approved by" sections

## Usage

1. **Login**: Access the system with your credentials
2. **Create Claims**: Add expense items with descriptions and receipts
3. **Upload Receipts**: Attach receipt images to expense items
4. **Print Claims**: Choose from multiple print formats
5. **Approval Process**: Submit claims for approval workflow

## Development

### Recent Enhancements
- Fixed decimal input cursor jumping issue
- Implemented comprehensive print system with receipt images
- Added proper expense claim table format with dynamic category columns
- Enhanced error handling for missing receipt files
- Optimized layout for landscape printing

## Contributing

1. Fork the repository on GitLab
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a merge request

## License

Internal company use only.

## Repository

- **GitLab**: https://gitlab.kryedu.org/company_apps/company_expense_claim_system
