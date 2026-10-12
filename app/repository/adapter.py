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


import urllib.request
import urllib.error

def parse_github_url(url: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Parses a Git or GitHub URL into (owner, repo_name, repo_id).
    """
    if not url:
        return None, None, "repo"
    cleaned = url.strip().rstrip("/")
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]

    match = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+)", cleaned, re.IGNORECASE)
    if match:
        owner = match.group(1)
        repo_name = match.group(2)
        repo_id = re.sub(r"[^\w.-]", "_", repo_name).lower()
        return owner, repo_name, repo_id

    parts = [p for p in cleaned.split("/") if p]
    repo_name = parts[-1] if parts else "repo"
    repo_id = re.sub(r"[^\w.-]", "_", repo_name).lower()
    return None, repo_name, repo_id


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
        self.discovered_components = self._discover_initial_components()

    def _discover_initial_components(self) -> List[str]:
        if self.component_map:
            return sorted(list(set(self.component_map.values())))
        profiler = RepositoryProfiler(self.config)
        return profiler.discover_components(self.repo_dir)

    def _load_component_map(self) -> Dict[str, str]:
        if self.config.component_rules_file and os.path.exists(self.config.component_rules_file):
            try:
                with open(self.config.component_rules_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("rules", {})
            except Exception as e:
                logger.warning(f"Error loading component rules: {e}")
        return {}

    def ensure_repository_ready(self) -> bool:
        """
        Ensures the repository is cloned, commits are extracted, and metadata is populated.
        """
        os.makedirs(self.repo_dir, exist_ok=True)
        # 1. Clone if remote URL provided and local files missing
        self.clone_if_needed()

        # 2. Refresh discovered components now that repo is cloned
        self.discovered_components = self._discover_initial_components()

        # 3. Ensure commits exist (via commits.json or git log)
        self.ensure_git_history()

        # 4. Ensure issues and PRs exist (via GitHub API or commit synthesis)
        self.ensure_github_metadata()

        return True

    def clone_if_needed(self) -> bool:
        git_dir = os.path.join(self.repo_dir, ".git")
        if os.path.exists(git_dir):
            return True
        if os.path.exists(self.repo_dir) and any(f.endswith(".py") for _, _, files in os.walk(self.repo_dir) for f in files):
            return True

        url = self.config.repository_url
        if not url or "mock" in url or not (url.startswith("http://") or url.startswith("https://") or url.startswith("git@")):
            logger.info(f"No remote URL to clone for {self.config.repository_id}")
            return False

        logger.info(f"Cloning {url} into {self.repo_dir}...")
        try:
            # Try fast shallow clone with depth=100
            git.Repo.clone_from(url, self.repo_dir, depth=100)
            logger.info(f"Successfully shallow-cloned {url} (depth=100)")
            return True
        except Exception as e:
            logger.warning(f"Shallow clone failed ({e}), attempting standard clone...")
            try:
                git.Repo.clone_from(url, self.repo_dir)
                logger.info(f"Successfully cloned {url}")
                return True
            except Exception as ex:
                logger.error(f"Clone failed: {ex}")
                return False

    def ensure_git_history(self, max_commits: int = 100):
        commits_file = os.path.join(self.repo_dir, "commits.json")
        if os.path.exists(commits_file):
            return

        git_dir = os.path.join(self.repo_dir, ".git")
        if not os.path.exists(git_dir):
            return

        logger.info(f"Extracting git history for {self.config.repository_id}...")
        commits = []
        try:
            repo = git.Repo(self.repo_dir)
            for c in repo.iter_commits(max_count=max_commits):
                try:
                    files = list(c.stats.files.keys())
                except Exception:
                    files = []

                diff_text = ""
                try:
                    if c.parents:
                        diffs = c.diff(c.parents[0], create_patch=True)
                        chunks = []
                        for d in diffs[:3]:
                            if d.diff:
                                text = d.diff.decode("utf-8", errors="ignore") if isinstance(d.diff, bytes) else str(d.diff)
                                chunks.append(text[:300])
                        diff_text = "\n".join(chunks)
                except Exception:
                    pass

                commits.append({
                    "sha": c.hexsha,
                    "author": f"{c.author.name} <{c.author.email}>",
                    "timestamp": datetime.fromtimestamp(c.committed_date, tz=timezone.utc).isoformat(),
                    "message": c.message.strip(),
                    "files": files,
                    "diff": diff_text[:1500]
                })

            if commits:
                with open(commits_file, "w", encoding="utf-8") as f:
                    json.dump(commits, f, indent=2)
                logger.info(f"Saved {len(commits)} commits to {commits_file}")
        except Exception as e:
            logger.warning(f"Could not extract commits from git repo: {e}")

    def ensure_github_metadata(self):
        issues_file = os.path.join(self.repo_dir, "issues.json")
        prs_file = os.path.join(self.repo_dir, "prs.json")
        if os.path.exists(issues_file) and os.path.exists(prs_file):
            return

        url = self.config.repository_url
        owner, repo_name, _ = parse_github_url(url)
        issues = []
        prs = []

        if owner and repo_name:
            issues, prs = self._fetch_github_api_metadata(owner, repo_name)

        # Fallback to synthesizing issues and PRs from commit messages if remote API not available
        if not issues and not prs:
            issues, prs = self._synthesize_metadata_from_commits()

        if issues and not os.path.exists(issues_file):
            with open(issues_file, "w", encoding="utf-8") as f:
                json.dump(issues, f, indent=2)

        if prs and not os.path.exists(prs_file):
            with open(prs_file, "w", encoding="utf-8") as f:
                json.dump(prs, f, indent=2)

    def _fetch_github_api_metadata(self, owner: str, repo_name: str, max_items: int = 30) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        issues = []
        prs = []
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}/issues?state=all&per_page={max_items}"
        headers = {"User-Agent": "HistoryRAG-Ingest/1.0"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=7) as response:
                if response.status == 200:
                    raw = json.loads(response.read().decode("utf-8"))
                    for item in raw:
                        num = item.get("number")
                        title = item.get("title", "")
                        body = item.get("body", "") or ""
                        created_at = item.get("created_at")
                        updated_at = item.get("updated_at")
                        labels = [l.get("name", "") for l in item.get("labels", [])]
                        state = item.get("state", "closed")

                        if "pull_request" in item:
                            prs.append({
                                "id": f"pr-{num}",
                                "number": num,
                                "title": title,
                                "body": body[:2000],
                                "created_at": created_at,
                                "updated_at": updated_at,
                                "state": state,
                                "merged": state == "closed",
                                "files_changed": []
                            })
                        else:
                            issues.append({
                                "id": f"issue-{num}",
                                "number": num,
                                "title": title,
                                "body": body[:2000],
                                "created_at": created_at,
                                "updated_at": updated_at,
                                "state": state,
                                "labels": labels,
                                "comments": []
                            })
                    logger.info(f"Fetched {len(issues)} issues and {len(prs)} PRs from GitHub API for {owner}/{repo_name}")
        except Exception as e:
            logger.info(f"GitHub API fetch skipped or rate-limited for {owner}/{repo_name}: {e}")

        return issues, prs

    def _synthesize_metadata_from_commits(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        commits_file = os.path.join(self.repo_dir, "commits.json")
        if not os.path.exists(commits_file):
            return [], []

        try:
            with open(commits_file, "r", encoding="utf-8") as f:
                commits = json.load(f)
        except Exception:
            return [], []

        issues = []
        prs = []
        seen_issues = set()
        seen_prs = set()

        for c in commits:
            msg = c.get("message", "")
            sha = c.get("sha", "")
            ts = c.get("timestamp", datetime.now(timezone.utc).isoformat())
            files = c.get("files", [])
            primary_comp = self.map_file_to_component(files[0]) if files else "core"

            # Check PR pattern: e.g. "Merge pull request #123" or "(#123)"
            pr_match = re.search(r"(?:pull request #|PR #|\(#)(\d+)\)?", msg, re.IGNORECASE)
            if pr_match:
                pr_num = pr_match.group(1)
                if pr_num not in seen_prs:
                    seen_prs.add(pr_num)
                    prs.append({
                        "id": f"pr-{pr_num}",
                        "title": msg.split("\n")[0][:100],
                        "body": msg,
                        "component": primary_comp,
                        "created_at": ts,
                        "merged": True,
                        "merge_commit_sha": sha,
                        "files_changed": files
                    })

            # Check issue pattern: e.g. "Fixes #45" or "closes #45" or "issue #45"
            issue_match = re.search(r"(?:fix(?:es)?|close(?:s)?|resolve(?:s)?|issue) #?(\d+)", msg, re.IGNORECASE)
            if issue_match:
                issue_num = issue_match.group(1)
                if issue_num not in seen_issues and issue_num not in seen_prs:
                    seen_issues.add(issue_num)
                    issues.append({
                        "id": f"issue-{issue_num}",
                        "title": msg.split("\n")[0][:100],
                        "body": f"Developer issue discussion regarding: {msg}",
                        "component": primary_comp,
                        "created_at": ts,
                        "state": "closed",
                        "labels": ["enhancement", primary_comp],
                        "comments": []
                    })

        return issues, prs

    def map_file_to_component(self, file_path: str) -> str:
        norm_path = file_path.replace("\\", "/")
        # 1. Match against explicit component map rules if present
        for prefix, comp in self.component_map.items():
            if norm_path.startswith(prefix) or f"/{prefix}" in norm_path:
                return comp

        # 2. Match against discovered components
        for comp in self.discovered_components:
            if f"/{comp}/" in norm_path or norm_path.startswith(f"{comp}/"):
                return comp
            filename = os.path.basename(norm_path).split(".")[0]
            if filename == comp:
                return comp

        # 3. Dynamic heuristic fallback based on path segments
        parts = [p for p in norm_path.split("/") if p and p not in ("tests", "test", "src", "app", "lib", "source")]
        if len(parts) > 1:
            # If parts[0] is repo name or common root, take next segment
            if parts[0] in (self.config.repository_id, "netbox", "src"):
                return parts[1].split(".")[0]
            return parts[0]
        elif len(parts) == 1:
            name = parts[0].split(".")[0]
            return name if name not in ("__init__", "conftest") else "core"
        return "core"

    def is_test_file(self, file_path: str) -> bool:
        norm_path = file_path.replace("\\", "/").lower()
        filename = os.path.basename(norm_path)
        if "/tests/" in norm_path or norm_path.startswith("tests/") or "/test/" in norm_path or norm_path.startswith("test/"):
            return True
        if filename.startswith("test_") or filename.endswith("_test.py") or ".test." in filename or ".spec." in filename:
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
        self.ensure_repository_ready()
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
            ignored_dirs = {
                ".git", ".github", "node_modules", "venv", ".venv", "__pycache__",
                "build", "dist", ".pytest_cache", ".tox", "egg-info", "site-packages"
            }
            code_extensions = (
                ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".cpp", ".c", ".h", ".rs",
                ".md", ".txt", ".yml", ".yaml", ".json"
            )
            for root, dirs, files in os.walk(self.repo_dir):
                dirs[:] = [d for d in dirs if d not in ignored_dirs and not d.endswith(".egg-info")]
                for file in files:
                    if file in ("commits.json", "issues.json", "prs.json", "metadata.db"):
                        continue
                    if file.endswith(code_extensions):
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
            if re.search(r"\b" + re.escape(comp.lower()) + r"\b", text_lower):
                return comp
        for comp in self.discovered_components:
            if re.search(r"\b" + re.escape(comp.lower()) + r"\b", text_lower):
                return comp
        return "core"
