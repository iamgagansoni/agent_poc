from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum

from agents.orchestrator import AgentType

router = APIRouter()

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User message")
    agent_type: AgentType = Field(default=AgentType.OPENAI, description="Agent type to use")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for continuing a conversation")

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    status: str = Field(..., description="Status of the request")
    response: Optional[str] = Field(default=None, description="Agent response")
    tool_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Results from tool calls")
    conversation_id: str = Field(..., description="Conversation ID")
    error: Optional[str] = Field(default=None, description="Error message if any")

def get_orchestrator():
    """Get the orchestrator instance from the main application."""
    from api.main import app
    return app.state.orchestrator

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, orchestrator=Depends(lambda: get_orchestrator())):
    """
    Process a chat message with the specified agent.
    
    Args:
        request: Chat request containing message and agent preferences
        orchestrator: Dependency-injected orchestrator instance
        
    Returns:
        ChatResponse: The processed response
    """
    try:
        result = await orchestrator.process(
            user_input = request.message,
            agent_type = request.agent_type,
            conversation_id = request.conversation_id
        )

        return ChatResponse(
            status=result.get("status", "error"),
            response=result.get("response"),
            tool_results=result.get("tool_results"),
            conversation_id=result.get("conversation_id"),
            error=result.get("message") if result.get("status") == "error" else None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/conversations/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str, 
    orchestrator=Depends(lambda: get_orchestrator()),
    limit: int = Query(10, description="Maximum number of messages to return"),
    agent_type: AgentType = Query(AgentType.OPENAI,description="Agent type to query")
):
    """
    Get conversation history by ID.
    
    Args:
        conversation_id: The ID of the conversation to retrieve
        orchestrator: Dependency-injected orchestrator instance
        limit: Maximum number of messages to return
        agent_type: Which agent's memory to query
    Returns:
        Dict containing conversation history
    """
    try:
        # This is a simplified implementation
        # In a real application, you would query the database directly
        
        # For OpenAI agent, retrieve from its memory
        agent = None
        if agent_type == AgentType.OPENAI:
            agent = orchestrator.openai_agent
        elif agent_type == AgentType.GROQ:
            agent = orchestrator.groq_agent
        else:
            raise HTTPException(status_code=400, detail="Invalid agent type")
            
        agent.set_conversation_id(conversation_id)
        history = agent.retrieve_memory(
            {"conversation_id": conversation_id},
            use_long_term=True
        )
        
        # Sort by timestamp and limit
        history.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        history = history[:limit]
        
        return {
            "conversation_id": conversation_id,
            "messages": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", response_model=List[str])
async def get_available_agents():
    """
    Get a list of available agent types.
    
    Returns:
        List of agent type names
    """
    return [agent_type.value for agent_type in AgentType]