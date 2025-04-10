from typing import List, Dict, Callable

class MessageChunker:
    def __init__(
        self,
        max_tokens: int = 2000,
        token_estimator: Callable[[str], int] = lambda x: len(x.split())
    ):
        """
        Initialize the MessageChunker with configuration.
        
        Args:
            max_tokens: Maximum tokens allowed per chunk
            token_estimator: Function to estimate token count from text
        """
        self.max_tokens = max_tokens
        self.token_estimator = token_estimator
    
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