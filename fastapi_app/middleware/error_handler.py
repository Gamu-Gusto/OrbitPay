import traceback
import uuid
from datetime import datetime, timezone

from fastapi import Request
from fastapi.responses import JSONResponse

from core.logging_config import logger


async def global_error_handler(request: Request, exc: Exception):
    request_id = str(uuid.uuid4())[:8]
    user_id = None
    try:
        # Try to extract user_id from request state if available
        user_id = getattr(request.state, "user_id", None)
    except Exception:
        pass

    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "user_id": user_id,
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred.", "request_id": request_id},
    )
