import boto3
import json
import base64
from typing import Dict, Any, Optional, List
from loguru import logger
from botocore.exceptions import ClientError

from config.settings import settings, BEDROCK_MODELS
from utils.image_utils import encode_image_to_base64, decode_base64_image

class BedrockService:
    """Service for interacting with AWS Bedrock models"""
    
    def __init__(self):
        self.bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=settings.BEDROCK_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_session_token=settings.AWS_SESSION_TOKEN,
        )
        
    async def generate_text_response(
        self,
        prompt: str,
        model_name: str = "claude",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text response using Bedrock LLM"""
        try:
            model_config = BEDROCK_MODELS.get(model_name, BEDROCK_MODELS["claude"])
            model_id = model_config["model_id"]
            model_kwargs = {**model_config["model_kwargs"], **kwargs}
            
            # Prepare request body based on model type
            if "claude" in model_id:
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [{"role": "user", "content": prompt}],
                    **model_kwargs
                }
            else:
                body = {
                    "inputText": prompt,
                    **model_kwargs
                }
            
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            logger.info(f"Generated text response using {model_id}")
            
            # Extract text based on model type
            if "claude" in model_id:
                text = response_body.get('content', [{}])[0].get('text', '')
                tokens_used = response_body.get('usage', {}).get('output_tokens', 0)
            else:
                text = response_body.get('outputText', '')
                tokens_used = response_body.get('inputTextTokenCount', 0) + response_body.get('outputTextTokenCount', 0)
            
            return {
                "text": text,
                "model_used": model_id,
                "tokens_used": tokens_used,
                "raw_response": response_body
            }
            
        except ClientError as e:
            logger.error(f"Error generating text with Bedrock: {str(e)}")
            raise Exception(f"Bedrock text generation failed: {str(e)}")
    
    async def analyze_image(
        self,
        image_data: str,
        prompt: str = "Analyze this image",
        model_name: str = "claude"
    ) -> Dict[str, Any]:
        """Analyze image using Bedrock multimodal model"""
        try:
            model_config = BEDROCK_MODELS.get(model_name, BEDROCK_MODELS["claude"])
            model_id = model_config["model_id"]
            model_kwargs = model_config["model_kwargs"]
            
            # Prepare multimodal request for Claude
            if "claude" in model_id:
                # Ensure image_data is base64 encoded
                if not image_data.startswith('data:'):
                    image_data = f"data:image/jpeg;base64,{image_data}"
                
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_data.split(',')[1] if ',' in image_data else image_data
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ],
                    **model_kwargs
                }
            else:
                raise ValueError(f"Image analysis not supported for model: {model_id}")
            
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            logger.info(f"Analyzed image using {model_id}")
            
            # Extract analysis text
            analysis_text = response_body.get('content', [{}])[0].get('text', '')
            tokens_used = response_body.get('usage', {}).get('output_tokens', 0)
            
            return {
                "analysis": analysis_text,
                "model_used": model_id,
                "tokens_used": tokens_used,
                "raw_response": response_body
            }
            
        except ClientError as e:
            logger.error(f"Error analyzing image with Bedrock: {str(e)}")
            raise Exception(f"Bedrock image analysis failed: {str(e)}")
    
    async def generate_image(
        self,
        prompt: str,
        model_name: str = "titan_image",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate image using Bedrock image generation model"""
        try:
            model_config = BEDROCK_MODELS.get(model_name, BEDROCK_MODELS["titan_image"])
            model_id = model_config["model_id"]
            model_kwargs = {**model_config["model_kwargs"], **kwargs}
            
            # Prepare request body based on model type
            if "titan-image" in model_id:
                body = {
                    "taskType": "TEXT_IMAGE",
                    "textToImageParams": {
                        "text": prompt,
                        **model_kwargs
                    },
                    "imageGenerationConfig": {
                        "numberOfImages": model_kwargs.get("numberOfImages", 1),
                        "quality": model_kwargs.get("quality", "premium"),
                        "height": model_kwargs.get("height", 1024),
                        "width": model_kwargs.get("width", 1024),
                    }
                }
            elif "stability" in model_id:
                body = {
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": model_kwargs.get("cfg_scale", 7),
                    "steps": model_kwargs.get("steps", 30),
                    "height": model_kwargs.get("height", 1024),
                    "width": model_kwargs.get("width", 1024),
                }
            else:
                raise ValueError(f"Image generation not supported for model: {model_id}")
            
            response = self.bedrock_client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            logger.info(f"Generated image using {model_id}")
            
            # Extract images based on model type
            if "titan-image" in model_id:
                images = [img.get("base64") for img in response_body.get("images", [])]
            elif "stability" in model_id:
                images = [artifact.get("base64") for artifact in response_body.get("artifacts", [])]
            else:
                images = []
            
            return {
                "images": images,
                "model_used": model_id,
                "prompt_used": prompt,
                "raw_response": response_body
            }
            
        except ClientError as e:
            logger.error(f"Error generating image with Bedrock: {str(e)}")
            raise Exception(f"Bedrock image generation failed: {str(e)}")
    
    async def multimodal_chat(
        self,
        text_prompt: str,
        image_data: Optional[str] = None,
        model_name: str = "claude",
        **kwargs
    ) -> Dict[str, Any]:
        """Combined text and image processing"""
        try:
            if image_data:
                # Multimodal analysis
                combined_prompt = f"{text_prompt}\n\nPlease analyze the provided image and respond to the question."
                return await self.analyze_image(
                    image_data=image_data,
                    prompt=combined_prompt,
                    model_name=model_name
                )
            else:
                # Text-only response
                return await self.generate_text_response(
                    prompt=text_prompt,
                    model_name=model_name,
                    **kwargs
                )
                
        except Exception as e:
            logger.error(f"Error in multimodal chat: {str(e)}")
            raise

# Global service instance
bedrock_service = BedrockService() 