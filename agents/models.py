import datetime
from typing import Any, Dict, List, Optional, Union
import uuid
from pydantic import BaseModel,Field

from langchain_core.messages import HumanMessage,AIMessage,SystemMessage,ToolMessage as LCToolMessage
class Message(BaseModel):
    """Base class """
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class AgentState(BaseModel):
    """current state"""
    messages: List[Union[HumanMessage, AIMessage, SystemMessage, LCToolMessage]] = Field(default_factory=list)
    current_tool_calls: List[Dict] = Field(default_factory=list)
    memory_lookups: Dict[str, Any] = Field(default_factory=dict)

class OrchestratorState(BaseModel):
    """State Managed by Orchestrator"""
    messages: List[Union[HumanMessage, AIMessage, SystemMessage, LCToolMessage]] = Field(default_factory=list)
    current_agent: Optional[str] = None
    agent_outputs : Dict[str,List[Dict]] = Field(default_factory=dict)
    routing_history: List[Dict] = Field(default_factory=list)
    task_status: Dict[str, str] = Field(default_factory=dict)