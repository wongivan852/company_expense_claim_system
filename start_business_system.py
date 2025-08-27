#!/usr/bin/env python3
"""Launch script for the enhanced Krystal Institute Expense Claim System."""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_requirements():
    """Check if required dependencies are installed."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'pydantic',
        'PIL',  # Pillow
        'cv2',  # opencv-python
        'pytesseract'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'cv2':
                import cv2
            else:
                __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"❌ {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {missing_packages}")
        print("\n🔧 Please install missing packages:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def check_database():
    """Check if database is initialized."""
    db_file = Path("expense_claims.db")
    
    if not db_file.exists():
        logger.info("Database not found. Initializing...")
        return False
    
    logger.info("✅ Database found")
    return True


def initialize_database():
    """Initialize the database with business data."""
    logger.info("Initializing database...")
    
    try:
        # Run the database initialization script
        result = subprocess.run([
            sys.executable, "init_business_db.py"
        ], capture_output=True, text=True, check=True)
        
        logger.info("Database initialized successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Database initialization failed: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False


def start_server():
    """Start the FastAPI server."""
    logger.info("Starting the expense claim system server...")
    
    try:
        # Start the server
        os.system("python -m app.main")
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")


def main():
    """Main function to launch the system."""
    print("=" * 80)
    print("🏢 KRYSTAL INSTITUTE EXPENSE CLAIM SYSTEM")
    print("Enhanced Backend Architecture with Business Logic")
    print("=" * 80)
    
    print("\n🔍 System Check...")
    
    # Check requirements
    print("\n1. Checking dependencies...")
    if not check_requirements():
        print("\n❌ Please install missing dependencies first")
        sys.exit(1)
    
    # Check database
    print("\n2. Checking database...")
    if not check_database():
        print("\n🔧 Initializing database with business data...")
        if not initialize_database():
            print("❌ Database initialization failed")
            sys.exit(1)
    
    print("\n✅ All checks passed!")
    
    print("\n" + "=" * 80)
    print("🚀 STARTING EXPENSE CLAIM SYSTEM")
    print("=" * 80)
    
    print("\n📊 System Information:")
    print("• Companies: 4 business entities")
    print("• Categories: 9 expense categories")
    print("• Currencies: 6 supported currencies (HKD base)")
    print("• Languages: English, Chinese Simplified/Traditional")
    print("• Features: OCR, Multi-currency, Approval workflow")
    
    print("\n🌐 Access Points:")
    print("• API Server: http://localhost:8084")
    print("• API Documentation: http://localhost:8084/docs")
    print("• Interactive API: http://localhost:8084/redoc")
    
    print("\n🔐 Demo Login Credentials:")
    print("• jeff.wong@krystal-institute.com (CEO/Manager)")
    print("• ivan.wong@krystal-institute.com (CTO/Manager)")
    print("• manager@krystal-tech.com (Manager)")
    print("• employee@krystal-tech.com (Employee)")
    print("• Password for all demo users: demo123")
    
    print("\n💡 Business Workflow:")
    print("1. Employee creates expense claim")
    print("2. Employee adds expense items with receipts")
    print("3. Employee submits claim for approval")
    print("4. Manager checks/reviews claim")
    print("5. Finance approves claim")
    print("6. System processes payment")
    
    print("\n🔧 Key Features:")
    print("• Real-time currency conversion")
    print("• OCR receipt processing (Chinese + English)")
    print("• Multi-level approval workflow")
    print("• Email notifications")
    print("• Category-based reporting")
    print("• Comprehensive audit trail")
    
    print("\n" + "-" * 80)
    print("Press Ctrl+C to stop the server")
    print("-" * 80)
    
    # Start the server
    start_server()


if __name__ == "__main__":
    main()