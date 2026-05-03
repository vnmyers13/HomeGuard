from celery import shared_task

@shared_task
def purge_expired_screenshots():
    """Purge old screenshots - placeholder."""
    pass

@shared_task
def compute_disk_usage():
    """Compute disk usage - placeholder."""
    pass
