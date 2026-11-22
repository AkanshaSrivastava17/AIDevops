"""
Universal Polyglot AST Adapter powered by Tree-sitter.
Provides syntax-aware AST chunking and import dependency graph analysis
across Python, JavaScript, TypeScript, Go, and Java.
Falls back gracefully to Python built-in AST when needed.
"""
import os
import re
import ast
import logging
from typing import List, Dict, Tuple, Optional, Set, Any

from app.ingestion.schema import NormalizedDocument, DocumentType, EventType, DependencyLink

logger = logging.getLogger(__name__)

# Tree-sitter Language Initialization
TREE_SITTER_AVAILABLE = False
PARSERS: Dict[str, Any] = {}
LANGUAGES: Dict[str, Any] = {}

try:
    from tree_sitter import Language, Parser
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    import tree_sitter_go as tsgo
    import tree_sitter_java as tsjava

    LANGUAGES = {
        "python": Language(tspython.language()),
        "javascript": Language(tsjavascript.language()),
        "typescript": Language(tstypescript.language_typescript()),
        "tsx": Language(tstypescript.language_tsx()),
        "go": Language(tsgo.language()),
        "java": Language(tsjava.language()),
    }
    TREE_SITTER_AVAILABLE = True
except Exception as e:
    logger.warning(f"Tree-sitter language loading notice: {e}. Falling back to standard parser.")


EXTENSION_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".java": "java",
}


class UniversalASTAdapter:
    """
    Universal AST Adapter that parses Python, JavaScript, TypeScript, Go, and Java
    using Tree-sitter, extracting granular AST code chunks and component import dependencies.
    """

    def __init__(self, component_mapping_fn=None, candidate_components: Optional[List[str]] = None):
        self.component_mapping_fn = component_mapping_fn or (lambda path: "core")
        self.candidate_components = set(candidate_components or [])
        self.parsers: Dict[str, Any] = {}

        if TREE_SITTER_AVAILABLE:
            for lang_key, lang_obj in LANGUAGES.items():
                try:
                    self.parsers[lang_key] = Parser(lang_obj)
                except Exception as e:
                    logger.debug(f"Could not initialize parser for {lang_key}: {e}")

    def is_supported_file(self, file_path: str) -> bool:
        """Returns True if file extension is supported for AST parsing."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in EXTENSION_MAP

    def get_language(self, file_path: str) -> Optional[str]:
        """Returns the detected language identifier for the given file."""
        ext = os.path.splitext(file_path)[1].lower()
        return EXTENSION_MAP.get(ext)

    def parse_file(
        self,
        file_path: str,
        code: str,
        repo_id: str,
        timestamp: str
    ) -> Tuple[List[NormalizedDocument], List[DependencyLink]]:
        """
        Parses source code file using Tree-sitter (or Python ast fallback)
        and returns logical symbol chunks and import dependency links.
        """
        lang = self.get_language(file_path)
        if not lang:
            return [], []

        # If Python and Tree-sitter not available, use built-in AST
        if lang == "python" and (not TREE_SITTER_AVAILABLE or "python" not in self.parsers):
            return self._parse_python_builtin(file_path, code, repo_id, timestamp)

        parser = self.parsers.get(lang)
        if not parser:
            if lang == "python":
                return self._parse_python_builtin(file_path, code, repo_id, timestamp)
            return [], []

        try:
            code_bytes = code.encode("utf-8", errors="ignore")
            tree = parser.parse(code_bytes)
        except Exception as e:
            logger.debug(f"Tree-sitter parse error in {file_path}: {e}")
            if lang == "python":
                return self._parse_python_builtin(file_path, code, repo_id, timestamp)
            return [], []

        source_comp = self.component_mapping_fn(file_path)
        lines = code.splitlines()

        chunks: List[NormalizedDocument] = []
        dependencies: List[DependencyLink] = []

        # Walk syntax tree to extract symbols & imports
        self._extract_ast(
            node=tree.root_node,
            lang=lang,
            file_path=file_path,
            lines=lines,
            source_comp=source_comp,
            repo_id=repo_id,
            timestamp=timestamp,
            chunks=chunks,
            dependencies=dependencies
        )

        return chunks, dependencies

    def _extract_ast(
        self,
        node,
        lang: str,
        file_path: str,
        lines: List[str],
        source_comp: str,
        repo_id: str,
        timestamp: str,
        chunks: List[NormalizedDocument],
        dependencies: List[DependencyLink]
    ):
        ntype = node.type

        # 1. Logical Symbol Definition: Function / Method / Class / Struct / Interface
        if ntype in (
            "function_definition", "function_declaration", "method_declaration",
            "class_definition", "class_declaration", "interface_declaration",
            "type_declaration"
        ):
            name_node = node.child_by_field_name("name")
            if not name_node and ntype == "type_declaration":
                for c in node.children:
                    if c.type == "type_spec":
                        name_node = c.child_by_field_name("name")
                        break
            symbol_name = name_node.text.decode("utf-8", errors="ignore") if name_node else "anonymous"

            start_line = node.start_point[0]
            end_line = node.end_point[0] + 1
            chunk_code = "\n".join(lines[start_line:end_line])

            sym_type = "class" if "class" in ntype or "type" in ntype or "interface" in ntype else "function"

            is_test = "test" in file_path.lower() or "spec" in file_path.lower()
            doc = NormalizedDocument(
                document_id=f"ast-{file_path}-{symbol_name}-{start_line}",
                repository_id=repo_id,
                type=DocumentType.TEST if is_test else DocumentType.CODE,
                path=file_path,
                component=source_comp,
                event_timestamp=timestamp,
                event_type=EventType.TEST_CHANGE if is_test else EventType.CODE_CHUNK,
                title=f"{sym_type.capitalize()} {symbol_name} in {file_path}",
                content=f"{sym_type} {symbol_name} ({lang}):\n{chunk_code[:2500]}",
                metadata={
                    "symbol_name": symbol_name,
                    "symbol_type": sym_type,
                    "language": lang,
                    "start_line": start_line + 1,
                    "end_line": end_line,
                    "ast_parsed": True,
                    "parser": "tree-sitter"
                }
            )
            chunks.append(doc)

        # 2. Imports and Dependency Links
        if ntype in ("import_statement", "import_from_statement", "import_declaration"):
            import_text = node.text.decode("utf-8", errors="ignore").strip()
            module_name = ""

            if lang == "python":
                mod_node = node.child_by_field_name("module_name")
                if mod_node:
                    module_name = mod_node.text.decode("utf-8", errors="ignore")
                else:
                    for c in node.children:
                        if c.type == "dotted_name":
                            module_name = c.text.decode("utf-8", errors="ignore")
                            break
            elif lang in ("javascript", "typescript", "tsx"):
                src_node = node.child_by_field_name("source")
                if src_node:
                    module_name = src_node.text.decode("utf-8", errors="ignore").strip("'\"")
            elif lang == "go":
                for c in node.named_children:
                    if c.type == "import_spec":
                        p = c.child_by_field_name("path")
                        if p:
                            module_name = p.text.decode("utf-8", errors="ignore").strip("'\"")
                            self._add_dependency(source_comp, module_name, import_text, file_path, dependencies)
                    elif c.type == "import_spec_list":
                        for spec in c.children:
                            if spec.type == "import_spec":
                                p = spec.child_by_field_name("path")
                                if p:
                                    m = p.text.decode("utf-8", errors="ignore").strip("'\"")
                                    self._add_dependency(source_comp, m, spec.text.decode("utf-8", errors="ignore"), file_path, dependencies)
                return
            elif lang == "java":
                for c in node.children:
                    if c.type == "scoped_identifier":
                        module_name = c.text.decode("utf-8", errors="ignore")
                        break

            if module_name:
                self._add_dependency(source_comp, module_name, import_text, file_path, dependencies)

        # Recurse children
        for child in node.children:
            self._extract_ast(
                child, lang, file_path, lines, source_comp,
                repo_id, timestamp, chunks, dependencies
            )

    def _add_dependency(
        self,
        source_comp: str,
        module_name: str,
        statement: str,
        file_path: str,
        dependencies: List[DependencyLink]
    ):
        target_comp = self._map_import_to_component(module_name)
        if target_comp and target_comp != source_comp:
            dependencies.append(DependencyLink(
                source_component=source_comp,
                target_component=target_comp,
                import_statement=statement,
                source_file=file_path
            ))

    def _map_import_to_component(self, module_name: str) -> Optional[str]:
        """Maps an imported module, file path, or package to a component name."""
        if not module_name:
            return None

        # Clean relative path prefixes like './dcim', '../auth/service', etc.
        cleaned = module_name.replace("\\", "/").strip("./").strip("/")
        parts = re.split(r"[/.]", cleaned)

        # 1. Match against known candidate components
        for p in parts:
            if p in self.candidate_components:
                return p

        # 2. NetBox standard components
        known_components = (
            "dcim", "ipam", "tenancy", "circuits", "virtualization",
            "extras", "wireless", "users", "utilities", "core"
        )
        for p in parts:
            if p.lower() in known_components:
                return p.lower()

        # 3. Check custom component mapping function
        if self.component_mapping_fn:
            try:
                mapped = self.component_mapping_fn(f"{cleaned}.py")
                if mapped and mapped not in ("core", "default"):
                    return mapped
            except Exception:
                pass

        return None

    def _parse_python_builtin(
        self,
        file_path: str,
        code: str,
        repo_id: str,
        timestamp: str
    ) -> Tuple[List[NormalizedDocument], List[DependencyLink]]:
        """Fallback to Python's standard ast module."""
        try:
            tree = ast.parse(code, filename=file_path)
        except Exception as e:
            logger.debug(f"Fallback AST parse error in {file_path}: {e}")
            return [], []

        source_comp = self.component_mapping_fn(file_path)
        lines = code.splitlines()
        chunks: List[NormalizedDocument] = []
        dependencies: List[DependencyLink] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target_comp = self._map_import_to_component(alias.name)
                    if target_comp and target_comp != source_comp:
                        dependencies.append(DependencyLink(
                            source_component=source_comp,
                            target_component=target_comp,
                            import_statement=f"import {alias.name}",
                            source_file=file_path
                        ))
            elif isinstance(node, ast.ImportFrom):
                target_comp = self._map_import_to_component(node.module or "")
                if target_comp and target_comp != source_comp:
                    dependencies.append(DependencyLink(
                        source_component=source_comp,
                        target_component=target_comp,
                        import_statement=f"from {node.module} import ...",
                        source_file=file_path
                    ))

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                start_line = node.lineno - 1
                end_line = getattr(node, "end_lineno", len(lines))
                chunk_code = "\n".join(lines[start_line:end_line])
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
                    content=f"{node_type} {node.name}:\n{chunk_code[:2000]}",
                    metadata={
                        "symbol_name": node.name,
                        "symbol_type": node_type,
                        "language": "python",
                        "start_line": start_line + 1,
                        "end_line": end_line,
                        "ast_parsed": True,
                        "parser": "python-builtin"
                    }
                )
                chunks.append(doc)

        return chunks, dependencies
