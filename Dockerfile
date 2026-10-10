FROM python:3.12-slim-trixie@sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe AS builder

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock README.md notes_mcp.py LICENSE ./
COPY uv-bootstrap-requirements.lock ./
RUN python -m pip install --no-cache-dir --require-hashes --no-deps \
    -r uv-bootstrap-requirements.lock
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.12-slim-trixie@sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe

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
ARG DEBIAN_SNAPSHOT=20261009T000000Z
RUN printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s trixie main\n' "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list \
    && printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/%s trixie-security main\n' "$DEBIAN_SNAPSHOT" >> /etc/apt/sources.list \
    && rm -f /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get upgrade -y --no-install-recommends \
    && apt-get install --no-install-recommends -y ripgrep=14.1.1-1+b4 \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /vault /app \
    && chmod 0755 /app \
    && chown 65532:65532 /vault \
    && chmod 0750 /vault
COPY --from=builder /opt/venv /opt/venv
COPY docker_entrypoint.py LICENSE /app/
RUN chmod 0644 /app/docker_entrypoint.py /app/LICENSE
USER 65532:65532
WORKDIR /app
ENTRYPOINT ["python", "/app/docker_entrypoint.py"]
