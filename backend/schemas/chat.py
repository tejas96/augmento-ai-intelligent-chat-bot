from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    MULTIMODAL = "multimodal"

class ChatRequest(BaseModel):
    """Request schema for chat endpoints"""
    question: str = Field(..., description="The user's question or prompt")
    image_url: Optional[str] = Field(None, description="URL of the image to analyze")
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    message_type: MessageType = Field(MessageType.TEXT, description="Type of message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation tracking")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Model temperature")
    max_tokens: Optional[int] = Field(4000, ge=1, le=8000, description="Maximum tokens in response")
    
    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://') or v.startswith('s3://')):
            raise ValueError('Invalid image URL format')
        return v
    
    @field_validator('message_type')
    @classmethod
    def validate_message_type(cls, v, info):
        values = info.data if hasattr(info, 'data') else {}
        if v == MessageType.MULTIMODAL and not (values.get('image_url') or values.get('image_data')):
            raise ValueError('Multimodal message requires either image_url or image_data')
        return v

class ChatResponse(BaseModel):
    """Response schema for chat endpoints"""
    model_config = {"protected_namespaces": ()}
    
    response: str = Field(..., description="The AI's response")
    session_id: str = Field(..., description="Session ID for conversation tracking")
    message_type: MessageType = Field(..., description="Type of message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    model_used: str = Field(..., description="Model used for generation")
    tokens_used: Optional[int] = Field(None, description="Number of tokens used")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ImageAnalysisRequest(BaseModel):
    """Request schema for image analysis"""
    image_url: Optional[str] = Field(None, description="URL of the image to analyze")
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    prompt: str = Field("Analyze this image", description="Analysis prompt")
    
    @field_validator('image_url')
    @classmethod
    def validate_image_url(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://') or v.startswith('s3://')):
            raise ValueError('Invalid image URL format')
        return v

class ImageAnalysisResponse(BaseModel):
    """Response schema for image analysis"""
    analysis: str = Field(..., description="Image analysis result")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Analysis confidence")
    detected_objects: Optional[List[str]] = Field(None, description="Detected objects in image")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ImageGenerationRequest(BaseModel):
    """Request schema for image generation"""
    prompt: str = Field(..., description="Text prompt for image generation")
    negative_prompt: Optional[str] = Field(None, description="Negative prompt")
    width: Optional[int] = Field(1024, ge=256, le=2048, description="Image width")
    height: Optional[int] = Field(1024, ge=256, le=2048, description="Image height")
    num_images: Optional[int] = Field(1, ge=1, le=4, description="Number of images to generate")
    quality: Optional[str] = Field("premium", description="Image quality")

class ImageGenerationResponse(BaseModel):
    """Response schema for image generation"""
    model_config = {"protected_namespaces": ()}
    
    images: List[str] = Field(..., description="Generated image URLs or base64 data")
    prompt_used: str = Field(..., description="Prompt used for generation")
    model_used: str = Field(..., description="Model used for generation")
    generation_time: Optional[float] = Field(None, description="Generation time in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class UploadImageRequest(BaseModel):
    """Request schema for image upload"""
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the image")
    
class UploadImageResponse(BaseModel):
    """Response schema for image upload"""
    upload_url: str = Field(..., description="Presigned URL for upload")
    image_url: str = Field(..., description="URL to access uploaded image")
    expires_at: datetime = Field(..., description="URL expiration time")
    upload_id: str = Field(..., description="Unique upload ID")

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp") 