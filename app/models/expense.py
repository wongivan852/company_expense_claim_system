"""Database models for the expense claim system."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Decimal,
    Boolean,
    Text,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


class User(Base):
    """User model for employees who can submit claims."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    employee_id = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=False)
    department = Column(String)
    position = Column(String)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_manager = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    managed_users = relationship("User", backref="manager", remote_side=[id])
    expense_claims = relationship("ExpenseClaim", back_populates="claimant")
    approved_claims = relationship(
        "ExpenseClaim",
        foreign_keys="ExpenseClaim.approved_by_id",
        back_populates="approved_by",
    )
    checked_claims = relationship(
        "ExpenseClaim",
        foreign_keys="ExpenseClaim.checked_by_id",
        back_populates="checked_by",
    )


class Company(Base):
    """Company model for different entities."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, index=True)
    address = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    expense_claims = relationship("ExpenseClaim", back_populates="company")


class ExpenseClaim(Base):
    """Main expense claim model."""

    __tablename__ = "expense_claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String, unique=True, index=True)

    # Basic Information
    claimant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    event_name = Column(String)  # e.g., "IAICC event"
    period_from = Column(DateTime)
    period_to = Column(DateTime)

    # Status and Workflow
    status = Column(
        String, default="draft"
    )  # draft, submitted, checked, approved, rejected, paid

    # Approval workflow
    checked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Totals
    total_amount_original = Column(Decimal(10, 2), default=0)
    total_amount_hkd = Column(Decimal(10, 2), default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    claimant = relationship(
        "User", foreign_keys=[claimant_id], back_populates="expense_claims"
    )
    company = relationship("Company", back_populates="expense_claims")
    checked_by = relationship(
        "User", foreign_keys=[checked_by_id], back_populates="checked_claims"
    )
    approved_by = relationship(
        "User", foreign_keys=[approved_by_id], back_populates="approved_claims"
    )
    expense_items = relationship(
        "ExpenseItem", back_populates="expense_claim", cascade="all, delete-orphan"
    )


class ExpenseCategory(Base):
    """Expense categories like Travel, Purchase, Catering, Miscellaneous."""

    __tablename__ = "expense_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    name_chinese = Column(String)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    expense_items = relationship("ExpenseItem", back_populates="category")


class Currency(Base):
    """Currency model for multi-currency support."""

    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False)  # HKD, RMB, USD, etc.
    name = Column(String, nullable=False)
    symbol = Column(String(5))
    is_base_currency = Column(Boolean, default=False)  # HKD is base currency
    is_active = Column(Boolean, default=True)

    # Relationships
    expense_items = relationship("ExpenseItem", back_populates="currency")
    exchange_rates = relationship("ExchangeRate", back_populates="currency")


class ExchangeRate(Base):
    """Exchange rates for currency conversion."""

    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    rate_to_hkd = Column(Decimal(10, 6), nullable=False)  # Rate to convert to HKD
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    currency = relationship("Currency", back_populates="exchange_rates")


class ExpenseItem(Base):
    """Individual expense line items."""

    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, index=True)
    expense_claim_id = Column(Integer, ForeignKey("expense_claims.id"), nullable=False)

    # Item details
    item_number = Column(Integer)  # Sequential number within the claim
    expense_date = Column(DateTime, nullable=False)
    description = Column(Text, nullable=False)
    description_chinese = Column(Text)

    # Category
    category_id = Column(Integer, ForeignKey("expense_categories.id"), nullable=False)

    # Amount and Currency
    original_amount = Column(Decimal(10, 2), nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    exchange_rate = Column(Decimal(10, 6), nullable=False)
    amount_hkd = Column(Decimal(10, 2), nullable=False)

    # Receipt information
    has_receipt = Column(Boolean, default=True)
    receipt_notes = Column(Text)  # e.g., "Paper receipt", "without receipt"

    # Additional metadata
    location = Column(String)  # e.g., "SZ Bay Port to CUHKSRI"
    participants = Column(String)  # e.g., "Total 2 persons included Jeff and Ivan"
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    expense_claim = relationship("ExpenseClaim", back_populates="expense_items")
    category = relationship("ExpenseCategory", back_populates="expense_items")
    currency = relationship("Currency", back_populates="expense_items")
    attachments = relationship(
        "ExpenseAttachment", back_populates="expense_item", cascade="all, delete-orphan"
    )


class ExpenseAttachment(Base):
    """File attachments for expense items (receipts, invoices, etc.)."""

    __tablename__ = "expense_attachments"

    id = Column(Integer, primary_key=True, index=True)
    expense_item_id = Column(Integer, ForeignKey("expense_items.id"), nullable=False)

    # File information
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String)

    # Metadata
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    expense_item = relationship("ExpenseItem", back_populates="attachments")
    uploaded_by = relationship("User")
