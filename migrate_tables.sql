-- SQL Script to migrate tables from claims_ to expense_claims_ prefix
-- This preserves all data during the integration to business_platform

-- Rename main tables
ALTER TABLE claims_company RENAME TO expense_claims_company;
ALTER TABLE claims_currency RENAME TO expense_claims_currency;
ALTER TABLE claims_exchangerate RENAME TO expense_claims_exchangerate;
ALTER TABLE claims_expensecategory RENAME TO expense_claims_expensecategory;
ALTER TABLE claims_expenseclaim RENAME TO expense_claims_expenseclaim;
ALTER TABLE claims_expenseitem RENAME TO expense_claims_expenseitem;
ALTER TABLE claims_claimcomment RENAME TO expense_claims_claimcomment;
ALTER TABLE claims_claimstatushistory RENAME TO expense_claims_claimstatushistory;
