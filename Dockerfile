# Dockerfile

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app/src

# Copy lock and pyproject first
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy the rest of the code
ADD . /app

# Sync again (now with the new code, including src/)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# 2nd stage: smaller final image
FROM python:3.12-slim-bookworm

WORKDIR /app

COPY --from=uv --chown=app:app /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
# Optional
ENV ELIZA_PATH=/Users/mcpagentai_dev/eliza
ENV ELIZA_API_URL=http://192.168.0.1:5173/
ENV LOCAL_TIMEZONE=Europe/Warsaw
ENV LOG_LEVEL=DEBUG


# Optional: copy your .env if you need defaults inside the container:
# COPY .env .env

ENTRYPOINT ["mcpagentai"]
