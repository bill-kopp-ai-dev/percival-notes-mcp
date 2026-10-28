#!/usr/bin/env bash
# Restore a Notes vault backup, preserving the numeric owner, and verify it.
#
# The restore is only complete when the content manifest matches AND the
# runtime identity can read and write the restored vault. A restore that keeps
# the archive but loses the owner leaves a vault that lists files and still
# cannot be read or written by the server.

set -euo pipefail

RUNTIME_UID="${PERCIVAL_NOTES_UID:-65532}"
RUNTIME_GID="${PERCIVAL_NOTES_GID:-65532}"

usage() {
    cat <<'EOF'
Usage: vault-restore.sh --archive <tar> --target <dir> [options]

Options:
  --archive <tar>     Backup archive created by vault-backup.sh (required).
  --target <dir>      Directory where the vault is restored (required).
                      It must be empty or not exist yet.
  --verify <dir>      Verify an already restored directory against the archive
                      manifest without extracting anything.
  --uid <id>          Runtime identity expected to own the vault (default 65532).
  --gid <id>          Runtime group expected to own the vault (default 65532).
  --verify-only       Verify the archive and its manifest without extracting.
  --help              Show this help.
EOF
}

fail() {
    printf 'vault-restore: %s\n' "$1" >&2
    exit 1
}

ARCHIVE=""
TARGET=""
VERIFY_DIR=""
VERIFY_ONLY=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --archive) ARCHIVE="${2:-}"; shift 2 ;;
        --target) TARGET="${2:-}"; shift 2 ;;
        --verify) VERIFY_DIR="${2:-}"; shift 2 ;;
        --uid) RUNTIME_UID="${2:-}"; shift 2 ;;
        --gid) RUNTIME_GID="${2:-}"; shift 2 ;;
        --verify-only) VERIFY_ONLY=1; shift ;;
        --help|-h) usage; exit 0 ;;
        *) fail "unknown argument: $1" ;;
    esac
done

[ -n "$ARCHIVE" ] || { usage >&2; fail "--archive is required"; }
[ -f "$ARCHIVE" ] || fail "archive not found: $ARCHIVE"
command -v sha256sum >/dev/null || fail "sha256sum is required"
command -v tar >/dev/null || fail "tar is required"

ARCHIVE="$(cd "$(dirname "$ARCHIVE")" && pwd -P)/$(basename "$ARCHIVE")"
MANIFEST="$ARCHIVE.manifest"
CHECKSUM="$ARCHIVE.sha256"
METADATA="$ARCHIVE.meta"
[ -f "$MANIFEST" ] || fail "manifest not found: $MANIFEST"

if [ -f "$CHECKSUM" ]; then
    (cd "$(dirname "$ARCHIVE")" && sha256sum --check --status "$(basename "$CHECKSUM")") \
        || fail "archive checksum mismatch: $(basename "$ARCHIVE")"
    printf 'vault-restore: checksum ok (%s)\n' "$(basename "$ARCHIVE")"
else
    fail "checksum not found: $CHECKSUM"
fi

# Read the whole listing first: piping tar into an early-exiting reader can
# leave tar with SIGPIPE and abort the restore under `set -o pipefail`.
archive_listing="$(tar -tf "$ARCHIVE")"
VAULT_NAME="$(printf '%s\n' "$archive_listing" | cut -d/ -f1 | sort -u | sed -n '1p')"
[ -n "$VAULT_NAME" ] || fail "cannot read the vault name from the archive"

if [ "$VERIFY_ONLY" -eq 1 ]; then
    printf 'vault-restore: archive verified; files=%s\n' "$(($(wc -l < "$MANIFEST") - 1))"
    exit 0
fi

if [ -n "$VERIFY_DIR" ]; then
    RESTORED="$(cd "$VERIFY_DIR" && pwd -P)"
    [ -d "$RESTORED" ] || fail "verified directory does not exist: $VERIFY_DIR"
elif [ -n "$TARGET" ]; then
    if [ -e "$TARGET" ] && [ -n "$(ls -A "$TARGET" 2>/dev/null)" ]; then
        fail "target directory is not empty: $TARGET"
    fi
    mkdir -p "$TARGET"
    TARGET="$(cd "$TARGET" && pwd -P)"

    if [ "$(id -u)" -ne 0 ]; then
        fail "restore must run as root to reproduce the numeric owner (uid $RUNTIME_UID)"
    fi

    # --numeric-owner keeps the stored ids; --same-owner applies them on extract.
    # The vault is restored inside the target directory, never over another vault.
    tar --numeric-owner --same-owner -xpf "$ARCHIVE" -C "$TARGET"
    RESTORED="$TARGET/$VAULT_NAME"
    [ -d "$RESTORED" ] || fail "archive did not restore the vault directory"
else
    usage >&2
    fail "--target or --verify is required"
fi

content_failures=0
owner_failures=0
checked=0
while IFS=$'\t' read -r digest uid gid mode path; do
    case "$digest" in
        ''|'#'*) continue ;;
    esac
    checked=$((checked + 1))
    file="$RESTORED/$path"
    if [ ! -f "$file" ]; then
        printf 'vault-restore: MISSING %s\n' "$path" >&2
        content_failures=$((content_failures + 1))
        continue
    fi
    actual_digest="$(sha256sum "$file" | cut -d' ' -f1)"
    if [ "$actual_digest" != "$digest" ]; then
        printf 'vault-restore: CONTENT MISMATCH %s\n' "$path" >&2
        content_failures=$((content_failures + 1))
    fi
    actual_uid="$(stat -c '%u' "$file")"
    actual_gid="$(stat -c '%g' "$file")"
    actual_mode="$(stat -c '%a' "$file")"
    if [ "$actual_uid" != "$uid" ] || [ "$actual_gid" != "$gid" ]; then
        printf 'vault-restore: OWNER MISMATCH %s (expected %s:%s, got %s:%s)\n' \
            "$path" "$uid" "$gid" "$actual_uid" "$actual_gid" >&2
        owner_failures=$((owner_failures + 1))
    fi
    if [ "$actual_mode" != "$mode" ]; then
        printf 'vault-restore: MODE MISMATCH %s (expected %s, got %s)\n' \
            "$path" "$mode" "$actual_mode" >&2
        content_failures=$((content_failures + 1))
    fi
done < "$MANIFEST"

printf 'vault-restore: verified files=%s content_failures=%s owner_failures=%s\n' \
    "$checked" "$content_failures" "$owner_failures"
if [ "$content_failures" -ne 0 ]; then
    fail "restore content does not match the manifest"
fi
if [ "$owner_failures" -ne 0 ]; then
    fail "restore did not preserve the numeric owner; the vault is unusable by the server"
fi

if [ -n "$VERIFY_DIR" ]; then
    printf 'vault-restore: directory matches the archive manifest\n'
    exit 0
fi

# Read-after-restore: the runtime identity must be able to read and write.
as_runtime() {
    if command -v setpriv >/dev/null; then
        setpriv --reuid="$RUNTIME_UID" --regid="$RUNTIME_GID" --clear-groups "$@"
    elif command -v runuser >/dev/null; then
        runuser -u "#$RUNTIME_UID" -- "$@"
    elif command -v su >/dev/null; then
        su -s /bin/sh "#$RUNTIME_UID" -c "$(printf '%q ' "$@")"
    else
        fail "no setpriv, runuser or su available to check the runtime identity"
    fi
}

probe_file="$(awk -F'\t' 'NR > 1 { print $5; exit }' "$MANIFEST")"
[ -n "$probe_file" ] || fail "the manifest has no file to probe"
as_runtime cat "$RESTORED/$probe_file" >/dev/null 2>&1 \
    || fail "the runtime identity (uid $RUNTIME_UID) cannot read the restored vault"
as_runtime touch "$RESTORED/.restore-write-probe" 2>/dev/null \
    || fail "the runtime identity (uid $RUNTIME_UID) cannot write the restored vault"
as_runtime rm -f "$RESTORED/.restore-write-probe" 2>/dev/null \
    || fail "the runtime identity (uid $RUNTIME_UID) cannot clean up its probe file"

printf 'vault-restore: restored %s (uid %s gid %s); read-after-restore ok\n' \
    "$RESTORED" "$(stat -c '%u' "$RESTORED")" "$(stat -c '%g' "$RESTORED")"
