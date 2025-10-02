from __future__ import annotations

import time
import uuid

from aiohttp import web

from config.log_setup import get_logger

logger = get_logger(__name__)


@web.middleware
async def request_logging_middleware(request: web.Request, handler):
    start = time.time()
    request_id = str(uuid.uuid4())
    request["request_id"] = request_id
    logger.info("--> %s %s rqid=%s", request.method, request.rel_url, request_id)
    response: web.StreamResponse | None = None
    status: int | None = None
    try:
        response = await handler(request)
        status = getattr(response, "status", None)
        return response
    except web.HTTPException as exc:
        status = exc.status
        raise
    except Exception:
        status = request.get("_override_status", 500)
        raise
    finally:
        duration = (time.time() - start) * 1000
        if status is None:
            status = request.get("_override_status")
        if status is None and response is not None:
            status = getattr(response, "status", None)
        logger.info(
            "<-- %s %s %s %.2fms rqid=%s",
            request.method,
            request.rel_url,
            status if status is not None else "?",
            duration,
            request_id,
        )
