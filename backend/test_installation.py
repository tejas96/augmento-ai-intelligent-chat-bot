#!/usr/bin/env python3
"""
Test script to verify installation and imports work correctly
"""

import sys
import importlib

def test_imports():
    """Test that all required packages can be imported"""
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'langchain',
        'langchain_aws',
        'langchain_core',
        'langgraph',
        'boto3',
        'botocore',
        'pydantic',
        'pydantic_settings',
        'loguru',
        'PIL',  # Pillow
        'requests',
        'typing_extensions',
        'orjson',
        'httpx',
        'aiofiles',
    ]
    
    failed_imports = []
    successful_imports = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            successful_imports.append(package)
            print(f"✅ {package}")
        except ImportError as e:
            failed_imports.append((package, str(e)))
            print(f"❌ {package}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"✅ Successful imports: {len(successful_imports)}")
    print(f"❌ Failed imports: {len(failed_imports)}")
    
    if failed_imports:
        print("\n🔧 Failed imports:")
        for package, error in failed_imports:
            print(f"  - {package}: {error}")
        return False
    
    return True

def test_core_functionality():
    """Test core functionality"""
    
    try:
        # Test FastAPI
        from fastapi import FastAPI
        app = FastAPI()
        print("✅ FastAPI initialization")
        
        # Test LangChain imports
        from langchain_core.messages import HumanMessage
        from langchain_core.prompts import PromptTemplate
        print("✅ LangChain core imports")
        
        # Test LangGraph imports
        from langgraph.graph import StateGraph
        print("✅ LangGraph imports")
        
        # Test AWS imports
        import boto3
        print("✅ AWS SDK imports")
        
        # Test our modules
        from config.settings import settings
        print("✅ Configuration module")
        
        from schemas.chat import ChatRequest, MessageType
        print("✅ Schema modules")
        
        return True
        
    except Exception as e:
        print(f"❌ Core functionality test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🔍 Testing LangGraph Multimodal Chatbot Installation\n")
    
    print("1. Testing package imports...")
    imports_ok = test_imports()
    
    print("\n2. Testing core functionality...")
    functionality_ok = test_core_functionality()
    
    print("\n" + "="*50)
    if imports_ok and functionality_ok:
        print("🎉 All tests passed! Installation successful.")
        print("\nNext steps:")
        print("1. Configure your .env file with AWS credentials")
        print("2. Run: make dev")
        print("3. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 