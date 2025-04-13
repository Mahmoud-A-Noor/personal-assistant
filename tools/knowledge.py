# from typing import Dict, Any, Optional, List, Union, TypedDict
# from dataclasses import dataclass
# import anyio
# import functools
# from pydantic import BaseModel, field_validator, Field
# from pydantic_ai import Tool
# from core.knowledge import KnowledgeBase
# from models.knowledge import (
#     KnowledgeUpdateInput,
#     MetadataUpdateInput,
#     BatchMetadataUpdateInput,
#     BatchKnowledgeUpdateInput
# )

# class KnowledgeResult(TypedDict):
#     """A knowledge base search result."""
#     id: str
#     """Unique identifier"""
#     title: str
#     """Item title"""
#     content: str
#     """Item content"""
#     metadata: dict
#     """Associated metadata"""
#     score: Optional[float]
#     """Similarity score (0-1) for semantic search results"""

# @dataclass
# class KnowledgeSearchTool:
#     """The Knowledge search tool."""
    
#     kb: KnowledgeBase
#     """The knowledge base instance."""
    
#     max_results: int = 5
#     """Maximum number of results to return."""
    
#     async def search(self, query: str) -> List[KnowledgeResult]:
#         """Searches knowledge base using full-text search.
        
#         Args:
#             query: Search term to look for.
            
#         Returns:
#             List of matching knowledge items.
#         """
#         search_fn = functools.partial(self.kb.search_knowledge, query, self.max_results)
#         results = await anyio.to_thread.run_sync(search_fn)
#         if len(results) == 0:
#             raise RuntimeError('No search results found.')
#         return results

#     async def semantic_search(self, query: str) -> List[KnowledgeResult]:
#         """Find semantically similar knowledge using vector embeddings.
        
#         Args:
#             query: Natural language query string.
            
#         Returns:
#             List of similar knowledge items.
#         """
#         search_fn = functools.partial(self.kb.semantic_search, query, self.max_results)
#         results = await anyio.to_thread.run_sync(search_fn)
#         if len(results) == 0:
#             raise RuntimeError('No similar items found.')
#         return results

#     async def query_by_metadata(self, field: str, value: Union[int, List[str], str]) -> List[KnowledgeResult]:
#         """Search knowledge base by specific metadata field.
        
#         Args:
#             field: Metadata field to query.
#             value: Value to query for.
            
#         Returns:
#             List of matching knowledge items.
#         """
#         query_fn = functools.partial(self.kb.query_by_metadata, field, value, self.max_results)
#         results = await anyio.to_thread.run_sync(query_fn)
#         if len(results) == 0:
#             raise RuntimeError('No items found matching metadata criteria.')
#         return results

# @dataclass
# class KnowledgeManagementTool:
#     """Tool for managing knowledge items."""
    
#     kb: KnowledgeBase
#     """The knowledge base instance."""
    
#     async def upsert(self, input: KnowledgeUpdateInput) -> bool:
#         """Add or update knowledge in the knowledge base.
        
#         Args:
#             input: Knowledge update input containing title, content and metadata.
            
#         Returns:
#             True if operation succeeded.
#         """
#         upsert_fn = functools.partial(
#             self.kb.upsert_knowledge,
#             title=input.title,
#             content=input.content,
#             metadata=input.to_metadata()
#         )
#         return await anyio.to_thread.run_sync(upsert_fn)

#     async def update_metadata(self, input: MetadataUpdateInput) -> bool:
#         """Update specific metadata field for a knowledge item.
        
#         Args:
#             input: Metadata update input containing field and value.
            
#         Returns:
#             True if update succeeded.
#         """
#         item = await self._get_item_for_update(input)
#         if not item:
#             return False
        
#         await self._apply_metadata_update(item, input.field, input.value)
#         upsert_fn = functools.partial(
#             self.kb.upsert_knowledge,
#             title=item.title,
#             content=item.content,
#             metadata=item.metadata
#         )
#         return await anyio.to_thread.run_sync(upsert_fn)

#     async def batch_upsert(self, input: BatchKnowledgeUpdateInput) -> List[bool]:
#         """Batch upsert multiple knowledge items.
        
#         Args:
#             input: Batch of knowledge items to upsert.
            
#         Returns:
#             List of success status for each item.
#         """
#         results = []
#         for item in input.items:
#             result = await self.upsert(item)
#             results.append(result)
#         return results

#     async def batch_update_metadata(self, input: BatchMetadataUpdateInput) -> List[bool]:
#         """Batch update metadata for multiple items.
        
#         Args:
#             input: Batch of metadata updates.
            
#         Returns:
#             List of success status for each update.
#         """
#         results = []
#         for update in input.updates:
#             result = await self.update_metadata(update)
#             results.append(result)
#         return results

#     async def get_metadata(self, id: str) -> Optional[dict]:
#         """Get metadata for a specific item.
        
#         Args:
#             id: Item ID.
            
#         Returns:
#             Metadata dictionary if found.
#         """
#         get_fn = functools.partial(self.kb.get_by_id, id)
#         item = await anyio.to_thread.run_sync(get_fn)
#         return item.metadata.dict() if item else None

#     async def add_reference(self, id: str, reference: str) -> bool:
#         """Add a reference to an item's metadata.
        
#         Args:
#             id: Item ID.
#             reference: Reference to add.
            
#         Returns:
#             True if reference was added.
#         """
#         get_fn = functools.partial(self.kb.get_by_id, id)
#         item = await anyio.to_thread.run_sync(get_fn)
#         if not item:
#             return False
        
#         if reference not in item.metadata.references:
#             item.metadata.references.append(reference)
#             upsert_fn = functools.partial(
#                 self.kb.upsert_knowledge,
#                 title=item.title,
#                 content=item.content,
#                 metadata=item.metadata
#             )
#             return await anyio.to_thread.run_sync(upsert_fn)
#         return True

#     async def add_topic(self, id: str, topic: str) -> bool:
#         """Add a topic to an item's metadata.
        
#         Args:
#             id: Item ID.
#             topic: Topic to add.
            
#         Returns:
#             True if topic was added.
#         """
#         get_fn = functools.partial(self.kb.get_by_id, id)
#         item = await anyio.to_thread.run_sync(get_fn)
#         if not item:
#             return False
        
#         if topic not in item.metadata.related_topics:
#             item.metadata.related_topics.append(topic)
#             upsert_fn = functools.partial(
#                 self.kb.upsert_knowledge,
#                 title=item.title,
#                 content=item.content,
#                 metadata=item.metadata
#             )
#             return await anyio.to_thread.run_sync(upsert_fn)
#         return True

#     async def _get_item_for_update(self, input: MetadataUpdateInput):
#         """Helper to retrieve item for update operations."""
#         if input.id:
#             get_fn = functools.partial(self.kb.get_by_id, input.id)
#             return await anyio.to_thread.run_sync(get_fn)
#         else:
#             search_fn = functools.partial(self.kb.search_knowledge, input.query, 1)
#             results = await anyio.to_thread.run_sync(search_fn)
#             return results[0] if results else None

#     async def _apply_metadata_update(self, item, field: str, value):
#         """Helper to apply metadata updates."""
#         if field == "importance":
#             item.metadata.importance = value
#         elif field == "related_topics":
#             item.metadata.related_topics = value
#         elif field == "references":
#             item.metadata.references = value
#         elif field == "language":
#             item.metadata.language = value
#         elif field == "tags":
#             item.metadata.tags = value

# def get_knowledge_tools(kb: Optional[KnowledgeBase] = None, max_results: int = 5) -> List[Tool]:
#     """Creates knowledge base tools.
    
#     Args:
#         kb: The knowledge base instance.
#         max_results: Maximum number of results to return.
#     """
#     kb = kb or KnowledgeBase()
#     search_tools = KnowledgeSearchTool(kb=kb, max_results=max_results)
#     management_tools = KnowledgeManagementTool(kb=kb)
    
#     return [
#         Tool(
#             search_tools.search,
#             name='knowledge_search',
#             description='Search knowledge base using full-text search'
#         ),
#         Tool(
#             search_tools.semantic_search,
#             name='knowledge_semantic_search', 
#             description='Find semantically similar knowledge using vector embeddings'
#         ),
#         Tool(
#             search_tools.query_by_metadata,
#             name='knowledge_query_by_metadata',
#             description='Search knowledge base by specific metadata field'
#         ),
#         Tool(
#             management_tools.upsert,
#             name='knowledge_upsert',
#             description='Add or update knowledge in the knowledge base'
#         ),
#         Tool(
#             management_tools.update_metadata,
#             name='knowledge_update_metadata',
#             description='Update specific metadata field for a knowledge item'
#         ),
#         Tool(
#             management_tools.batch_upsert,
#             name='knowledge_batch_upsert',
#             description='Batch upsert multiple knowledge items'
#         ),
#         Tool(
#             management_tools.batch_update_metadata,
#             name='knowledge_batch_update_metadata',
#             description='Batch update metadata for multiple knowledge items'
#         ),
#         Tool(
#             management_tools.get_metadata,
#             name='knowledge_get_metadata',
#             description='Get metadata for a specific knowledge item'
#         ),
#         Tool(
#             management_tools.add_reference,
#             name='knowledge_add_reference',
#             description='Add a reference to a knowledge item\'s metadata'
#         ),
#         Tool(
#             management_tools.add_topic,
#             name='knowledge_add_topic',
#             description='Add a topic to a knowledge item\'s metadata'
#         )
#     ]