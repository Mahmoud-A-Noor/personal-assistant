import os
from typing import Dict, List
from datetime import datetime as dt
import tika
tika.initVM()
from tika.parser import from_file

class DocumentExtractor:
    def __init__(self):
        """Initialize the DocumentExtractor with supported file types and metadata extraction capabilities."""
        self.supported_extensions = {
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.odt', '.ods', '.odp', '.rtf', '.pdf', '.msg', '.eml', '.txt'
        }
        
    def extract(self, file_path: str) -> Dict:
        """
        Extract content and metadata from any file type using Tika.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing extracted content and metadata
            
        Raises:
            ValueError: If file type is not supported
            Exception: If there's an error extracting the file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")
            
        try:
            # Use Tika to extract content
            raw = from_file(file_path)
            content = raw['content'].strip() if raw['content'] else ''
            
            # Get metadata
            metadata = self._get_file_metadata(file_path)
            
            return {
                'content': content,
                'metadata': metadata
            }
        except Exception as e:
            raise Exception(f"Error extracting file {file_path}: {str(e)}")
            
    def _get_file_metadata(self, file_path: str) -> Dict:
        """Get metadata about the file."""
        stats = os.stat(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        
        return {
            'file_size': stats.st_size,
            'file_name': os.path.basename(file_path),
            'created_time': dt.fromtimestamp(stats.st_ctime).isoformat(),
            'modified_time': dt.fromtimestamp(stats.st_mtime).isoformat(),
            'content_type': self._get_content_type(ext)
        }
        
    def _get_content_type(self, ext: str) -> str:
        """Get the content type based on file extension."""
        content_types = {
            '.doc': 'document',
            '.docx': 'document',
            '.xls': 'spreadsheet',
            '.xlsx': 'spreadsheet',
            '.ppt': 'presentation',
            '.pptx': 'presentation',
            '.odt': 'document',
            '.ods': 'spreadsheet',
            '.odp': 'presentation',
            '.rtf': 'document',
            '.pdf': 'document',
            '.msg': 'email',
            '.eml': 'email',
            '.txt': 'text'
        }
        return content_types.get(ext, 'unknown')
        
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions."""
        return sorted(list(self.supported_extensions))