from typing import List
from sentence_transformers import SentenceTransformer

class LocalEmbedding:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()