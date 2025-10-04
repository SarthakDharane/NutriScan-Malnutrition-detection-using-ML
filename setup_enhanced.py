#!/usr/bin/env python3
"""
Setup Script for Enhanced Malnutrition Analysis System
Helps configure and test the new features
"""

import os
import sys
import subprocess
import shutil

def print_header():
    """Print setup header"""
    print("🚀 Enhanced Malnutrition Analysis System Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check Python version compatibility"""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'flask', 'tensorflow', 'numpy', 'matplotlib', 
        'seaborn', 'pillow', 'scikit-learn'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("\n✅ All required packages are installed")
    return True

def setup_directories():
    """Create necessary directories"""
    print("\n📁 Setting up directories...")
    
    directories = [
        'app/static/uploads',
        'app/static/plots',
        'scripts'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")

def run_database_migration():
    """Run database migration"""
    print("\n🗄️ Running database migration...")
    
    try:
        result = subprocess.run([
            sys.executable, 'scripts/migrate_database.py'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ Database migration completed successfully")
            return True
        else:
            print("❌ Database migration failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False

def run_tests():
    """Run feature tests"""
    print("\n🧪 Running feature tests...")
    
    try:
        result = subprocess.run([
            sys.executable, 'test_enhanced_features.py'
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed:")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the application: python run.py")
    print("2. Open your browser to: http://localhost:5000")
    print("3. Register an account and log in")
    print("4. Upload skin and nail images for analysis")
    print("5. Explore the enhanced reports and chatbot")
    print("\n📚 Documentation:")
    print("- README.md: Complete system overview")
    print("- Code comments: Implementation details")
    print("- Test script: Feature verification")
    print("\n🆘 Need help? Check the README or create an issue")

def main():
    """Main setup function"""
    print_header()
    
    # Check prerequisites
    if not check_python_version():
        return 1
    
    if not check_dependencies():
        return 1
    
    # Setup system
    setup_directories()
    
    # Run migration
    if not run_database_migration():
        print("\n⚠️ Database migration failed. You may need to run it manually:")
        print("python scripts/migrate_database.py")
    
    # Run tests
    if not run_tests():
        print("\n⚠️ Some tests failed. Check the implementation.")
    
    # Success
    print_next_steps()
    return 0

if __name__ == "__main__":
    sys.exit(main())
