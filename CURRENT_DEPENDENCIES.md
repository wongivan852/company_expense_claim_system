# Current Dependencies - Pre-Restructure

## Apps in company_expense_claim_system

### Core Apps (Keep):
- **apps.accounts** - User account management
- **apps.expense_claims** - Expense claim functionality (CORE)
- **apps.documents** - Document uploads for expenses
- **apps.reports** - Expense reporting and analytics
- **apps.core** - Shared utilities

### Apps to Extract:
- **apps.leave_management** → Move to company-leave-system
- **apps.stripe_management** → Remove (link to stripe-dashboard instead)

## Database Dependencies

### Models that reference each other:
- ExpenseClaim → User (Foreign Key to accounts)
- ExpenseClaim → Company (Foreign Key)
- Document → ExpenseClaim (Foreign Key)
- LeaveApplication → User (Foreign Key)
- LeaveBalance → User (Foreign Key)

### Shared Dependencies:
- All apps use apps.accounts for User model
- All apps use apps.core for utilities

## URL Dependencies

Current URL structure:
- /expense-claims/ → apps.expense_claims
- /documents/ → apps.documents
- /reports/ → apps.reports
- /leave/ → apps.leave_management (TO BE REMOVED)
- /stripe/ → apps.stripe_management (TO BE REMOVED)
- /accounts/ → apps.accounts

## Static/Media Files

- Expense receipts: media/receipts/
- Documents: media/documents/
- Leave attachments: media/leave_attachments/

## Template Dependencies

Templates using cross-app data:
- dashboard.html - Uses both expense and leave stats
- base.html - Navigation includes all apps

