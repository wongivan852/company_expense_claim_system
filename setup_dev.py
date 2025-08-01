"""Development setup script."""

import os
import subprocess
import sys


def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"\n{description}...")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up Company Expense Claim System Development Environment")

    # Check if virtual environment exists
    if not os.path.exists(".venv"):
        print("❌ Virtual environment not found. Please create one first:")
        print("python -m venv .venv")
        print("source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate")
        sys.exit(1)

    # Check if .env file exists
    if not os.path.exists(".env"):
        print("\n📝 Creating .env file from template...")
        if os.path.exists(".env.example"):
            subprocess.run("cp .env.example .env", shell=True)
            print("✅ .env file created. Please edit it with your configuration.")
        else:
            print("❌ .env.example not found")

    # Install dependencies (if not already installed)
    print("\n📦 Installing dependencies...")
    if run_command("pip install -r requirements.txt", "Installing Python packages"):
        print("✅ All dependencies installed")

    # Run code formatting
    print("\n🎨 Formatting code...")
    run_command("black app/ tests/", "Code formatting with Black")
    run_command("isort app/ tests/", "Import sorting with isort")

    # Run linting
    print("\n🔍 Running code quality checks...")
    run_command(
        "flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203,W503",
        "Linting with flake8",
    )

    # Run tests
    print("\n🧪 Running tests...")
    run_command("pytest tests/ -v", "Running test suite")

    print("\n🎉 Development environment setup complete!")
    print("\n📚 Next steps:")
    print("1. Edit .env file with your database and email configuration")
    print("2. Set up PostgreSQL database")
    print("3. Run: alembic init alembic")
    print("4. Run: alembic revision --autogenerate -m 'Initial migration'")
    print("5. Run: alembic upgrade head")
    print("6. Start development server: uvicorn app.main:app --reload")
    print("\n🌐 API will be available at:")
    print("   - Application: http://localhost:8000")
    print("   - Documentation: http://localhost:8000/docs")
    print("   - Alternative docs: http://localhost:8000/redoc")


if __name__ == "__main__":
    main()
