from __future__ import annotations
import time
from aiohttp import web

async def health(request: web.Request):
    started_at = request.app['started_at']
    uptime = time.time() - started_at if started_at else 0.0
    return web.json_response({
        "status": "ok",
        "uptime_seconds": round(uptime, 3),
        "started_at_epoch": started_at,
        "request_id": request.get('request_id'),
    })
