from abc import ABC, abstractmethod
from typing import Dict, Any, List
from memory.memory_interface import MemoryInterface

class BaseAgent(ABC):

    def __init__(self,
                 short_term_memory: MemoryInterface,
                 long_term_memory: MemoryInterface,
                 tools: List[Any] = None):
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory
        self.tools = tools or []
        self.conversation_id = None

    def set_conversation_id(self, conversation_id: str):
        self.conversation_id = conversation_id

    def save_to_memory(self, data: Dict[str, Any],long_term: bool = False) -> bool:
        if not self.conversation_id:
            raise ValueError("Conversation ID not set")
        
        key = f"{self.conversation_id}:{data.get('timestamp', 'unknown')}"
        short_term_saved = self.short_term_memory.save(key,data)

        long_term_saved = True
        if long_term:
            long_term_saved = self.long_term_memory.save(key,data)
        
        return short_term_saved and long_term_saved

    def retrieve_memory(self, query: Dict[str,Any], use_long_term: bool = False) -> List[Dict[str,Any]]:
        if not self.conversation_id:
            raise ValueError("Conversation ID not set")
        short_term_results = self.short_term_memory.search(query)

        if use_long_term:
            long_term_results = self.long_term_memory.search(query)

            seen_keys = set()
            combined_results = []

            for result in short_term_results + long_term_results:
                result_tuple = tuple(sorted(result.items()))

                if result_tuple not in seen_keys:
                    seen_keys.add(result_tuple)
                    combined_results.append(result)
            
            return combined_results
        return short_term_results
    
    @abstractmethod
    async def process(self, user_input: str) -> Dict[str, Any]:
        pass


    def _available_tools(self) -> List[Dict[str, Any]]:
        return [ 
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools
        ]
    
    def _get_tool_by_name(self, name: str) -> Any:
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    