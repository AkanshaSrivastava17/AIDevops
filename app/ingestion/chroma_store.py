"""
ChromaDB Vector Store wrapper for semantic code and history retrieval.
Follows Section 7.1, 8.2 of the plan.
"""
import os
import logging
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.config import Settings
from app.ingestion.schema import NormalizedDocument

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    def __init__(self, persist_dir: str = "data/processed/chroma"):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )

    def get_or_create_collection(self, repository_id: str):
        collection_name = f"repo_{repository_id.replace('-', '_')}"
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"repository_id": repository_id}
        )

    def index_documents(self, repository_id: str, documents: List[NormalizedDocument], batch_size: int = 100):
        if not documents:
            return
        collection = self.get_or_create_collection(repository_id)
        
        # Batch insert
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            ids = [d.document_id for d in batch]
            texts = [f"{d.title}\n{d.content[:1500]}" for d in batch]
            metadatas = [
                {
                    "repository_id": d.repository_id,
                    "type": d.type.value,
                    "component": d.component,
                    "event_timestamp": d.event_timestamp,
                    "event_type": d.event_type.value,
                    "path": d.path or "",
                    "commit_sha": d.commit_sha or "",
                    "issue_id": d.issue_id or "",
                    "pr_id": d.pr_id or ""
                }
                for d in batch
            ]
            collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        logger.info(f"Indexed {len(documents)} documents into collection for {repository_id}")

    def query(
        self,
        repository_id: str,
        query_text: str,
        top_k: int = 15,
        type_filter: Optional[List[str]] = None,
        component_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        collection = self.get_or_create_collection(repository_id)
        
        # Build where filter
        where_conditions = []
        if type_filter:
            if len(type_filter) == 1:
                where_conditions.append({"type": type_filter[0]})
            else:
                where_conditions.append({"type": {"$in": type_filter}})
        if component_filter:
            where_conditions.append({"component": component_filter})

        where = None
        if len(where_conditions) == 1:
            where = where_conditions[0]
        elif len(where_conditions) > 1:
            where = {"$and": where_conditions}

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=top_k,
                where=where
            )
        except Exception as e:
            logger.warning(f"Chroma query failed, returning empty list: {e}")
            return []

        hits = []
        if results and "ids" in results and results["ids"]:
            ids_list = results["ids"][0]
            docs_list = results.get("documents", [[]])[0]
            metas_list = results.get("metadatas", [[]])[0]
            dists_list = results.get("distances", [[]])[0] if "distances" in results and results["distances"] else [0.0]*len(ids_list)

            for doc_id, text, meta, dist in zip(ids_list, docs_list, metas_list, dists_list):
                hits.append({
                    "document_id": doc_id,
                    "content": text,
                    "metadata": meta,
                    "distance": dist,
                    "similarity": max(0.0, 1.0 - (dist if dist is not None else 0.5))
                })
        return hits
