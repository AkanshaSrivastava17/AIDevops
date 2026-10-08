"""
Generic fallback layer: Path-based chunking and regex test discovery.
Used when Python-specific evidence is unavailable (Limited Mode, Section 3.4.1).
"""
import re
from typing import List, Tuple
from app.ingestion.schema import NormalizedDocument, DocumentType, EventType


class GenericFallbackAdapter:
    def __init__(self, chunk_size: int = 60, overlap: int = 15):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_file(
        self,
        file_path: str,
        content: str,
        repo_id: str,
        component: str,
        timestamp: str
    ) -> List[NormalizedDocument]:
        lines = content.splitlines()
        chunks: List[NormalizedDocument] = []
        
        if not lines:
            return chunks

        is_test = bool(
            re.search(r"(?:tests?/|test_.*|_test\..*)", file_path, re.IGNORECASE)
        )
        doc_type = DocumentType.TEST if is_test else DocumentType.CODE
        event_type = EventType.TEST_CHANGE if is_test else EventType.CODE_CHUNK

        start = 0
        chunk_idx = 0
        while start < len(lines):
            end = min(start + self.chunk_size, len(lines))
            chunk_text = "\n".join(lines[start:end])
            
            doc = NormalizedDocument(
                document_id=f"generic-{file_path}-c{chunk_idx}",
                repository_id=repo_id,
                type=doc_type,
                path=file_path,
                component=component,
                event_timestamp=timestamp,
                event_type=event_type,
                title=f"{file_path} (lines {start+1}-{end})",
                content=chunk_text,
                metadata={
                    "start_line": start + 1,
                    "end_line": end,
                    "ast_parsed": False,
                    "is_test": is_test
                }
            )
            chunks.append(doc)
            chunk_idx += 1
            if end == len(lines):
                break
            start += (self.chunk_size - self.overlap)

        return chunks
