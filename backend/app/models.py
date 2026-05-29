import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Call(Base):
    __tablename__ = "calls"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    language: Mapped[str] = mapped_column(String(32), default="auto")
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    transcripts: Mapped[list["Transcript"]] = relationship(back_populates="call", cascade="all, delete-orphan")
    insights: Mapped["ClinicalInsight"] = relationship(back_populates="call", uselist=False, cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    call_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"))
    speaker: Mapped[str] = mapped_column(String(32), default="Unknown")
    text: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, default=0.0)
    end_time: Mapped[float] = mapped_column(Float, default=0.0)
    call: Mapped[Call] = relationship(back_populates="transcripts")


class ClinicalInsight(Base):
    __tablename__ = "clinical_insights"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    call_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("calls.id", ondelete="CASCADE"), unique=True)
    symptoms: Mapped[dict] = mapped_column(JSONB, default=list)
    prescriptions: Mapped[dict] = mapped_column(JSONB, default=list)
    follow_ups: Mapped[dict] = mapped_column(JSONB, default=list)
    soap_note: Mapped[dict] = mapped_column(JSONB, default=dict)
    patient_sentiment: Mapped[dict] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    call: Mapped[Call] = relationship(back_populates="insights")
