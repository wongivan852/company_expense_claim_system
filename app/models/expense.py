"""Enhanced database models for the expense claim system with real business requirements."""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Index,
    UniqueConstraint,
    Enum,
    Numeric,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from app.database import Base


class ClaimStatus(str, enum.Enum):
    """Expense claim status enumeration."""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    CHECKED = "checked"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


class ExpenseCategories(str, enum.Enum):
    """Standard expense categories based on PDF form."""
    KEYNOTE_SPEECH = "keynote_speech"  # 主題演講
    SPONSOR_GUEST = "sponsor_guest"  # 贊助嘉賓
    COURSE_OPERATIONS_MARKETING = "course_operations_marketing"  # 課程運營推廣
    EXHIBITION_PROCUREMENT = "exhibition_procurement"  # 展覽采購
    OTHER_MISCELLANEOUS = "other_miscellaneous"  # 其他雜項
    BUSINESS_NEGOTIATIONS = "business_negotiations"  # 業務商談
    INSTRUCTOR_MISCELLANEOUS = "instructor_miscellaneous"  # 講師雜項
    PROCUREMENT_MISCELLANEOUS = "procurement_miscellaneous"  # 采購雜項
    TRANSPORTATION = "transportation"  # 交通


class SupportedCurrencies(str, enum.Enum):
    """Supported currencies with ISO codes."""
    HKD = "HKD"
    USD = "USD"
    RMB = "RMB"
    CNY = "CNY"  # Alternative for RMB
    JPY = "JPY"
    EUR = "EUR"


class User(Base):
    """Enhanced user model for employees who can submit claims."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    employee_id = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=False)
    full_name_chinese = Column(String)  # Chinese name support
    department = Column(String)
    position = Column(String)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    is_manager = Column(Boolean, default=False)
    is_finance = Column(Boolean, default=False)  # Finance team members
    is_active = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=False)
    language_preference = Column(String, default="en")  # en, zh-CN, zh-TW
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships with explicit foreign keys
    managed_users = relationship("User", backref="manager", remote_side=[id])
    company = relationship("Company", back_populates="employees")
    
    # Expense claims as claimant
    expense_claims = relationship(
        "ExpenseClaim", 
        foreign_keys="ExpenseClaim.claimant_id",
        back_populates="claimant"
    )
    
    # Claims approved by this user
    approved_claims = relationship(
        "ExpenseClaim",
        foreign_keys="ExpenseClaim.approved_by_id",
        back_populates="approved_by",
    )
    
    # Claims checked by this user
    checked_claims = relationship(
        "ExpenseClaim",
        foreign_keys="ExpenseClaim.checked_by_id",
        back_populates="checked_by",
    )

    # Indexes for performance
    __table_args__ = (
        Index("idx_user_company_active", "company_id", "is_active"),
        Index("idx_user_manager", "manager_id"),
    )


class Company(Base):
    """Enhanced company model for the four specific business entities."""

    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    name_chinese = Column(String)  # Chinese company name
    code = Column(String, unique=True, index=True)
    address = Column(Text)
    address_chinese = Column(Text)
    business_registration = Column(String)  # Company registration number
    tax_id = Column(String)
    default_currency = Column(String, default="HKD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    employees = relationship("User", back_populates="company")
    expense_claims = relationship("ExpenseClaim", back_populates="company")


class ExpenseClaim(Base):
    """Enhanced expense claim model with workflow and multi-language support."""

    __tablename__ = "expense_claims"

    id = Column(Integer, primary_key=True, index=True)
    claim_number = Column(String, unique=True, index=True)

    # Basic Information
    claimant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    event_name = Column(String)  # e.g., "IAICC event"
    event_name_chinese = Column(String)  # Chinese event name
    project_name = Column(String)  # Additional project reference
    period_from = Column(DateTime, nullable=False)
    period_to = Column(DateTime, nullable=False)

    # Status and Workflow
    status = Column(Enum(ClaimStatus), default=ClaimStatus.DRAFT, index=True)

    # Approval workflow with timestamps
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    checked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=True)
    check_notes = Column(Text)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_notes = Column(Text)

    # Financial totals
    total_amount_original = Column(Numeric(12, 2), default=0)
    total_amount_hkd = Column(Numeric(12, 2), default=0)
    
    # Category-wise totals for reporting
    keynote_total_hkd = Column(Numeric(12, 2), default=0)
    sponsor_total_hkd = Column(Numeric(12, 2), default=0)
    course_ops_total_hkd = Column(Numeric(12, 2), default=0)
    exhibition_total_hkd = Column(Numeric(12, 2), default=0)
    misc_total_hkd = Column(Numeric(12, 2), default=0)
    business_total_hkd = Column(Numeric(12, 2), default=0)
    instructor_total_hkd = Column(Numeric(12, 2), default=0)
    procurement_total_hkd = Column(Numeric(12, 2), default=0)
    transport_total_hkd = Column(Numeric(12, 2), default=0)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships with explicit foreign keys
    claimant = relationship(
        "User", 
        foreign_keys=[claimant_id], 
        back_populates="expense_claims"
    )
    company = relationship("Company", back_populates="expense_claims")
    checked_by = relationship(
        "User", 
        foreign_keys=[checked_by_id], 
        back_populates="checked_claims"
    )
    approved_by = relationship(
        "User", 
        foreign_keys=[approved_by_id], 
        back_populates="approved_claims"
    )
    expense_items = relationship(
        "ExpenseItem", back_populates="expense_claim", cascade="all, delete-orphan"
    )

    # Indexes for performance optimization
    __table_args__ = (
        Index("idx_claim_claimant_status", "claimant_id", "status"),
        Index("idx_claim_company_period", "company_id", "period_from", "period_to"),
        Index("idx_claim_approval_workflow", "status", "submitted_at", "approved_at"),
        Index("idx_claim_date_range", "period_from", "period_to"),
    )


class ExpenseCategory(Base):
    """Enhanced expense categories with multi-language support."""

    __tablename__ = "expense_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    name_chinese_simplified = Column(String)  # 简体中文
    name_chinese_traditional = Column(String)  # 繁体中文
    code = Column(Enum(ExpenseCategories), unique=True, nullable=False)
    description = Column(Text)
    description_chinese = Column(Text)
    is_active = Column(Boolean, default=True, index=True)
    sort_order = Column(Integer, default=0)
    requires_receipt = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    expense_items = relationship("ExpenseItem", back_populates="category")

    __table_args__ = (
        Index("idx_category_active_sort", "is_active", "sort_order"),
    )


class Currency(Base):
    """Enhanced currency model with real-time exchange rate support."""

    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(Enum(SupportedCurrencies), unique=True, nullable=False)
    name = Column(String, nullable=False)
    name_chinese = Column(String)
    symbol = Column(String(5))
    is_base_currency = Column(Boolean, default=False)  # HKD is base currency
    is_active = Column(Boolean, default=True)
    decimal_places = Column(Integer, default=2)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    expense_items = relationship("ExpenseItem", back_populates="currency")
    exchange_rates = relationship("ExchangeRate", back_populates="currency")

    __table_args__ = (
        Index("idx_currency_active", "is_active"),
    )


class ExchangeRate(Base):
    """Enhanced exchange rates with multiple data sources and caching."""

    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    rate_to_hkd = Column(Numeric(12, 8), nullable=False)  # Higher precision
    rate_from_hkd = Column(Numeric(12, 8), nullable=False)  # Reverse rate
    effective_date = Column(DateTime, nullable=False, index=True)
    source = Column(String, default="manual")  # manual, api, central_bank
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    currency = relationship("Currency", back_populates="exchange_rates")

    # Unique constraint for currency and date
    __table_args__ = (
        UniqueConstraint("currency_id", "effective_date", name="uq_currency_date"),
        Index("idx_exchange_rate_lookup", "currency_id", "effective_date", "is_active"),
    )


class ExpenseItem(Base):
    """Enhanced expense line items with detailed tracking."""

    __tablename__ = "expense_items"

    id = Column(Integer, primary_key=True, index=True)
    expense_claim_id = Column(Integer, ForeignKey("expense_claims.id"), nullable=False)

    # Item details
    item_number = Column(Integer, nullable=False)  # Sequential number within claim
    expense_date = Column(DateTime, nullable=False, index=True)
    description = Column(Text, nullable=False)
    description_chinese = Column(Text)

    # Category
    category_id = Column(Integer, ForeignKey("expense_categories.id"), nullable=False)

    # Amount and Currency with enhanced precision
    original_amount = Column(Numeric(12, 2), nullable=False)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False)
    exchange_rate = Column(Numeric(12, 8), nullable=False)
    amount_hkd = Column(Numeric(12, 2), nullable=False)

    # Receipt information
    has_receipt = Column(Boolean, default=True)
    receipt_reference = Column(String)  # Reference number for physical receipts
    receipt_notes = Column(Text)  # e.g., "Paper receipt", "Digital receipt"

    # Enhanced metadata
    location = Column(String)  # Location of expense
    location_chinese = Column(String)
    participants = Column(String)  # People involved
    business_purpose = Column(Text)  # Business justification
    vendor_name = Column(String)  # Name of vendor/supplier
    
    # Tax information
    tax_amount = Column(Numeric(12, 2), default=0)
    tax_rate = Column(Numeric(5, 4), default=0)  # Tax rate percentage
    
    # Approval flags
    requires_special_approval = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)

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

    # Indexes for performance
    __table_args__ = (
        Index("idx_expense_item_claim_date", "expense_claim_id", "expense_date"),
        Index("idx_expense_item_category", "category_id", "expense_date"),
        Index("idx_expense_item_amount", "amount_hkd", "expense_date"),
        UniqueConstraint("expense_claim_id", "item_number", name="uq_claim_item_number"),
    )


class ExpenseAttachment(Base):
    """Enhanced file attachments with OCR and compression support."""

    __tablename__ = "expense_attachments"

    id = Column(Integer, primary_key=True, index=True)
    expense_item_id = Column(Integer, ForeignKey("expense_items.id"), nullable=False)

    # File information
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    compressed_path = Column(String)  # Path to compressed version
    thumbnail_path = Column(String)  # Path to thumbnail
    file_size = Column(Integer)
    compressed_size = Column(Integer)
    mime_type = Column(String)
    file_hash = Column(String)  # SHA-256 hash for deduplication

    # OCR and processing
    ocr_text = Column(Text)  # Extracted text from OCR
    ocr_confidence = Column(Numeric(5, 4))  # OCR confidence score
    ocr_language = Column(String)  # Detected language
    is_processed = Column(Boolean, default=False)
    processing_status = Column(String, default="pending")  # pending, processing, completed, failed

    # Enhanced metadata
    image_width = Column(Integer)
    image_height = Column(Integer)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    expense_item = relationship("ExpenseItem", back_populates="attachments")
    uploaded_by = relationship("User")

    # Indexes
    __table_args__ = (
        Index("idx_attachment_item", "expense_item_id"),
        Index("idx_attachment_processing", "processing_status", "upload_date"),
        Index("idx_attachment_hash", "file_hash"),
    )


class ExchangeRateHistory(Base):
    """Historical exchange rates for audit and reporting."""
    
    __tablename__ = "exchange_rate_history"
    
    id = Column(Integer, primary_key=True, index=True)
    currency_code = Column(String(3), nullable=False)
    rate_to_hkd = Column(Numeric(12, 8), nullable=False)
    rate_date = Column(DateTime, nullable=False)
    source = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index("idx_rate_history_currency_date", "currency_code", "rate_date"),
    )


class AuditLog(Base):
    """Audit trail for all expense claim operations."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String, nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)  # CREATE, UPDATE, DELETE
    old_values = Column(Text)  # JSON string
    new_values = Column(Text)  # JSON string
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_audit_table_record", "table_name", "record_id"),
        Index("idx_audit_user_timestamp", "user_id", "timestamp"),
    )