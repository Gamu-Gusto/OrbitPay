import json
import logging
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        # Merge extra kwargs passed via extra= dict
        for key in vars(record):
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            ):
                val = getattr(record, key, None)
                if val is not None and key not in log_obj:
                    log_obj[key] = val
        return json.dumps(log_obj)


def _build_logger() -> logging.Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    _logger = logging.getLogger("orbitpay")
    if not _logger.handlers:
        _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False
    return _logger


logger = _build_logger()
