from langchain.chains.base import Chain
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import PromptTemplate
from langchain_aws import ChatBedrock
from langchain_core.callbacks.manager import CallbackManagerForChainRun
from typing import Dict, Any, List, Optional
import asyncio
import time
from loguru import logger

from services.bedrock_service import bedrock_service
from config.settings import settings, BEDROCK_MODELS

class MultimodalAnalysisChain(Chain):
    """Chain for multimodal analysis combining text and image processing"""
    
    def __init__(self, **kwargs):
        # Initialize parent chain first
        super().__init__(**kwargs)
        
        # Initialize LLM and prompt template
        self.llm = ChatBedrock(
            model_id=BEDROCK_MODELS["claude"]["model_id"],
            region_name=settings.BEDROCK_REGION,
            model_kwargs=BEDROCK_MODELS["claude"]["model_kwargs"]
        )
        
        self.prompt_template = PromptTemplate(
            input_variables=["question", "image_analysis"],
            template="""
            You are a helpful AI assistant that can analyze images and answer questions.
            
            User Question: {question}
            
            Image Analysis: {image_analysis}
            
            Please provide a comprehensive answer based on the user's question and the image analysis.
            If the image analysis is relevant to the question, incorporate it into your response.
            If the question is about the image, use the image analysis as your primary source.
            
            Answer:
            """
        )
    
    @property
    def input_keys(self) -> List[str]:
        return ["question", "image_data"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["answer", "metadata"]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute the multimodal chain"""
        start_time = time.time()
        
        question = inputs["question"]
        image_data = inputs.get("image_data")
        
        try:
            if image_data:
                # Run image analysis
                analysis_result = asyncio.run(
                    bedrock_service.analyze_image(
                        image_data=image_data,
                        prompt=f"Analyze this image in the context of this question: {question}"
                    )
                )
                
                image_analysis = analysis_result["analysis"]
                
                # Generate comprehensive response
                prompt = self.prompt_template.format(
                    question=question,
                    image_analysis=image_analysis
                )
                
                response = self.llm.invoke(prompt).content
                
                metadata = {
                    "has_image": True,
                    "image_analysis": image_analysis,
                    "processing_time": time.time() - start_time,
                    "tokens_used": analysis_result.get("tokens_used", 0),
                    "model_used": analysis_result.get("model_used")
                }
                
            else:
                # Text-only response
                response = self.llm.invoke(question).content
                
                metadata = {
                    "has_image": False,
                    "processing_time": time.time() - start_time,
                    "model_used": BEDROCK_MODELS["claude"]["model_id"]
                }
            
            return {
                "answer": response,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error in multimodal chain: {str(e)}")
            raise

class ImageAnalysisChain(Chain):
    """Chain specifically for image analysis tasks"""
    
    def __init__(self, **kwargs):
        # Initialize parent chain first
        super().__init__(**kwargs)
        
        # Initialize analysis prompts
        self.analysis_prompts = {
            "general": "Analyze this image and describe what you see in detail.",
            "objects": "Identify and list all objects visible in this image.",
            "scene": "Describe the scene, setting, and context of this image.",
            "text": "Extract and transcribe any text visible in this image.",
            "emotions": "Analyze the emotions and mood conveyed in this image.",
            "technical": "Provide technical details about this image including composition, lighting, and quality.",
            "accessibility": "Describe this image for someone who cannot see it, focusing on important visual elements."
        }
    
    @property
    def input_keys(self) -> List[str]:
        return ["image_data", "analysis_type", "custom_prompt"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["analysis", "metadata"]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute image analysis"""
        start_time = time.time()
        
        image_data = inputs["image_data"]
        analysis_type = inputs.get("analysis_type", "general")
        custom_prompt = inputs.get("custom_prompt")
        
        try:
            # Choose prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self.analysis_prompts.get(analysis_type, self.analysis_prompts["general"])
            
            # Analyze image
            result = asyncio.run(
                bedrock_service.analyze_image(
                    image_data=image_data,
                    prompt=prompt
                )
            )
            
            metadata = {
                "analysis_type": analysis_type,
                "prompt_used": prompt,
                "processing_time": time.time() - start_time,
                "tokens_used": result.get("tokens_used", 0),
                "model_used": result.get("model_used")
            }
            
            return {
                "analysis": result["analysis"],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error in image analysis chain: {str(e)}")
            raise

class ConversationalChain(Chain):
    """Chain for maintaining conversational context"""
    
    def __init__(self, max_history_length: int = 10, **kwargs):
        # Initialize parent chain first
        super().__init__(**kwargs)
        
        # Initialize conversation attributes
        self.conversation_history = []
        self.max_history_length = max_history_length
        self.llm = ChatBedrock(
            model_id=BEDROCK_MODELS["claude"]["model_id"],
            region_name=settings.BEDROCK_REGION,
            model_kwargs=BEDROCK_MODELS["claude"]["model_kwargs"]
        )
    
    @property
    def input_keys(self) -> List[str]:
        return ["message", "session_id"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["response", "metadata"]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute conversational chain"""
        start_time = time.time()
        
        message = inputs["message"]
        session_id = inputs.get("session_id")
        
        try:
            # Add user message to history
            self.conversation_history.append(HumanMessage(content=message))
            
            # Trim history if too long
            if len(self.conversation_history) > self.max_history_length:
                self.conversation_history = self.conversation_history[-self.max_history_length:]
            
            # Create context from history
            context = "\n".join([
                f"{'User' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
                for msg in self.conversation_history[-5:]  # Last 5 messages
            ])
            
            # Generate response
            response = self.llm.invoke(f"Conversation context:\n{context}\n\nPlease respond to the latest message.").content
            
            # Add assistant response to history
            self.conversation_history.append(AIMessage(content=response))
            
            metadata = {
                "session_id": session_id,
                "history_length": len(self.conversation_history),
                "processing_time": time.time() - start_time,
                "model_used": BEDROCK_MODELS["claude"]["model_id"]
            }
            
            return {
                "response": response,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error in conversational chain: {str(e)}")
            raise
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    def get_history(self) -> List[BaseMessage]:
        """Get conversation history"""
        return self.conversation_history.copy()

class ImageGenerationChain(Chain):
    """Chain for image generation tasks"""
    
    def __init__(self, **kwargs):
        # Initialize parent chain first
        super().__init__(**kwargs)
        
        # Initialize generation prompts
        self.generation_prompts = {
            "enhance": "Create a detailed, high-quality version of: {prompt}",
            "artistic": "Create an artistic interpretation of: {prompt}",
            "realistic": "Create a photorealistic image of: {prompt}",
            "abstract": "Create an abstract representation of: {prompt}",
            "style_transfer": "Create an image in the style of {style}: {prompt}"
        }
    
    @property
    def input_keys(self) -> List[str]:
        return ["prompt", "generation_type", "style", "model_name"]
    
    @property
    def output_keys(self) -> List[str]:
        return ["images", "metadata"]
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Execute image generation"""
        start_time = time.time()
        
        prompt = inputs["prompt"]
        generation_type = inputs.get("generation_type", "realistic")
        style = inputs.get("style", "")
        model_name = inputs.get("model_name", "titan_image")
        
        try:
            # Enhance prompt based on generation type
            if generation_type in self.generation_prompts:
                if generation_type == "style_transfer" and style:
                    enhanced_prompt = self.generation_prompts[generation_type].format(
                        prompt=prompt, style=style
                    )
                else:
                    enhanced_prompt = self.generation_prompts[generation_type].format(
                        prompt=prompt
                    )
            else:
                enhanced_prompt = prompt
            
            # Generate image
            result = asyncio.run(
                bedrock_service.generate_image(
                    prompt=enhanced_prompt,
                    model_name=model_name
                )
            )
            
            metadata = {
                "generation_type": generation_type,
                "original_prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "style": style,
                "processing_time": time.time() - start_time,
                "model_used": result.get("model_used")
            }
            
            return {
                "images": result["images"],
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error in image generation chain: {str(e)}")
            raise

# Factory functions for creating chain instances
def create_multimodal_chain():
    """Create a new MultimodalAnalysisChain instance"""
    return MultimodalAnalysisChain()

def create_image_analysis_chain():
    """Create a new ImageAnalysisChain instance"""
    return ImageAnalysisChain()

def create_conversational_chain():
    """Create a new ConversationalChain instance"""
    return ConversationalChain()

def create_image_generation_chain():
    """Create a new ImageGenerationChain instance"""
    return ImageGenerationChain()

# Global chain instances - create them lazily
multimodal_chain = None
image_analysis_chain = None
conversational_chain = None
image_generation_chain = None

def get_multimodal_chain():
    global multimodal_chain
    if multimodal_chain is None:
        multimodal_chain = create_multimodal_chain()
    return multimodal_chain

def get_image_analysis_chain():
    global image_analysis_chain
    if image_analysis_chain is None:
        image_analysis_chain = create_image_analysis_chain()
    return image_analysis_chain

def get_conversational_chain():
    global conversational_chain
    if conversational_chain is None:
        conversational_chain = create_conversational_chain()
    return conversational_chain

def get_image_generation_chain():
    global image_generation_chain
    if image_generation_chain is None:
        image_generation_chain = create_image_generation_chain()
    return image_generation_chain 