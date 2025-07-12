from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import uvicorn

from routers.chat import chat_router
from config.settings import settings

# Initialize FastAPI app
app = FastAPI(
    title="LangGraph Multimodal Chatbot",
    description="A multimodal chatbot powered by LangGraph and AWS Bedrock",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "LangGraph Multimodal Chatbot API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "langgraph-chatbot"}

if __name__ == "__main__":
    logger.info("Starting LangGraph Multimodal Chatbot API")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 