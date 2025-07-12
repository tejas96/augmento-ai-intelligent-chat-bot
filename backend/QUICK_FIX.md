# 🚀 Quick Installation Fix

If you're having dependency conflicts, try these solutions **in order**:

## 🔧 Automated Fix (Recommended)

```bash
cd backend
python fix_installation.py
```

This script automatically tries multiple installation methods for you.

## 📋 Manual Methods

### Method 1: Standard
```bash
make install
```

### Method 2: Safe Installation
```bash
make install-safe
```

### Method 3: Minimal (Core Only)
```bash
make install-minimal
```

### Method 4: Individual Packages
```bash
pip install fastapi uvicorn langchain boto3 pydantic loguru
```

## 🧪 Test Installation

```bash
make test-install
```

## 🐳 Docker Fallback

If all else fails:

```bash
docker-compose up -d
```

## 💡 Common Issues & Solutions

| Problem | Error Message | Solution |
|---------|---------------|----------|
| **Pydantic Warnings** | `Field "model_used" has conflict with protected namespace "model_"` | ✅ **Fixed** - Added `model_config = {"protected_namespaces": ()}` |
| **Claude Model Error** | `Claude v3 models are not supported by BedrockLLM` | ✅ **Fixed** - Using `ChatBedrock` instead |
| **Chain Field Error** | `"MultimodalAnalysisChain" object has no field "llm"` | ✅ **Fixed** - Implemented lazy loading |
| **Version Conflicts** | `langchain==0.1.0 requires langchain-core>=0.1.7` | `make install-safe` |
| **boto3 Conflicts** | `langchain-aws==0.1.17 requires boto3>=1.34.131` | `pip install boto3>=1.34.131` |
| **Import Errors** | `ModuleNotFoundError: No module named 'langchain_aws'` | `make install-minimal` |

## 🔍 Specific Error Fixes

### 1. Pydantic Protected Namespace Error
```bash
# Error: Field "model_used" in ChatResponse has conflict with protected namespace "model_"
# Status: ✅ FIXED in schemas/chat.py
```

### 2. Claude Model Compatibility
```bash
# Error: Claude v3 models are not supported by this LLM
# Status: ✅ FIXED - Updated to use ChatBedrock from langchain_aws
```

### 3. Chain Initialization Error
```bash
# Error: "MultimodalAnalysisChain" object has no field "llm"
# Status: ✅ FIXED - Implemented lazy loading pattern
```

### 4. Server Startup Issues
```bash
# If server won't start:
python main.py  # Check for specific errors

# Common solutions:
python fix_installation.py  # Fix dependencies
cp env.template .env       # Set up environment
```

## ⚡ One-Liner Setup

```bash
cd backend && python fix_installation.py && cp env.template .env && python main.py
```

## 🧪 Quick Test Commands

```bash
# Test health
curl http://localhost:8000/health

# Test installation
python test_installation.py

# Test API (requires AWS credentials)
curl -X POST "http://localhost:8000/api/v1/chat/text?question=Hello&session_id=test"
```

## 🎯 Success Indicators

✅ **Installation Success**: `python test_installation.py` shows all green checkmarks
✅ **Server Running**: `curl http://localhost:8000/health` returns `{"status":"healthy"}`
✅ **API Working**: Interactive docs available at `http://localhost:8000/docs`

---

**Still stuck?** Check `INSTALL.md` for detailed troubleshooting or `README.md` for complete documentation. 