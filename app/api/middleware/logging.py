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
    try:
        response = await handler(request)
        return response
    finally:
        duration = (time.time() - start) * 1000
        status = (
            request.get("_override_status")
            or getattr(
                getattr(locals().get("response", None), "status", None),
                "__int__",
                lambda: None,
            )()
        )
        logger.info(
            "<-- %s %s %s %.2fms rqid=%s",
            request.method,
            request.rel_url,
            status,
            duration,
            request_id,
        )
