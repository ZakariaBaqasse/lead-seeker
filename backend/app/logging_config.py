import logging
import sys
from app.config import settings


def configure_logging() -> None:
    """Configure structured logging. JSON in production, human-readable in dev."""
    is_dev = "localhost" in settings.DATABASE_URL

    if is_dev:
        fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        logging.basicConfig(
            level=logging.INFO,
            format=fmt,
            stream=sys.stdout,
        )
    else:
        fmt = '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}'
        logging.basicConfig(
            level=logging.INFO,
            format=fmt,
            stream=sys.stdout,
        )

    # Quieten noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)
