"""FastAPI application factory."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response

from app.api import admin, calls, health, incidents, network, pipeline
from app.config import Settings
from app.db import make_engine, make_session_factory
from app.observability.context import request_id_var

API_TITLE = "Aegis-Net API"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(title=API_TITLE, version=health.VERSION,
                  description="Network intelligence and autonomous DevSecOps platform (synthetic data).")
    engine = make_engine(settings.database_url)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = make_session_factory(engine)

    @app.middleware("http")
    async def request_id(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        incoming = request.headers.get("X-Request-ID", "")
        rid = incoming if 0 < len(incoming) <= 64 and incoming.replace("-", "").isalnum() else uuid.uuid4().hex
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response

    for module in (health, pipeline, calls, network, incidents, admin):
        app.include_router(module.router)
    return app
