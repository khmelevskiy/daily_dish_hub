import logging


LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def setup_logging(level: int = logging.INFO, enable_access_log: bool = False) -> None:
    """Configure application-wide logging format and levels.

    - Unified formatter across app and uvicorn loggers
    - Reduced noise by default (uvicorn.access at WARNING unless explicitly enabled)
    """
    logging.basicConfig(level=level, format=LOG_FORMAT, datefmt=DATE_FORMAT)

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Align uvicorn/fastapi loggers with our formatter and level
    for name in ("uvicorn", "uvicorn.error", "fastapi"):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setFormatter(formatter)

    # Access logs can be very verbose; keep at WARNING by default
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.setLevel(level if enable_access_log else logging.WARNING)
    for handler in access_logger.handlers:
        handler.setFormatter(formatter)
