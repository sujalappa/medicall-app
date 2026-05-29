from __future__ import annotations

import json
import logging
from textblob import TextBlob

from app.config import settings
from app.services.llm import chat_with_fallback
from app.services.privacy import redact_pii

logger = logging.getLogger("medicall.intelligence")

LLM_INTELLIGENCE_PROMPT = """\
You are an expert clinical documentation assistant. Analyze the following doctor-patient call transcript and return a JSON object with this exact structure:

{{
  "symptoms": [
    {{"text": "description of symptom", "timestamp": 12.5, "speaker": "Patient", "severity": "high|medium|low", "duration": "e.g., 3 days"}}
  ],
  "prescriptions": [
    {{"text": "medication or test ordered", "timestamp": 45.0, "speaker": "Physician"}}
  ],
  "follow_ups": [
    {{"text": "follow-up action or appointment", "timestamp": 60.0, "speaker": "Physician"}}
  ],
  "soap_note": {{
    "subjective": "Patient's subjective description of their issue.",
    "objective": "Objective findings, observations, or lab results mentioned.",
    "assessment": "The physician's diagnosis or overall assessment.",
    "plan": "The treatment plan and next steps."
  }}
}}

Rules:
- Symptoms: Identify any medical symptoms described by the patient. Include the exact text, timestamp, severity, and duration if mentioned.
- Prescriptions: Identify any medications, tests, or lifestyle changes ordered by the physician.
- Follow-ups: Identify any specific follow-up appointments or timelines mentioned.
- SOAP Note: Provide a concise, professional medical summary using the standard Subjective, Objective, Assessment, Plan format.
- If a section has nothing, return an empty list or empty string.

Transcript:
{transcript}
"""


def patient_sentiment_timeline(segments: list[dict]) -> list[dict]:
    out = []
    for s in segments:
        if s["speaker"] == "Patient":
            score = TextBlob(s["text"]).sentiment.polarity
            label = "neutral"
            if score > 0.2:
                label = "relieved"
            elif score < -0.2:
                label = "distressed"
            out.append({"timestamp": s["start_time"], "score": score, "label": label, "speaker": s["speaker"]})
        elif s["speaker"] == "Physician":
            score = TextBlob(s["text"]).sentiment.polarity
            label = "neutral"
            if score > 0.2:
                label = "empathetic/reassuring"
            out.append({"timestamp": s["start_time"], "score": score, "label": label, "speaker": s["speaker"]})
    return out


def llm_intelligence(segments: list[dict]) -> dict:
    transcript = "\n".join(
        f"[{s['start_time']:.1f}s] {s['speaker']}: {s['text']}" for s in segments
    )
    transcript = redact_pii(transcript)
    prompt = LLM_INTELLIGENCE_PROMPT.format(transcript=transcript)

    try:
        answer, model = chat_with_fallback(
            messages=[{"role": "user", "content": prompt}],
            primary_model=settings.hf_model_analysis,
            secondary_model=settings.hf_model_qa,
        )
        # Find json boundaries if the model wraps it in markdown
        start = answer.find("{")
        end = answer.rfind("}") + 1
        if start != -1 and end != 0:
            answer = answer[start:end]
            
        result = json.loads(answer)
        logger.info("LLM intelligence completed with model=%s", model)
        return result
    except Exception:
        logger.exception("LLM intelligence failed")
        return {}


def run_intelligence(segments: list[dict]) -> dict:
    sentiment = patient_sentiment_timeline(segments)
    
    if settings.use_llm_intelligence:
        llm_result = llm_intelligence(segments)
        if llm_result:
            return {
                "symptoms": llm_result.get("symptoms", []),
                "prescriptions": llm_result.get("prescriptions", []),
                "follow_ups": llm_result.get("follow_ups", []),
                "soap_note": llm_result.get("soap_note", {}),
                "patient_sentiment": sentiment,
            }

    # Fallback empty structure
    return {
        "symptoms": [],
        "prescriptions": [],
        "follow_ups": [],
        "soap_note": {},
        "patient_sentiment": sentiment,
    }


LLM_ROLE_PROMPT = """\
You are analyzing a medical clinical call transcript to identify speaker roles.

The transcript uses these speaker labels: {speaker_labels}

Your task: map each speaker label to one of these roles:
- "Physician" — the doctor or medical professional asking diagnostic questions or providing a plan
- "Patient" — the individual describing symptoms or answering medical questions

Return ONLY a JSON object mapping each speaker label to a role. No explanation, no markdown.

Example:
{{"SPEAKER_00": "Physician", "SPEAKER_01": "Patient"}}

Transcript:
{transcript}
"""


def identify_roles(segments: list[dict]) -> dict[str, str]:
    speaker_labels = sorted(set(s["speaker"] for s in segments))

    if len(speaker_labels) <= 1:
        return {speaker_labels[0]: "Physician"} if speaker_labels else {}

    transcript = "\n".join(
        f"[{s['speaker']} @ {s['start_time']:.0f}s] {s['text']}" for s in segments[:100]
    )

    prompt = LLM_ROLE_PROMPT.format(
        speaker_labels=", ".join(speaker_labels),
        transcript=transcript,
    )

    try:
        answer, model = chat_with_fallback(
            messages=[{"role": "user", "content": prompt}],
            primary_model=settings.hf_model_analysis,
            secondary_model=settings.hf_model_qa,
        )
        start = answer.find("{")
        end = answer.rfind("}") + 1
        if start != -1 and end != 0:
            answer = answer[start:end]
            
        result = json.loads(answer)
        logger.info("LLM role identification completed with model=%s", model)
        return {k: v for k, v in result.items() if v in ("Physician", "Patient")}
    except Exception:
        logger.exception("LLM role identification failed")
        return {}
