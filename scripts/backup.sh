#!/usr/bin/env bash
# ============================================================
# HomeGuard - Backup Script
# ============================================================
# Creates encrypted backups of HomeGuard critical data.
# Can be run manually or via cron (daily at 2:00 AM).
#
# Usage: bash scripts/backup.sh [--verify] [--restore /path/to/backup]
# Cron: 0 2 * * * /homeguard/scripts/backup.sh >> /var/log/homeguard/backup.log 2>&1
# ============================================================

set -euo pipefail

# --------------------------------------------------
# Configuration
# --------------------------------------------------
BACKUP_DIR="${BACKUP_DIR:-/var/backups/opendataremoval}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_NAME="opendataremoval-${TIMESTAMP}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"
ENCRYPTED_PATH="${ARCHIVE_PATH}.gpg"
LOG_DIR="${LOG_DIR:-/var/log/homeguard}"
MAX_BACKUPS=7
GPG_RECIPIENT="${GPG_RECIPIENT:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --------------------------------------------------
# Backup functions
# --------------------------------------------------
create_backup() {
    log_info "Starting HomeGuard backup at $(date)"
    log_info "Backup directory: ${BACKUP_DIR}"

    # Create backup directory if needed
    mkdir -p "${BACKUP_DIR}"
    chmod 700 "${BACKUP_DIR}"
    mkdir -p "${LOG_DIR}"
    chmod 750 "${LOG_DIR}"

    # Build list of files to backup
    local FILES_TO_BACKUP=()

    # Docker volumes data
    if docker volume inspect opendataremoval_db_data &>/dev/null; then
        FILES_TO_BACKUP+=("db_data")
        log_info "Including PostgreSQL volume data"
    fi

    # Configuration files
    if [ -f .env ]; then
        cp .env "${BACKUP_DIR}/.env.$TIMESTAMP"
        chmod 600 "${BACKUP_DIR}/.env.$TIMESTAMP"
        log_info "Backed up .env file"
    fi

    # Playbooks
    if [ -d playbooks ]; then
        FILES_TO_BACKUP+=("playbooks")
        log_info "Including playbooks"
    fi

    # Workflows
    if [ -d workflows ]; then
        FILES_TO_BACKUP+=("workflows")
        log_info "Including n8n workflows"
    fi

    # Database dump (preferred method)
    if command -v docker &>/dev/null; then
        log_info "Creating database dump..."
        docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            --no-owner --no-privileges \
            | gzip > "${BACKUP_DIR}/db-dump-${TIMESTAMP}.sql.gz" 2>/dev/null || {
            log_warn "Database dump failed (service may be down)"
        }
    fi

    # Create tar archive of local files
    if [ ${#FILES_TO_BACKUP[@]} -gt 0 ]; then
        log_info "Creating archive: ${ARCHIVE_PATH}"
        tar czf "${ARCHIVE_PATH}" -C /src "${FILES_TO_BACKUP[@]}" 2>/dev/null || {
            log_warn "Some files could not be archived"
        }
    else
        log_info "No local files to archive, creating minimal backup"
        echo "HomeGuard backup - ${TIMESTAMP}" > "${ARCHIVE_PATH}"
    fi

    # Encrypt with GPG
    if [ -f "${ARCHIVE_PATH}" ] && [ -s "${ARCHIVE_PATH}" ]; then
        if [ -n "$GPG_RECIPIENT" ]; then
            gpg --batch --yes --recipient "${GPG_RECIPIENT}" --encrypt "${ARCHIVE_PATH}"
            log_info "Encrypted backup: ${ENCRYPTED_PATH}"
        else
            # Encrypt locally without recipient (for local backup only)
            gpg --batch --yes --symmetric --cipher-algo AES256 \
                --passphrase "$(cat .env 2>/dev/null | grep DB_ENCRYPTION_KEY | cut -d= -f2 || echo '')" \
                --output "${ENCRYPTED_PATH}" \
                "${ARCHIVE_PATH}"
            log_info "Locally encrypted backup: ${ENCRYPTED_PATH}"
        fi

        # Remove unencrypted archive
        rm -f "${ARCHIVE_PATH}"
    fi

    # Clean old backups (keep last N)
    log_info "Cleaning old backups (keeping last ${MAX_BACKUPS})..."
    ls -t "${BACKUP_DIR}"/opendataremoval-*.gpg 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f
    ls -t "${BACKUP_DIR}"/db-dump-*.sql.gz 2>/dev/null | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm -f

    log_info "Backup complete at $(date)"
    log_info "Files in backup directory:"
    ls -lh "${BACKUP_DIR}/" 2>/dev/null || true
}

verify_backup() {
    log_info "Verifying latest backup..."

    local LATEST
    LATEST=$(ls -t "${BACKUP_DIR}"/opendataremoval-*.gpg 2>/dev/null | head -1)

    if [ -z "$LATEST" ]; then
        log_error "No backup files found in ${BACKUP_DIR}"
        return 1
    fi

    log_info "Latest backup: ${LATEST}"

    # Try to list contents (decrypt in memory)
    if [ -n "$GPG_RECIPIENT" ]; then
        gpg --batch --yes --decrypt "${LATEST}" 2>/dev/null | tar tzf - >/dev/null 2>&1
    else
        gpg --batch --yes --decrypt "${LATEST}" 2>/dev/null | tar tzf - >/dev/null 2>&1
    fi

    if [ $? -eq 0 ]; then
        log_info "Backup verification: PASSED"
        return 0
    else
        log_error "Backup verification: FAILED"
        return 1
    fi
}

restore_backup() {
    local BACKUP_FILE="$1"

    if [ ! -f "$BACKUP_FILE" ]; then
        log_error "Backup file not found: $BACKUP_FILE"
        return 1
    fi

    log_warn "RESTORING FROM BACKUP: $BACKUP_FILE"
    log_warn "This will overwrite current data!"

    # Decrypt
    local DECRYPTED="/tmp/homeguard-restore-$(date +%s).tar.gz"
    if [ -n "$GPG_RECIPIENT" ]; then
        gpg --batch --yes --decrypt "$BACKUP_FILE" > "$DECRYPTED"
    else
        gpg --batch --yes --decrypt "$BACKUP_FILE" > "$DECRYPTED"
    fi

    # Restore database
    if command -v docker &>/dev/null; then
        log_info "Restoring database..."
        gunzip -c "$DECRYPTED" 2>/dev/null | docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" || {
            log_warn "Database restore may have failed"
        }
    fi

    # Restore files
    if [ -d playbooks ] || [ -d workflows ]; then
        log_info "Restoring local files..."
        tar xzf "$DECRYPTED" -C / 2>/dev/null || log_warn "File restore may have failed"
    fi

    rm -f "$DECRYPTED"
    log_info "Restore complete"
}

# --------------------------------------------------
# Main
# --------------------------------------------------
main() {
    case "${1:-}" in
        --verify)
            verify_backup
            ;;
        --restore)
            if [ -z "${2:-}" ]; then
                log_error "Usage: $0 --restore <backup-file>"
                exit 1
            fi
            restore_backup "$2"
            ;;
        --help|-h)
            echo "Usage: $0 [--verify] [--restore <file>] [--help]"
            echo ""
            echo "Options:"
            echo "  --verify    Verify the latest backup"
            echo "  --restore   Restore from a specific backup file"
            echo "  --help      Show this help"
            ;;
        *)
            create_backup
            ;;
    esac
}

main "$@"
