from __future__ import annotations

from app.services.intelligence import run_intelligence
from app.services.rag import build_or_load_index, chunk_transcript


class CallProcessingGraph:
    """Orchestrator: insights -> rag_index -> finalize."""

    def __init__(self, segments: list[dict], call_id: str) -> None:
        self.state: dict = {
            "segments": segments,
            "call_id": call_id,
            "symptoms": [],
            "prescriptions": [],
            "follow_ups": [],
            "soap_note": {},
            "patient_sentiment": [],
            "index_ready": False,
        }

    def insights_node(self) -> None:
        result = run_intelligence(self.state["segments"])
        self.state["symptoms"] = result.get("symptoms", [])
        self.state["prescriptions"] = result.get("prescriptions", [])
        self.state["follow_ups"] = result.get("follow_ups", [])
        self.state["soap_note"] = result.get("soap_note", {})
        self.state["patient_sentiment"] = result.get("patient_sentiment", [])

    def rag_index_node(self) -> None:
        chunks = chunk_transcript(self.state["segments"])
        build_or_load_index(self.state["call_id"], chunks)
        self.state["index_ready"] = True

    def run(self) -> dict:
        self.insights_node()
        self.rag_index_node()
        return self.state
