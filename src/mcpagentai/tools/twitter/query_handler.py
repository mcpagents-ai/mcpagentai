from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class QueryHandler(ABC):
    """Base interface for all query handlers that can be plugged into the Twitter agent"""
    
    @property
    @abstractmethod
    def query_type(self) -> str:
        """Return the type of queries this handler can process (e.g., 'weather', 'stock')"""
        pass
    
    @property
    @abstractmethod
    def available_params(self) -> Dict[str, str]:
        """Return a dictionary of available parameters and their descriptions"""
        pass
    
    @abstractmethod
    def handle_query(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Handle a query with the given parameters
        Returns a formatted string response or None if query cannot be handled
        """
        pass
    
    @property
    @abstractmethod
    def examples(self) -> Dict[str, str]:
        """Return example queries and their expected parameter outputs"""
        pass 