import logging

logger = logging.getLogger(__name__)

def on_startup(job_store):
    """
    Recover jobs stuck in 'running' state.
    """
    recovered = 0
    for job_id, job in job_store.all().items():
        if job["status"] == "running":
            job_store.update(job_id, "failed", "recovered_after_restart")
            recovered += 1

    logger.info(
        "Startup recovery complete",
        extra={"recovered_jobs": recovered},
    )


def on_shutdown():
    """
    Hook for graceful shutdown.
    """
    logger.info("Service shutting down gracefully")
