#!/usr/bin/env bash
# ============================================================
# HomeGuard - Host Security Hardening Script
# ============================================================
# This script applies host-level security hardening for the
# production deployment of HomeGuard.
#
# Prerequisites: root/sudo access, Debian/Ubuntu-based system
# Usage: sudo bash scripts/host_security.sh
# ============================================================

set -euo pipefail

# --------------------------------------------------
# Color helpers
# --------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --------------------------------------------------
# 1. UFW Firewall Configuration
# --------------------------------------------------
configure_ufw() {
    log_info "Configuring UFW firewall..."

    # Install UFW if not present
    if ! command -v ufw &>/dev/null; then
        apt-get update && apt-get install -y ufw
    fi

    # Reset to defaults
    ufw --force reset

    # Default policies: deny all incoming, allow all outgoing
    ufw default deny incoming
    ufw default allow outgoing
    log_info "Default policies: deny incoming, allow outgoing"

    # Allow SSH (keep current port or use custom)
    local SSH_PORT="${SSH_PORT:-22}"
    ufw allow "${SSH_PORT}/tcp" comment "SSH access"
    log_info "Allowed SSH on port ${SSH_PORT}"

    # Allow HTTP/HTTPS (if exposed to internet)
    ufw allow 80/tcp comment "HTTP"
    ufw allow 443/tcp comment "HTTPS"
    log_info "Allowed HTTP/HTTPS"

    # Allow API port (internal network only via Docker)
    # Note: API is bound to docker network, not directly exposed
    # ufw allow 8000/tcp comment "HomeGuard API"

    # Allow n8n (if exposed)
    ufw allow 5678/tcp comment "n8n workflow automation"

    # Log dropped packets
    ufw logging medium
    log_info "Logging set to medium"

    # Enable UFW (confirm yes automatically)
    echo "y" | ufw enable
    log_info "UFW enabled"

    # Verify
    ufw status verbose
}

# --------------------------------------------------
# 2. Fail2Ban Configuration
# --------------------------------------------------
configure_fail2ban() {
    log_info "Configuring Fail2Ban..."

    # Install Fail2Ban
    if ! command -v fail2ban-client &>/dev/null; then
        apt-get update && apt-get install -y fail2ban
    fi

    # Create custom jail configuration
    mkdir -p /etc/fail2ban/jail.d
    cat > /etc/fail2ban/jail.d/homeguard.conf <<'JAIL_EOF'
# HomeGuard Fail2Ban Configuration
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5
backend = auto
banaction = ufw

# SSH jail - protect SSH brute force
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200
findtime = 300

# HomeGuard API auth jail - protect login endpoints
[homeguard-api]
enabled = true
port = 8000
filter = homeguard-api
logpath = /var/log/homeguard/api.log
maxretry = 10
bantime = 3600
findtime = 300

# n8n webhook jail
[n8n]
enabled = false
port = 5678
filter = nginx-http-auth
logpath = /var/log/nginx/n8n.error.log
maxretry = 5
bantime = 1800
JAIL_EOF

    # Create filter for HomeGuard API auth failures
    mkdir -p /etc/fail2ban/filter.d
    cat > /etc/fail2ban/filter.d/homeguard-api.conf <<'FILTER_EOF'
# Fail2Ban filter for HomeGuard API auth failures
[Definition]
failregex = ^.*ERROR.*auth.*Failed password.*$
            ^.*ERROR.*login.*401.*$
            ^.*WARNING.*authentication failure.*$
ignoreregex =
FILTER_EOF

    # Start and enable Fail2Ban
    systemctl enable fail2ban
    systemctl restart fail2ban
    log_info "Fail2Ban configured and restarted"

    # Verify
    fail2ban-client status
    fail2ban-client status sshd
}

# --------------------------------------------------
# 3. System Hardening
# --------------------------------------------------
configure_system_hardening() {
    log_info "Applying system hardening..."

    # Restrict file creation mask
    echo "umask 027" >> /etc/profile.d/homeguard.sh
    chmod 644 /etc/profile.d/homeguard.sh

    # Disable unused services
    local services_to_disable=(
        "bluetooth"
        "cups"
        "avahi-daemon"
        "modemmanager"
    )
    for svc in "${services_to_disable[@]}"; do
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            systemctl disable "$svc"
            log_info "Disabled unused service: $svc"
        fi
    done

    # Configure kernel parameters
    cat > /etc/sysctl.d/99-homeguard.conf <<'SYSCTL_EOF'
# HomeGuard kernel hardening
net.ipv4.tcp_syncookies = 1
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.rp_filter = 1
kernel.randomize_va_space = 2
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
SYSCTL_EOF

    sysctl -p /etc/sysctl.d/99-homeguard.conf
    log_info "Kernel parameters applied"

    # Set log file permissions
    mkdir -p /var/log/homeguard
    chmod 750 /var/log/homeguard
    chown root:adm /var/log/homeguard
    log_info "Log directory secured"
}

# --------------------------------------------------
# 4. GPG Backup Configuration
# --------------------------------------------------
configure_gpg_backup() {
    log_info "Configuring GPG backup..."

    local BACKUP_DIR="${BACKUP_DIR:-/var/backups/opendataremoval}"
    local GPG_RECIPIENT="${GPG_RECIPIENT:-}"

    # Create backup directory
    mkdir -p "${BACKUP_DIR}"
    chmod 700 "${BACKUP_DIR}"

    # Generate GPG key if not exists (non-interactive)
    if [ -z "$GPG_RECIPIENT" ]; then
        # Use existing key or generate a new one
        GPG_RECIPIENT=$(gpg --list-keys --with-colons 2>/dev/null | grep "^pub" | head -1 | cut -d: -f5)
        if [ -z "$GPG_RECIPIENT" ]; then
            log_warn "No GPG key found. Generate one with:"
            log_warn "  gpg --full-generate-key"
            log_warn "Then set GPG_RECIPIENT=<key-id>"
            return 0
        fi
    fi

    # Create backup script
    cat > /usr/local/bin/homeguard-backup <<BACKUP_EOF
#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR}"
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
ARCHIVE="\${BACKUP_DIR}/opendataremoval-\${TIMESTAMP}.tar.gz"
ENCRYPTED="\${ARCHIVE}.gpg"

# Backup critical files
tar czf "\${ARCHIVE}" \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    -C / \
    etc/opendataremoval/ \
    var/backups/opendataremoval/ \
    usr/local/bin/homeguard-backup 2>/dev/null || true

# Encrypt with GPG
gpg --batch --yes --recipient "${GPG_RECIPIENT}" --encrypt "\${ARCHIVE}"
rm -f "\${ARCHIVE}"

# Keep only last 7 backups
ls -t "\${BACKUP_DIR}"/opendataremoval-*.gpg 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "\${ENCRYPTED} created at \$(date)"
BACKUP_EOF

    chmod 750 /usr/local/bin/homeguard-backup
    chown root:adm /usr/local/bin/homeguard-backup

    # Create sample .env backup
    if [ -f .env ]; then
        cp .env "${BACKUP_DIR}/.env.backup"
        chmod 600 "${BACKUP_DIR}/.env.backup"
    fi

    # Run initial backup
    /usr/local/bin/homeguard-backup
    log_info "Initial backup created"

    # Verify
    local count
    count=$(gpg --decrypt "${BACKUP_DIR}/opendataremoval-*.gpg" 2>/dev/null | grep -c DB_ENCRYPTION_KEY || echo "0")
    log_info "Backup verification: DB_ENCRYPTION_KEY found = ${count}"
}

# --------------------------------------------------
# 5. Cron Backup Schedule
# --------------------------------------------------
configure_cron_backup() {
    log_info "Configuring cron backup schedule..."

    local CRON_JOB="0 2 * * * /usr/local/bin/homeguard-backup >> /var/log/homeguard/backup.log 2>&1"

    # Add cron job
    (crontab -l 2>/dev/null | grep -v homeguard-backup; echo "${CRON_JOB}") | crontab -
    log_info "Cron job added: daily backup at 2:00 AM"

    # Verify
    crontab -l | grep backup
}

# --------------------------------------------------
# Main
# --------------------------------------------------
main() {
    log_info "============================================"
    log_info "HomeGuard Host Security Hardening"
    log_info "============================================"
    log_warn "This script requires root/sudo access."
    log_warn "It will modify firewall, install packages, and change system settings."

    if [ "${1:-}" != "--force" ]; then
        read -p "Continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "Aborted."
            exit 0
        fi
    fi

    configure_ufw
    configure_fail2ban
    configure_system_hardening
    configure_gpg_backup
    configure_cron_backup

    log_info "============================================"
    log_info "Host security hardening complete!"
    log_info "============================================"
    log_info ""
    log_info "Next steps:"
    log_info "  1. Run security verification: scripts/security_verification.py"
    log_info "  2. Test backup restore: scripts/backup_restore_test.sh"
    log_info "  3. Review firewall: sudo ufw status verbose"
    log_info "  4. Review fail2ban: sudo fail2ban-client status"
}

main "$@"
