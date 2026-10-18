"""Gunicorn configuration.

Gunicorn writes its error log (startup messages, worker lifecycle, and real
errors) to stderr by default, and Railway labels everything on stderr as
severity "error". Route both the error log and the access log to stdout so
that normal INFO output is not mislabelled. Log levels are unchanged, so
genuine errors are still emitted at ERROR level in the message text.
"""

loglevel = "info"

logconfig_dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "root": {"level": "INFO", "handlers": ["stdout"]},
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["stdout"],
            "propagate": False,
            "qualname": "gunicorn.error",
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["stdout"],
            "propagate": False,
            "qualname": "gunicorn.access",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": "ext://sys.stdout",
        },
    },
    "formatters": {
        "generic": {
            "format": "[%(asctime)s] [%(process)d] [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
            "class": "logging.Formatter",
        },
    },
}
