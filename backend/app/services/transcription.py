from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

import torch

from app.config import settings
from app.services.intelligence import identify_roles
from app.services.models import get_diarization, get_whisper

logger = logging.getLogger("saleslens.transcription")


def _merge_turns(
    turns: list[tuple[float, float, str]],
    gap: float,
) -> list[tuple[float, float, str]]:
    if not turns:
        return []

    turns.sort(key=lambda t: t[0])
    merged = [turns[0]]

    for start, end, label in turns[1:]:
        prev_start, prev_end, prev_label = merged[-1]
        if label == prev_label and (start - prev_end) <= gap:
            merged[-1] = (prev_start, max(prev_end, end), prev_label)
        else:
            merged.append((start, end, label))

    return merged


def _normalize_speaker_bounds() -> tuple[int, int]:
    min_speakers = max(1, int(settings.diarization_min_speakers))
    max_speakers = max(min_speakers, int(settings.diarization_max_speakers))
    return min_speakers, max_speakers


def _collect_turns(diarization: Any) -> list[tuple[float, float, str]]:
    turns = []

    # pyannote 4.x returns a DiarizeOutput dataclass.
    # The actual Annotation lives in .speaker_diarization
    if hasattr(diarization, "speaker_diarization"):
        ann = diarization.speaker_diarization
        for turn, _, speaker in ann.itertracks(yield_label=True):
            turns.append((float(turn.start), float(turn.end), str(speaker)))
    elif hasattr(diarization, "itertracks"):
        # pyannote 3.x returns an Annotation directly
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turns.append((float(turn.start), float(turn.end), str(speaker)))
    else:
        # Fallback: use serialize() if available
        try:
            data = diarization.serialize()
            for item in data.get("diarization", []):
                turns.append((float(item["start"]), float(item["end"]), str(item["speaker"])))
        except Exception:
            logger.warning("Could not parse diarization output: %s", type(diarization))

    return turns


def _overlap_duration(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def _nearest_label(
    start: float, end: float, turns: list[tuple[float, float, str]]
) -> str | None:
    if not turns:
        return None

    midpoint = (start + end) / 2.0
    best_label = None
    best_distance = float("inf")
    for t_start, t_end, label in turns:
        if t_start <= midpoint <= t_end:
            return label
        distance = min(abs(midpoint - t_start), abs(midpoint - t_end))
        if distance < best_distance:
            best_distance = distance
            best_label = label
    return best_label


def _assign_label_for_span(
    start: float,
    end: float,
    turns: list[tuple[float, float, str]],
    min_overlap_ratio: float,
) -> tuple[str | None, float]:
    if not turns:
        return None, 0.0

    duration = max(0.001, end - start)
    best_label = None
    best_overlap = 0.0
    for t_start, t_end, label in turns:
        ov = _overlap_duration(start, end, t_start, t_end)
        if ov > best_overlap:
            best_overlap = ov
            best_label = label

    overlap_ratio = best_overlap / duration
    if best_label is not None and overlap_ratio >= min_overlap_ratio:
        return best_label, overlap_ratio

    return _nearest_label(start, end, turns), overlap_ratio


def _speakerize_with_words(
    segment: dict,
    turns: list[tuple[float, float, str]],
) -> list[dict]:
    words = segment.get("words") or []
    if not words:
        return []

    chunks = []
    current_label: str | None = None
    current_tokens: list[str] = []
    chunk_start = 0.0
    chunk_end = 0.0

    for word in words:
        w_start = float(word["start_time"])
        w_end = float(word["end_time"])
        token = str(word["text"])
        label, _ = _assign_label_for_span(w_start, w_end, turns, min_overlap_ratio=0.0)
        label = label or "Speaker"

        if current_label is None:
            current_label = label
            chunk_start = w_start
            chunk_end = w_end
            current_tokens = [token]
            continue

        if label == current_label:
            current_tokens.append(token)
            chunk_end = w_end
            continue

        text = "".join(current_tokens).strip()
        if text:
            chunks.append(
                {
                    "speaker": current_label,
                    "text": text,
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                }
            )

        current_label = label
        chunk_start = w_start
        chunk_end = w_end
        current_tokens = [token]

    if current_label is not None and current_tokens:
        text = "".join(current_tokens).strip()
        if text:
            chunks.append(
                {
                    "speaker": current_label,
                    "text": text,
                    "start_time": chunk_start,
                    "end_time": chunk_end,
                }
            )

    return chunks


def _apply_role_mapping(
    segments: list[dict], turns: list[tuple[float, float, str]]
) -> list[dict]:
    if not segments:
        return segments

    role_map = identify_roles(segments)
    if role_map:
        for seg in segments:
            seg["speaker"] = role_map.get(seg["speaker"], seg["speaker"])
        return segments

    labels = sorted(set(label for _, _, label in turns))
    if len(labels) >= 2:
        fallback = {labels[0]: "Agent", labels[1]: "Customer"}
        for i, label in enumerate(labels[2:], start=3):
            fallback[label] = f"Speaker {i}"
        for seg in segments:
            seg["speaker"] = fallback.get(seg["speaker"], seg["speaker"])
    elif labels:
        for seg in segments:
            if seg["speaker"] == labels[0]:
                seg["speaker"] = "Agent"

    return segments


def _emit_diarization_metrics(
    segments: list[dict], turns: list[tuple[float, float, str]]
) -> None:
    if not settings.diarization_debug_metrics:
        return

    speakers = sorted(set(label for _, _, label in turns))
    unassigned = sum(1 for s in segments if str(s.get("speaker", "")).startswith("Speaker"))
    switches = 0
    prev = None
    for s in segments:
        curr = s.get("speaker")
        if prev is not None and curr != prev:
            switches += 1
        prev = curr

    total = max(1, len(segments))
    logger.info(
        "Diarization metrics: speakers=%d segments=%d unassigned_ratio=%.3f switch_rate=%.3f",
        len(speakers),
        len(segments),
        unassigned / total,
        switches / total,
    )


def apply_diarization(audio_path: str, segments: list[dict]) -> list[dict]:
    pipeline = get_diarization()
    if pipeline is None:
        return segments

    min_speakers, max_speakers = _normalize_speaker_bounds()
    try:
        import soundfile as sf
        import torch
        data, sample_rate = sf.read(audio_path, dtype="float32")
        if data.ndim == 1:
            data = data.reshape(-1, 1)
        waveform = torch.from_numpy(data).T
        
        diarization = pipeline(
            {"waveform": waveform, "sample_rate": sample_rate},
            min_speakers=min_speakers,
            max_speakers=max_speakers,
        )
    except Exception:
        logger.exception("Diarization failed - falling back to heuristic")
        return segments

    raw_turns = _collect_turns(diarization)
    if not raw_turns:
        return segments

    turns = _merge_turns(raw_turns, gap=settings.diarization_merge_gap_sec)

    diarized_segments: list[dict] = []
    for seg in segments:
        if settings.diarization_enable_word_level and seg.get("words"):
            diarized_segments.extend(_speakerize_with_words(seg, turns))
            continue

        label, _ = _assign_label_for_span(
            float(seg["start_time"]),
            float(seg["end_time"]),
            turns,
            min_overlap_ratio=settings.diarization_min_overlap_ratio,
        )
        diarized_segments.append(
            {
                "speaker": label or seg.get("speaker", "Speaker"),
                "text": seg["text"],
                "start_time": float(seg["start_time"]),
                "end_time": float(seg["end_time"]),
            }
        )

    diarized_segments = _apply_role_mapping(diarized_segments, turns)
    _emit_diarization_metrics(diarized_segments, turns)
    return diarized_segments


def transcribe_segments(audio_path: str) -> tuple[list[dict], str]:
    model = get_whisper()

    with torch.inference_mode():
        segments_raw, info = model.transcribe(
            audio_path,
            vad_filter=settings.whisper_vad_filter,
            language=None,
            beam_size=settings.whisper_beam_size,
            initial_prompt=settings.whisper_initial_prompt,
            word_timestamps=settings.diarization_enable_word_level,
        )

        out = []
        for seg in segments_raw:
            text = seg.text.strip()
            if text:
                words = []
                for w in (getattr(seg, "words", None) or []):
                    token = str(getattr(w, "word", "") or "")
                    if not token.strip():
                        continue
                    start = float(getattr(w, "start", seg.start))
                    end = float(getattr(w, "end", seg.end))
                    words.append(
                        {
                            "text": token,
                            "start_time": start,
                            "end_time": end,
                        }
                    )
                out.append(
                    {
                        "speaker": "Speaker",
                        "text": text,
                        "start_time": float(seg.start),
                        "end_time": float(seg.end),
                        "words": words,
                    }
                )

    out = apply_diarization(audio_path, out)
    for seg in out:
        seg.pop("words", None)
    return out, getattr(info, "language", "auto")


def stream_segments(segments: list[dict]) -> Generator[dict, None, None]:
    total = max(len(segments), 1)
    for idx, segment in enumerate(segments, start=1):
        words = segment["text"].split()
        rolling = []
        for w in words:
            rolling.append(w)
            partial_text = " ".join(rolling)
            yield {
                "type": "transcript_segment",
                "is_partial": True,
                "progress": int(((idx - 1) / total) * 100),
                "segment": {
                    "speaker": segment["speaker"],
                    "text": partial_text,
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                },
            }
        yield {
            "type": "transcript_segment",
            "is_partial": False,
            "progress": int((idx / total) * 100),
            "segment": segment,
        }
