# Comprehensive Installation Guide

## 🛠️ Multiple Installation Methods

We've encountered and fixed several common issues. Here are multiple installation methods to handle different dependency conflict scenarios:

### Method 1: Automated Fix (Recommended)

```bash
# Run our automated fix script
python fix_installation.py
```

This script:
- Detects your Python environment
- Upgrades pip to latest version
- Removes conflicting packages
- Tries multiple installation approaches
- Verifies everything works

### Method 2: Standard Installation

```bash
# Clean any existing installations
pip uninstall -y langchain langchain-core langchain-aws langgraph langchain-community

# Install with flexible version constraints
make install
```

### Method 3: Safe Installation (If Method 2 Fails)

```bash
# Install with conflict resolution
make install-safe
```

### Method 4: Minimal Installation (Fallback)

```bash
# Install only essential packages
make install-minimal
```

## 🔧 What We Fixed

### Critical Issues Resolved:

#### 1. **Pydantic v2 Compatibility**
```bash
# Error: Field "model_used" in ChatResponse has conflict with protected namespace "model_"
# Solution: Added model_config = {"protected_namespaces": ()} to schemas
```
✅ **Status**: Fixed in `schemas/chat.py`

#### 2. **Claude Model Compatibility**
```bash
# Error: Claude v3 models are not supported by BedrockLLM
# Solution: Switched to ChatBedrock from langchain_aws
```
✅ **Status**: Fixed in `chains/multimodal_chain.py`

#### 3. **Chain Initialization Issues**
```bash
# Error: "MultimodalAnalysisChain" object has no field "llm"
# Solution: Implemented lazy loading pattern for chain instances
```
✅ **Status**: Fixed with lazy loading in `chains/multimodal_chain.py`

#### 4. **Dependency Version Conflicts**
```bash
# Error: langchain==0.1.0 requires langchain-core>=0.1.7 but you have langchain-core==0.1.0
# Solution: Used flexible version ranges instead of strict pinning
```
✅ **Status**: Fixed in `requirements.txt`

### Previous Issues:
1. **Strict Version Pinning**: Exact versions caused conflicts
2. **boto3/langchain-aws Mismatch**: `boto3==1.34.84` vs required `>=1.34.131`
3. **LangChain Version Matrix**: Complex interdependencies
4. **Built-in Package Conflicts**: `uuid` and `asyncio` conflicting with Python 3.11+

### Current Solution:
1. **Flexible Version Ranges**: Let pip resolve compatible versions
2. **Multiple Installation Options**: Fallback methods for difficult environments
3. **Minimal Requirements**: Core functionality only option
4. **Automated Fixes**: Script handles most common issues

## 📋 Installation Steps

### 1. Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 2. Choose Installation Method

```bash
# Option A: Automated fix (recommended)
python fix_installation.py

# Option B: If automated fix fails, try standard installation
make install

# Option C: If conflicts occur, try safe installation
make install-safe

# Option D: If still failing, use minimal installation
make install-minimal
```

### 3. Test Installation

```bash
# Verify everything works
python test_installation.py

# Or using make command
make test-install
```

### 4. Configure Environment

```bash
# Copy environment template
cp env.template .env

# Edit with your AWS credentials
nano .env  # or your preferred editor
```

### 5. Start Development Server

```bash
# Start the server
python main.py

# Or using make command
make dev
```

## 🔍 Troubleshooting Specific Issues

### Issue 1: Pydantic Protected Namespace Warnings

**Error:**
```
Field "model_used" in ChatResponse has conflict with protected namespace "model_"
```

**Solution:**
✅ **Already Fixed** - We added `model_config = {"protected_namespaces": ()}` to the affected schemas.

### Issue 2: Claude Model Not Supported

**Error:**
```
Claude v3 models are not supported by this LLM. Please use ChatBedrock instead.
```

**Solution:**
✅ **Already Fixed** - We updated the code to use `ChatBedrock` from `langchain_aws` instead of the deprecated `BedrockLLM`.

### Issue 3: Chain Field Errors

**Error:**
```
"MultimodalAnalysisChain" object has no field "llm"
```

**Solution:**
✅ **Already Fixed** - We implemented lazy loading for chain instances to avoid Pydantic field validation issues.

### Issue 4: Server Won't Start

**Error:**
```
ValidationError: 2 validation errors for MultimodalAnalysisChain
```

**Solution:**
✅ **Already Fixed** - We restructured the chain initialization to use lazy loading patterns.

### Issue 5: Dependency Conflicts

**Try these in order:**

```bash
# 1. Use our automated fix
python fix_installation.py

# 2. Clear pip cache
pip cache purge

# 3. Force reinstall
pip install --force-reinstall --no-cache-dir -r requirements.txt

# 4. Use minimal requirements
make install-minimal

# 5. Install packages individually
pip install fastapi uvicorn langchain boto3 pydantic loguru
```

### Issue 6: LangChain Import Errors

If you get import errors, try:

```bash
# Install specific compatible versions
pip install langchain>=0.1.20 langchain-core>=0.1.50 langchain-aws>=0.1.15
```

### Issue 7: AWS SDK Conflicts

```bash
# Update boto3 to latest compatible version
pip install boto3>=1.34.131 botocore>=1.34.131
```

### Issue 8: Python Version Problems

```bash
# Check Python version (must be 3.11+)
python --version

# Check you're in the right virtual environment
which python
```

## 📦 Package Information

### Core Packages (Required)
- `fastapi` - Web framework
- `langchain` - LLM framework
- `langgraph` - Workflow orchestration
- `langchain-aws` - AWS Bedrock integration
- `boto3` - AWS SDK
- `pydantic` - Data validation

### Optional Packages (Development)
- `pytest` - Testing
- `black` - Code formatting
- `ruff` - Linting
- `mypy` - Type checking

## 🧪 Testing Your Installation

### Quick Test
```bash
python -c "import fastapi, langchain, boto3; print('✅ Core imports work')"
```

### Full Test
```bash
python test_installation.py
```

### Server Test
```bash
# Start server
python main.py

# Test health endpoint (in another terminal)
curl http://localhost:8000/health
```

## 🐳 Docker Alternative

If pip installation continues to fail:

```bash
# Use Docker instead
docker-compose build
docker-compose up -d
docker-compose logs -f backend
```

## 📝 Expected Output

After successful installation, `python test_installation.py` should show:

```
🔍 Testing LangGraph Multimodal Chatbot Installation

1. Testing package imports...
✅ fastapi
✅ uvicorn
✅ langchain
✅ langchain_aws
✅ langchain_core
✅ langgraph
✅ boto3
✅ pydantic
✅ loguru
... (all packages)

📊 Summary:
✅ Successful imports: 18
❌ Failed imports: 0

2. Testing core functionality...
✅ FastAPI initialization
✅ LangChain core imports
✅ LangGraph imports
✅ AWS SDK imports
✅ Configuration module
✅ Schema modules
✅ Chain lazy loading

🎉 All tests passed! Installation successful.
```

## 🚀 Next Steps

Once installation is successful:

1. **Configure AWS**: Add credentials to `.env`
2. **Start Server**: Run `python main.py`
3. **Test API**: Visit `http://localhost:8000/docs`
4. **Test Health**: `curl http://localhost:8000/health`
5. **Make Requests**: Try the example endpoints

## 💡 Pro Tips

1. **Use Virtual Environment**: Always activate your venv first
2. **Start with Automated Fix**: Run `python fix_installation.py` first
3. **Check Dependencies**: Run `pip list` to see what's installed
4. **Test Before Configuring**: Verify installation works before adding AWS credentials
5. **Docker Fallback**: Use Docker if pip keeps failing

## 🔧 Development Mode

```bash
# Start development server with auto-reload
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using make
make dev
```

## 📊 Common Success Paths

1. **Most Users (80%)**: `python fix_installation.py` → `cp env.template .env` → `python main.py`
2. **Some Users (15%)**: `make install` → configure → test
3. **Few Users (5%)**: `make install-minimal` → Docker fallback

## 🆘 Still Having Issues?

If none of the methods work:

1. **Check Python version**: Must be 3.11+
2. **Check virtual environment**: Make sure it's activated
3. **Clear everything**: Delete venv and start fresh
4. **Use Docker**: Build and run with `docker-compose up`
5. **Check logs**: Look for specific error messages
6. **Report Issue**: Create an issue with your error logs

The key is to try the methods in order - most users will succeed with the automated fix script! 