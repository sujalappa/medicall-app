from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from app.config import settings
from app.services.llm import chat_with_fallback
from app.services.privacy import redact_pii


def chunk_transcript(segments: list[dict], chunk_size: int | None = None) -> list[dict]:
    max_len = chunk_size or settings.transcript_chunk_size
    chunks = []
    buf = []
    buf_len = 0
    start = 0.0
    for s in segments:
        t = s["text"]
        if not buf:
            start = s["start_time"]
        if buf_len + len(t) > max_len and buf:
            chunks.append(
                {
                    "text": " ".join(buf),
                    "start_time": start,
                    "end_time": s["start_time"],
                }
            )
            buf = []
            buf_len = 0
            start = s["start_time"]
        buf.append(t)
        buf_len += len(t)
    if buf:
        chunks.append(
            {
                "text": " ".join(buf),
                "start_time": start,
                "end_time": segments[-1]["end_time"],
            }
        )
    return chunks


def ensure_index_dir() -> None:
    Path(settings.index_dir).mkdir(parents=True, exist_ok=True)


def embed_texts(texts: list[str]) -> np.ndarray:
    import httpx
    url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{settings.embedding_model}"
    headers = {"Authorization": f"Bearer {settings.hf_token}"} if settings.hf_token else {}
    
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
            if resp.status_code == 200:
                data = resp.json()
                return np.array(data, dtype="float32")
            else:
                return np.zeros((len(texts), settings.embedding_dim), dtype="float32")
    except Exception:
        return np.zeros((len(texts), settings.embedding_dim), dtype="float32")


def embed_text(text: str) -> np.ndarray:
    return embed_texts([text])[0]


def build_or_load_index(
    call_id: str, chunks: list[dict]
) -> tuple[faiss.IndexFlatIP, list[dict]]:
    ensure_index_dir()
    index_path = Path(settings.index_dir) / f"{call_id}.faiss"
    meta_path = Path(settings.index_dir) / f"{call_id}.json"
    dim = settings.embedding_dim

    if index_path.exists() and meta_path.exists():
        index = faiss.read_index(str(index_path))
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        return index, metadata

    if chunks:
        texts = [c["text"] for c in chunks]
        vectors = embed_texts(texts)
    else:
        vectors = np.zeros((1, dim), dtype="float32")

    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    metadata = chunks if chunks else [{"text": "", "start_time": 0.0, "end_time": 0.0}]

    faiss.write_index(index, str(index_path))
    meta_path.write_text(json.dumps(metadata), encoding="utf-8")
    return index, metadata


def query_transcript(call_id: str, question: str, segments: list[dict]) -> dict:
    chunks = chunk_transcript(segments)
    index, metadata = build_or_load_index(call_id, chunks)
    query_vec = embed_text(question).reshape(1, -1)
    k = min(5, len(metadata))
    scores, ids = index.search(query_vec, k)
    selected = [metadata[i] for i in ids[0] if i < len(metadata)]
    context = "\n".join(
        f"[{c['start_time']:.2f}-{c['end_time']:.2f}] {c['text']}" for c in selected
    )
    context = redact_pii(context)
    prompt = (
        "You are a clinical call intelligence assistant. Answer only from the provided transcript context. "
        "If unsure, say you are unsure.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    answer, used_model = chat_with_fallback(
        messages=[{"role": "user", "content": prompt}],
        primary_model=settings.hf_model_qa,
        secondary_model=settings.hf_model_analysis,
    )
    citations = [
        {"start_time": c["start_time"], "end_time": c["end_time"]} for c in selected[:3]
    ]
    return {"answer": answer, "citations": citations, "model": used_model}
