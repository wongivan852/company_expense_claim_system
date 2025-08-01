"""Seed data for initial setup based on the expense claim template."""

from sqlalchemy.orm import Session
from app.models import Company, Currency, ExchangeRate, ExpenseCategory, User
from app.core.security import get_password_hash
from datetime import datetime


def seed_companies(db: Session):
    """Seed company data."""
    companies = [
        {"name": "CG Global Entertainment Ltd", "code": "CGGE", "address": "Hong Kong"},
        {"name": "CUHKSRI", "code": "CUHKSRI", "address": "Shenzhen, China"},
    ]

    for company_data in companies:
        existing = (
            db.query(Company).filter(Company.code == company_data["code"]).first()
        )
        if not existing:
            company = Company(**company_data)
            db.add(company)

    db.commit()


def seed_currencies(db: Session):
    """Seed currency data."""
    currencies = [
        {
            "code": "HKD",
            "name": "Hong Kong Dollar",
            "symbol": "HK$",
            "is_base_currency": True,
        },
        {
            "code": "RMB",
            "name": "Chinese Yuan Renminbi",
            "symbol": "¥",
            "is_base_currency": False,
        },
        {"code": "USD", "name": "US Dollar", "symbol": "$", "is_base_currency": False},
        {"code": "EUR", "name": "Euro", "symbol": "€", "is_base_currency": False},
    ]

    for currency_data in currencies:
        existing = (
            db.query(Currency).filter(Currency.code == currency_data["code"]).first()
        )
        if not existing:
            currency = Currency(**currency_data)
            db.add(currency)

    db.commit()


def seed_exchange_rates(db: Session):
    """Seed initial exchange rates."""
    # Get currencies
    hkd = db.query(Currency).filter(Currency.code == "HKD").first()
    rmb = db.query(Currency).filter(Currency.code == "RMB").first()
    usd = db.query(Currency).filter(Currency.code == "USD").first()
    eur = db.query(Currency).filter(Currency.code == "EUR").first()

    exchange_rates = [
        {
            "currency_id": hkd.id,
            "rate_to_hkd": 1.0,
            "effective_date": datetime(2024, 11, 1),
        },  # Base currency
        {
            "currency_id": rmb.id,
            "rate_to_hkd": 1.08,
            "effective_date": datetime(2024, 11, 1),
        },  # From the claim
        {
            "currency_id": usd.id,
            "rate_to_hkd": 7.8,
            "effective_date": datetime(2024, 11, 1),
        },  # Approximate
        {
            "currency_id": eur.id,
            "rate_to_hkd": 8.5,
            "effective_date": datetime(2024, 11, 1),
        },  # Approximate
    ]

    for rate_data in exchange_rates:
        existing = (
            db.query(ExchangeRate)
            .filter(
                ExchangeRate.currency_id == rate_data["currency_id"],
                ExchangeRate.effective_date == rate_data["effective_date"],
            )
            .first()
        )
        if not existing:
            rate = ExchangeRate(**rate_data)
            db.add(rate)

    db.commit()


def seed_expense_categories(db: Session):
    """Seed expense categories based on the claim template."""
    categories = [
        {
            "name": "Travel",
            "name_chinese": "交通",
            "description": "Transportation expenses including taxi, MTR, cross-border travel",
        },
        {
            "name": "Purchase",
            "name_chinese": "采购",
            "description": "Equipment, supplies, and material purchases",
        },
        {
            "name": "Catering",
            "name_chinese": "餐饮",
            "description": "Meals, drinks, tips, and entertainment expenses",
        },
        {
            "name": "Miscellaneous",
            "name_chinese": "雜項",
            "description": "Other miscellaneous expenses including delivery fees, mailing",
        },
        {
            "name": "Accommodation",
            "name_chinese": "住宿",
            "description": "Hotel and accommodation expenses",
        },
        {
            "name": "Communication",
            "name_chinese": "通讯",
            "description": "Phone, internet, data sim expenses",
        },
    ]

    for category_data in categories:
        existing = (
            db.query(ExpenseCategory)
            .filter(ExpenseCategory.name == category_data["name"])
            .first()
        )
        if not existing:
            category = ExpenseCategory(**category_data)
            db.add(category)

    db.commit()


def seed_users(db: Session):
    """Seed initial user data."""
    # Get the company
    cgge = db.query(Company).filter(Company.code == "CGGE").first()

    users = [
        {
            "email": "ivan.wong@cgge.com",
            "employee_id": "CGGE001",
            "full_name": "Ivan Wong",
            "department": "IT",
            "position": "Employee",
            "is_manager": False,
            "hashed_password": get_password_hash("password123"),
        },
        {
            "email": "manager@cgge.com",
            "employee_id": "CGGE999",
            "full_name": "Manager User",
            "department": "Management",
            "position": "Manager",
            "is_manager": True,
            "hashed_password": get_password_hash("manager123"),
        },
        {
            "email": "admin@cgge.com",
            "employee_id": "CGGE000",
            "full_name": "Admin User",
            "department": "IT",
            "position": "System Administrator",
            "is_manager": True,
            "hashed_password": get_password_hash("admin123"),
        },
    ]

    for user_data in users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(**user_data)
            db.add(user)

    db.commit()

    # Set manager relationships
    ivan = db.query(User).filter(User.email == "ivan.wong@cgge.com").first()
    manager = db.query(User).filter(User.email == "manager@cgge.com").first()

    if ivan and manager and not ivan.manager_id:
        ivan.manager_id = manager.id
        db.commit()


def seed_all_data(db: Session):
    """Seed all initial data."""
    print("🌱 Seeding companies...")
    seed_companies(db)

    print("🌱 Seeding currencies...")
    seed_currencies(db)

    print("🌱 Seeding exchange rates...")
    seed_exchange_rates(db)

    print("🌱 Seeding expense categories...")
    seed_expense_categories(db)

    print("🌱 Seeding users...")
    seed_users(db)

    print("✅ All seed data created successfully!")


if __name__ == "__main__":
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        seed_all_data(db)
    finally:
        db.close()
