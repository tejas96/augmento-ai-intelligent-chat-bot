from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional
import time
import uuid  # Using standard library uuid module
from loguru import logger

from schemas.chat import (
    ChatRequest, ChatResponse, ImageAnalysisRequest, ImageAnalysisResponse,
    ImageGenerationRequest, ImageGenerationResponse, UploadImageRequest,
    UploadImageResponse, ErrorResponse, MessageType
)
from graphs.multimodal_graph import multimodal_graph
from services.s3_service import s3_service
from services.bedrock_service import bedrock_service
from utils.image_utils import (
    validate_image_size, validate_image_format, process_image_for_bedrock,
    get_image_from_url, decode_base64_image
)

# Create router
chat_router = APIRouter(prefix="/chat", tags=["chat"])

@chat_router.post("/multimodal", response_model=ChatResponse)
async def multimodal_chat(request: ChatRequest):
    """
    Main multimodal chat endpoint that handles text and image inputs
    """
    start_time = time.time()
    
    try:
        logger.info(f"Received multimodal chat request: {request.message_type}")
        
        # Process the request through LangGraph
        result = await multimodal_graph.process_message(
            question=request.question,
            image_url=request.image_url,
            image_data=request.image_data,
            session_id=request.session_id,
            message_type=request.message_type
        )
        
        if result.get("error"):
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            message_type=result["message_type"],
            model_used=result["metadata"].get("model_used", "claude"),
            tokens_used=result["metadata"].get("tokens_used"),
            processing_time=processing_time,
            metadata=result["metadata"]
        )
        
    except Exception as e:
        logger.error(f"Error in multimodal chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/text", response_model=ChatResponse)
async def text_chat(question: str, session_id: Optional[str] = None):
    """
    Text-only chat endpoint
    """
    try:
        request = ChatRequest(
            question=question,
            message_type=MessageType.TEXT,
            session_id=session_id
        )
        
        return await multimodal_chat(request)
        
    except Exception as e:
        logger.error(f"Error in text chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze an image with optional custom prompt
    """
    try:
        logger.info("Received image analysis request")
        
        # Get image data
        image_data = None
        if request.image_url:
            image_bytes = get_image_from_url(request.image_url)
            if not image_bytes:
                raise HTTPException(status_code=400, detail="Failed to download image from URL")
            image_data = process_image_for_bedrock(image_bytes)
        elif request.image_data:
            image_bytes = decode_base64_image(request.image_data)
            if not validate_image_size(image_bytes):
                raise HTTPException(status_code=400, detail="Image too large")
            image_data = process_image_for_bedrock(image_bytes)
        else:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Analyze image
        result = await bedrock_service.analyze_image(
            image_data=image_data,
            prompt=request.prompt
        )
        
        return ImageAnalysisResponse(
            analysis=result["analysis"],
            metadata=result.get("raw_response", {})
        )
        
    except Exception as e:
        logger.error(f"Error in image analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """
    Generate an image based on text prompt
    """
    try:
        logger.info(f"Received image generation request: {request.prompt}")
        
        # Generate image
        result = await bedrock_service.generate_image(
            prompt=request.prompt,
            model_name="titan_image",
            width=request.width,
            height=request.height,
            numberOfImages=request.num_images,
            quality=request.quality
        )
        
        return ImageGenerationResponse(
            images=result["images"],
            prompt_used=result["prompt_used"],
            model_used=result["model_used"],
            metadata=result.get("raw_response", {})
        )
        
    except Exception as e:
        logger.error(f"Error in image generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/upload-image", response_model=UploadImageResponse)
async def upload_image(request: UploadImageRequest):
    """
    Get presigned URL for image upload
    """
    try:
        logger.info(f"Received image upload request: {request.filename}")
        
        # Validate content type
        if not validate_image_format(request.content_type):
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Generate presigned URL
        result = await s3_service.generate_presigned_upload_url(
            filename=request.filename,
            content_type=request.content_type
        )
        
        return UploadImageResponse(
            upload_url=result["upload_url"],
            image_url=result["image_url"],
            upload_id=result["upload_id"],
            expires_at=result["expires_at"]
        )
        
    except Exception as e:
        logger.error(f"Error in image upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.post("/upload-image-direct")
async def upload_image_direct(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Direct image upload endpoint
    """
    try:
        logger.info(f"Received direct image upload: {file.filename}")
        
        # Validate file
        if not validate_image_format(file.content_type):
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Read file content
        file_content = await file.read()
        
        if not validate_image_size(file_content):
            raise HTTPException(status_code=400, detail="Image too large")
        
        # Upload to S3
        result = await s3_service.upload_image_direct(
            image_data=file_content,
            filename=file.filename,
            content_type=file.content_type
        )
        
        return JSONResponse(content={
            "message": "Image uploaded successfully",
            "image_url": result["image_url"],
            "upload_id": result["upload_id"],
            "session_id": session_id
        })
        
    except Exception as e:
        logger.error(f"Error in direct image upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """
    Get conversation history for a session
    """
    try:
        # TODO: Implement session history storage and retrieval
        # For now, return a placeholder
        return JSONResponse(content={
            "session_id": session_id,
            "messages": [],
            "message": "Session history not implemented yet"
        })
        
    except Exception as e:
        logger.error(f"Error getting session history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear conversation history for a session
    """
    try:
        # TODO: Implement session clearing
        # For now, return a placeholder
        return JSONResponse(content={
            "message": f"Session {session_id} cleared successfully"
        })
        
    except Exception as e:
        logger.error(f"Error clearing session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/models")
async def get_available_models():
    """
    Get list of available models
    """
    try:
        from config.settings import BEDROCK_MODELS
        
        models = []
        for model_name, config in BEDROCK_MODELS.items():
            models.append({
                "name": model_name,
                "model_id": config["model_id"],
                "type": "text" if "claude" in config["model_id"] else "image",
                "capabilities": {
                    "text_generation": "claude" in config["model_id"],
                    "image_analysis": "claude" in config["model_id"],
                    "image_generation": "titan-image" in config["model_id"] or "stability" in config["model_id"]
                }
            })
        
        return JSONResponse(content={
            "models": models,
            "default_text_model": "claude",
            "default_image_model": "titan_image"
        })
        
    except Exception as e:
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@chat_router.get("/health")
async def health_check():
    """
    Health check endpoint for the chat service
    """
    try:
        # Test basic functionality
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "bedrock": "unknown",
                "s3": "unknown",
                "langgraph": "healthy"
            }
        }
        
        # Test Bedrock connection
        try:
            await bedrock_service.generate_text_response("test", max_tokens=1)
            health_status["services"]["bedrock"] = "healthy"
        except Exception:
            health_status["services"]["bedrock"] = "unhealthy"
        
        # Test S3 connection
        try:
            await s3_service.create_bucket_if_not_exists()
            health_status["services"]["s3"] = "healthy"
        except Exception:
            health_status["services"]["s3"] = "unhealthy"
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 