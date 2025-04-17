from abc import ABC,abstractmethod
from typing import Dict,List,Any,Optional

class MemoryInterface(ABC):
    """Abstract base class"""

    @abstractmethod
    def save(self, key : str, data : Dict[str,Any]) -> bool:
        pass
    
    @abstractmethod
    def load(self, key : str) -> Optional[Dict[str,Any]]:
        pass

    @abstractmethod
    def delete(self, key : str) -> bool:
        pass

    @abstractmethod
    def search(self, query : Dict[str,Any]) -> List[Dict[str,Any]]:
        pass