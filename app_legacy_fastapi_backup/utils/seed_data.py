"""Enhanced seed data initialization with real business requirements."""

import logging
from decimal import Decimal
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.expense import (
    Company, User, Currency, ExchangeRate, ExpenseCategory,
    ExpenseCategories, SupportedCurrencies
)
from app.services.currency_service import initialize_currencies
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


def init_business_companies(db: Session):
    """Initialize the four specific business companies."""
    
    companies_data = [
        {
            "name": "Krystal Institute Limited",
            "name_chinese": "晶體研究院有限公司",
            "code": "KIL",
            "address": "Hong Kong",
            "address_chinese": "香港",
            "business_registration": "KIL-2024-001",
            "tax_id": "TAX-KIL-001",
            "default_currency": "HKD"
        },
        {
            "name": "Krystal Technology Limited",
            "name_chinese": "晶體科技有限公司",
            "code": "KTL",
            "address": "Hong Kong",
            "address_chinese": "香港",
            "business_registration": "KTL-2024-002",
            "tax_id": "TAX-KTL-002",
            "default_currency": "HKD"
        },
        {
            "name": "CG Global Entertainment Limited",
            "name_chinese": "CG環球娛樂有限公司",
            "code": "CGEL",
            "address": "Hong Kong",
            "address_chinese": "香港",
            "business_registration": "CGEL-2024-003",
            "tax_id": "TAX-CGEL-003",
            "default_currency": "HKD"
        },
        {
            "name": "数谱环球(深圳)科技有限公司",
            "name_chinese": "数谱环球(深圳)科技有限公司",
            "code": "SPGZ",
            "address": "Shenzhen, China",
            "address_chinese": "中国深圳",
            "business_registration": "SPGZ-2024-004",
            "tax_id": "TAX-SPGZ-004",
            "default_currency": "RMB"
        }
    ]
    
    for company_data in companies_data:
        existing = db.query(Company).filter(Company.code == company_data["code"]).first()
        if not existing:
            company = Company(**company_data)
            db.add(company)
            logger.info(f"Created company: {company_data['name']}")
    
    try:
        db.commit()
        logger.info("Successfully initialized business companies")
    except Exception as e:
        logger.error(f"Failed to initialize companies: {e}")
        db.rollback()


def init_expense_categories(db: Session):
    """Initialize expense categories based on PDF form structure."""
    
    categories_data = [
        {
            "name": "Keynote Speech",
            "name_chinese_simplified": "主题演讲",
            "name_chinese_traditional": "主題演講",
            "code": ExpenseCategories.KEYNOTE_SPEECH,
            "description": "Expenses related to keynote speeches and main presentations",
            "description_chinese": "主题演讲和主要演示相关费用",
            "sort_order": 1,
            "requires_receipt": True
        },
        {
            "name": "Sponsor/Guest",
            "name_chinese_simplified": "赞助嘉宾",
            "name_chinese_traditional": "贊助嘉賓",
            "code": ExpenseCategories.SPONSOR_GUEST,
            "description": "Expenses for sponsors and guest speakers",
            "description_chinese": "赞助商和嘉宾演讲者费用",
            "sort_order": 2,
            "requires_receipt": True
        },
        {
            "name": "Course Operations & Marketing",
            "name_chinese_simplified": "课程运营推广",
            "name_chinese_traditional": "課程運營推廣",
            "code": ExpenseCategories.COURSE_OPERATIONS_MARKETING,
            "description": "Course operations and marketing expenses",
            "description_chinese": "课程运营和市场推广费用",
            "sort_order": 3,
            "requires_receipt": True
        },
        {
            "name": "Exhibition Procurement",
            "name_chinese_simplified": "展览采购",
            "name_chinese_traditional": "展覽采購",
            "code": ExpenseCategories.EXHIBITION_PROCUREMENT,
            "description": "Exhibition and procurement related expenses",
            "description_chinese": "展览和采购相关费用",
            "sort_order": 4,
            "requires_receipt": True
        },
        {
            "name": "Other Miscellaneous",
            "name_chinese_simplified": "其他杂项",
            "name_chinese_traditional": "其他雜項",
            "code": ExpenseCategories.OTHER_MISCELLANEOUS,
            "description": "Other miscellaneous expenses",
            "description_chinese": "其他杂项费用",
            "sort_order": 5,
            "requires_receipt": True
        },
        {
            "name": "Business Negotiations",
            "name_chinese_simplified": "业务商谈",
            "name_chinese_traditional": "業務商談",
            "code": ExpenseCategories.BUSINESS_NEGOTIATIONS,
            "description": "Business meeting and negotiation expenses",
            "description_chinese": "商务会议和谈判费用",
            "sort_order": 6,
            "requires_receipt": True
        },
        {
            "name": "Instructor Miscellaneous",
            "name_chinese_simplified": "讲师杂项",
            "name_chinese_traditional": "講師雜項",
            "code": ExpenseCategories.INSTRUCTOR_MISCELLANEOUS,
            "description": "Instructor related miscellaneous expenses",
            "description_chinese": "讲师相关杂项费用",
            "sort_order": 7,
            "requires_receipt": True
        },
        {
            "name": "Procurement Miscellaneous",
            "name_chinese_simplified": "采购杂项",
            "name_chinese_traditional": "采購雜項",
            "code": ExpenseCategories.PROCUREMENT_MISCELLANEOUS,
            "description": "Procurement related miscellaneous expenses",
            "description_chinese": "采购相关杂项费用",
            "sort_order": 8,
            "requires_receipt": True
        },
        {
            "name": "Transportation",
            "name_chinese_simplified": "交通",
            "name_chinese_traditional": "交通",
            "code": ExpenseCategories.TRANSPORTATION,
            "description": "Transportation and travel expenses",
            "description_chinese": "交通和旅行费用",
            "sort_order": 9,
            "requires_receipt": True
        }
    ]
    
    for category_data in categories_data:
        existing = db.query(ExpenseCategory).filter(
            ExpenseCategory.code == category_data["code"]
        ).first()
        if not existing:
            category = ExpenseCategory(**category_data)
            db.add(category)
            logger.info(f"Created expense category: {category_data['name']}")
    
    try:
        db.commit()
        logger.info("Successfully initialized expense categories")
    except Exception as e:
        logger.error(f"Failed to initialize expense categories: {e}")
        db.rollback()


def init_demo_users(db: Session):
    """Initialize demo users for testing."""
    
    # Get companies
    companies = {
        company.code: company.id 
        for company in db.query(Company).all()
    }
    
    users_data = [
        # KIL Users
        {
            "email": "jeff.wong@krystal-institute.com",
            "employee_id": "KIL001",
            "full_name": "Jeff Wong",
            "full_name_chinese": "黃志強",
            "department": "Management",
            "position": "CEO",
            "company_id": companies.get("KIL"),
            "is_manager": True,
            "is_finance": True,
            "language_preference": "en",
            "password": "demo123"
        },
        {
            "email": "ivan.wong@krystal-institute.com",
            "employee_id": "KIL002",
            "full_name": "Ivan Wong",
            "full_name_chinese": "黃一帆",
            "department": "Technology",
            "position": "CTO",
            "company_id": companies.get("KIL"),
            "is_manager": True,
            "language_preference": "en",
            "password": "demo123"
        },
        # KTL Users
        {
            "email": "manager@krystal-tech.com",
            "employee_id": "KTL001",
            "full_name": "Technology Manager",
            "full_name_chinese": "技術經理",
            "department": "Technology",
            "position": "Manager",
            "company_id": companies.get("KTL"),
            "is_manager": True,
            "language_preference": "zh-TW",
            "password": "demo123"
        },
        {
            "email": "employee@krystal-tech.com",
            "employee_id": "KTL002",
            "full_name": "Tech Employee",
            "full_name_chinese": "技術員工",
            "department": "Technology",
            "position": "Developer",
            "company_id": companies.get("KTL"),
            "language_preference": "zh-TW",
            "password": "demo123"
        },
        # CGEL Users
        {
            "email": "manager@cg-global.com",
            "employee_id": "CGEL001",
            "full_name": "Entertainment Manager",
            "full_name_chinese": "娛樂經理",
            "department": "Entertainment",
            "position": "Manager",
            "company_id": companies.get("CGEL"),
            "is_manager": True,
            "language_preference": "zh-TW",
            "password": "demo123"
        },
        {
            "email": "artist@cg-global.com",
            "employee_id": "CGEL002",
            "full_name": "Creative Artist",
            "full_name_chinese": "創意藝術家",
            "department": "Creative",
            "position": "Artist",
            "company_id": companies.get("CGEL"),
            "language_preference": "zh-TW",
            "password": "demo123"
        },
        # SPGZ Users (Chinese company)
        {
            "email": "manager@shuzhi-global.com",
            "employee_id": "SPGZ001",
            "full_name": "Shenzhen Manager",
            "full_name_chinese": "深圳經理",
            "department": "Technology",
            "position": "總經理",
            "company_id": companies.get("SPGZ"),
            "is_manager": True,
            "is_finance": True,
            "language_preference": "zh-CN",
            "password": "demo123"
        },
        {
            "email": "employee@shuzhi-global.com",
            "employee_id": "SPGZ002",
            "full_name": "Tech Specialist",
            "full_name_chinese": "技術專員",
            "department": "Technology",
            "position": "技術專員",
            "company_id": companies.get("SPGZ"),
            "language_preference": "zh-CN",
            "password": "demo123"
        }
    ]
    
    for user_data in users_data:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            password = user_data.pop("password")
            user = User(
                **user_data,
                hashed_password=get_password_hash(password)
            )
            db.add(user)
            logger.info(f"Created user: {user_data['full_name']}")
    
    # Set up manager relationships
    try:
        db.commit()
        
        # Update manager relationships
        jeff = db.query(User).filter(User.employee_id == "KIL001").first()
        ivan = db.query(User).filter(User.employee_id == "KIL002").first()
        if jeff and ivan:
            ivan.manager_id = jeff.id
        
        ktl_manager = db.query(User).filter(User.employee_id == "KTL001").first()
        ktl_employee = db.query(User).filter(User.employee_id == "KTL002").first()
        if ktl_manager and ktl_employee:
            ktl_employee.manager_id = ktl_manager.id
        
        cgel_manager = db.query(User).filter(User.employee_id == "CGEL001").first()
        cgel_artist = db.query(User).filter(User.employee_id == "CGEL002").first()
        if cgel_manager and cgel_artist:
            cgel_artist.manager_id = cgel_manager.id
        
        spgz_manager = db.query(User).filter(User.employee_id == "SPGZ001").first()
        spgz_employee = db.query(User).filter(User.employee_id == "SPGZ002").first()
        if spgz_manager and spgz_employee:
            spgz_employee.manager_id = spgz_manager.id
        
        db.commit()
        logger.info("Successfully initialized demo users with manager relationships")
        
    except Exception as e:
        logger.error(f"Failed to initialize demo users: {e}")
        db.rollback()


def init_exchange_rates_with_business_data(db: Session):
    """Initialize exchange rates with realistic business values."""
    
    # Current realistic exchange rates (as of 2024)
    business_rates = [
        {
            "currency_code": "USD",
            "rate_to_hkd": Decimal("7.8000"),
            "source": "business_manual"
        },
        {
            "currency_code": "RMB", 
            "rate_to_hkd": Decimal("1.0800"),
            "source": "business_manual"
        },
        {
            "currency_code": "CNY",
            "rate_to_hkd": Decimal("1.0800"),
            "source": "business_manual"
        },
        {
            "currency_code": "JPY",
            "rate_to_hkd": Decimal("0.0528"),
            "source": "business_manual"
        },
        {
            "currency_code": "EUR",
            "rate_to_hkd": Decimal("8.4500"),
            "source": "business_manual"
        }
    ]
    
    for rate_data in business_rates:
        currency = db.query(Currency).filter(
            Currency.code == rate_data["currency_code"]
        ).first()
        
        if currency:
            # Check if rate already exists for today
            existing_rate = (
                db.query(ExchangeRate)
                .filter(
                    ExchangeRate.currency_id == currency.id,
                    ExchangeRate.effective_date >= datetime.utcnow().date()
                )
                .first()
            )
            
            if not existing_rate:
                exchange_rate = ExchangeRate(
                    currency_id=currency.id,
                    rate_to_hkd=rate_data["rate_to_hkd"],
                    rate_from_hkd=Decimal("1.0") / rate_data["rate_to_hkd"],
                    effective_date=datetime.utcnow(),
                    source=rate_data["source"],
                    is_active=True
                )
                db.add(exchange_rate)
                logger.info(f"Added exchange rate for {rate_data['currency_code']}: {rate_data['rate_to_hkd']}")
    
    try:
        db.commit()
        logger.info("Successfully initialized business exchange rates")
    except Exception as e:
        logger.error(f"Failed to initialize exchange rates: {e}")
        db.rollback()


def init_all_business_data(db: Session):
    """Initialize all business data in the correct order."""
    
    logger.info("Starting business data initialization...")
    
    # 1. Initialize currencies first
    logger.info("Initializing currencies...")
    initialize_currencies(db)
    
    # 2. Initialize companies
    logger.info("Initializing business companies...")
    init_business_companies(db)
    
    # 3. Initialize expense categories
    logger.info("Initializing expense categories...")
    init_expense_categories(db)
    
    # 4. Initialize demo users
    logger.info("Initializing demo users...")
    init_demo_users(db)
    
    # 5. Initialize business exchange rates
    logger.info("Initializing exchange rates...")
    init_exchange_rates_with_business_data(db)
    
    logger.info("Business data initialization completed successfully!")


def create_sample_expense_claims(db: Session):
    """Create sample expense claims for testing."""
    
    from app.services.expense_service import ExpenseClaimService
    from datetime import datetime, timedelta
    
    # Get users and companies
    ivan = db.query(User).filter(User.employee_id == "KIL002").first()
    ktl_employee = db.query(User).filter(User.employee_id == "KTL002").first()
    
    kil_company = db.query(Company).filter(Company.code == "KIL").first()
    ktl_company = db.query(Company).filter(Company.code == "KTL").first()
    
    # Get categories
    transport_cat = db.query(ExpenseCategory).filter(
        ExpenseCategory.code == ExpenseCategories.TRANSPORTATION
    ).first()
    keynote_cat = db.query(ExpenseCategory).filter(
        ExpenseCategory.code == ExpenseCategories.KEYNOTE_SPEECH
    ).first()
    
    # Get currencies
    hkd_currency = db.query(Currency).filter(Currency.code == "HKD").first()
    usd_currency = db.query(Currency).filter(Currency.code == "USD").first()
    rmb_currency = db.query(Currency).filter(Currency.code == "RMB").first()
    
    if not all([ivan, kil_company, transport_cat, hkd_currency]):
        logger.warning("Cannot create sample claims - missing required data")
        return
    
    expense_service = ExpenseClaimService(db)
    
    try:
        # Sample claim 1: IAICC Event for Ivan
        claim1 = expense_service.create_claim(
            claimant_id=ivan.id,
            company_id=kil_company.id,
            event_name="IAICC AI Conference 2024",
            event_name_chinese="IAICC人工智能會議2024",
            period_from=datetime.utcnow() - timedelta(days=7),
            period_to=datetime.utcnow() - timedelta(days=1)
        )
        
        # Add transportation expense
        expense_service.add_expense_item(
            claim_id=claim1.id,
            expense_data={
                "expense_date": datetime.utcnow() - timedelta(days=5),
                "description": "Taxi from SZ Bay Port to CUHKSRI",
                "description_chinese": "从深圳湾口岸到中大(深圳)的士费",
                "category_id": transport_cat.id,
                "original_amount": Decimal("85.00"),
                "currency_id": rmb_currency.id,
                "currency_code": "RMB",
                "location": "Shenzhen to CUHK",
                "location_chinese": "深圳到中大",
                "participants": "Total 2 persons included Jeff and Ivan",
                "business_purpose": "Transportation to AI conference venue"
            }
        )
        
        # Add keynote speaker fee
        if keynote_cat:
            expense_service.add_expense_item(
                claim_id=claim1.id,
                expense_data={
                    "expense_date": datetime.utcnow() - timedelta(days=3),
                    "description": "Keynote speaker honorarium",
                    "description_chinese": "主题演讲嘉宾费",
                    "category_id": keynote_cat.id,
                    "original_amount": Decimal("5000.00"),
                    "currency_id": hkd_currency.id,
                    "currency_code": "HKD",
                    "business_purpose": "Payment for keynote speech at IAICC conference"
                }
            )
        
        logger.info(f"Created sample claim: {claim1.claim_number}")
        
        # Sample claim 2: KTL employee business trip
        if ktl_employee and ktl_company:
            claim2 = expense_service.create_claim(
                claimant_id=ktl_employee.id,
                company_id=ktl_company.id,
                event_name="Business Development Trip",
                event_name_chinese="業務發展出差",
                period_from=datetime.utcnow() - timedelta(days=14),
                period_to=datetime.utcnow() - timedelta(days=10)
            )
            
            # Add meal expense
            expense_service.add_expense_item(
                claim_id=claim2.id,
                expense_data={
                    "expense_date": datetime.utcnow() - timedelta(days=12),
                    "description": "Business lunch with client",
                    "description_chinese": "与客户商务午餐",
                    "category_id": transport_cat.id,  # Using transport as example
                    "original_amount": Decimal("350.00"),
                    "currency_id": hkd_currency.id,
                    "currency_code": "HKD",
                    "business_purpose": "Client relationship building"
                }
            )
            
            logger.info(f"Created sample claim: {claim2.claim_number}")
            
    except Exception as e:
        logger.error(f"Failed to create sample claims: {e}")


if __name__ == "__main__":
    # This can be run directly for testing
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        init_all_business_data(db)
        create_sample_expense_claims(db)
    finally:
        db.close()