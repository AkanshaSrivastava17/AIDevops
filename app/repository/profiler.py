"""
Repository Profiler: Inspects repository and produces CapabilityProfile.
Decides between Enhanced, Limited, or Insufficient Evidence analysis modes.
"""
import os
import ast
import json
import logging
from typing import List, Dict, Optional, Tuple
from app.repository.models import CapabilityProfile, AnalysisMode, RepositoryConfig

logger = logging.getLogger(__name__)


class RepositoryProfiler:
    def __init__(self, config: Optional[RepositoryConfig] = None):
        self.config = config

    def profile_repository(
        self,
        repo_path: str,
        has_git: bool = True,
        commit_count: int = 0,
        issue_count: int = 0,
        pr_count: int = 0,
    ) -> CapabilityProfile:
        repo_id = self.config.repository_id if self.config else os.path.basename(repo_path)
        
        # 1. Inspect source code presence
        source_files = self._find_source_files(repo_path)
        has_source = len(source_files) > 0
        
        # 2. Check git history presence
        has_git_history = has_git and commit_count > 0
        
        # 3. Detect language
        language = self._detect_language(source_files)
        
        # 4. Detect tests and test framework
        tests_found, test_framework, test_files = self._detect_tests(repo_path)
        
        # 5. Check Python AST & import parsing capability
        python_ast = False
        import_analysis = False
        if language == "Python" and has_source:
            python_ast, import_analysis = self._verify_python_ast(source_files)

        # 6. Check issues and PRs availability
        issues_available = issue_count > 0
        prs_available = pr_count > 0
        
        # 7. Discovered components
        discovered_components = self._discover_components(repo_path)

        # 8. Determine Analysis Mode
        # - Enhanced: Python AST, import analysis, and pytest detected
        # - Limited: History is available but Python-specific evidence is not (generic fallback)
        # - Insufficient evidence: No usable Git history or no source code
        if not has_source or (not has_git_history and commit_count == 0):
            analysis_mode = AnalysisMode.INSUFFICIENT_EVIDENCE
            summary = "Insufficient repository evidence: source code or usable Git history missing."
        elif python_ast and import_analysis and (test_framework == "pytest" or tests_found):
            analysis_mode = AnalysisMode.ENHANCED
            summary = (
                f"Enhanced Mode: Python AST, import dependency graph, and {test_framework or 'tests'} detected. "
                "All impact-score terms and deep test-linking active."
            )
        else:
            analysis_mode = AnalysisMode.LIMITED
            summary = (
                "Limited Mode: Python AST/import dependency analysis unavailable. "
                "Falling back to generic path-based and co-change analysis with reduced confidence."
            )

        return CapabilityProfile(
            repository_id=repo_id,
            language=language,
            test_framework=test_framework,
            git_history=has_git_history,
            source_code=has_source,
            issues=issues_available,
            prs=prs_available,
            tests=tests_found,
            python_ast=python_ast,
            import_analysis=import_analysis,
            analysis_mode=analysis_mode,
            discovered_components=discovered_components,
            total_commits=commit_count,
            total_issues=issue_count,
            total_prs=pr_count,
            total_tests=len(test_files),
            profile_summary=summary,
        )

    def _find_source_files(self, repo_path: str) -> List[str]:
        if not os.path.exists(repo_path):
            return []
        sources = []
        exclude_dirs = {".git", ".github", "venv", ".venv", "__pycache__", "node_modules", "dist", "build"}
        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            for file in files:
                if file.endswith((".py", ".js", ".ts", ".go", ".java", ".cpp", ".c", ".rs")):
                    sources.append(os.path.join(root, file))
        return sources

    def _detect_language(self, source_files: List[str]) -> str:
        if not source_files:
            return self.config.language if self.config else "Unknown"
        py_count = sum(1 for f in source_files if f.endswith(".py"))
        js_count = sum(1 for f in source_files if f.endswith((".js", ".ts")))
        go_count = sum(1 for f in source_files if f.endswith(".go"))
        if py_count >= js_count and py_count >= go_count:
            return "Python"
        elif js_count > py_count and js_count >= go_count:
            return "JavaScript/TypeScript"
        elif go_count > py_count:
            return "Go"
        return "Generic"

    def _detect_tests(self, repo_path: str) -> Tuple[bool, Optional[str], List[str]]:
        if not os.path.exists(repo_path):
            return False, None, []
        test_files = []
        is_pytest = False
        
        # Check configuration files
        for root, _, files in os.walk(repo_path):
            for file in files:
                if file in ("pytest.ini", "setup.cfg", "pyproject.toml", "conftest.py"):
                    is_pytest = True
                if (
                    file.startswith("test_")
                    or file.endswith("_test.py")
                    or "tests" in root.replace("\\", "/").split("/")
                ) and file.endswith((".py", ".js", ".ts", ".go")):
                    test_files.append(os.path.join(root, file))
                    
        has_tests = len(test_files) > 0
        framework = "pytest" if is_pytest or has_tests else None
        return has_tests, framework, test_files

    def _verify_python_ast(self, source_files: List[str]) -> Tuple[bool, bool]:
        parsed = 0
        imported = 0
        sample = source_files[:20]
        for f in sample:
            if not f.endswith(".py"):
                continue
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as fp:
                    tree = ast.parse(fp.read(), filename=f)
                parsed += 1
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        imported += 1
                        break
            except Exception:
                continue
        ast_ok = parsed > 0
        import_ok = imported > 0
        return ast_ok, import_ok

    def discover_components(self, repo_path: str) -> List[str]:
        return self._discover_components(repo_path)

    def _discover_components(self, repo_path: str) -> List[str]:
        # If frozen rules exist in config, use those
        if self.config and self.config.component_rules_file and os.path.exists(self.config.component_rules_file):
            try:
                with open(self.config.component_rules_file, "r", encoding="utf-8") as f:
                    map_data = json.load(f)
                    return map_data.get("candidate_components", [])
            except Exception as e:
                logger.warning(f"Could not load frozen component map: {e}")

        # Automatic heuristic discovery from top-level package directories
        if not os.path.exists(repo_path):
            return ["core", "utils", "api"]

        ignored = {
            ".git", ".github", "tests", "test", "docs", "static", "scripts", "docker",
            "venv", ".venv", "__pycache__", "build", "dist", "data", "configs", ".pytest_cache",
            "egg-info", ".tox", "site-packages"
        }
        components = set()

        # 1. Check if there's a 'src' directory containing the main package
        src_path = os.path.join(repo_path, "src")
        target_root = src_path if (os.path.exists(src_path) and os.path.isdir(src_path)) else repo_path

        # 2. Check top-level package directories or submodules
        for entry in os.listdir(target_root):
            full_path = os.path.join(target_root, entry)
            if os.path.isdir(full_path) and entry not in ignored:
                subdirs = [
                    d for d in os.listdir(full_path)
                    if os.path.isdir(os.path.join(full_path, d)) and d not in ignored
                ]
                if len(subdirs) >= 2:
                    for s in subdirs:
                        components.add(s)
                else:
                    # Also check python files inside this module (e.g. models, views, routing)
                    py_files = [
                        f[:-3] for f in os.listdir(full_path)
                        if f.endswith(".py") and f not in ("__init__.py", "conftest.py", "__main__.py")
                    ]
                    if len(py_files) >= 2:
                        for pf in py_files:
                            components.add(pf)
                    else:
                        components.add(entry)

        # 3. If still empty, inspect root .py files (e.g. app.py, models.py, views.py)
        if not components and os.path.exists(repo_path):
            for f in os.listdir(repo_path):
                if f.endswith(".py") and f not in ("setup.py", "conftest.py", "__init__.py"):
                    components.add(f[:-3])

        clean_comps = [c for c in sorted(list(components)) if c and not c.startswith(".")]
        return clean_comps if clean_comps else ["core", "default"]
