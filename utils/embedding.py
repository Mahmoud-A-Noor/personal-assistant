from typing import List, Union, Dict, Tuple, Any
from fastembed import (
    TextEmbedding,
    SparseTextEmbedding,
    LateInteractionTextEmbedding,
    ImageEmbedding,
    LateInteractionMultimodalEmbedding,
    TextCrossEncoder
)
from enum import Enum
import numpy as np

class EmbeddingModel(Enum):
    """Supported embedding models"""
    MINILM = "sentence-transformers/all-MiniLM-L6-v2"
    MPNET = "sentence-transformers/all-mpnet-base-v2"
    BGE_SMALL = "BAAI/bge-small-en-v1.5"

class EmbeddingTechnique(Enum):
    """Supported embedding techniques"""
    DENSE = "dense"
    SPARSE = "sparse"
    LATE_INTERACTION = "late_interaction"
    IMAGE = "image"
    MULTIMODAL = "multimodal"
    CROSS_ENCODER = "cross_encoder"

class QdrantFastEmbedder:
    """
    Comprehensive interface for FastEmbed with support for multiple embedding techniques.
    """
    
    def __init__(self, 
                model: EmbeddingModel = EmbeddingModel.BGE_SMALL,
                technique: EmbeddingTechnique = EmbeddingTechnique.DENSE):
        """
        Initialize with specified model and technique.
        
        Args:
            model: Embedding model to use
            technique: Embedding technique to apply
        """
        self.technique = technique
        self.model_name = model.value
        
        # Initialize appropriate embedding model based on technique
        if technique == EmbeddingTechnique.DENSE:
            self.embedder = TextEmbedding(self.model_name)
        elif technique == EmbeddingTechnique.SPARSE:
            self.embedder = SparseTextEmbedding(self.model_name)
        elif technique == EmbeddingTechnique.LATE_INTERACTION:
            self.embedder = LateInteractionTextEmbedding(self.model_name)
        elif technique == EmbeddingTechnique.IMAGE:
            self.embedder = ImageEmbedding(self.model_name)
        elif technique == EmbeddingTechnique.MULTIMODAL:
            self.embedder = LateInteractionMultimodalEmbedding(self.model_name)
        elif technique == EmbeddingTechnique.CROSS_ENCODER:
            self.embedder = TextCrossEncoder(self.model_name)
        else:
            raise ValueError(f"Unsupported technique: {technique}")
        
        self._dimension = self._get_model_dimension(model, technique)
    
    def _get_model_dimension(self, model: EmbeddingModel, technique: EmbeddingTechnique) -> int:
        """Get dimension for a given model and technique"""
        # Base dimensions for each technique
        dimensions = {
            EmbeddingTechnique.DENSE: {
                EmbeddingModel.MINILM: 384,
                EmbeddingModel.MPNET: 768,
                EmbeddingModel.BGE_SMALL: 384
            },
            EmbeddingTechnique.SPARSE: {
                EmbeddingModel.MINILM: 30000,  # Typical sparse dimension
                EmbeddingModel.MPNET: 30000,
                EmbeddingModel.BGE_SMALL: 30000
            },
            # Add dimensions for other techniques
        }
        return dimensions.get(technique, {}).get(model, 768)  # Default dimension
    
    def embed(self, inputs: Union[str, List[str], Any]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings based on the configured technique.
        Supports text for most techniques, and images for image/multimodal techniques.
        """
        if isinstance(inputs, (str, list)) and not isinstance(inputs, list):
            inputs = [inputs]
        
        embeddings = list(self.embedder.embed(inputs))
        return embeddings[0].tolist() if len(embeddings) == 1 else [e.tolist() for e in embeddings]
    
    def rerank(self, query: str, documents: List[str], top_k: int = None) -> List[Tuple[int, float]]:
        """
        Rerank documents based on relevance to query (using cross-encoder)
        Returns list of (index, score) tuples sorted by relevance
        """
        if not isinstance(self.embedder, TextCrossEncoder):
            raise ValueError("Reranking requires cross-encoder technique")
            
        scores = self.embedder.predict([(query, doc) for doc in documents])
        ranked = sorted(zip(range(len(documents)), scores), key=lambda x: x[1], reverse=True)
        return ranked[:top_k] if top_k else ranked
    
    def get_technique_info(self) -> Dict[str, Any]:
        """Get information about current technique"""
        return {
            "technique": self.technique.value,
            "model": self.model_name,
            "dimension": self._dimension,
            "description": self._get_technique_description()
        }
    
    def _get_technique_description(self) -> str:
        """Get description of current technique"""
        descriptions = {
            EmbeddingTechnique.DENSE: "Standard dense vector embeddings",
            EmbeddingTechnique.SPARSE: "Sparse embeddings for efficient retrieval",
            EmbeddingTechnique.LATE_INTERACTION: "Late interaction models like ColBERT",
            EmbeddingTechnique.IMAGE: "Image embeddings",
            EmbeddingTechnique.MULTIMODAL: "Multimodal (text+image) embeddings",
            EmbeddingTechnique.CROSS_ENCODER: "Cross-encoder for reranking"
        }
        return descriptions.get(self.technique, "Unknown technique")