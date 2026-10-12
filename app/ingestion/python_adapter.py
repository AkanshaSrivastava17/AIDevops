"""
Python-specific enhancement layer: AST chunking and import dependency analysis.
Enables Enhanced Analysis Mode according to Sections 3.4.1, 7.1, 8.2 of the plan.
"""
import ast
import logging
from typing import List, Dict, Tuple, Optional
from app.ingestion.schema import NormalizedDocument, DocumentType, EventType, DependencyLink

logger = logging.getLogger(__name__)


class PythonASTAdapter:
    def __init__(self, component_mapping_fn=None, candidate_components: Optional[List[str]] = None):
        self.component_mapping_fn = component_mapping_fn or (lambda path: "core")
        self.candidate_components = set(candidate_components or [])

    def parse_file(self, file_path: str, code: str, repo_id: str, timestamp: str) -> Tuple[List[NormalizedDocument], List[DependencyLink]]:
        chunks: List[NormalizedDocument] = []
        dependencies: List[DependencyLink] = []
        
        try:
            tree = ast.parse(code, filename=file_path)
        except Exception as e:
            logger.debug(f"AST parse error in {file_path}: {e}")
            return [], []

        source_comp = self.component_mapping_fn(file_path)
        lines = code.splitlines()

        # 1. Extract imports and build dependency links
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imp_name = alias.name
                    target_comp = self._map_import_to_component(imp_name)
                    if target_comp and target_comp != source_comp:
                        dependencies.append(DependencyLink(
                            source_component=source_comp,
                            target_component=target_comp,
                            import_statement=f"import {imp_name}",
                            source_file=file_path
                        ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                target_comp = self._map_import_to_component(module)
                if target_comp and target_comp != source_comp:
                    dependencies.append(DependencyLink(
                        source_component=source_comp,
                        target_component=target_comp,
                        import_statement=f"from {module} import ...",
                        source_file=file_path
                    ))

        # 2. Extract logical AST chunks: Classes and Functions
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno - 1
                end_line = getattr(node, "end_lineno", len(lines))
                chunk_code = "\n".join(lines[start_line:end_line])
                
                docstring = ast.get_docstring(node) or ""
                node_type = "class" if isinstance(node, ast.ClassDef) else "function"
                
                doc = NormalizedDocument(
                    document_id=f"ast-{file_path}-{node.name}-{start_line}",
                    repository_id=repo_id,
                    type=DocumentType.TEST if "test" in file_path.lower() else DocumentType.CODE,
                    path=file_path,
                    component=source_comp,
                    event_timestamp=timestamp,
                    event_type=EventType.TEST_CHANGE if "test" in file_path.lower() else EventType.CODE_CHUNK,
                    title=f"{node_type.capitalize()} {node.name} in {file_path}",
                    content=f"{node_type} {node.name}:\n{docstring}\n{chunk_code[:2000]}",
                    metadata={
                        "symbol_name": node.name,
                        "symbol_type": node_type,
                        "start_line": start_line + 1,
                        "end_line": end_line,
                        "ast_parsed": True
                    }
                )
                chunks.append(doc)

        return chunks, dependencies

    def _map_import_to_component(self, module_name: str) -> Optional[str]:
        parts = module_name.split(".")
        # 1. Match against known candidate components
        for p in parts:
            if p in self.candidate_components:
                return p

        # 2. Known fallback for NetBox / standard apps
        if len(parts) > 1 and parts[0] == "netbox":
            return parts[1]
        elif len(parts) > 0 and parts[0] in (
            "dcim", "ipam", "tenancy", "circuits", "virtualization", "extras", "wireless", "users", "utilities"
        ):
            return parts[0]

        # 3. Check if component_mapping_fn can map the pseudo module path
        if self.component_mapping_fn:
            try:
                mapped = self.component_mapping_fn(f"{module_name.replace('.', '/')}.py")
                if mapped and mapped not in ("core", "default"):
                    return mapped
            except Exception:
                pass

        # 4. If multipart import, check if subpackage matches
        if len(parts) > 1 and parts[1] in self.candidate_components:
            return parts[1]
        elif len(parts) > 0 and parts[0] in self.candidate_components:
            return parts[0]

        return None
