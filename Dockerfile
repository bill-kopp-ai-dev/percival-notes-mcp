FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS builder

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
WORKDIR /app
RUN python -m pip install --no-cache-dir uv==0.12.18
COPY pyproject.toml uv.lock README.md notes_mcp.py LICENSE ./
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e

ARG VERSION=0.0.0
ARG GIT_SHA=unknown

LABEL org.opencontainers.image.title="Percival Notes MCP" \
      org.opencontainers.image.description="Percival MCP server for OKF v0.2 markdown notes and ripgrep search" \
      org.opencontainers.image.source="https://github.com/bill-kopp-ai-dev/percival-notes-mcp" \
      org.opencontainers.image.documentation="https://github.com/bill-kopp-ai-dev/percival-notes-mcp/blob/main/README.md" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="Positronic Bean Labs" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${GIT_SHA}"

ENV PATH=/opt/venv/bin:$PATH \
    HOME=/tmp \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN apt-get update \
    && apt-get install --no-install-recommends -y ripgrep=13.0.0-4+b2 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /vault /app \
    && chmod 0755 /vault /app
COPY --from=builder /opt/venv /opt/venv
COPY docker_entrypoint.py LICENSE /app/
RUN chmod 0644 /app/docker_entrypoint.py /app/LICENSE
USER 65532:65532
WORKDIR /app
ENTRYPOINT ["python", "/app/docker_entrypoint.py"]
