# ----------------------------------------------
# 1st Stage: Build Python dependencies using uv
# ----------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

WORKDIR /app

# Set environment variables for uv
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app/src

# Copy Python dependency files and install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy the rest of the application code
ADD . /app

# Run uv sync again after copying the full code
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable


# ------------------------------------------------
# 2nd Stage: Install Node.js dependencies
# ------------------------------------------------
FROM node:18-slim AS node_builder

WORKDIR /app

# Create a minimal package.json for installing agent-twitter-client
RUN printf '{\n\
  "name": "agent-twitter-client-setup",\n\
  "version": "1.0.0",\n\
  "dependencies": {\n\
    "agent-twitter-client": "^0.0.18",\n\
    "tough-cookie": "^4.0.0"\n\
  }\n\
}\n' > package.json

# Install the required Node.js packages
RUN npm install

# --------------------------------------------
# 3rd Stage: Final runtime image
# --------------------------------------------
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy Python virtual environment from the uv stage
COPY --from=uv /app/.venv /app/.venv

# Copy Node.js dependencies from the node_builder stage
COPY --from=node_builder /app/node_modules /app/node_modules
COPY --from=node_builder /app/package.json /app/package.json

# Install Node.js in the runtime container
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set up environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV ELIZA_PATH=/app/eliza
ENV ELIZA_API_URL=http://192.168.1.14:5173/
ENV LOCAL_TIMEZONE=Europe/Warsaw
ENV LOG_LEVEL=DEBUG

ENV TWITTER_USERNAME=
ENV TWITTER_PASSWORD=
ENV TWITTER_EMAIL=

# Verify installations
RUN python --version && node -v && npm -v

# Ensure the mcpagentai script exists
RUN if ! [ -x "$(command -v mcpagentai)" ]; then \
      echo "mcpagentai not found in PATH"; \
      exit 1; \
    fi

# Set the default entry point
ENTRYPOINT ["mcpagentai"]
