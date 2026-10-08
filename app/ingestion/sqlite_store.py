"""
SQLite Structured Metadata Store.
Handles relational lookups, event-level timestamp filtering, and co-change statistics.
"""
import os
import json
import sqlite3
import logging
from typing import List, Dict, Optional, Any, Tuple
from app.ingestion.schema import NormalizedDocument, DocumentType, EventType, DependencyLink

logger = logging.getLogger(__name__)


class SQLiteMetadataStore:
    def __init__(self, db_path: str = "data/processed/metadata.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    repository_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    path TEXT,
                    component TEXT NOT NULL,
                    commit_sha TEXT,
                    issue_id TEXT,
                    pr_id TEXT,
                    event_timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    language TEXT,
                    source_url TEXT,
                    title TEXT,
                    content TEXT,
                    metadata_json TEXT
                )
            """)
            # Co-change events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS co_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id TEXT NOT NULL,
                    commit_sha TEXT NOT NULL,
                    component_a TEXT NOT NULL,
                    component_b TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            # Dependencies table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dependencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id TEXT NOT NULL,
                    source_component TEXT NOT NULL,
                    target_component TEXT NOT NULL,
                    import_statement TEXT NOT NULL,
                    source_file TEXT NOT NULL
                )
            """)
            # Tests table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    repository_id TEXT NOT NULL,
                    test_file TEXT NOT NULL,
                    component TEXT NOT NULL,
                    framework TEXT,
                    UNIQUE(repository_id, test_file)
                )
            """)
            # Indices for rapid querying and timestamp filtering
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_repo_time ON documents(repository_id, event_timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_comp ON documents(repository_id, component)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(repository_id, type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cochange_time ON co_changes(repository_id, timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cochange_comps ON co_changes(repository_id, component_a, component_b)")
            conn.commit()

    def store_documents(self, documents: List[NormalizedDocument]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for doc in documents:
                cursor.execute("""
                    INSERT OR REPLACE INTO documents (
                        document_id, repository_id, type, path, component,
                        commit_sha, issue_id, pr_id, event_timestamp, event_type,
                        language, source_url, title, content, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc.document_id, doc.repository_id, doc.type.value, doc.path, doc.component,
                    doc.commit_sha, doc.issue_id, doc.pr_id, doc.event_timestamp, doc.event_type.value,
                    doc.language, doc.source_url, doc.title, doc.content, json.dumps(doc.metadata)
                ))

                # Track test mapping
                if doc.type == DocumentType.TEST and doc.path:
                    cursor.execute("""
                        INSERT OR IGNORE INTO tests (repository_id, test_file, component, framework)
                        VALUES (?, ?, ?, ?)
                    """, (doc.repository_id, doc.path, doc.component, "pytest"))
            conn.commit()

    def record_co_changes(self, repo_id: str, commit_sha: str, timestamp: str, components: List[str]):
        if len(components) < 2:
            return
        unique_comps = sorted(list(set(components)))
        pairs = []
        for i in range(len(unique_comps)):
            for j in range(i + 1, len(unique_comps)):
                pairs.append((unique_comps[i], unique_comps[j]))
                pairs.append((unique_comps[j], unique_comps[i]))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for comp_a, comp_b in pairs:
                cursor.execute("""
                    INSERT INTO co_changes (repository_id, commit_sha, component_a, component_b, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (repo_id, commit_sha, comp_a, comp_b, timestamp))
            conn.commit()

    def record_dependencies(self, repo_id: str, dependencies: List[DependencyLink]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for dep in dependencies:
                cursor.execute("""
                    INSERT INTO dependencies (repository_id, source_component, target_component, import_statement, source_file)
                    VALUES (?, ?, ?, ?, ?)
                """, (repo_id, dep.source_component, dep.target_component, dep.import_statement, dep.source_file))
            conn.commit()

    def query_documents(
        self,
        repository_id: str,
        max_timestamp: Optional[str] = None,
        types: Optional[List[str]] = None,
        components: Optional[List[str]] = None,
        exclude_ids: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[NormalizedDocument]:
        query = "SELECT * FROM documents WHERE repository_id = ?"
        params: List[Any] = [repository_id]

        # Strict event-level temporal filtering (Section 8.1, 16.3)
        if max_timestamp:
            query += " AND event_timestamp < ?"
            params.append(max_timestamp)

        if types:
            placeholders = ",".join("?" for _ in types)
            query += f" AND type IN ({placeholders})"
            params.extend(types)

        if components:
            placeholders = ",".join("?" for _ in components)
            query += f" AND component IN ({placeholders})"
            params.extend(components)

        if exclude_ids:
            placeholders = ",".join("?" for _ in exclude_ids)
            query += f" AND document_id NOT IN ({placeholders})"
            params.extend(exclude_ids)

        query += " ORDER BY event_timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            docs = []
            for r in rows:
                docs.append(NormalizedDocument(
                    document_id=r["document_id"],
                    repository_id=r["repository_id"],
                    type=DocumentType(r["type"]),
                    path=r["path"],
                    component=r["component"],
                    commit_sha=r["commit_sha"],
                    issue_id=r["issue_id"],
                    pr_id=r["pr_id"],
                    event_timestamp=r["event_timestamp"],
                    event_type=EventType(r["event_type"]),
                    language=r["language"] or "Python",
                    source_url=r["source_url"] or "",
                    title=r["title"] or "",
                    content=r["content"] or "",
                    metadata=json.loads(r["metadata_json"] or "{}")
                ))
            return docs

    def get_co_change_counts(
        self,
        repository_id: str,
        source_component: str,
        max_timestamp: Optional[str] = None
    ) -> Dict[str, int]:
        query = """
            SELECT component_b, COUNT(*) as count
            FROM co_changes
            WHERE repository_id = ? AND component_a = ?
        """
        params: List[Any] = [repository_id, source_component]
        if max_timestamp:
            query += " AND timestamp < ?"
            params.append(max_timestamp)
        query += " GROUP BY component_b"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return {r["component_b"]: r["count"] for r in rows}

    def get_dependencies_for_component(self, repository_id: str, component: str) -> List[Dict[str, Any]]:
        query = """
            SELECT source_component, target_component, import_statement, source_file
            FROM dependencies
            WHERE repository_id = ? AND (source_component = ? OR target_component = ?)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (repository_id, component, component))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_available_tests(self, repository_id: str, component: Optional[str] = None) -> List[str]:
        query = "SELECT DISTINCT test_file FROM tests WHERE repository_id = ?"
        params: List[Any] = [repository_id]
        if component:
            query += " AND component = ?"
            params.append(component)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [r["test_file"] for r in rows]

    def get_repository_stats(self, repository_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT type, COUNT(*) as count FROM documents WHERE repository_id = ? GROUP BY type", (repository_id,))
            type_counts = {r["type"]: r["count"] for r in cursor.fetchall()}
            cursor.execute("SELECT COUNT(DISTINCT component) as count FROM documents WHERE repository_id = ?", (repository_id,))
            comp_count = cursor.fetchone()["count"]
            cursor.execute("SELECT MAX(event_timestamp) as latest FROM documents WHERE repository_id = ?", (repository_id,))
            latest = cursor.fetchone()["latest"]
            return {
                "repository_id": repository_id,
                "counts_by_type": type_counts,
                "total_documents": sum(type_counts.values()),
                "components_count": comp_count,
                "latest_event_time": latest
            }
