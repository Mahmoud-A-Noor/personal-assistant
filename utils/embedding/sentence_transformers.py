from typing import List, Union, Dict
from enum import Enum
from sentence_transformers import SentenceTransformer

class EmbeddingModel(Enum):
    """Supported embedding models"""
    MINILM = "sentence-transformers/all-MiniLM-L6-v2"
    MPNET = "sentence-transformers/all-mpnet-base-v2"
    BGE_SMALL = "BAAI/bge-small-en-v1.5"

class SentenceTransformerEmbedder:
    """
    Interface for sentence-transformers library with support for multiple embedding techniques.
    """
    
    def __init__(self, model: EmbeddingModel = EmbeddingModel.BGE_SMALL):
        """
        Initialize with specified model.
        
        Args:
            model: Embedding model to use
        """
        self.model_name = model.value
        self.embedder = SentenceTransformer(self.model_name)
        self._dimension = self._get_model_dimension(model)
    
    def _get_model_dimension(self, model: EmbeddingModel) -> int:
        """Get dimension for a given model"""
        dimensions = {
            EmbeddingModel.MINILM: 384,
            EmbeddingModel.MPNET: 768,
            EmbeddingModel.BGE_SMALL: 384
        }
        return dimensions.get(model, 768)  # Default dimension
    
    def embed(self, inputs: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for input text(s).
        """
        if isinstance(inputs, str):
            inputs = [inputs]
        
        embeddings = self.embedder.encode(inputs)
        return embeddings[0].tolist() if len(embeddings) == 1 else [e.tolist() for e in embeddings]
    
    def get_info(self) -> Dict[str, any]:
        """Get information about current model"""
        return {
            "model": self.model_name,
            "dimension": self._dimension,
            "description": "SentenceTransformer model"
        }
