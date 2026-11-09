import json
import re
import uuid
from functools import lru_cache
from pathlib import Path

import chromadb
import pymupdf
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain_groq import ChatGroq

from app.config import settings
from app.models import SourceChunk

MAX_WORDS = 800
OVERLAP = 160
MIN_SCORE = 0.25


@lru_cache(maxsize=1)
def vector_client():
    Path(settings.chroma_path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=settings.chroma_path)


@lru_cache(maxsize=1)
def embedding_function():
    return SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")


def collection_for(user_id: int):
    return vector_client().get_or_create_collection(
        name=f"student_{user_id}",
        embedding_function=embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def llm(api_key: str | None = None):
    configured_key = api_key or settings.groq_api_key
    if not configured_key:
        raise RuntimeError("AI is not configured. Enter a Groq API key in Settings.")
    return ChatGroq(model=settings.llm_model, api_key=configured_key, temperature=0)


def llm_json(prompt: str, api_key: str | None = None):
    text = llm(api_key).invoke(prompt, max_tokens=6144).content
    if not isinstance(text, str):
        text = "".join(str(part.get("text", "")) for part in text if isinstance(part, dict))
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("The AI provider returned incomplete or invalid JSON.") from exc


def extract_pages(path: Path) -> list[tuple[int, str]]:
    if path.suffix.lower() == ".pdf":
        with pymupdf.open(path) as pdf:
            return [(index + 1, page.get_text()) for index, page in enumerate(pdf)]
    return [(1, path.read_text(encoding="utf-8", errors="replace"))]


def split_pages(pages: list[tuple[int, str]]) -> list[dict]:
    chunks = []
    for page_number, text in pages:
        words = text.split()
        start = 0
        while start < len(words):
            part = words[start : start + MAX_WORDS]
            body = " ".join(part).strip()
            if body:
                heading = next(
                    (line.strip(" #:\t") for line in body.splitlines() if re.match(r"^\s*(chapter|section)\b", line, re.I)),
                    "",
                )
                chunks.append({"id": uuid.uuid4().hex, "text": body, "page": page_number, "section": heading})
            if start + MAX_WORDS >= len(words):
                break
            start += MAX_WORDS - OVERLAP
    return chunks


def index_chunks(user_id: int, document_id: int, filename: str, chunks: list[dict], db):
    collection = collection_for(user_id)
    collection.add(
        ids=[chunk["id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[
            {
                "document_id": document_id,
                "filename": filename,
                "page": chunk["page"],
                "section": chunk["section"],
            }
            for chunk in chunks
        ],
    )
    db.add_all(
        [
            SourceChunk(
                id=chunk["id"],
                document_id=document_id,
                text=chunk["text"],
                page=chunk["page"],
                section=chunk["section"],
            )
            for chunk in chunks
        ]
    )


def retrieve(user_id: int, query: str, count: int = 6, topic: str | None = None):
    collection = collection_for(user_id)
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[query], n_results=min(count, collection.count()))
    found = []
    for chunk_id, text, metadata, distance in zip(
        result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        score = 1 - distance
        if score < MIN_SCORE:
            continue
        if topic and topic.casefold() not in text.casefold() and topic.casefold() not in metadata["filename"].casefold():
            continue
        found.append({"id": chunk_id, "text": text, "metadata": metadata, "score": score})
    return found


def render_citation(chunk: dict) -> str:
    metadata = chunk["metadata"]
    pieces = [metadata.get("filename", "uploaded material")]
    if metadata.get("section"):
        pieces.append(metadata["section"])
    pieces.append(f"Page {metadata.get('page', 1)}")
    return "Source: " + ", ".join(pieces)


def remove_document_vectors(user_id: int, chunk_ids: list[str]):
    if chunk_ids:
        collection_for(user_id).delete(ids=chunk_ids)
