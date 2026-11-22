"""
Python-specific enhancement layer: AST chunking and import dependency analysis.
Delegates to UniversalASTAdapter (Tree-sitter powered) with Python built-in AST fallback.
"""
from typing import List, Dict, Tuple, Optional
from app.ingestion.schema import NormalizedDocument, DependencyLink
from app.ingestion.universal_adapter import UniversalASTAdapter


class PythonASTAdapter(UniversalASTAdapter):
    """
    Backwards-compatible Python AST adapter that leverages UniversalASTAdapter.
    """
    def __init__(self, component_mapping_fn=None, candidate_components: Optional[List[str]] = None):
        super().__init__(component_mapping_fn=component_mapping_fn, candidate_components=candidate_components)
