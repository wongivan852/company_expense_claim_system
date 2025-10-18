"""Pydantic schemas for expense claim system."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# Base schemas
class ExpenseAttachmentBase(BaseModel):
    filename: str
    original_filename: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class ExpenseAttachmentCreate(ExpenseAttachmentBase):
    pass


class ExpenseAttachment(ExpenseAttachmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    upload_date: datetime
    uploaded_by_id: int


# Currency schemas
class CurrencyBase(BaseModel):
    code: str = Field(..., max_length=3)
    name: str
    symbol: Optional[str] = None
    is_base_currency: bool = False


class CurrencyCreate(CurrencyBase):
    pass


class Currency(CurrencyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool = True


# Exchange Rate schemas
class ExchangeRateBase(BaseModel):
    currency_id: int
    rate_to_hkd: Decimal = Field(..., decimal_places=6)
    effective_date: datetime


class ExchangeRateCreate(ExchangeRateBase):
    pass


class ExchangeRate(ExchangeRateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    currency: Currency


# Expense Category schemas
class ExpenseCategoryBase(BaseModel):
    name: str
    name_chinese: Optional[str] = None
    description: Optional[str] = None


class ExpenseCategoryCreate(ExpenseCategoryBase):
    pass


class ExpenseCategory(ExpenseCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool = True
    created_at: datetime


# Company schemas
class CompanyBase(BaseModel):
    name: str
    code: str
    address: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class Company(CompanyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool = True
    created_at: datetime


# User schemas
class UserBase(BaseModel):
    email: str
    full_name: str
    employee_id: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    manager_id: Optional[int] = None
    is_manager: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    manager_id: Optional[int] = None


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


# Expense Item schemas
class ExpenseItemBase(BaseModel):
    expense_date: datetime
    description: str
    description_chinese: Optional[str] = None
    category_id: int
    original_amount: Decimal = Field(..., decimal_places=2)
    currency_id: int
    exchange_rate: Decimal = Field(..., decimal_places=6)
    amount_hkd: Decimal = Field(..., decimal_places=2)
    has_receipt: bool = True
    receipt_notes: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[str] = None
    notes: Optional[str] = None


class ExpenseItemCreate(ExpenseItemBase):
    pass


class ExpenseItemUpdate(BaseModel):
    expense_date: Optional[datetime] = None
    description: Optional[str] = None
    description_chinese: Optional[str] = None
    category_id: Optional[int] = None
    original_amount: Optional[Decimal] = None
    currency_id: Optional[int] = None
    exchange_rate: Optional[Decimal] = None
    amount_hkd: Optional[Decimal] = None
    has_receipt: Optional[bool] = None
    receipt_notes: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[str] = None
    notes: Optional[str] = None


class ExpenseItem(ExpenseItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_number: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Related objects
    category: ExpenseCategory
    currency: Currency
    attachments: List[ExpenseAttachment] = []


# Expense Claim schemas
class ExpenseClaimBase(BaseModel):
    company_id: int
    event_name: Optional[str] = None
    period_from: datetime
    period_to: datetime


class ExpenseClaimCreate(ExpenseClaimBase):
    expense_items: List[ExpenseItemCreate] = []


class ExpenseClaimUpdate(BaseModel):
    event_name: Optional[str] = None
    period_from: Optional[datetime] = None
    period_to: Optional[datetime] = None
    status: Optional[str] = None


class ExpenseClaimSubmit(BaseModel):
    """Schema for submitting a claim for approval."""

    pass


class ExpenseClaimApproval(BaseModel):
    """Schema for approving/rejecting a claim."""

    action: str = Field(..., regex="^(approve|reject)$")
    notes: Optional[str] = None


class ExpenseClaim(ExpenseClaimBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_number: str
    claimant_id: int
    status: str = "draft"
    total_amount_original: Decimal = Field(default=0, decimal_places=2)
    total_amount_hkd: Decimal = Field(default=0, decimal_places=2)

    # Workflow timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    checked_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None

    # Related objects
    claimant: User
    company: Company
    checked_by: Optional[User] = None
    approved_by: Optional[User] = None
    expense_items: List[ExpenseItem] = []


# Summary schemas for reporting
class ExpenseClaimSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    claim_number: str
    claimant_name: str
    company_name: str
    event_name: Optional[str] = None
    period_from: datetime
    period_to: datetime
    status: str
    total_amount_hkd: Decimal
    item_count: int
    created_at: datetime
    submitted_at: Optional[datetime] = None


# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserLogin(BaseModel):
    email: str
    password: str
