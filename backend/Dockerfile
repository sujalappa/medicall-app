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

# Copy dependency definition files
COPY --chown=user pyproject.toml uv.lock* ./

# Install uv and sync dependencies (excluding project build to avoid package mapping issues)
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev --no-install-project

# Copy application files (with ownership set to non-root user)
COPY --chown=user . .

# Expose Hugging Face Space port
EXPOSE 7860

# Run alembic migrations and start uvicorn
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 7860"]
