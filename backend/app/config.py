from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url", mode="before")
    @classmethod
    def format_database_url(cls, v: str) -> str:
        if not v:
            return v
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg://", 1)
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg://", 1)
        return v

    app_env: str = "dev"
    api_port: int = 8000
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/medicall"
    )
    redis_url: str = "redis://localhost:6379/0"
    hf_token: str = ""
    hf_router_base_url: str = "https://router.huggingface.co/v1"
    hf_model_analysis: str = "Qwen/Qwen2.5-7B-Instruct"
    hf_model_qa: str = "Qwen/Qwen2.5-7B-Instruct"
    whisper_model_size: str = "medium"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_beam_size: int = 5
    whisper_vad_filter: bool = True
    whisper_initial_prompt: str = (
        "The following is a medical clinical call conversation between a physician and a patient. "
        "Use proper punctuation and capitalization."
    )
    diarization_device: str = "cpu"
    diarization_model: str = "pyannote/speaker-diarization-community-1"
    diarization_min_speakers: int = 1
    diarization_max_speakers: int = 4
    diarization_merge_gap_sec: float = 0.3
    diarization_min_overlap_ratio: float = 0.2
    diarization_enable_word_level: bool = True
    diarization_debug_metrics: bool = True
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    embedding_dim: int = 384
    upload_dir: str = "./storage/uploads"
    index_dir: str = "./storage/indexes"
    transcript_chunk_size: int = 800
    use_llm_intelligence: bool = True
    max_gpu_memory_mb: int = 0


settings = Settings()
