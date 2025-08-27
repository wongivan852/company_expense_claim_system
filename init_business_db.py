#!/usr/bin/env python3
"""Initialize database with business data for the enhanced expense claim system."""

import logging
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database import engine, SessionLocal, Base
from app.utils.seed_data import init_all_business_data, create_sample_expense_claims

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('init_db.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def create_database_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        return False


def initialize_business_data():
    """Initialize all business data."""
    logger.info("Initializing business data...")
    
    db = SessionLocal()
    try:
        # Initialize all business data
        init_all_business_data(db)
        
        # Create sample expense claims for testing
        create_sample_expense_claims(db)
        
        logger.info("Business data initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize business data: {e}")
        return False
        
    finally:
        db.close()


def main():
    """Main initialization function."""
    logger.info("Starting database initialization for Krystal Institute Expense System")
    
    print("=" * 70)
    print("KRYSTAL INSTITUTE EXPENSE CLAIM SYSTEM")
    print("Database Initialization Script")
    print("=" * 70)
    
    # Step 1: Create database tables
    print("\n1. Creating database tables...")
    if not create_database_tables():
        print("❌ Failed to create database tables")
        sys.exit(1)
    print("✅ Database tables created successfully")
    
    # Step 2: Initialize business data
    print("\n2. Initializing business data...")
    if not initialize_business_data():
        print("❌ Failed to initialize business data")
        sys.exit(1)
    print("✅ Business data initialized successfully")
    
    print("\n" + "=" * 70)
    print("DATABASE INITIALIZATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    
    print("\n📊 Business Data Summary:")
    print("• Companies: 4 business entities")
    print("  - Krystal Institute Limited (KIL)")
    print("  - Krystal Technology Limited (KTL)")  
    print("  - CG Global Entertainment Limited (CGEL)")
    print("  - 数谱环球(深圳)科技有限公司 (SPGZ)")
    
    print("\n• Expense Categories: 9 categories")
    print("  - Keynote Speech (主題演講)")
    print("  - Sponsor/Guest (贊助嘉賓)")
    print("  - Course Operations & Marketing (課程運營推廣)")
    print("  - Exhibition Procurement (展覽采購)")
    print("  - Other Miscellaneous (其他雜項)")
    print("  - Business Negotiations (業務商談)")
    print("  - Instructor Miscellaneous (講師雜項)")
    print("  - Procurement Miscellaneous (采購雜項)")
    print("  - Transportation (交通)")
    
    print("\n• Currencies: 6 supported currencies")
    print("  - HKD (Hong Kong Dollar) - Base currency")
    print("  - USD (US Dollar)")
    print("  - RMB/CNY (Chinese Yuan)")
    print("  - JPY (Japanese Yen)")
    print("  - EUR (Euro)")
    
    print("\n• Demo Users: 8 test users across all companies")
    print("  - jeff.wong@krystal-institute.com (CEO, Manager)")
    print("  - ivan.wong@krystal-institute.com (CTO, Manager)")
    print("  - manager@krystal-tech.com (Manager)")
    print("  - employee@krystal-tech.com (Employee)")
    print("  - manager@cg-global.com (Manager)")
    print("  - artist@cg-global.com (Employee)")
    print("  - manager@shuzhi-global.com (Manager)")
    print("  - employee@shuzhi-global.com (Employee)")
    
    print("\n🔐 Demo Login Credentials:")
    print("• All demo users have password: demo123")
    print("• Use any email above to log in")
    
    print("\n🌍 Multi-language Support:")
    print("• English (en)")
    print("• Chinese Simplified (zh-CN)")
    print("• Chinese Traditional (zh-TW)")
    
    print("\n💱 Exchange Rates:")
    print("• USD/HKD: 7.8000")
    print("• RMB/HKD: 1.0800")
    print("• JPY/HKD: 0.0528")
    print("• EUR/HKD: 8.4500")
    
    print("\n🔧 System Features:")
    print("• Real-time currency conversion")
    print("• OCR receipt processing")
    print("• Multi-level approval workflow")
    print("• Email notifications")
    print("• Comprehensive reporting")
    print("• Audit trail")
    
    print("\n🚀 Next Steps:")
    print("1. Start the API server: python -m app.main")
    print("2. Access API docs: http://localhost:8084/docs")
    print("3. Test with demo users")
    print("4. Upload receipt images to test OCR")
    print("5. Create and submit expense claims")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()