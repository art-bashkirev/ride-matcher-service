from __future__ import annotations
import asyncio
import contextlib
import time
from typing import Optional
from aiohttp import web

from config.log_setup import get_logger
from config.settings import get_config


logger = get_logger(__name__)

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        cfg = get_config()
        self._host = host or cfg.http_host
        self._port = port or cfg.http_port
        # Inline logging middleware
        async def request_logging_middleware(request, handler):
            import uuid
            start = time.time()
            request_id = str(uuid.uuid4())
            request['request_id'] = request_id
            logger.info("--> %s %s rqid=%s", request.method, request.rel_url, request_id)
            try:
                response = await handler(request)
                return response
            finally:
                duration = (time.time() - start) * 1000
                status = getattr(locals().get('response', None), 'status', None)
                logger.info("<-- %s %s %s %.2fms rqid=%s", request.method, request.rel_url, status, duration, request_id)

        self._app = web.Application(middlewares=[request_logging_middleware])
        self._app['started_at'] = None
        self._runner = None
        self._site = None
        self._started = False
        # Inline health route
        async def health(request):
            started_at = request.app['started_at']
            uptime = time.time() - started_at if started_at else 0.0
            return web.json_response({
                "status": "ok",
                "uptime_seconds": round(uptime, 3),
                "started_at_epoch": started_at,
                "request_id": request.get('request_id'),
            })
        self._app.router.add_get('/healthz', health)

    async def start(self):
        if self._started:
            logger.debug("ApiServerService already started")
            return
        logger.info("Starting API server on %s:%s", self._host, self._port)
        self._runner = web.AppRunner(self._app, access_log=None)
        await self._runner.setup()
        self._site = web.TCPSite(self._runner, host=self._host, port=self._port)
        await self._site.start()
        self._app['started_at'] = time.time()
        self._started = True
        logger.info("API server started on http://%s:%s", self._host, self._port)

    async def stop(self):
        if not self._started:
            return
        logger.info("Stopping API server")
        with contextlib.suppress(Exception):
            if self._site:
                await self._site.stop()
            if self._runner:
                await self._runner.cleanup()
        self._started = False
        logger.info("API server stopped")
