from typing import List, Dict, Callable

class TextChunker:
    def __init__(
        self,
        max_tokens: int = 2000,
        token_estimator: Callable[[str], int] = lambda x: len(x.split()),
        overlap: int = 100,
        separators: List[str] = None
    ):
        """
        Initialize the MessageChunker with configuration.
        
        Args:
            max_tokens: Maximum tokens allowed per chunk
            token_estimator: Function to estimate token count from text
            overlap: Number of tokens to overlap between chunks
            separators: List of separators to split text on
        """
        self.max_tokens = max_tokens
        self.token_estimator = token_estimator
        self.overlap = overlap
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def chunk_text(self, text: str) -> List[str]:
        """
        Advanced text chunking with overlap and semantic boundaries
        """
        if not text:
            return []
            
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        # Try all separators in order of priority
        for sep in self.separators:
            if sep in text:
                sentences = text.split(sep)
                for sentence in sentences:
                    sentence_tokens = self.token_estimator(sentence)
                    
                    # If adding this would exceed limit (with overlap)
                    if current_tokens + sentence_tokens > self.max_tokens - self.overlap:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            
                            # Carry over overlap tokens
                            overlap_part = " ".join(current_chunk.split()[-self.overlap:])
                            current_chunk = overlap_part + " " + sentence
                            current_tokens = self.token_estimator(overlap_part) + sentence_tokens + 1
                        else:
                            current_chunk = sentence
                            current_tokens = sentence_tokens
                    else:
                        current_chunk += sep + sentence if current_chunk else sentence
                        current_tokens += sentence_tokens
        
        # Fallback if no separators found - split by max_tokens
        if not chunks and not current_chunk:
            words = text.split()
            current_chunk = ""
            current_tokens = 0
            for word in words:
                word_tokens = self.token_estimator(word)
                if current_tokens + word_tokens > self.max_tokens:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = word
                        current_tokens = word_tokens
                else:
                    current_chunk += " " + word if current_chunk else word
                    current_tokens += word_tokens
        
        # Add final chunk if it exists
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks

    def chunk_and_embed(
        self, 
        text: str, 
        embedder: Callable[[str], List[float]]
    ) -> List[dict]:
        """
        Chunk text and generate embeddings in one operation
        Returns list of dicts with keys: text, embedding
        """
        chunks = self.chunk_text(text)
        return [
            {
                "text": chunk,
                "embedding": embedder(chunk)
            }
            for chunk in chunks
        ]

    def chunk_messages(self, messages: List[Dict]) -> List[List[Dict]]:
        """
        Split messages into chunks that fit within token limits.
        
        Args:
            messages: List of message dictionaries (must have "content" key)
            
        Returns:
            List of message chunks where each chunk is within token limit
        """
        chunks = []
        current_chunk = []
        current_tokens = 0

        for msg in messages:
            msg_tokens = self.token_estimator(msg["content"])
            
            if current_tokens + msg_tokens > self.max_tokens and current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
                
            current_chunk.append(msg)
            current_tokens += msg_tokens

        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def update_max_tokens(self, new_max: int):
        """Update the maximum tokens per chunk"""
        self.max_tokens = new_max

    def update_token_estimator(self, new_estimator: Callable[[str], int]):
        """Update the token estimation function"""
        self.token_estimator = new_estimator