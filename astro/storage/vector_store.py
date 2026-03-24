from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional


class VectorStore:
    """Pluggable vector store; optional chromadb when extra installed."""

    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_dir = persist_dir
        self._client = None

    def _ensure_client(self) -> None:
        if self._client is not None:
            return
        try:
            import chromadb  # type: ignore

            path = self.persist_dir or Path(".chromadb")
            path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(path))
        except ImportError:
            self._client = False

    def upsert(self, collection: str, ids: List[str], documents: List[str], metadatas: Optional[List[Dict]] = None) -> None:
        self._ensure_client()
        if not self._client:
            return
        col = self._client.get_or_create_collection(collection)
        col.add(ids=ids, documents=documents, metadatas=metadatas)

    def query(self, collection: str, text: str, n: int = 5) -> List[Dict[str, Any]]:
        self._ensure_client()
        if not self._client:
            return []
        col = self._client.get_or_create_collection(collection)
        res = col.query(query_texts=[text], n_results=n)
        out: List[Dict[str, Any]] = []
        if res.get("documents") and res["documents"][0]:
            for i, doc in enumerate(res["documents"][0]):
                out.append(
                    {
                        "document": doc,
                        "metadata": (res.get("metadatas") or [[]])[0][i]
                        if res.get("metadatas")
                        else {},
                        "distance": (res.get("distances") or [[]])[0][i]
                        if res.get("distances")
                        else None,
                    }
                )
        return out
