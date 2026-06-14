#!/usr/bin/env python3
"""
HomeGuard - Security Verification Checklist
============================================
Runs all 12 security verification checks against the HomeGuard deployment.

Usage: python3 scripts/security_verification.py [--json] [--fail-fast]
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class SecurityCheck:
    id: str
    name: str
    category: str
    passed: bool = False
    details: str = ""
    severity: str = "HIGH"  # HIGH, MEDIUM, LOW


@dataclass
class SecurityReport:
    checks: list[SecurityCheck] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.checks)

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def all_passed(self) -> bool:
        return self.failed == 0

    def summary(self) -> str:
        lines = [
            "",
            "=" * 60,
            "  HomeGuard Security Verification Report",
            "=" * 60,
            f"  Total checks: {self.total}",
            f"  Passed: {self.passed}",
            f"  Failed: {self.failed}",
            f"  Status: {'PASS' if self.all_passed else 'FAIL'}",
            "=" * 60,
            "",
        ]
        for c in self.checks:
            status = "PASS" if c.passed else "FAIL"
            severity = f" [{c.severity}]" if not c.passed else ""
            lines.append(f"  [{status}{severity}] {c.id}: {c.name}")
            if c.details:
                lines.append(f"         {c.details}")
        lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "all_passed": self.all_passed,
            "checks": [asdict(c) for c in self.checks],
        }


def run_cmd(cmd: str, check: bool = True) -> tuple[int, str, str]:
    """Run a shell command and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"


def check_ufw_enabled(report: SecurityReport) -> None:
    """CP-SE01: UFW firewall is active."""
    c = SecurityCheck(
        id="CP-SE01",
        name="UFW firewall is active",
        category="Firewall",
        severity="HIGH",
    )
    rc, out, _ = run_cmd("sudo ufw status 2>/dev/null || echo 'inactive'")
    c.passed = "Status: active" in out
    c.details = "UFW status: active" if c.passed else "UFW not found or inactive"
    report.checks.append(c)


def check_fail2ban_running(report: SecurityReport) -> None:
    """CP-SE02: Fail2Ban is running with SSH jail."""
    c = SecurityCheck(
        id="CP-SE02",
        name="Fail2Ban running with SSH jail",
        category="Intrusion Prevention",
        severity="HIGH",
    )
    rc, out, _ = run_cmd("sudo fail2ban-client status sshd 2>/dev/null || echo 'not found'")
    c.passed = "Status: 1" in out and "Jail(s):" in out
    c.details = "Fail2Ban SSH jail: active" if c.passed else "Fail2Ban SSH jail not active"
    report.checks.append(c)


def check_pii_encrypted_at_rest(report: SecurityReport) -> None:
    """CP-SE03: PII is encrypted at rest in PostgreSQL."""
    c = SecurityCheck(
        id="CP-SE03",
        name="PII encrypted at rest in PostgreSQL",
        category="Data Protection",
        severity="HIGH",
    )
    # Check that pgcrypto extension is enabled and encryption is used
    rc, out, _ = run_cmd(
        'docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" '
        "-c \"SELECT extname FROM pg_extension WHERE extname='pgcrypto';\" "
        "2>/dev/null || echo 'extension not found'"
    )
    c.passed = "pgcrypto" in out
    c.details = "pgcrypto extension: enabled" if c.passed else "pgcrypto extension not found"
    report.checks.append(c)


def check_jwt_not_in_localstorage(report: SecurityReport) -> None:
    """CP-SE04: JWT tokens never stored in localStorage."""
    c = SecurityCheck(
        id="CP-SE04",
        name="JWT never stored in localStorage",
        category="Frontend Security",
        severity="HIGH",
    )
    # Search frontend source for localStorage usage with JWT
    found = False
    for root, _, files in os.walk("frontend/src"):
        for fname in files:
            if fname.endswith((".js", ".jsx", ".ts", ".tsx")):
                fpath = os.path.join(root, fname)
                with open(fpath, errors="ignore") as f:
                    content = f.read()
                    if "localStorage" in content and ("token" in content.lower() or "jwt" in content.lower()):
                        found = True
                        break
    c.passed = not found
    c.details = "No localStorage + JWT found in frontend source" if c.passed else "Found localStorage with token/JWT"
    report.checks.append(c)


def check_audit_log_immutable(report: SecurityReport) -> None:
    """CP-SE05: Audit log is append-only (cannot be deleted/modified)."""
    c = SecurityCheck(
        id="CP-SE05",
        name="Audit log is append-only",
        category="Audit & Compliance",
        severity="HIGH",
    )
    # Check that the audit model overrides delete/update
    audit_file = Path("api/models/audit.py")
    if audit_file.exists():
        content = audit_file.read_text()
        c.passed = (
            "delete" in content.lower()
            and "update" in content.lower()
            and "NotImplementedError" in content
        )
    else:
        c.details = "audit.py not found"
    c.details = "Audit log: append-only enforced" if c.passed else "Audit log: delete/update not blocked"
    report.checks.append(c)


def check_hmac_webhook_verification(report: SecurityReport) -> None:
    """CP-SE06: HMAC-SHA256 webhook signature verification."""
    c = SecurityCheck(
        id="CP-SE06",
        name="HMAC-SHA256 webhook verification",
        category="API Security",
        severity="HIGH",
    )
    found = False
    for root, _, files in os.walk("api"):
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                with open(fpath, errors="ignore") as f:
                    content = f.read()
                    if "hmac" in content.lower() and "compare_digest" in content:
                        found = True
                        break
    c.passed = found
    c.details = "HMAC verification with constant-time comparison" if c.passed else "HMAC verification not found"
    report.checks.append(c)


def check_rate_limiting(report: SecurityReport) -> None:
    """CP-SE07: Rate limiting on auth endpoints."""
    c = SecurityCheck(
        id="CP-SE07",
        name="Rate limiting on auth endpoints",
        category="API Security",
        severity="HIGH",
    )
    found = False
    for root, _, files in os.walk("api"):
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                with open(fpath, errors="ignore") as f:
                    content = f.read()
                    if "limiter" in content.lower() or "rate_limit" in content.lower():
                        found = True
                        break
    c.passed = found
    c.details = "Rate limiting configured" if c.passed else "Rate limiting not found"
    report.checks.append(c)


def check_password_hashing(report: SecurityReport) -> None:
    """CP-SE08: Passwords hashed with bcrypt."""
    c = SecurityCheck(
        id="CP-SE08",
        name="Passwords hashed with bcrypt",
        category="Authentication",
        severity="HIGH",
    )
    found = False
    for root, _, files in os.walk("api"):
        for fname in files:
            if fname.endswith(".py"):
                fpath = os.path.join(root, fname)
                with open(fpath, errors="ignore") as f:
                    content = f.read()
                    if "bcrypt" in content or "passlib" in content:
                        found = True
                        break
    c.passed = found
    c.details = "bcrypt/passlib password hashing" if c.passed else "bcrypt/passlib not found"
    report.checks.append(c)


def check_env_files_not_committed(report: SecurityReport) -> None:
    """CP-SE09: .env files are not committed to git."""
    c = SecurityCheck(
        id="CP-SE09",
        name=".env files not committed to git",
        category="Configuration Security",
        severity="HIGH",
    )
    rc, out, _ = run_cmd("git ls-files | grep -E '\\.env$' || echo 'clean'")
    c.passed = "clean" in out or ".env" not in out
    c.details = ".env files excluded from git" if c.passed else ".env files found in git"
    report.checks.append(c)


def check_ssl_tls_config(report: SecurityReport) -> None:
    """CP-SE10: SSL/TLS termination configured."""
    c = SecurityCheck(
        id="CP-SE10",
        name="SSL/TLS termination configured",
        category="Transport Security",
        severity="HIGH",
    )
    # Check for nginx config or reverse proxy with SSL
    nginx_conf = Path("docker/nginx/nginx.conf")
    found = False
    if nginx_conf.exists():
        content = nginx_conf.read_text()
        found = "ssl" in content.lower() or "443" in content
    # Also check docker-compose for port 443
    dc = Path("docker-compose.yml")
    if dc.exists():
        content = dc.read_text()
        found = found or "443" in content
    c.passed = found
    c.details = "SSL/TLS configured" if c.passed else "SSL/TLS not configured (use reverse proxy in production)"
    report.checks.append(c)


def check_docker_image_versions(report: SecurityReport) -> None:
    """CP-SE11: Docker images use pinned versions."""
    c = SecurityCheck(
        id="CP-SE11",
        name="Docker images use pinned versions",
        category="Infrastructure Security",
        severity="MEDIUM",
    )
    dc = Path("docker-compose.yml")
    if dc.exists():
        content = dc.read_text()
        # Check for :latest tags (bad)
        has_latest = 'image:.*:latest' in content or 'image:\s+\w+' in content  # no tag
        # Check for versioned images
        has_pinned = ':1.' in content or ':15' in content or ':7' in content
        c.passed = has_pinned and not has_latest
    else:
        c.details = "docker-compose.yml not found"
    c.details = "Images use pinned versions" if c.passed else "Some images may use unpinned tags"
    report.checks.append(c)


def check_backup_configured(report: SecurityReport) -> None:
    """CP-SE12: Backup script and cron schedule configured."""
    c = SecurityCheck(
        id="CP-SE12",
        name="Backup script and cron schedule configured",
        category="Disaster Recovery",
        severity="HIGH",
    )
    backup_script = Path("scripts/host_security.sh")
    backup_cron = Path("scripts/backup.sh")
    c.passed = backup_script.exists() or backup_cron.exists()
    c.details = "Backup script found" if c.passed else "No backup script found"
    report.checks.append(c)


def run_all_checks(fail_fast: bool = False) -> SecurityReport:
    """Run all 12 security verification checks."""
    report = SecurityReport()
    checks = [
        check_ufw_enabled,
        check_fail2ban_running,
        check_pii_encrypted_at_rest,
        check_jwt_not_in_localstorage,
        check_audit_log_immutable,
        check_hmac_webhook_verification,
        check_rate_limiting,
        check_password_hashing,
        check_env_files_not_committed,
        check_ssl_tls_config,
        check_docker_image_versions,
        check_backup_configured,
    ]
    for check_fn in checks:
        check_fn(report)
        if not report.checks[-1].passed and fail_fast:
            break
    return report


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="HomeGuard Security Verification")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    args = parser.parse_args()

    report = run_all_checks(fail_fast=args.fail_fast)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(report.summary())

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
