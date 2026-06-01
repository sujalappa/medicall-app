FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set up user with UID 1000 for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# Copy dependency definition files from backend directory
COPY --chown=user backend/pyproject.toml backend/uv.lock* ./
COPY --chown=user README.md /home/user/

# Install uv and sync dependencies (excluding project build to avoid package mapping issues)
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev --no-install-project

# Copy backend application files
COPY --chown=user backend/ .

# Expose Hugging Face Space port
EXPOSE 7860

# Run alembic migrations and start uvicorn without installing the project
CMD ["sh", "-c", "uv run --no-project alembic upgrade head && uv run --no-project uvicorn app.main:app --host 0.0.0.0 --port 7860"]
