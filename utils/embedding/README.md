# Embedding Utilities

This folder contains implementations for different embedding backends:

## QdrantFastEmbedder (`qdrant.py`)
- Interfaces with FastEmbed (optimized for Qdrant)
- Optimized for production use with Qdrant vector database
- Faster inference with Rust backend
- Limited to models supported by FastEmbed
- Best for: Production deployments with Qdrant

## SentenceTransformerEmbedder (`sentence_transformers.py`)
- Interfaces with sentence-transformers
- Wider model selection from HuggingFace Hub
- More flexible for research/experimentation
- Slower than FastEmbed but supports more models
- Best for: Research, prototyping, or when needing specific models
