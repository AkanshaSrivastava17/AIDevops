"""
Repository Adapter: Clones/inspects Git repository, loads issue/PR discussions,
and normalizes all raw repository artifacts into the common schema.
"""
import os
import re
import json
import yaml
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Tuple
import git

from app.repository.models import RepositoryConfig, CapabilityProfile
from app.repository.profiler import RepositoryProfiler
from app.ingestion.schema import NormalizedDocument, DocumentType, EventType

logger = logging.getLogger(__name__)


class RepositoryAdapter:
    def __init__(self, config_path_or_obj):
        if isinstance(config_path_or_obj, str):
            with open(config_path_or_obj, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.config = RepositoryConfig(**data)
        elif isinstance(config_path_or_obj, RepositoryConfig):
            self.config = config_path_or_obj
        else:
            self.config = RepositoryConfig(**config_path_or_obj)

        self.repo_dir = os.path.join("data", "raw", self.config.repository_id)
        self.component_map = self._load_component_map()

    def _load_component_map(self) -> Dict[str, str]:
        if self.config.component_rules_file and os.path.exists(self.config.component_rules_file):
            try:
                with open(self.config.component_rules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("rules", {})
            except Exception as e:
                logger.warning(f"Error loading component rules: {e}")
        return {}

    def map_file_to_component(self, file_path: str) -> str:
        norm_path = file_path.replace("\\", "/")
        # Match against frozen component map rules
        for prefix, comp in self.component_map.items():
            if norm_path.startswith(prefix) or f"/{prefix}" in norm_path:
                return comp

        # Heuristic fallback: check directory parts
        parts = [p for p in norm_path.split("/") if p and p not in ("tests", "src", "app")]
        if len(parts) > 1:
            return parts[1] if parts[0] in ("netbox", "src") else parts[0]
        elif len(parts) == 1:
            return parts[0].split(".")[0]
        return "core"

    def is_test_file(self, file_path: str) -> bool:
        norm_path = file_path.replace("\\", "/").lower()
        filename = os.path.basename(norm_path)
        if "/tests/" in norm_path or norm_path.startswith("tests/"):
            return True
        if filename.startswith("test_") or filename.endswith("_test.py") or ".test." in filename:
            return True
        return False

    def get_profile(self) -> CapabilityProfile:
        profiler = RepositoryProfiler(self.config)
        git_dir = os.path.join(self.repo_dir, ".git")
        has_git = os.path.exists(git_dir) or os.path.exists(self.repo_dir)
        
        # Load counts if available
        commits_cache = os.path.join(self.repo_dir, "commits.json")
        commit_count = 0
        if os.path.exists(commits_cache):
            try:
                with open(commits_cache, "r", encoding="utf-8") as f:
                    commit_count = len(json.load(f))
            except Exception:
                pass
        elif has_git and os.path.exists(git_dir):
            try:
                repo = git.Repo(self.repo_dir)
                commit_count = sum(1 for _ in repo.iter_commits(max_count=200))
            except Exception:
                commit_count = 0

        issues_cache = os.path.join(self.repo_dir, "issues.json")
        issue_count = 0
        if os.path.exists(issues_cache):
            try:
                with open(issues_cache, "r", encoding="utf-8") as f:
                    issue_count = len(json.load(f))
            except Exception:
                pass

        prs_cache = os.path.join(self.repo_dir, "prs.json")
        pr_count = 0
        if os.path.exists(prs_cache):
            try:
                with open(prs_cache, "r", encoding="utf-8") as f:
                    pr_count = len(json.load(f))
            except Exception:
                pass

        return profiler.profile_repository(
            repo_path=self.repo_dir,
            has_git=has_git,
            commit_count=commit_count,
            issue_count=issue_count,
            pr_count=pr_count
        )

    def extract_normalized_documents(self) -> List[NormalizedDocument]:
        documents: List[NormalizedDocument] = []
        os.makedirs(self.repo_dir, exist_ok=True)

        # 1. Ingest commits
        commits_file = os.path.join(self.repo_dir, "commits.json")
        if os.path.exists(commits_file):
            try:
                with open(commits_file, "r", encoding="utf-8") as f:
                    raw_commits = json.load(f)
                    for c in raw_commits:
                        files = c.get("files", [])
                        comps = list({self.map_file_to_component(f) for f in files})
                        primary_comp = comps[0] if comps else "core"
                        doc = NormalizedDocument(
                            document_id=f"commit-{c['sha'][:8]}",
                            repository_id=self.config.repository_id,
                            type=DocumentType.COMMIT,
                            path=files[0] if files else None,
                            component=primary_comp,
                            commit_sha=c["sha"],
                            event_timestamp=c["timestamp"],
                            event_type=EventType.COMMIT,
                            language=self.config.language,
                            title=c.get("message", "").split("\n")[0][:120],
                            content=f"Commit: {c['sha'][:8]}\nMessage: {c.get('message', '')}\nFiles: {', '.join(files)}",
                            metadata={
                                "author": c.get("author", "Unknown"),
                                "files_changed": files,
                                "components": comps,
                                "diff": c.get("diff", "")
                            }
                        )
                        documents.append(doc)
            except Exception as e:
                logger.error(f"Error loading commits.json: {e}")

        # 2. Ingest Issues with event-level timestamps
        issues_file = os.path.join(self.repo_dir, "issues.json")
        if os.path.exists(issues_file):
            try:
                with open(issues_file, "r", encoding="utf-8") as f:
                    raw_issues = json.load(f)
                    for issue in raw_issues:
                        iid = str(issue.get("id", ""))
                        comp = issue.get("component") or self._infer_component_from_text(
                            issue.get("title", "") + " " + issue.get("body", "")
                        )
                        # Issue created event
                        doc = NormalizedDocument(
                            document_id=f"issue-{iid}",
                            repository_id=self.config.repository_id,
                            type=DocumentType.ISSUE,
                            component=comp,
                            issue_id=iid,
                            event_timestamp=issue.get("created_at", datetime.now(timezone.utc).isoformat()),
                            event_type=EventType.ISSUE_CREATED,
                            language=self.config.language,
                            title=issue.get("title", ""),
                            content=f"Issue #{iid}: {issue.get('title', '')}\n\n{issue.get('body', '')}",
                            metadata={
                                "labels": issue.get("labels", []),
                                "state": issue.get("state", "open"),
                                "linked_prs": issue.get("linked_prs", []),
                                "updated_at": issue.get("updated_at")
                            }
                        )
                        documents.append(doc)
                        # Issue comments
                        for idx, comment in enumerate(issue.get("comments", [])):
                            c_doc = NormalizedDocument(
                                document_id=f"issue-{iid}-c{idx}",
                                repository_id=self.config.repository_id,
                                type=DocumentType.ISSUE,
                                component=comp,
                                issue_id=iid,
                                event_timestamp=comment.get("created_at", issue.get("created_at")),
                                event_type=EventType.ISSUE_COMMENT,
                                language=self.config.language,
                                title=f"Comment on Issue #{iid}",
                                content=f"Comment by {comment.get('user', 'dev')} on #{iid}:\n{comment.get('body', '')}",
                                metadata={"comment_index": idx, "user": comment.get("user")}
                            )
                            documents.append(c_doc)
            except Exception as e:
                logger.error(f"Error loading issues.json: {e}")

        # 3. Ingest Pull Requests with event-level timestamps
        prs_file = os.path.join(self.repo_dir, "prs.json")
        if os.path.exists(prs_file):
            try:
                with open(prs_file, "r", encoding="utf-8") as f:
                    raw_prs = json.load(f)
                    for pr in raw_prs:
                        pr_id = str(pr.get("id", ""))
                        comp = pr.get("component") or self._infer_component_from_text(
                            pr.get("title", "") + " " + pr.get("body", "")
                        )
                        doc = NormalizedDocument(
                            document_id=f"pr-{pr_id}",
                            repository_id=self.config.repository_id,
                            type=DocumentType.PR,
                            component=comp,
                            pr_id=pr_id,
                            commit_sha=pr.get("merge_commit_sha"),
                            event_timestamp=pr.get("created_at", datetime.now(timezone.utc).isoformat()),
                            event_type=EventType.PR_CREATED,
                            language=self.config.language,
                            title=pr.get("title", ""),
                            content=f"Pull Request #{pr_id}: {pr.get('title', '')}\n\n{pr.get('body', '')}",
                            metadata={
                                "state": pr.get("state", "closed"),
                                "merged": pr.get("merged", True),
                                "files_changed": pr.get("files_changed", []),
                                "linked_issues": pr.get("linked_issues", []),
                                "updated_at": pr.get("updated_at")
                            }
                        )
                        documents.append(doc)
            except Exception as e:
                logger.error(f"Error loading prs.json: {e}")

        # 4. Ingest local source and test files
        if os.path.exists(self.repo_dir):
            for root, _, files in os.walk(self.repo_dir):
                for file in files:
                    if file in ("commits.json", "issues.json", "prs.json", "metadata.db"):
                        continue
                    if file.endswith((".py", ".md", ".txt", ".yml", ".yaml")):
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, self.repo_dir).replace("\\", "/")
                        is_test = self.is_test_file(rel_path)
                        comp = self.map_file_to_component(rel_path)
                        try:
                            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                                content = f.read()
                            doc = NormalizedDocument(
                                document_id=f"file-{rel_path}",
                                repository_id=self.config.repository_id,
                                type=DocumentType.TEST if is_test else DocumentType.CODE,
                                path=rel_path,
                                component=comp,
                                event_timestamp=datetime.now(timezone.utc).isoformat(),
                                event_type=EventType.TEST_CHANGE if is_test else EventType.CODE_CHUNK,
                                language=self.config.language,
                                title=rel_path,
                                content=content[:4000],  # truncated sample if long
                                metadata={"is_test": is_test, "full_length": len(content)}
                            )
                            documents.append(doc)
                        except Exception:
                            pass

        return documents

    def _infer_component_from_text(self, text: str) -> str:
        text_lower = text.lower()
        for comp in self.component_map.values():
            if re.search(r"\b" + re.escape(comp) + r"\b", text_lower):
                return comp
        return "core"
