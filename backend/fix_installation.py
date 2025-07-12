#!/usr/bin/env python3
"""
Automated installation fix script for LangGraph Multimodal Chatbot
This script tries different installation methods automatically
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.11+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.11+")
        return False

def check_virtual_env():
    """Check if we're in a virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  Not in virtual environment - recommended to use venv")
        return False

def main():
    """Main installation fix process"""
    print("🔧 LangGraph Multimodal Chatbot - Installation Fix Script")
    print("=" * 60)
    
    # Step 1: Check environment
    print("\n1️⃣ Checking Environment")
    python_ok = check_python_version()
    venv_ok = check_virtual_env()
    
    if not python_ok:
        print("\n❌ Python version incompatible. Please use Python 3.11+")
        return 1
    
    # Step 2: Upgrade pip
    print("\n2️⃣ Upgrading pip")
    if not run_command("pip install --upgrade pip", "Upgrading pip"):
        print("⚠️  Pip upgrade failed, continuing anyway...")
    
    # Step 3: Clean existing installations
    print("\n3️⃣ Cleaning Existing Installations")
    run_command(
        "pip uninstall -y langchain langchain-core langchain-aws langgraph langchain-community",
        "Removing conflicting packages"
    )
    
    # Step 4: Try installation methods
    installation_methods = [
        ("make install", "Standard installation"),
        ("make install-safe", "Safe installation with conflict resolution"),
        ("make install-minimal", "Minimal installation"),
        ("pip install fastapi uvicorn langchain boto3 pydantic loguru", "Individual package installation")
    ]
    
    print("\n4️⃣ Trying Installation Methods")
    for command, description in installation_methods:
        if run_command(command, description):
            print(f"\n🎉 SUCCESS: {description} worked!")
            break
    else:
        print("\n❌ All installation methods failed")
        print("\n💡 Recommendations:")
        print("1. Try using Docker: docker-compose up -d")
        print("2. Create a fresh virtual environment")
        print("3. Check the INSTALL.md file for manual troubleshooting")
        return 1
    
    # Step 5: Test installation
    print("\n5️⃣ Testing Installation")
    if run_command("python test_installation.py", "Testing imports and functionality"):
        print("\n🎉 Installation completed successfully!")
        print("\nNext steps:")
        print("1. Copy environment template: cp env.template .env")
        print("2. Edit .env with your AWS credentials")
        print("3. Start the server: make dev")
        print("4. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("\n⚠️  Installation completed but tests failed")
        print("You may need to configure environment variables or check AWS credentials")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 