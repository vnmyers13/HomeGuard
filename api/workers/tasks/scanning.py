from celery import shared_task

@shared_task
def dispatch_daily_scan():
    """Daily full scan - placeholder for Sprint 1."""
    pass

@shared_task
def scan_broker(profile_id, broker_id, scan_run_id):
    """Scan a single broker for a profile - placeholder."""
    pass
