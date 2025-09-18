from __future__ import annotations
import asyncio
import contextlib
import time
from typing import Optional
from aiohttp import web

from config.log_setup import get_logger
from config.settings import get_config
from .middleware.logging import request_logging_middleware
from .routes.health import health

logger = get_logger(__name__)

class ApiServerService:
    """High-level API server service with middleware and routes."""

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        cfg = get_config()
        self._host = host or cfg.http_host
        self._port = port or cfg.http_port
        self._app = web.Application(middlewares=[request_logging_middleware])
        self._app['started_at'] = None
        self._runner: Optional[web.AppRunner] = None
        self._site: Optional[web.TCPSite] = None
        self._started = False
        self._register_routes()

    def _register_routes(self):
        self._app.router.add_get('/healthz', health)

    @property
    def app(self) -> web.Application:
        return self._app

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
