# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### 1. Prerequisites
- Python 3.11+ (tested with 3.11.11)
- AWS Account with Bedrock access
- Docker (optional)

### 2. Quick Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run automated installation fix
python fix_installation.py

# Configure environment
cp env.template .env
# Edit .env with your AWS credentials

# Start the server
python main.py
```

🎉 **Your server is now running at http://localhost:8000**

### 3. Test Your Installation

```bash
# Test health endpoint
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"langgraph-chatbot"}

# Test API documentation
open http://localhost:8000/docs
```

## 🔧 Alternative Installation Methods

### Method 1: Automated Fix (Recommended)
```bash
python fix_installation.py
```

### Method 2: Standard Installation
```bash
make install
```

### Method 3: Minimal Installation (Fallback)
```bash
make install-minimal
```

### Method 4: Docker (If pip fails)
```bash
docker-compose up -d
```

## ⚙️ AWS Configuration

### Quick AWS Setup

```bash
# Set up AWS credentials (choose one method)

# Method 1: Environment variables
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_REGION=us-east-1

# Method 2: AWS CLI
aws configure

# Method 3: IAM roles (recommended for production)
```

### Essential Environment Variables

Edit your `.env` file with:

```env
# Required
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-multimodal-chatbot-bucket

# Optional (with defaults)
DEBUG=true
PORT=8000
MAX_FILE_SIZE=10485760

# Bedrock Models
BEDROCK_CLAUDE_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_TITAN_IMAGE_MODEL=amazon.titan-image-generator-v1
BEDROCK_STABILITY_MODEL=stability.stable-diffusion-xl-base-v1-0
```

## 🧪 Test Your Setup

### 1. Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"langgraph-chatbot"}
```

### 2. Test Text Chat
```bash
curl -X POST "http://localhost:8000/api/v1/chat/text?question=Hello%20world&session_id=test"
```

### 3. Test API Documentation
Visit: http://localhost:8000/docs

## 🚀 Running the Application

### Development Mode

```bash
# Start development server
python main.py

# Or using Make
make dev

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Background Mode

```bash
# Start in background
nohup python main.py > server.log 2>&1 &

# Check if running
curl http://localhost:8000/health
```

## 🐳 Docker Quick Start

```bash
# Build and run with Docker
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/health` | GET | Basic health check |
| `/api/v1/chat/text` | POST | Text-only chat |
| `/api/v1/chat/multimodal` | POST | Multimodal chat (text + image) |
| `/api/v1/chat/analyze-image` | POST | Image analysis only |
| `/api/v1/chat/generate-image` | POST | Image generation |
| `/api/v1/chat/upload-image` | POST | Get presigned URL for upload |
| `/docs` | GET | Interactive API documentation |

## 📝 Common Use Cases

### 1. Text Chat
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat/text",
    params={"question": "Explain quantum computing", "session_id": "test"}
)
print(response.json())
```

### 2. Image Analysis
```python
response = requests.post(
    "http://localhost:8000/api/v1/chat/analyze-image",
    json={
        "image_url": "https://example.com/photo.jpg",
        "prompt": "What's in this image?"
    }
)
print(response.json()["analysis"])
```

### 3. Image Generation
```python
response = requests.post(
    "http://localhost:8000/api/v1/chat/generate-image",
    json={
        "prompt": "A futuristic cityscape at sunset",
        "width": 1024,
        "height": 1024
    }
)
print(response.json()["images"])
```

### 4. Multimodal Chat
```python
response = requests.post(
    "http://localhost:8000/api/v1/chat/multimodal",
    json={
        "question": "Describe this image and suggest improvements",
        "image_url": "https://example.com/design.jpg",
        "message_type": "multimodal",
        "session_id": "test"
    }
)
print(response.json()["response"])
```

## 🛠️ Development Commands

```bash
# Installation and testing
python fix_installation.py  # Fix dependencies
python test_installation.py # Test installation
make test-install           # Alternative test command

# Code quality
make format                 # Format code
make lint                   # Run linting
make test                   # Run tests

# Docker
make docker-build           # Build Docker image
make docker-run             # Run containers
make docker-stop            # Stop containers

# Server management
python main.py              # Start server
make dev                    # Development mode
make health                 # Check service health
```

## 🔍 Troubleshooting

### Common Issues

#### 1. **Installation Fails**
```bash
# Try automated fix
python fix_installation.py

# Or use minimal installation
make install-minimal
```

#### 2. **Server Won't Start**
```bash
# Check for specific errors
python main.py

# Verify installation
python test_installation.py
```

#### 3. **Pydantic Warnings**
```bash
# Expected warning (already fixed in code):
# Field "model_used" has conflict with protected namespace "model_"
# Status: ✅ Fixed automatically
```

#### 4. **AWS Credentials Not Found**
```bash
# Check AWS configuration
aws sts get-caller-identity

# Verify environment variables
echo $AWS_ACCESS_KEY_ID
cat .env
```

#### 5. **Bedrock Model Access Denied**
```bash
# Check if model is enabled in your AWS account
aws bedrock list-foundation-models --region us-east-1
```

#### 6. **S3 Bucket Permissions**
```bash
# Create bucket if it doesn't exist
aws s3 mb s3://your-bucket-name --region us-east-1
```

#### 7. **Docker Issues**
```bash
# Check Docker logs
docker-compose logs backend

# Rebuild containers
docker-compose build --no-cache
```

### Success Indicators

✅ **Installation**: `python test_installation.py` shows all green checkmarks
✅ **Server**: `curl http://localhost:8000/health` returns `{"status":"healthy"}`
✅ **API**: Interactive docs available at `http://localhost:8000/docs`
✅ **AWS**: Can list Bedrock models with `aws bedrock list-foundation-models`

### Getting Help

- Check the main [README.md](../README.md) for detailed documentation
- Review [INSTALL.md](INSTALL.md) for comprehensive troubleshooting
- Use [QUICK_FIX.md](QUICK_FIX.md) for specific error solutions
- Visit http://localhost:8000/docs for API documentation
- Check AWS CloudWatch for Bedrock/S3 errors

## 🎯 Next Steps

1. **Test API**: Use the interactive docs at `http://localhost:8000/docs`
2. **Customize Models**: Edit `config/settings.py` to modify model parameters
3. **Add Features**: Extend the LangGraph workflows in `graphs/multimodal_graph.py`
4. **Frontend Integration**: Connect to a Next.js or React frontend
5. **Production Deployment**: Use the Terraform configurations in `infrastructure/`
6. **Monitoring**: Set up CloudWatch alarms and logging

## 📊 Success Path Summary

**Most Common Path (80% of users):**
```bash
cd backend
python fix_installation.py
cp env.template .env
# Edit .env with AWS credentials
python main.py
curl http://localhost:8000/health
```

**Alternative Path (15% of users):**
```bash
cd backend
make install
cp env.template .env
# Configure AWS
python main.py
```

**Docker Fallback (5% of users):**
```bash
cd backend
cp env.template .env
# Configure AWS
docker-compose up -d
```

## 📚 Learn More

- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **AWS Bedrock**: https://docs.aws.amazon.com/bedrock/
- **FastAPI**: https://fastapi.tiangolo.com/
- **LangChain**: https://python.langchain.com/docs/

Happy coding! 🎉 