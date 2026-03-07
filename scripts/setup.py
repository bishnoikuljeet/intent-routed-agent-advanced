"""
Setup script to initialize the project environment
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create necessary directories"""
    directories = [
        "data/docs",
        "data/vector_store",
        "data/cache",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created directory: {directory}")


def check_env_file():
    """Check if .env file exists"""
    if not Path(".env").exists():
        print("⚠ .env file not found. Copying from .env.example...")
        if Path(".env.example").exists():
            import shutil
            shutil.copy(".env.example", ".env")
            print("✓ Created .env file. Please edit it with your API keys.")
        else:
            print("✗ .env.example not found!")
            return False
    else:
        print("✓ .env file exists")
    return True


def verify_python_version():
    """Verify Python version is 3.11+"""
    if sys.version_info < (3, 11):
        print(f"✗ Python 3.11+ required. Current version: {sys.version}")
        return False
    print(f"✓ Python version: {sys.version_info.major}.{sys.version_info.minor}")
    return True


def main():
    print("=" * 60)
    print("Intent Routed Agent Advanced - Setup")
    print("=" * 60)
    print()
    
    if not verify_python_version():
        sys.exit(1)
    
    create_directories()
    print()
    
    check_env_file()
    print()
    
    print("=" * 60)
    print("Setup complete!")
    print()
    print("Next steps:")
    print("1. Edit .env file with your Azure OpenAI credentials")
    print("2. Install dependencies: pip install -e .")
    print("3. Run API: python main.py")
    print("4. Or run CLI: python cli/cli.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
