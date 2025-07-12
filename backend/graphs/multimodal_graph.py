from typing import Dict, Any, List, Optional, Literal, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
import uuid
import time
from loguru import logger

from chains.multimodal_chain import get_multimodal_chain, get_image_analysis_chain, get_conversational_chain, get_image_generation_chain
from services.bedrock_service import bedrock_service
from services.s3_service import s3_service
from utils.image_utils import get_image_from_url, process_image_for_bedrock
from schemas.chat import MessageType

class MultimodalState(TypedDict):
    """State for the multimodal chatbot graph"""
    messages: List[BaseMessage]
    question: str
    image_url: Optional[str]
    image_data: Optional[str]
    message_type: MessageType
    session_id: str
    response: str
    metadata: Dict[str, Any]
    processing_steps: List[str]
    error: Optional[str]
    requires_image_analysis: bool
    requires_text_generation: bool
    requires_image_generation: bool

# Define tools for the graph
@tool
def analyze_image_tool(image_data: str, prompt: str = "Analyze this image") -> Dict[str, Any]:
    """Tool to analyze images using Bedrock"""
    try:
        result = get_image_analysis_chain().run({
            "image_data": image_data,
            "analysis_type": "general",
            "custom_prompt": prompt
        })
        return result
    except Exception as e:
        logger.error(f"Error in analyze_image_tool: {str(e)}")
        return {"error": str(e)}

@tool
def generate_text_tool(prompt: str, context: str = "") -> Dict[str, Any]:
    """Tool to generate text responses using Bedrock"""
    try:
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        result = get_conversational_chain().run({
            "message": full_prompt,
            "session_id": str(uuid.uuid4())
        })
        return result
    except Exception as e:
        logger.error(f"Error in generate_text_tool: {str(e)}")
        return {"error": str(e)}

@tool
def generate_image_tool(prompt: str, style: str = "realistic") -> Dict[str, Any]:
    """Tool to generate images using Bedrock"""
    try:
        result = get_image_generation_chain().run({
            "prompt": prompt,
            "generation_type": style,
            "style": "",
            "model_name": "titan_image"
        })
        return result
    except Exception as e:
        logger.error(f"Error in generate_image_tool: {str(e)}")
        return {"error": str(e)}

# Create tool node
tools = [analyze_image_tool, generate_text_tool, generate_image_tool]
tool_node = ToolNode(tools)

class MultimodalChatbotGraph:
    """LangGraph-based multimodal chatbot workflow"""
    
    def __init__(self):
        self.graph = self._create_graph()
        self.app = self.graph.compile()
    
    def _create_graph(self) -> StateGraph:
        """Create the LangGraph workflow"""
        workflow = StateGraph(MultimodalState)
        
        # Add nodes
        workflow.add_node("input_processing", self._process_input)
        workflow.add_node("route_request", self._route_request)
        workflow.add_node("image_analysis", self._analyze_image)
        workflow.add_node("text_generation", self._generate_text)
        workflow.add_node("image_generation", self._generate_image)
        workflow.add_node("response_synthesis", self._synthesize_response)
        workflow.add_node("error_handling", self._handle_error)
        
        # Add edges
        workflow.add_edge(START, "input_processing")
        workflow.add_edge("input_processing", "route_request")
        
        # Conditional routing
        workflow.add_conditional_edges(
            "route_request",
            self._route_decision,
            {
                "image_analysis": "image_analysis",
                "text_generation": "text_generation",
                "image_generation": "image_generation",
                "error": "error_handling"
            }
        )
        
        # Connect analysis nodes to response synthesis
        workflow.add_edge("image_analysis", "response_synthesis")
        workflow.add_edge("text_generation", "response_synthesis")
        workflow.add_edge("image_generation", "response_synthesis")
        
        # End conditions
        workflow.add_edge("response_synthesis", END)
        workflow.add_edge("error_handling", END)
        
        return workflow
    
    def _process_input(self, state: MultimodalState) -> MultimodalState:
        """Process and validate input"""
        logger.info("Processing input")
        
        try:
            state["processing_steps"].append("input_processing")
            
            # Generate session ID if not provided
            if not state.get("session_id"):
                state["session_id"] = str(uuid.uuid4())
            
            # Process image if provided
            if state.get("image_url"):
                image_data = get_image_from_url(state["image_url"])
                if image_data:
                    state["image_data"] = process_image_for_bedrock(image_data)
                    state["message_type"] = MessageType.MULTIMODAL
                else:
                    state["error"] = "Failed to process image from URL"
                    return state
            
            # Determine processing requirements
            state["requires_image_analysis"] = bool(state.get("image_data"))
            state["requires_text_generation"] = True  # Always need text response
            state["requires_image_generation"] = "generate image" in state["question"].lower()
            
            # Add user message to conversation
            state["messages"].append(HumanMessage(content=state["question"]))
            
            return state
            
        except Exception as e:
            logger.error(f"Error in input processing: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _route_request(self, state: MultimodalState) -> MultimodalState:
        """Route request based on content analysis"""
        logger.info("Routing request")
        
        state["processing_steps"].append("routing")
        
        # Check for errors
        if state.get("error"):
            return state
        
        # Analyze question intent
        question_lower = state["question"].lower()
        
        if any(keyword in question_lower for keyword in ["generate", "create", "draw", "make an image"]):
            state["requires_image_generation"] = True
        elif state.get("image_data"):
            state["requires_image_analysis"] = True
        else:
            state["requires_text_generation"] = True
        
        return state
    
    def _route_decision(self, state: MultimodalState) -> Literal["image_analysis", "text_generation", "image_generation", "error"]:
        """Decide which node to execute next"""
        if state.get("error"):
            return "error"
        elif state.get("requires_image_generation"):
            return "image_generation"
        elif state.get("requires_image_analysis"):
            return "image_analysis"
        else:
            return "text_generation"
    
    def _analyze_image(self, state: MultimodalState) -> MultimodalState:
        """Analyze image content"""
        logger.info("Analyzing image")
        
        try:
            state["processing_steps"].append("image_analysis")
            
            if not state.get("image_data"):
                state["error"] = "No image data available for analysis"
                return state
            
            # Analyze image with context
            result = image_analysis_chain.run({
                "image_data": state["image_data"],
                "analysis_type": "general",
                "custom_prompt": f"Analyze this image in the context of this question: {state['question']}"
            })
            
            # Store analysis result
            state["metadata"]["image_analysis"] = result["analysis"]
            state["metadata"]["image_analysis_metadata"] = result["metadata"]
            
            # Generate text response incorporating image analysis
            prompt = f"""
            User Question: {state['question']}
            
            Image Analysis: {result['analysis']}
            
            Please provide a comprehensive answer based on the user's question and the image analysis.
            """
            
            text_result = generate_text_tool.invoke({"prompt": prompt})
            state["response"] = text_result["response"]
            state["metadata"]["text_generation"] = text_result["metadata"]
            
            return state
            
        except Exception as e:
            logger.error(f"Error in image analysis: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _generate_text(self, state: MultimodalState) -> MultimodalState:
        """Generate text response"""
        logger.info("Generating text response")
        
        try:
            state["processing_steps"].append("text_generation")
            
            # Generate response
            result = conversational_chain.run({
                "message": state["question"],
                "session_id": state["session_id"]
            })
            
            state["response"] = result["response"]
            state["metadata"]["text_generation"] = result["metadata"]
            
            return state
            
        except Exception as e:
            logger.error(f"Error in text generation: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _generate_image(self, state: MultimodalState) -> MultimodalState:
        """Generate image based on prompt"""
        logger.info("Generating image")
        
        try:
            state["processing_steps"].append("image_generation")
            
            # Extract image prompt from question
            prompt = state["question"]
            
            # Generate image
            result = image_generation_chain.run({
                "prompt": prompt,
                "generation_type": "realistic",
                "style": "",
                "model_name": "titan_image"
            })
            
            state["metadata"]["image_generation"] = result["metadata"]
            state["metadata"]["generated_images"] = result["images"]
            
            # Create text response about image generation
            state["response"] = f"I've generated an image based on your prompt: '{prompt}'. The image has been created successfully."
            
            return state
            
        except Exception as e:
            logger.error(f"Error in image generation: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _synthesize_response(self, state: MultimodalState) -> MultimodalState:
        """Synthesize final response"""
        logger.info("Synthesizing response")
        
        try:
            state["processing_steps"].append("response_synthesis")
            
            # Add AI message to conversation
            state["messages"].append(AIMessage(content=state["response"]))
            
            # Finalize metadata
            state["metadata"]["session_id"] = state["session_id"]
            state["metadata"]["message_type"] = state["message_type"]
            state["metadata"]["processing_steps"] = state["processing_steps"]
            state["metadata"]["total_processing_time"] = time.time() - state["metadata"].get("start_time", time.time())
            
            return state
            
        except Exception as e:
            logger.error(f"Error in response synthesis: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _handle_error(self, state: MultimodalState) -> MultimodalState:
        """Handle errors gracefully"""
        logger.error(f"Handling error: {state.get('error')}")
        
        state["processing_steps"].append("error_handling")
        state["response"] = f"I apologize, but I encountered an error while processing your request: {state.get('error', 'Unknown error')}"
        
        # Add error response to conversation
        state["messages"].append(AIMessage(content=state["response"]))
        
        return state
    
    async def process_message(
        self,
        question: str,
        image_url: Optional[str] = None,
        image_data: Optional[str] = None,
        session_id: Optional[str] = None,
        message_type: MessageType = MessageType.TEXT
    ) -> Dict[str, Any]:
        """Process a message through the graph"""
        
        # Initialize state
        initial_state = MultimodalState(
            messages=[],
            question=question,
            image_url=image_url,
            image_data=image_data,
            message_type=message_type,
            session_id=session_id or str(uuid.uuid4()),
            response="",
            metadata={"start_time": time.time()},
            processing_steps=[],
            error=None,
            requires_image_analysis=False,
            requires_text_generation=False,
            requires_image_generation=False
        )
        
        # Run the graph
        try:
            final_state = await self.app.ainvoke(initial_state)
            
            return {
                "response": final_state["response"],
                "session_id": final_state["session_id"],
                "message_type": final_state["message_type"],
                "metadata": final_state["metadata"],
                "error": final_state.get("error")
            }
            
        except Exception as e:
            logger.error(f"Error in graph execution: {str(e)}")
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "session_id": session_id or str(uuid.uuid4()),
                "message_type": message_type,
                "metadata": {"error": str(e)},
                "error": str(e)
            }

# Global graph instance
multimodal_graph = MultimodalChatbotGraph() 