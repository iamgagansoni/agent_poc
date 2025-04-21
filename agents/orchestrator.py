import uuid
import asyncio
from enum import Enum
from typing import Dict, List, Any, Optional
from typing_extensions import TypedDict
from datetime import datetime
import langsmith
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from config.logger import Logging
from config.settings import MONGODB_URI,MONGODB_LOG_DB, MONGODB_LOG_COLLECTION

# Configure logging
logger_obj = Logging(MONGODB_URI,MONGODB_LOG_DB,MONGODB_LOG_COLLECTION)
logger=logger_obj.setup_logger()


class AgentType(str, Enum):
    OPENAI = "openai"
    GROQ = "groq"

class Memory(TypedDict):
    conversation_id: str
    history: List[Dict[str, Any]]
    short_term: Dict[str, Any]
    long_term: Dict[str, Any]

class AgentState(BaseModel):
    agent_type: AgentType = Field(default=AgentType.OPENAI)
    user_input: str = Field(default="")
    system_message: Optional[str] = Field(default=None)
    response: Optional[Dict[str, Any]] = Field(default=None)
    memory: Memory = Field(default_factory=lambda: {
        "conversation_id": str(uuid.uuid4()),
        "history": [],
        "short_term": {},
        "long_term": {}
    })
    error: Optional[str] = Field(default=None)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    require_human_input: bool = Field(default=False)

class Orchestrator:

    def __init__(self, openai_agent, groq_agent):
        self.openai_agent = openai_agent
        self.groq_agent = groq_agent
        self.graph = self._build_graph().compile()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(AgentState)

        graph.add_node("process_input", self._process_input)
        graph.add_node("supervisor", self._supervisor)
        graph.add_node("process_with_openai", self._process_with_openai)
        graph.add_node("process_with_groq", self._process_with_groq)
        graph.add_node("process_tools", self._process_tools)
        graph.add_node("format_response", self._format_response)

        graph.add_conditional_edges(
            "supervisor",
            self._supervisor_condition,
            {
                AgentType.OPENAI: "process_with_openai",
                AgentType.GROQ: "process_with_groq"
            }
        )

        graph.add_edge("process_input", "supervisor")
        graph.add_edge("process_with_openai", "process_tools")
        graph.add_edge("process_with_groq", "process_tools")
        graph.add_edge("process_tools", "format_response")
        graph.add_edge("format_response", END)

        graph.set_entry_point("process_input")

        return graph

    async def _process_input(self, state: AgentState) -> AgentState:
        current_time = datetime.now().isoformat()

        state.memory["history"].append({
            "role": "user",
            "content": state.user_input,
            "timestamp": current_time
        })

        state.memory["short_term"][current_time] = {
            "role": "user",
            "content": state.user_input
        }

        logger.debug(f"Processing input: {state.user_input}")
        return state

    def _supervisor_condition(self, state: AgentState) -> AgentType:
        return state.agent_type
    
    async def _supervisor(self, state: AgentState) -> AgentState:
        logger.debug(f"Supervisor checking state: {state.agent_type}")
        return state
    
    async def _process_with_openai(self, state: AgentState) -> AgentState:
        try:
            self.openai_agent.set_conversation_id(state.memory["conversation_id"])
            logger.debug(f"Processing with OpenAI: {state.user_input}")
            # Added timeout for agent processing
            response = await asyncio.wait_for(self.openai_agent.process(state.user_input), timeout=30.0)

            if not response:
                state.error = "OpenAI agent returned no response."
                logger.error("OpenAI agent returned no response.")
                return state

            state.response = response
            logger.debug(f"OpenAI response: {response}")

            if "tool_results" in response:
                state.tool_calls = response["tool_results"]
        
        except asyncio.TimeoutError:
            state.error = "OpenAI agent processing timed out."
            logger.error("OpenAI agent processing timed out.")
        except Exception as e:
            state.error = f"Error Processing with OpenAI Agent: {str(e)}"
            logger.error(f"Error Processing with OpenAI: {str(e)}")

        return state
    
    async def _process_with_groq(self, state: AgentState) -> AgentState:
        try:
            self.groq_agent.set_conversation_id(state.memory["conversation_id"])
            logger.debug(f"Processing with Groq: {state.user_input}")
            # Added timeout for agent processing
            response = await asyncio.wait_for(self.groq_agent.process(state.user_input), timeout=30.0)

            if not response:
                state.error = "Groq agent returned no response."
                logger.error("Groq agent returned no response.")
                return state

            state.response = response
            logger.debug(f"Groq response: {response}")

            if "tool_results" in response:
                state.tool_calls = response["tool_results"]
        
        except asyncio.TimeoutError:
            state.error = "Groq agent processing timed out."
            logger.error("Groq agent processing timed out.")
        except Exception as e:
            state.error = f"Error Processing with Groq Agent: {str(e)}"
            logger.error(f"Error Processing with Groq: {str(e)}")

        return state
    
    async def _process_tools(self, state: AgentState) -> AgentState:
        if state.tool_calls:
            current_time = datetime.now().isoformat()

            state.memory["long_term"][current_time] = {
                "role": "system",
                "content": "Tool execution",
                "tool_calls": state.tool_calls
            }
        return state
    
    async def _format_response(self, state: AgentState) -> AgentState:
        # Handle error
        if state.error is not None:
            state.system_message = state.error
            logger.debug(f"Error: {state.error}")
            return state

        # Guard against missing or malformed response
        if not state.response or not isinstance(state.response, dict):
            state.system_message = "No valid response generated by agents."
            logger.debug(f"Invalid response format")
            return state

        # Raw assistant output (expecting content to contain the result)
        raw_content = state.response.get("content", "").strip()

        # Check if the response contains a tool result
        if state.tool_calls:
            # Look for a tool result in the tool_calls
            for call in state.tool_calls:
                if call.get("tool_name") == "calculator":
                    # If the tool is "calculator", extract the result from the tool output
                    result = call.get("output", {}).get("result", "")
                    if result:
                        # Output just the result (e.g., "2" for 1+1)
                        formatted_response = str(result)
                        break
            else:
                formatted_response = raw_content
        else:
            formatted_response = raw_content

        logger.debug(f"Formatted Response: {formatted_response}")

        # Save to memory
        current_time = datetime.now().isoformat()

        state.memory["history"].append({
            "role": "assistant",
            "content": formatted_response,
            "timestamp": current_time
        })

        state.memory["long_term"][current_time] = {
            "role": "assistant",
            "content": formatted_response
        }

        # Set the cleaned system message
        state.system_message = formatted_response

        return state

    async def process(self, user_input: str, agent_type: AgentType = AgentType.OPENAI, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        state = AgentState(agent_type=agent_type, user_input=user_input)

        if conversation_id:
            state.memory["conversation_id"] = conversation_id

        logger.debug(f"Starting process for input: {user_input}")
        result = await self.graph.ainvoke(state)

        error = result.get("error")
        if error:
            logger.error(f"Error occurred: {error}")
            return {
                "status": "error",
                "message": error,
                "conversation_id": result["memory"]["conversation_id"]
            }

        response = result.get("response", {})
        return {
            "status": "success",
            "response": response.get("content", ""),
            "tool_results": result.get("tool_calls", []),
            "conversation_id": result["memory"]["conversation_id"]
        }
