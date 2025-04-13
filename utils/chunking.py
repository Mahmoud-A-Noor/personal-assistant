from typing import List, Dict, Optional, Callable
from enum import Enum
import re
import tiktoken

class ChunkingStrategy(Enum):
    """Supported chunking techniques optimized for RAG"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC_PARAGRAPHS = "semantic_paragraphs"
    RECURSIVE_CHARACTER = "recursive_character"
    SENTENCE_AWARE = "sentence_aware"

class SemanticChunker:
    """
    Advanced text chunking optimized for RAG pipelines with multiple strategies.
    
    Features:
    - Multiple chunking techniques optimized for semantic retrieval
    - Token-aware splitting
    - Context preservation with overlaps
    - Strategy-specific optimizations
    """
    
    def __init__(self, 
                strategy: ChunkingStrategy = ChunkingStrategy.SEMANTIC_PARAGRAPHS,
                chunk_size: int = 1000,
                overlap: int = 100,
                model_name: str = "gpt-4"):
        """
        Initialize chunker with specified strategy.
        
        Args:
            strategy: Chunking technique to use
            chunk_size: Target chunk size in tokens
            overlap: Overlap between chunks in tokens
            model_name: Model name for token counting
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.tokenizer = tiktoken.encoding_for_model(model_name)
        
        # Strategy-specific configurations
        self.separators = {
            ChunkingStrategy.FIXED_SIZE: ["\n\n", "\n", " "],
            ChunkingStrategy.SEMANTIC_PARAGRAPHS: ["\n\n", "\n", ". ", "? ", "! ", " "],
            ChunkingStrategy.RECURSIVE_CHARACTER: ["\n\n", "\n", ". ", " ", ""],
            ChunkingStrategy.SENTENCE_AWARE: [". ", "? ", "! ", "\n", " "]
        }
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks using configured strategy.
        Returns list of chunks preserving semantic boundaries.
        """
        if self.strategy == ChunkingStrategy.FIXED_SIZE:
            return self._fixed_size_chunking(text)
        elif self.strategy == ChunkingStrategy.SEMANTIC_PARAGRAPHS:
            return self._semantic_paragraph_chunking(text)
        elif self.strategy == ChunkingStrategy.RECURSIVE_CHARACTER:
            return self._recursive_character_chunking(text)
        elif self.strategy == ChunkingStrategy.SENTENCE_AWARE:
            return self._sentence_aware_chunking(text)
        else:
            raise ValueError(f"Unsupported chunking strategy: {self.strategy}")
    
    def _fixed_size_chunking(self, text: str) -> List[str]:
        """Fixed size chunks with simple token counting"""
        tokens = self.tokenizer.encode(text)
        chunks = []
        
        for i in range(0, len(tokens), self.chunk_size - self.overlap):
            chunk_start = max(0, i - self.overlap)
            chunk_end = i + self.chunk_size
            chunk = self.tokenizer.decode(tokens[chunk_start:chunk_end])
            chunks.append(chunk)
        
        return chunks
    
    def _semantic_paragraph_chunking(self, text: str) -> List[str]:
        """Chunk while preserving paragraph and sentence boundaries"""
        paragraphs = re.split(r"\n\n+", text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_tokens = len(self.tokenizer.encode(para))
            
            if current_size + para_tokens > self.chunk_size and current_chunk:
                chunks.append("\n\n".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.overlap // 100)
                current_chunk = current_chunk[overlap_start:]
                current_size = sum(len(self.tokenizer.encode(p)) for p in current_chunk)
            
            current_chunk.append(para)
            current_size += para_tokens
        
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        return chunks
    
    def _recursive_character_chunking(self, text: str) -> List[str]:
        """Recursively split by characters until chunks are small enough"""
        separators = self.separators[self.strategy]
        
        def recursive_split(t: str, s_idx: int = 0) -> List[str]:
            if len(self.tokenizer.encode(t)) <= self.chunk_size:
                return [t]
                
            if s_idx >= len(separators):
                return self._fixed_size_chunking(t)
                
            sep = separators[s_idx]
            splits = [s for s in t.split(sep) if s]
            
            if len(splits) == 1:
                return recursive_split(t, s_idx + 1)
                
            results = []
            current_chunk = ""
            
            for s in splits:
                s_with_sep = s + (sep if sep != "" else "")
                if len(self.tokenizer.encode(current_chunk + s_with_sep)) <= self.chunk_size:
                    current_chunk += s_with_sep
                else:
                    if current_chunk:
                        results.append(current_chunk)
                    current_chunk = s_with_sep
                    
            if current_chunk:
                results.append(current_chunk)
                
            return results
        
        return recursive_split(text)
    
    def _sentence_aware_chunking(self, text: str) -> List[str]:
        """Chunk while preserving complete sentences"""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sent in sentences:
            sent_tokens = len(self.tokenizer.encode(sent))
            
            if current_size + sent_tokens > self.chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # Start new chunk with overlap
                overlap_start = max(0, len(current_chunk) - self.overlap // 20)
                current_chunk = current_chunk[overlap_start:]
                current_size = sum(len(self.tokenizer.encode(s)) for s in current_chunk)
            
            current_chunk.append(sent)
            current_size += sent_tokens
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def get_strategy_info(self) -> Dict[str, str]:
        """Get information about current strategy"""
        descriptions = {
            ChunkingStrategy.FIXED_SIZE: "Simple fixed-size chunks with token counting",
            ChunkingStrategy.SEMANTIC_PARAGRAPHS: "Paragraph-aware chunks preserving document structure",
            ChunkingStrategy.RECURSIVE_CHARACTER: "Recursive splitting by characters for optimal boundaries",
            ChunkingStrategy.SENTENCE_AWARE: "Sentence-aware chunks for better semantic coherence"
        }
        return {
            "strategy": self.strategy.value,
            "description": descriptions[self.strategy],
            "optimal_use_case": self._get_optimal_use_case()
        }
    
    def _get_optimal_use_case(self) -> str:
        """Get recommended use case for current strategy"""
        use_cases = {
            ChunkingStrategy.FIXED_SIZE: "General purpose, code, or unstructured text",
            ChunkingStrategy.SEMANTIC_PARAGRAPHS: "Long-form content, articles, documents",
            ChunkingStrategy.RECURSIVE_CHARACTER: "Mixed content with varying structure",
            ChunkingStrategy.SENTENCE_AWARE: "NLP tasks requiring complete sentences"
        }
        return use_cases[self.strategy]