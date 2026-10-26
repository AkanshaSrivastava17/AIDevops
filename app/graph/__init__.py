"""
Knowledge Graph Package for History-RAG.
Implements Section 33 Enhancement #1: NetworkX relationship graph.
Explicit issue -> PR -> commit -> file -> test graph with multi-hop impact path analysis.
"""
from app.graph.knowledge_graph import RepositoryKnowledgeGraph

__all__ = ["RepositoryKnowledgeGraph"]
