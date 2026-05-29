# Diarization Evaluation Suite

Offline benchmark runner for comparing baseline pyannote diarization pipelines and Callhome fine-tuned models on timestamp-labeled two-speaker clips.

By default it loads `talkbank/callhome` with config `"eng"`.

## Models included by default

- `pyannote/speaker-diarization-community-1`
- `pyannote/speaker-diarization-3.1`
- `mhdp-africa/speaker-segmentation-fine-tuned-callhome`

## Setup

```bash
cd backend
uv sync --group dev
```

Set your Hugging Face token (required for gated dataset/models):

```bash
# PowerShell
$env:HF_TOKEN="hf_xxx"
```

## Quick run

```bash
cd backend
uv run --no-sync python eval/diarization_eval.py --max-samples 20
```

## Full run

```bash
cd backend
uv run --no-sync python eval/diarization_eval.py --split data
```

For CALLHOME specifically, prefer:

```bash
cd backend
uv run --no-sync python eval/diarization_eval.py --split data
```

## Custom run options

Evaluate only selected models:

```bash
uv run --no-sync python eval/diarization_eval.py `
  --model pyannote/speaker-diarization-community-1 `
  --model pyannote/speaker-diarization-3.1 `
  --model pyannote/speaker-diarization-3.0 `
  --dataset-config eng `
  --max-samples 50
```

Override dataset columns if needed:

```bash
uv run --no-sync python eval/diarization_eval.py `
  --audio-column audio `
  --timestamps-column timestamps_start `
  --timestamps-end-column timestamps_end `
  --speakers-column speakers
```

## Outputs

- `eval/diarization_results.csv`: aggregate per-model metrics
- `eval/diarization_results.json`: aggregate + per-clip details/errors

Metrics:

- `DER`: diarization error rate
- `JER`: jaccard error rate
- `avg_infer_seconds`: average inference time per clip

## Benchmark snapshot (2026-04-08)

Command used:

```bash
uv run -m eval.diarization_eval --split data --max-samples 35 \
  --model pyannote/speaker-diarization-community-1 \
  --model pyannote/speaker-diarization-3.1 \
  --model mhdp-africa/speaker-segmentation-fine-tuned-callhome
```

Results:

| Model | Clips | DER | JER | Avg sec/clip | Notes |
|---|---:|---:|---:|---:|---|
| `pyannote/speaker-diarization-community-1` | 35 | 0.1971 | 0.2808 | 41.73 | Best DER/JER in this run |
| `pyannote/speaker-diarization-3.1` | 35 | 0.2079 | 0.2948 | 35.87 | Faster but lower accuracy |
| `mhdp-africa/speaker-segmentation-fine-tuned-callhome` | 35 | 0.2079 | 0.2948 | 35.90 | Similar to 3.1 in this run |

Current default recommendation for SalesLens diarization: `pyannote/speaker-diarization-community-1`.
