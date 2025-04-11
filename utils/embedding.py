from typing import List
from sentence_transformers import SentenceTransformer

class LocalEmbedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2 model

    def generate_embedding(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()