from abc import ABC, abstractmethod
from typing import Dict, Any, Union, List, Optional
from pydantic_ai import Tool
import importlib
import pkgutil
from pathlib import Path

class BaseExtractor(ABC):
    """Base class for all knowledge extractors"""
    
    def __init__(self):
        pass
    
    @abstractmethod
    def extract(self, source: Union[str, bytes], file_type: Optional[str] = None) -> Dict[str, Any]:
        """Extract knowledge from the given source
        
        Args:
            source: The source to extract from (file path or bytes)
            file_type: Optional file type identifier (e.g., 'pdf', 'audio', 'image')
        """
        pass

    @classmethod
    def get_extractor_tools(cls) -> List[Tool]:
        """
        Get all available extractors as Pydantic AI tools
        
        Returns:
            List of Pydantic AI Tool instances for each available extractor
        """
        extractors = []
        # Get the base directory of extractors
        base_dir = Path(__file__).parent.parent
        
        # Discover all submodules in the knowledge_extractors package
        for _, name, _ in pkgutil.iter_modules([str(base_dir)]):
            if name != 'base':  # Skip base module
                try:
                    # Import the module
                    module = importlib.import_module(f'knowledge_extractors.{name}.extractor')
                    # Get the extractor class (assuming it's called {name.capitalize()}Extractor)
                    extractor_class = getattr(module, f'{name.capitalize()}Extractor')
                    # Create a tool instance
                    tool = Tool(
                        name=extractor_class.__name__,
                        description=f"Extract knowledge from {name} content",
                        function=extractor_class().extract
                    )
                    extractors.append(tool)
                except (ImportError, AttributeError) as e:
                    print(f"Warning: Could not load extractor {name}: {str(e)}")
                    continue
        
        return extractors

    @classmethod
    def get_extractor_by_type(cls, content_type: str) -> Optional[Tool]:
        """
        Get a specific extractor tool by content type
        
        Args:
            content_type: Type of content (e.g., 'document', 'code', 'image')
        
        Returns:
            Pydantic AI Tool instance for the specified content type, or None if not found
        """
        all_tools = cls.get_extractor_tools()
        for tool in all_tools:
            if tool.name.lower().startswith(content_type.lower()):
                return tool
        return None
    
