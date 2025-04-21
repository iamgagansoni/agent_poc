import time
import json
import uuid
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage,AIMessage,SystemMessage
from agents.base_agent import BaseAgent
from memory.memory_interface import MemoryInterface
from config.settings import GROQ_API_KEY, MONGODB_URI,MONGODB_LOG_DB, MONGODB_LOG_COLLECTION
from config.logger import Logging


# Configure logging
logger_obj = Logging(MONGODB_URI,MONGODB_LOG_DB,MONGODB_LOG_COLLECTION)
logger=logger_obj.setup_logger()

class GroqAgent(BaseAgent):
    def __init__(self, short_term_memory, long_term_memory, tools = None, model: str = "llama3-70b-8192"):
        super().__init__(short_term_memory, long_term_memory, tools)
        self.client = ChatGroq(
            api_key=GROQ_API_KEY,
            model=model
        )

    async def process(self, user_input):
        logger.info("Starting processing with GROQ Agent")
        try:
            if not self.conversation_id:
                self.set_conversation_id(str(uuid.uuid4()))
                logger.info(f"Created new conversation ID: {self.conversation_id}")
            
            logger.info(f"Retrieving memory for conversation: {self.conversation_id}")
            history = self.retrieve_memory({"conversation_id": self.conversation_id})
            history.sort(key=lambda x: x.get("timestamp", 0))
            
            logger.debug(f"Memory history contains {len(history)} entries")
            messages = []

            for entry in history:
                role = entry.get("role", "user")
                content = entry.get("content", "")
                
                logger.debug(f"Adding message with role: {role}, content preview: {content[:50]}...")
                
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                elif role == "system":
                    messages.append(SystemMessage(content=content))

            logger.info(f"Adding user input to messages. Preview: {user_input[:50]}...")
            messages.append(HumanMessage(content=user_input))
            timestamp = time.time()

            logger.info("Saving user message to memory")
            self.save_to_memory({
                "conversation_id": self.conversation_id,
                "role": "user",
                "content": user_input,
                "timestamp": timestamp
            })

            tools_for_langchain = []
            tool_map = {}

            if self.tools:
                logger.info(f"Preparing {len(self.tools)} tools for use")
                try:
                    for tool in self.tools:
                        tool_name = tool.name
                        tool_description = tool.description
                        logger.debug(f"Adding tool: {tool_name}")
                        
                        tool_map[tool_name] = tool
                        
                        tool_spec = {
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "description": tool_description,
                                "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') else {"type": "object", "properties": {}}
                            }
                        }
                        tools_for_langchain.append(tool_spec)
                    
                    logger.debug(f"Tools map: {list(tool_map.keys())}")
                    logger.debug(f"First tool spec: {json.dumps(tools_for_langchain[0], indent=2)}")
                except Exception as e:
                    logger.error(f"Error preparing tools: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
            else:
                logger.info("No tools available for this agent")

            if tools_for_langchain:
                logger.info("Invoking OpenAI with tools")
                try:
                    logger.debug(f"Sending {len(messages)} messages to OpenAI with {len(tools_for_langchain)} tools")
                    
                    response = self.client.invoke(
                        messages,
                        tools=tools_for_langchain
                    )
                    logger.debug(f"Response received. {response}")
                    logger.debug(f"Response Type: {type(response)}")
                    
                    content = response.content or ""
                    tool_calls = getattr(response, "tool_calls", None)
                    
                    if tool_calls:
                        logger.info(f"Found {len(tool_calls)} tool calls")
                        tool_results = []
                        
                        for i, tool_call in enumerate(tool_calls):
                            logger.info(f"Processing tool call {i+1}")
                            
                            if isinstance(tool_call, dict):
                                tool_name = tool_call.get("name")
                                tool_args = tool_call.get("args", {})
                            else:
                                tool_name = getattr(tool_call, "name", None)
                                tool_args = getattr(tool_call, "args", {})
                                if isinstance(tool_args, str):
                                    try:
                                        tool_args = json.loads(tool_args)
                                    except:
                                        logger.warning(f"Could not parse tool args JSON: {tool_args}")
                                        tool_args = {}
                            
                            logger.info(f"Tool name: {tool_name}")
                            logger.debug(f"Tool arguments: {tool_args}")
                            
                            if not tool_name:
                                logger.warning("Tool name is missing, skipping this tool call")
                                continue
                                
                            tool = tool_map.get(tool_name)

                            if tool:
                                try:
                                    logger.info(f"Executing tool: {tool_name}")
                                    
                                    if isinstance(tool_args, str):
                                        tool_args = json.loads(tool_args)

                                    try:
                                        result = tool.run(tool_args)
                                    except Exception as e:
                                        logger.error(f"Error executing tool: {e}")
                                    logger.info(f"Tool execution successful: {result}")
                                    
                                    tool_results.append({
                                        "tool_name": tool_name,
                                        "input": tool_args,
                                        "output": result
                                    })
                                except Exception as e:
                                    logger.error(f"Error executing tool: {str(e)}")
                                    import traceback
                                    logger.error(traceback.format_exc())
                                    
                                    tool_results.append({
                                        "tool_name": tool_name,
                                        "input": tool_args,
                                        "error": str(e)
                                    })
                            else:
                                logger.warning(f"Tool '{tool_name}' not found in tool map")
                        
                        logger.info("Saving assistant response with tool results to memory")
                        self.save_to_memory({
                            "conversation_id": self.conversation_id,
                            "role": "assistant",
                            "content": content,
                            "tool_results": tool_results,
                            "timestamp": time.time()
                        }, long_term=True)

                        return {
                            "content": content,
                            "tool_results": tool_results
                        }
                    else:
                        logger.info("No tool calls in response")
                        
                        logger.info("Saving assistant response to memory")
                        self.save_to_memory({
                            "conversation_id": self.conversation_id,
                            "role": "assistant",
                            "content": content,
                            "timestamp": time.time()
                        }, long_term=True)
                    
                        return {"content": content}
                        
                except Exception as e:
                    logger.error(f"Error during tool processing: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    raise
            
            logger.info("Invoking OpenAI without tools or no tool calls were made")
            response = self.client.invoke(messages)
            content = response.content
            logger.info(f"Response received. Content preview: {content[:50]}...")

            logger.info("Saving assistant response to memory")
            self.save_to_memory({
                "conversation_id": self.conversation_id,
                "role": "assistant",
                "content": content,
                "timestamp": time.time()
            }, long_term=True)
        
            return {"content": content}
            
        except Exception as e:
            logger.error(f"Error in process method: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            error_message = f"Error processing with OpenAI: {str(e)}"

            self.save_to_memory({
                "conversation_id": self.conversation_id,
                "role": "system",
                "content": error_message,
                "timestamp": time.time()
            })

            return {"error": error_message}