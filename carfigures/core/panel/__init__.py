import os
import pathlib

from fastapi import FastAPI
from fastapi_admin.app import app as admin_app
from fastapi_admin.exceptions import (
    forbidden_error_exception,
    not_found_error_exception,
    server_error_exception,
    unauthorized_error_exception,
)
from fastapi_admin.providers.login import UsernamePasswordProvider
from redis import asyncio as aioredis
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from tortoise.contrib.fastapi import register_tortoise

from carfigures.__main__ import TORTOISE_ORM
from carfigures.core.panel import resources, routes  # noqa: F401
from carfigures.core.models import Admin

BASE_DIR = pathlib.Path(".")


def init_fastapi_app() -> FastAPI:
    app = FastAPI()
    app.mount(
        "/static",
        StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    )

    @app.get("/")
    async def index():
        return RedirectResponse(url="/admin")

    admin_app.add_exception_handler(
        HTTP_500_INTERNAL_SERVER_ERROR,
        server_error_exception,  # type: ignore
    )
    admin_app.add_exception_handler(HTTP_404_NOT_FOUND, not_found_error_exception)  # type: ignore
    admin_app.add_exception_handler(HTTP_403_FORBIDDEN, forbidden_error_exception)  # type: ignore
    admin_app.add_exception_handler(
        HTTP_401_UNAUTHORIZED,
        unauthorized_error_exception,  # type: ignore
    )

    @app.on_event("startup")
    async def startup():
        redis = aioredis.from_url(
            os.environ["CARFIGURESBOT_REDIS_URL"], decode_responses=True, encoding="utf8"
        )
        await admin_app.configure(
            logo_url="https://i.imgur.com/EijzuYy.png",
            template_folders=[os.path.join(BASE_DIR, "carfigures", "templates")],
            favicon_url="https://raw.githubusercontent.com/fastapi-admin/"  # type: ignore
            "fastapi-admin/dev/images/favicon.png",
            providers=[
                UsernamePasswordProvider(
                    login_logo_url="https://preview.tabler.io/static/logo.svg",
                    admin_model=Admin,
                )
            ],
            redis=redis,
        )

    app.mount("/admin", admin_app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    register_tortoise(app, config=TORTOISE_ORM)

    return app


_app = init_fastapi_app()
