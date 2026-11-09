# Runtime base for the offline image build.
#
# Built ONCE with network access by the operator, then pinned by digest and
# consumed by `Dockerfile.offline`. It carries the Debian runtime that the
# product image needs (ripgrep and the shared libraries it links against) with
# every package pinned to an exact version of a dated Debian snapshot, and it
# applies the same hardening the runtime stage applies today: no package
# manager binaries, no setuid or setgid bits.
#
# Build with network access:
#   docker build -f docker/offline-runtime.Dockerfile \
#     --build-arg DEBIAN_SNAPSHOT=20261020T000000Z -t percival-notes-runtime:offline-base .
#
# The resulting digest replaces the apt stage of `Dockerfile.offline`. Keep the
# build log and the digest: they are part of the image provenance recorded in
# the F3 evidence.

FROM debian:forky-slim@sha256:4cee6ff3ebc49e32d55a857e25164ef8e5f8fecff2a186c6393f7e8bd8c23b53

ARG DEBIAN_SNAPSHOT=20261020T000000Z
LABEL org.opencontainers.image.title="Percival Notes MCP runtime base" \
      org.opencontainers.image.description="Debian runtime base for the offline Notes image build" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.vendor="Positronic Bean Labs" \
      org.opencontainers.image.version="1" \
      org.opencontainers.image.revision="unknown"

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
    && rm -rf /var/lib/apt/lists/*
