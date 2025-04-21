from abc import ABC, abstractmethod
from typing import Any, Dict, List

class ToolInterface(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[Dict[str,Any]]:
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass
    