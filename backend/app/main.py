from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, get_db
from app.models import Call, ClinicalInsight, Transcript
from app.schemas import CallOut, QueryRequest, UploadResponse
from app.services.models import (
    clear_gpu_cache,
    get_diarization,
    get_whisper,
)
from app.services.orchestrator import CallProcessingGraph
from app.services.rag import query_transcript
from app.services.redis_state import (
    append_event,
    get_events_since,
    get_state,
    set_state,
)
from app.services.transcription import stream_segments, transcribe_segments

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s"
)
logger = logging.getLogger("saleslens")

app = FastAPI(title="SalesLens API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    logger.info("Pre-loading models on %s ...", settings.whisper_device)
    try:
        get_whisper()
    except Exception:
        logger.exception("Failed to preload Whisper model")
    try:
        get_diarization()
    except Exception:
        logger.exception("Failed to preload diarization pipeline")
    logger.info("Model preloading complete.")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/calls/upload", response_model=UploadResponse)
async def upload_call(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> UploadResponse:
    call = Call(filename=file.filename, language="auto", duration=0.0)
    db.add(call)
    db.commit()
    db.refresh(call)

    out_path = Path(settings.upload_dir) / f"{call.id}_{file.filename}"
    content = await file.read()
    out_path.write_bytes(content)
    set_state(str(call.id), {"status": "queued", "progress": 0, "segments": []})
    
    # Start the heavy processing entirely in the background
    background_tasks.add_task(process_call_bg, str(call.id), str(out_path))
    
    return UploadResponse(call_id=call.id, status="queued")


async def process_call_bg(call_id: str, audio_path: str) -> None:
    # Only start if not already processing
    state = get_state(call_id)
    if state and state.get("status") == "processing":
        return

    set_state(call_id, {"status": "processing", "progress": 1, "segments": [], "last_seq": 0})
    append_event(call_id, {"type": "status", "status": "processing", "progress": 1})

    db = SessionLocal()
    try:
        segments, language = await asyncio.to_thread(transcribe_segments, audio_path)

        call = db.get(Call, uuid.UUID(call_id))
        if call:
            call.language = language or "auto"
            if segments:
                call.duration = float(segments[-1]["end_time"])
            db.commit()

        for event in stream_segments(segments):
            seg = event["segment"]
            if not event.get("is_partial", False):
                db.add(
                    Transcript(
                        call_id=uuid.UUID(call_id),
                        speaker=seg["speaker"],
                        text=seg["text"],
                        start_time=seg["start_time"],
                        end_time=seg["end_time"],
                    )
                )
                db.commit()
            seq = append_event(call_id, event)
            set_state(call_id, {"status": "processing", "progress": event["progress"], "last_seq": seq})

        pipeline = CallProcessingGraph(segments=segments, call_id=call_id)
        pipeline_state = await asyncio.to_thread(pipeline.run)

        symptoms = pipeline_state.get("symptoms", [])
        prescriptions = pipeline_state.get("prescriptions", [])
        follow_ups = pipeline_state.get("follow_ups", [])
        soap_note = pipeline_state.get("soap_note", {})
        patient_sentiment = pipeline_state.get("patient_sentiment", [])

        insight = db.query(ClinicalInsight).filter(ClinicalInsight.call_id == uuid.UUID(call_id)).first()
        if insight is None:
            insight = ClinicalInsight(
                call_id=uuid.UUID(call_id),
                symptoms=symptoms,
                prescriptions=prescriptions,
                follow_ups=follow_ups,
                soap_note=soap_note,
                patient_sentiment=patient_sentiment,
            )
            db.add(insight)
        else:
            insight.symptoms = symptoms
            insight.prescriptions = prescriptions
            insight.follow_ups = follow_ups
            insight.soap_note = soap_note
            insight.patient_sentiment = patient_sentiment
        db.commit()

        clear_gpu_cache()
        
        seq = append_event(call_id, {"type": "status", "status": "completed", "progress": 100})
        append_event(call_id, {"type": "completed"})
        set_state(call_id, {"status": "completed", "progress": 100, "segments": segments, "last_seq": seq})

    except Exception as e:
        logger.exception("Background processing failed")
        append_event(call_id, {"type": "error", "message": "Processing failed: " + str(e)})
        set_state(call_id, {"status": "error", "progress": 100})
    finally:
        db.close()


@app.websocket("/calls/{call_id}/stream")
async def stream_call(call_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    since_seq = int(websocket.query_params.get("since_seq", "0"))
    last_sent_seq = since_seq

    try:
        while True:
            state = get_state(call_id)
            if not state:
                await websocket.send_json({"type": "error", "message": "Unknown call_id"})
                await websocket.close()
                return

            events = get_events_since(call_id, last_sent_seq)
            for ev in events:
                seq = ev.get("seq")
                if seq is not None:
                    last_sent_seq = max(last_sent_seq, seq)
                await websocket.send_json(ev)
                
                # Close cleanly if we just sent the completed event
                if ev.get("type") == "completed" or ev.get("status") in ("completed", "error"):
                    await websocket.close()
                    return

            # Also check if it's already completed and no new events were found
            if state.get("status") in ("completed", "error"):
                await websocket.close()
                return

            await asyncio.sleep(0.5)
    except Exception:
        # Client disconnected or connection dropped - backend process will keep running!
        pass


@app.get("/calls/{call_id}/insights")
def get_insights(call_id: str, db: Session = Depends(get_db)) -> dict:
    insight = db.query(ClinicalInsight).filter(ClinicalInsight.call_id == uuid.UUID(call_id)).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insights not ready")
    return {
        "symptoms": insight.symptoms or [],
        "prescriptions": insight.prescriptions or [],
        "follow_ups": insight.follow_ups or [],
        "soap_note": insight.soap_note or {},
        "patient_sentiment": insight.patient_sentiment or [],
    }


@app.post("/calls/{call_id}/query")
def query_call(call_id: str, req: QueryRequest, db: Session = Depends(get_db)) -> dict:
    transcripts = (
        db.query(Transcript)
        .filter(Transcript.call_id == uuid.UUID(call_id))
        .order_by(Transcript.start_time)
        .all()
    )
    if not transcripts:
        raise HTTPException(status_code=404, detail="Transcript not found")
    segments = [
        {
            "speaker": t.speaker,
            "text": t.text,
            "start_time": t.start_time,
            "end_time": t.end_time,
        }
        for t in transcripts
    ]
    return query_transcript(call_id, req.question, segments)


@app.get("/calls", response_model=list[CallOut])
def list_calls(db: Session = Depends(get_db)) -> list[CallOut]:
    rows = db.execute(select(Call).order_by(Call.created_at.desc())).scalars().all()
    return [CallOut.model_validate(r, from_attributes=True) for r in rows]
