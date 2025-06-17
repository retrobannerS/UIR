from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.v1.api import api_router
from core.middleware import CacheBustingMiddleware
from db.base import Base
from db.session import engine


def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    create_tables()
    yield
    # Code to run on shutdown


def create_app() -> FastAPI:
    app = FastAPI(title="Text-to-SQL Service", lifespan=lifespan)

    app.add_middleware(CacheBustingMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/login")
    async def read_login():
        return FileResponse("templates/login.html")

    @app.get("/queries")
    async def read_queries(request: Request):
        return FileResponse("templates/index.html")

    @app.get("/help")
    async def read_help():
        return FileResponse("templates/help.html")

    @app.get("/settings")
    async def read_settings():
        return FileResponse("templates/settings.html")

    @app.get("/")
    async def read_root():
        return RedirectResponse(url="/queries")

    return app


app = create_app()
