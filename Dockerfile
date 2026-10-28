FROM python:3.12-slim-trixie@sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe AS python-runtime

FROM python:3.12-slim-trixie@sha256:2b4f19dae3a777dfc3b76730bda1e82e1f66ab2a2686fa93ca78edbfb4f04ffe AS builder

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock README.md notes_mcp.py LICENSE ./
COPY uv-bootstrap-requirements.lock ./
RUN python -m pip install --no-cache-dir --require-hashes --no-deps \
    -r uv-bootstrap-requirements.lock
RUN uv sync --frozen --no-dev --no-editable

FROM debian:forky-slim@sha256:4cee6ff3ebc49e32d55a857e25164ef8e5f8fecff2a186c6393f7e8bd8c23b53

COPY --from=python-runtime /usr/local/bin/python3.12 /usr/local/bin/python3.12
COPY --from=python-runtime /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=python-runtime /usr/local/lib/libpython3.12.so.1.0 /usr/local/lib/libpython3.12.so.1.0

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
ARG DEBIAN_SNAPSHOT=20261020T000000Z
RUN printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/%s forky main\n' "$DEBIAN_SNAPSHOT" > /etc/apt/sources.list \
    && printf 'deb [check-valid-until=no] http://snapshot.debian.org/archive/debian-security/%s forky-security main\n' "$DEBIAN_SNAPSHOT" >> /etc/apt/sources.list \
    && rm -f /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Check-Valid-Until=false update \
    && apt-get upgrade -y --no-install-recommends \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
        ca-certificates=20260816 ripgrep=15.2.0-1 \
        libssl3t64=3.6.5-1 libffi8=3.8.0-2 libsqlite3-0=3.53.4-2 \
        libreadline8t64=8.3-4 libncursesw6=6.6+20260608-2 libtinfo6=6.6+20260608-2 \
        libdb5.3t64=5.3.28+dfsg2-11+b1 libgdbm6t64=1.26-1+b2 \
        libbz2-1.0=1.0.8-6+b2 liblzma5=5.8.4-1 libuuid1=2.42.4-1 \
        libzstd1=1.5.7+dfsg-4 zlib1g=1:1.3.dfsg+really1.3.2-3 \
        libtk8.6=8.6.18-1 libtcl8.6=8.6.18+dfsg-1 \
    && ln -sf /usr/local/lib/libpython3.12.so.1.0 /usr/local/lib/libpython3.12.so \
    && ln -sf /usr/local/bin/python3.12 /usr/local/bin/python3 \
    && ln -sf /usr/local/bin/python3.12 /usr/local/bin/python \
    && rm -rf /usr/local/lib/python3.12/site-packages/pip \
        /usr/local/lib/python3.12/site-packages/pip-*.dist-info \
        /usr/local/lib/python3.12/ensurepip/_bundled \
    && rm -f /usr/bin/nsenter /usr/bin/infocmp \
    && rm -f /usr/bin/apt /usr/bin/apt-cache /usr/bin/apt-cdrom /usr/bin/apt-config \
        /usr/bin/apt-get /usr/bin/apt-mark /usr/bin/apt-key \
        /usr/bin/dpkg /usr/bin/dpkg-deb /usr/bin/dpkg-divert /usr/bin/dpkg-maintscript-helper \
        /usr/bin/dpkg-query /usr/bin/dpkg-realpath /usr/bin/dpkg-split \
        /usr/bin/dpkg-statoverride /usr/bin/dpkg-trigger \
    && rm -rf /usr/lib/apt /usr/lib/dpkg/methods /var/lib/apt /etc/apt \
    && chmod u-s,g-s /usr/bin/mount /usr/bin/chage /usr/bin/chfn /usr/bin/chsh \
        /usr/bin/gpasswd /usr/bin/passwd /usr/bin/su /usr/bin/umount \
        /usr/sbin/unix_chkpwd \
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
