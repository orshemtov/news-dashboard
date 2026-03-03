FROM --platform=linux/amd64 python:3.13-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install runtime dependencies (no dev deps, frozen, no cache)
RUN uv sync --frozen --no-cache --no-dev

# Copy application source
COPY src/ ./src/

# Pre-download the sentence-transformers model so it's baked into the image.
# The model is cached at /root/.cache/huggingface by default.
# Uses the default model from .env.example; override EMBEDDING_MODEL build-arg to change it.
ARG EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
RUN /app/.venv/bin/python -c \
    "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')"

EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
