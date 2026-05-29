import uuid
from datetime import datetime

from pydantic import BaseModel


class UploadResponse(BaseModel):
    call_id: uuid.UUID
    status: str


class QueryRequest(BaseModel):
    question: str


class TranscriptOut(BaseModel):
    speaker: str
    text: str
    start_time: float
    end_time: float


class ClinicalInsightOut(BaseModel):
    symptoms: list[dict]
    prescriptions: list[dict]
    follow_ups: list[dict]
    soap_note: dict
    patient_sentiment: list[dict]


class CallOut(BaseModel):
    id: uuid.UUID
    filename: str
    language: str
    duration: float
    created_at: datetime
