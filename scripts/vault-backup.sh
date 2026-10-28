#!/usr/bin/env bash
# Back up the Notes vault with numeric ownership and a verifiable manifest.
#
# The archive, its checksum and a per-file manifest (sha256, uid, gid, mode)
# are written OUTSIDE the vault, so a copy never lives inside the data it
# protects. Retention keeps the newest N daily and N weekly archives.
#
# Owner decision (2026-10-28): backups live outside the vault, with 7 daily
# and 4 weekly snapshots kept.

set -euo pipefail

KEEP_DAILY=7
KEEP_WEEKLY=4

usage() {
    cat <<'EOF'
Usage: vault-backup.sh --vault <dir> [options]

Options:
  --vault <dir>       Vault directory to back up (required).
  --dest <dir>        Backup directory (default: $PERCIVAL_NOTES_BACKUP_DIR or
                      $HOME/.local/share/percival-notes/backups).
  --label <name>      Label recorded in the archive metadata (default: vault).
  --keep-daily <n>    Daily snapshots to keep (default: 7).
  --keep-weekly <n>   Weekly snapshots to keep (default: 4).
  --help              Show this help.
EOF
}

fail() {
    printf 'vault-backup: %s\n' "$1" >&2
    exit 1
}

VAULT=""
DEST="${PERCIVAL_NOTES_BACKUP_DIR:-$HOME/.local/share/percival-notes/backups}"
LABEL="vault"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --vault) VAULT="${2:-}"; shift 2 ;;
        --dest) DEST="${2:-}"; shift 2 ;;
        --label) LABEL="${2:-}"; shift 2 ;;
        --keep-daily) KEEP_DAILY="${2:-}"; shift 2 ;;
        --keep-weekly) KEEP_WEEKLY="${2:-}"; shift 2 ;;
        --help|-h) usage; exit 0 ;;
        *) fail "unknown argument: $1" ;;
    esac
done

[ -n "$VAULT" ] || { usage >&2; fail "--vault is required"; }
[ -d "$VAULT" ] || fail "vault is not a directory: $VAULT"
command -v tar >/dev/null || fail "tar is required"
command -v sha256sum >/dev/null || fail "sha256sum is required"

VAULT="$(cd "$VAULT" && pwd -P)"
VAULT_NAME="$(basename "$VAULT")"
VAULT_PARENT="$(dirname "$VAULT")"
case "$LABEL" in
    *[!A-Za-z0-9._-]*) fail "label must use letters, digits, dot, underscore or dash" ;;
esac

if [ ! -d "$DEST" ]; then
    mkdir -p "$DEST"
    chmod 0700 "$DEST"
fi
DEST="$(cd "$DEST" && pwd -P)"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
ARCHIVE="$DEST/${STAMP}-${LABEL}.tar"
MANIFEST="$ARCHIVE.manifest"
CHECKSUM="$ARCHIVE.sha256"
METADATA="$ARCHIVE.meta"

# The archive stores numeric ids so the restore can reproduce the owner on
# any host, independently of the local passwd database.
tar --numeric-owner --one-file-system -cpf "$ARCHIVE" \
    -C "$VAULT_PARENT" "$VAULT_NAME"

{
    printf '# sha256\tuid\tgid\tmode\tpath\n'
    find "$VAULT" -type f -print0 \
        | sort -z \
        | while IFS= read -r -d '' file; do
            rel="${file#"$VAULT"/}"
            case "$rel" in
                *$'\t'*|*$'\n'*) fail "path with control characters is not supported: $rel" ;;
            esac
            digest="$(sha256sum "$file" | cut -d' ' -f1)"
            read -r file_uid file_gid file_mode <<< "$(stat -c '%u %g %a' "$file")"
            printf '%s\t%s\t%s\t%s\t%s\n' \
                "$digest" "$file_uid" "$file_gid" "$file_mode" "$rel"
        done
} > "$MANIFEST"

sha256sum "$ARCHIVE" > "$CHECKSUM"

{
    printf 'vault=%s\n' "$VAULT"
    printf 'label=%s\n' "$LABEL"
    printf 'created_at=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf 'archive=%s\n' "$(basename "$ARCHIVE")"
    printf 'vault_uid=%s\n' "$(stat -c '%u' "$VAULT")"
    printf 'vault_gid=%s\n' "$(stat -c '%g' "$VAULT")"
    printf 'files=%s\n' "$(($(wc -l < "$MANIFEST") - 1))"
} > "$METADATA"

chmod 0600 "$ARCHIVE" "$MANIFEST" "$CHECKSUM" "$METADATA"

prune() {
    # Keep the newest archive of each of the last N days (daily set) and the
    # newest archive of each of the last N ISO weeks (weekly set). Anything
    # outside both windows is removed with its manifest, checksum and metadata.
    local keep_daily="$1" keep_weekly="$2"
    local -a ordered=()
    local archive name stamp date day week
    while IFS= read -r archive; do
        [ -n "$archive" ] && ordered+=("$archive")
    done < <(ls -1 "$DEST"/*.tar 2>/dev/null || true)
    [ "${#ordered[@]}" -gt 0 ] || return 0
    mapfile -t ordered < <(printf '%s\n' "${ordered[@]}" | sort -r)

    declare -A used_day=() used_week=()
    local daily_kept=0 weekly_kept=0 keep
    for archive in "${ordered[@]}"; do
        name="$(basename "$archive")"
        stamp="${name%%-*}"
        date="${stamp:0:4}-${stamp:4:2}-${stamp:6:2}"
        day="${stamp:0:8}"
        week="$(date -u -d "$date" +%G-%V 2>/dev/null || echo "$day")"
        keep=0
        if [ "${used_day[$day]:-0}" = "0" ] && [ "$daily_kept" -lt "$keep_daily" ]; then
            used_day["$day"]=1
            daily_kept=$((daily_kept + 1))
            keep=1
        fi
        if [ "${used_week[$week]:-0}" = "0" ] && [ "$weekly_kept" -lt "$keep_weekly" ]; then
            used_week["$week"]=1
            weekly_kept=$((weekly_kept + 1))
            keep=1
        fi
        if [ "$keep" -eq 0 ]; then
            rm -f "$archive" "$archive.manifest" "$archive.sha256" "$archive.meta"
        fi
    done
}

prune "$KEEP_DAILY" "$KEEP_WEEKLY"

printf 'vault-backup: archive=%s files=%s\n' \
    "$(basename "$ARCHIVE")" "$(($(wc -l < "$MANIFEST") - 1))"
printf 'vault-backup: manifest=%s checksum=%s\n' \
    "$(basename "$MANIFEST")" "$(basename "$CHECKSUM")"
