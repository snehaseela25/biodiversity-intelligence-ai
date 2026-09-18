import json
import re
from pathlib import Path
from typing import List, Dict, Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings
from app.models.db import SessionLocal, Document, Chunk


class BiodiversityRetriever:
    """
    Lightweight local RAG retriever.

    It uses TF-IDF locally so the project can run without:
    - an external vector database
    - an embedding API
    - an LLM API

    The architecture can later be migrated to PostgreSQL + pgvector.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2)
        )

        self.documents: List[Dict[str, Any]] = []
        self.matrix = None

    def load_documents(self):
        """Load knowledge documents from the database."""

        db = SessionLocal()

        try:
            rows = db.query(Document).all()

            self.documents = [
                {
                    "id": row.id,
                    "title": row.title,
                    "source": row.source,
                    "year": row.year,
                    "topic": row.topic,
                    "url": row.url,
                    "text": row.text,
                }
                for row in rows
            ]

        finally:
            db.close()

        self._build_index()

    def _build_index(self):
        """Create the local TF-IDF index."""

        if not self.documents:
            self.matrix = None
            return

        texts = [
            f"{doc['title']} {doc['topic'] or ''} {doc['text']}"
            for doc in self.documents
        ]

        self.matrix = self.vectorizer.fit_transform(texts)

    def ingest_jsonl(self, filepath: Path) -> int:
        """
        Import scientific knowledge from a JSONL file.

        Each line should contain:
        title, source, year, topic, url, text
        """

        db = SessionLocal()
        count = 0

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()

                    if not line:
                        continue

                    item = json.loads(line)

                    title = item.get("title", "Untitled")
                    source = item.get("source", "Unknown")
                    year = item.get("year")
                    topic = item.get("topic")
                    url = item.get("url")
                    text = item.get("text", "")

                    existing = (
                        db.query(Document)
                        .filter(
                            Document.title == title,
                            Document.source == source
                        )
                        .first()
                    )

                    if existing:
                        continue

                    document = Document(
                        title=title,
                        source=source,
                        year=year,
                        topic=topic,
                        url=url,
                        text=text
                    )

                    db.add(document)
                    db.flush()

                    # Simple chunking for the RAG layer
                    chunks = self._chunk_text(text)

                    for chunk_text in chunks:
                        db.add(
                            Chunk(
                                document_id=document.id,
                                chunk_text=chunk_text
                            )
                        )

                    count += 1

            db.commit()

        finally:
            db.close()

        self.load_documents()

        return count

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 700) -> List[str]:
        """Split text into manageable retrieval chunks."""

        words = text.split()

        if not words:
            return []

        chunks = []

        for start in range(0, len(words), chunk_size):
            chunk = " ".join(words[start:start + chunk_size])
            chunks.append(chunk)

        return chunks

    def search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve the most relevant scientific documents."""

        if not self.documents:
            self.load_documents()

        if not self.documents or self.matrix is None:
            return []

        query_vector = self.vectorizer.transform([query])

        similarities = cosine_similarity(
            query_vector,
            self.matrix
        )[0]

        ranked_indexes = similarities.argsort()[::-1][:top_k]

        results = []

        for index in ranked_indexes:
            score = float(similarities[index])

            # Ignore completely unrelated documents
            if score <= 0:
                continue

            document = dict(self.documents[index])

            document["score"] = round(score, 4)

            results.append(document)

        return results


retriever = BiodiversityRetriever()