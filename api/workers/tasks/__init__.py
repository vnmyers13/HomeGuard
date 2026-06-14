"""Celery task modules for OpenDataRemoval background jobs."""

try:
    from api.workers.tasks.scanning import (
        scan_broker,
        dispatch_daily_scan,
    )

    from api.workers.tasks.registry import (
        check_broker_opt_out_urls,
        upsert_broker_from_discovery,
    )

    from api.workers.tasks.maintenance import (
        cleanup_old_scans,
        purge_expired_screenshots,
    )

    from api.workers.tasks.requests import (
        execute_removal_request,
        followup_removal_request,
    )

    from api.workers.tasks.notifications import (
        send_scan_complete_notification,
        send_daily_digest,
    )
except ImportError:
    from workers.tasks.scanning import (
        scan_broker,
        dispatch_daily_scan,
    )

    from workers.tasks.registry import (
        check_broker_opt_out_urls,
        upsert_broker_from_discovery,
    )

    from workers.tasks.maintenance import (
        cleanup_old_scans,
        purge_expired_screenshots,
    )

    from workers.tasks.requests import (
        execute_removal_request,
        followup_removal_request,
    )

    from workers.tasks.notifications import (
        send_scan_complete_notification,
        send_daily_digest,
    )

__all__ = [
    # Scanning tasks
    "scan_broker",
    "dispatch_daily_scan",
    # Registry tasks
    "check_broker_opt_out_urls",
    "upsert_broker_from_discovery",
    # Maintenance tasks
    "cleanup_old_scans",
    "purge_expired_screenshots",
    # Removal request tasks
    "execute_removal_request",
    "followup_removal_request",
    # Notification tasks
    "send_scan_complete_notification",
    "send_daily_digest",
]