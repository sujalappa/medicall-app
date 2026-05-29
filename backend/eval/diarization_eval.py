from __future__ import annotations

import argparse
import csv
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.config import settings

DEFAULT_MODELS = [
    "pyannote/speaker-diarization-community-1",
    "pyannote/speaker-diarization-3.1",
    "mhdp-africa/speaker-segmentation-fine-tuned-callhome",
]


@dataclass
class EvalResult:
    model_id: str
    clips: int
    avg_der: float | None
    avg_jer: float | None
    avg_infer_seconds: float | None
    failures: int
    status: str
    notes: str = ""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate diarization models on a two-speaker timestamp-labeled dataset."
    )
    parser.add_argument(
        "--dataset",
        default="talkbank/callhome",
        help="HF dataset id (default: talkbank/callhome)",
    )
    parser.add_argument(
        "--dataset-config",
        default="eng",
        help='HF dataset config/name (default: "eng")',
    )
    parser.add_argument(
        "--split",
        default="data",
        help='Dataset split to evaluate (default: "data" for talkbank/callhome)',
    )
    parser.add_argument(
        "--audio-column",
        default="audio",
        help="Audio column name (default: audio)",
    )
    parser.add_argument(
        "--timestamps-column",
        default="timestamps_start",
        help="Timestamp start column for start/end format (default: timestamps_start)",
    )
    parser.add_argument(
        "--timestamps-end-column",
        default="timestamps_end",
        help="Timestamp end column for start/end format (default: timestamps_end)",
    )
    parser.add_argument(
        "--speakers-column",
        default="speakers",
        help="Speaker labels column name (default: speakers)",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Limit number of clips (0 means all)",
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="Model id to evaluate (repeatable). If omitted, evaluate the default model set.",
    )
    parser.add_argument(
        "--output-csv",
        default="eval/diarization_results.csv",
        help="CSV path for aggregate results",
    )
    parser.add_argument(
        "--output-json",
        default="eval/diarization_results.json",
        help="JSON path for aggregate and per-clip results",
    )
    parser.add_argument(
        "--hf-token",
        default="",
        help="HF token override (defaults to backend HF_TOKEN from .env settings)",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Inference device",
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=2,
        help="Expected number of speakers for evaluation clips (default: 2)",
    )
    return parser.parse_args()


def _load_runtime_modules() -> dict[str, Any]:
    try:
        import numpy as np
        import torch
        from datasets import load_dataset
        from pyannote.audio import Model, Pipeline
        from pyannote.audio.pipelines import SpeakerDiarization
        from pyannote.core import Annotation, Segment, Timeline
        from pyannote.metrics.diarization import DiarizationErrorRate, JaccardErrorRate
        from tqdm import tqdm
    except Exception as exc:
        raise RuntimeError(
            "Missing evaluation dependencies. Install backend dev deps first:\n"
            "  uv sync --group dev\n"
            f"Original import error: {exc}"
        ) from exc

    return {
        "np": np,
        "torch": torch,
        "load_dataset": load_dataset,
        "Model": Model,
        "Pipeline": Pipeline,
        "SpeakerDiarization": SpeakerDiarization,
        "Annotation": Annotation,
        "Segment": Segment,
        "Timeline": Timeline,
        "DiarizationErrorRate": DiarizationErrorRate,
        "JaccardErrorRate": JaccardErrorRate,
        "tqdm": tqdm,
    }


def _select_device(torch_mod: Any, requested: str) -> str:
    if requested == "cpu":
        return "cpu"
    if requested == "cuda":
        if torch_mod.cuda.is_available():
            return "cuda"
        raise RuntimeError("Requested CUDA but torch.cuda.is_available() is false.")
    return "cuda" if torch_mod.cuda.is_available() else "cpu"


def _to_annotation(
    row: dict,
    annotation_cls: Any,
    segment_cls: Any,
    timestamps_key: str,
    timestamps_end_key: str,
    speakers_key: str,
) -> Any:
    speakers = row.get(speakers_key)
    timestamps = row.get(timestamps_key)
    timestamps_end = row.get(timestamps_end_key)

    if speakers is None:
        raise ValueError(f"Missing column '{speakers_key}' in dataset row.")

    if timestamps is None and timestamps_end is None:
        raise ValueError(
            "Missing timestamp columns. "
            f"Expected either '{timestamps_key}' as [[start,end], ...] or "
            f"'{timestamps_key}' + '{timestamps_end_key}' arrays."
        )

    pairs: list[tuple[float, float]] = []
    if timestamps is not None and timestamps_end is not None:
        if len(timestamps) != len(timestamps_end):
            raise ValueError("timestamps_start and timestamps_end length mismatch.")
        pairs = [(float(s), float(e)) for s, e in zip(timestamps, timestamps_end)]
    elif timestamps is not None:
        # Backward-compatible mode: timestamps contains [start, end] pairs.
        for i, ts in enumerate(timestamps):
            if not isinstance(ts, (list, tuple)) or len(ts) != 2:
                raise ValueError(f"Invalid timestamp pair at index={i}: {ts}")
            pairs.append((float(ts[0]), float(ts[1])))

    if len(pairs) != len(speakers):
        raise ValueError("timestamp entries and speakers length mismatch.")

    annotation = annotation_cls()
    for (start, end), speaker in zip(pairs, speakers):
        if end <= start:
            continue
        annotation[segment_cls(start, end)] = str(speaker)
    return annotation


def _build_pipeline(
    modules: dict[str, Any],
    model_id: str,
    hf_token: str,
    device: str,
) -> tuple[Any | None, str]:
    Pipeline = modules["Pipeline"]
    Model = modules["Model"]
    SpeakerDiarization = modules["SpeakerDiarization"]
    torch_mod = modules["torch"]

    is_pipeline_repo = "speaker-diarization-" in model_id
    auth_attempts = []
    if hf_token:
        if is_pipeline_repo:
            # Try both auth styles for compatibility across pyannote/huggingface-hub versions.
            auth_attempts.append({"token": hf_token})
            auth_attempts.append({"use_auth_token": hf_token})
        else:
            auth_attempts.append({"token": hf_token})
            auth_attempts.append({"use_auth_token": hf_token})
    else:
        auth_attempts.append({})

    last_exc: Exception | None = None

    for auth_kwargs in auth_attempts:
        try:
            pipeline = Pipeline.from_pretrained(model_id, **auth_kwargs)
            pipeline.to(torch_mod.device(device))
            return pipeline, "pipeline"
        except Exception as exc:
            last_exc = exc

    # For speaker-diarization pipelines, do not fall back to Model.from_pretrained
    # since these repos are pipeline repos and fallback creates misleading 404 errors.
    if is_pipeline_repo:
        return None, f"unloadable ({last_exc})"

    for auth_kwargs in auth_attempts:
        try:
            segmentation = Model.from_pretrained(model_id, **auth_kwargs)
            pipeline = SpeakerDiarization(segmentation=segmentation)
            pipeline.to(torch_mod.device(device))
            return pipeline, "segmentation"
        except Exception as exc:
            last_exc = exc

    return None, f"unloadable ({last_exc})"


def _run_model_eval(
    modules: dict[str, Any],
    dataset: Any,
    model_id: str,
    hf_token: str,
    device: str,
    audio_key: str,
    timestamps_key: str,
    timestamps_end_key: str,
    speakers_key: str,
    num_speakers: int,
) -> tuple[EvalResult, list[dict[str, Any]]]:
    tqdm = modules["tqdm"]
    torch_mod = modules["torch"]
    Annotation = modules["Annotation"]
    Segment = modules["Segment"]
    Timeline = modules["Timeline"]
    DiarizationErrorRate = modules["DiarizationErrorRate"]
    JaccardErrorRate = modules["JaccardErrorRate"]

    def _to_annotation_hypothesis(output: Any) -> Any:
        # pyannote community pipelines may return DiarizeOutput wrappers.
        if hasattr(output, "get_timeline"):
            return output
        if hasattr(output, "speaker_diarization"):
            ann = output.speaker_diarization
            if hasattr(ann, "get_timeline"):
                return ann
        if hasattr(output, "diarization"):
            ann = output.diarization
            if hasattr(ann, "get_timeline"):
                return ann
        raise TypeError(
            f"Unsupported diarization output type for metrics: {type(output).__name__}"
        )

    pipeline, load_mode = _build_pipeline(modules, model_id, hf_token, device)
    if pipeline is None:
        return (
            EvalResult(
                model_id=model_id,
                clips=0,
                avg_der=None,
                avg_jer=None,
                avg_infer_seconds=None,
                failures=0,
                status="skipped",
                notes=f"Failed to load model: {load_mode}",
            ),
            [],
        )

    der_scores: list[float] = []
    jer_scores: list[float] = []
    latencies: list[float] = []
    failures = 0
    per_clip: list[dict[str, Any]] = []

    for idx, row in enumerate(tqdm(dataset, desc=f"Evaluating {model_id}", unit="clip")):
        try:
            audio = row.get(audio_key)
            if not audio:
                raise ValueError(f"Missing audio column '{audio_key}'.")
            waveform = torch_mod.tensor(audio["array"], dtype=torch_mod.float32).unsqueeze(0)
            sample_rate = int(audio["sampling_rate"])
            clip_duration_sec = float(waveform.shape[1]) / float(sample_rate)
            uem = Timeline([Segment(0.0, clip_duration_sec)])

            reference = _to_annotation(
                row,
                annotation_cls=Annotation,
                segment_cls=Segment,
                timestamps_key=timestamps_key,
                timestamps_end_key=timestamps_end_key,
                speakers_key=speakers_key,
            )

            t0 = time.perf_counter()
            hypothesis_raw = pipeline(
                {"waveform": waveform, "sample_rate": sample_rate},
                min_speakers=num_speakers,
                max_speakers=num_speakers,
            )
            hypothesis = _to_annotation_hypothesis(hypothesis_raw)
            t1 = time.perf_counter()

            der_metric = DiarizationErrorRate(collar=0.0, skip_overlap=False)
            jer_metric = JaccardErrorRate(collar=0.0, skip_overlap=False)
            der = float(der_metric(reference, hypothesis, uem=uem))
            jer = float(jer_metric(reference, hypothesis, uem=uem))

            latency = t1 - t0
            der_scores.append(der)
            jer_scores.append(jer)
            latencies.append(latency)
            per_clip.append(
                {
                    "clip_index": idx,
                    "model_id": model_id,
                    "load_mode": load_mode,
                    "der": der,
                    "jer": jer,
                    "infer_seconds": latency,
                }
            )
        except Exception as exc:
            failures += 1
            per_clip.append(
                {
                    "clip_index": idx,
                    "model_id": model_id,
                    "load_mode": load_mode,
                    "error": str(exc),
                }
            )

    clips = len(der_scores)
    if clips == 0:
        return (
            EvalResult(
                model_id=model_id,
                clips=0,
                avg_der=None,
                avg_jer=None,
                avg_infer_seconds=None,
                failures=failures,
                status="failed",
                notes="No successful clips.",
            ),
            per_clip,
        )

    avg_der = sum(der_scores) / clips
    avg_jer = sum(jer_scores) / clips
    avg_latency = sum(latencies) / clips
    return (
        EvalResult(
            model_id=model_id,
            clips=clips,
            avg_der=avg_der,
            avg_jer=avg_jer,
            avg_infer_seconds=avg_latency,
            failures=failures,
            status="ok",
            notes=f"Loaded as {load_mode}",
        ),
        per_clip,
    )


def _write_results_csv(path: Path, rows: list[EvalResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "model_id",
                "status",
                "clips",
                "failures",
                "avg_der",
                "avg_jer",
                "avg_infer_seconds",
                "notes",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "model_id": r.model_id,
                    "status": r.status,
                    "clips": r.clips,
                    "failures": r.failures,
                    "avg_der": "" if r.avg_der is None else f"{r.avg_der:.6f}",
                    "avg_jer": "" if r.avg_jer is None else f"{r.avg_jer:.6f}",
                    "avg_infer_seconds": ""
                    if r.avg_infer_seconds is None
                    else f"{r.avg_infer_seconds:.6f}",
                    "notes": r.notes,
                }
            )


def _write_results_json(path: Path, aggregate: list[EvalResult], per_clip: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "aggregate": [
            {
                "model_id": r.model_id,
                "status": r.status,
                "clips": r.clips,
                "failures": r.failures,
                "avg_der": r.avg_der,
                "avg_jer": r.avg_jer,
                "avg_infer_seconds": r.avg_infer_seconds,
                "notes": r.notes,
            }
            for r in aggregate
        ],
        "per_clip": per_clip,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    load_dotenv()
    args = _parse_args()
    modules = _load_runtime_modules()
    load_dataset = modules["load_dataset"]

    device = _select_device(modules["torch"], args.device)
    models = args.model if args.model else DEFAULT_MODELS
    hf_token = args.hf_token or settings.hf_token
    if hf_token:
        os.environ["HF_TOKEN"] = hf_token
        os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
    print(f"Device: {device}")
    print(f"Dataset: {args.dataset} config={args.dataset_config} split={args.split}")
    print(f"Models: {len(models)}")
    print(f"HF token present: {'yes' if bool(hf_token) else 'no'}")

    # Load dataset dict first so we can validate split names across datasets.
    ds_dict = load_dataset(
        args.dataset,
        args.dataset_config,
        token=hf_token or None,
    )
    available_splits = list(ds_dict.keys())
    chosen_split = args.split
    if chosen_split not in ds_dict:
        if "data" in ds_dict:
            print(
                f'Warning: split "{chosen_split}" not found. '
                f'Falling back to "data". Available: {available_splits}'
            )
            chosen_split = "data"
        else:
            raise ValueError(
                f'Unknown split "{chosen_split}". Available splits: {available_splits}'
            )

    dataset = ds_dict[chosen_split]
    if args.max_samples and args.max_samples > 0:
        dataset = dataset.select(range(min(args.max_samples, len(dataset))))
    print(f"Using split: {chosen_split}")
    print(f"Clips to evaluate: {len(dataset)}")

    aggregate: list[EvalResult] = []
    per_clip: list[dict[str, Any]] = []
    for model_id in models:
        result, details = _run_model_eval(
            modules=modules,
            dataset=dataset,
            model_id=model_id,
            hf_token=hf_token,
            device=device,
            audio_key=args.audio_column,
            timestamps_key=args.timestamps_column,
            timestamps_end_key=args.timestamps_end_column,
            speakers_key=args.speakers_column,
            num_speakers=args.num_speakers,
        )
        aggregate.append(result)
        per_clip.extend(details)
        print(
            f"[{result.status}] {result.model_id} clips={result.clips} "
            f"DER={result.avg_der} JER={result.avg_jer} failures={result.failures}"
        )

    csv_path = Path(args.output_csv)
    json_path = Path(args.output_json)
    _write_results_csv(csv_path, aggregate)
    _write_results_json(json_path, aggregate, per_clip)
    print(f"Wrote CSV: {csv_path}")
    print(f"Wrote JSON: {json_path}")


if __name__ == "__main__":
    main()
