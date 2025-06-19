from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from api.v1.api import api_router
from core.middleware import CacheBustingMiddleware
from core.config import settings
from db.base import Base
from db.session import engine


def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    avatars_dir = os.path.join(settings.UPLOADS_DIR, "avatars")
    os.makedirs(avatars_dir, exist_ok=True)
    # create_tables()
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

    @app.get("/uploads/avatars/{filename:path}")
    async def get_avatar(filename: str):
        file_path = f"uploads/avatars/{filename}"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        return FileResponse(file_path, headers=headers)

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/login")
    async def read_login():
        return FileResponse("templates/login.html")

    @app.get("/queries", response_class=HTMLResponse)
    async def queries_page(request: Request):
        return HTMLResponse(content=open("templates/index.html").read())

    @app.get("/help", response_class=HTMLResponse)
    async def help_page(request: Request):
        return HTMLResponse(content=open("templates/help.html").read())

    @app.get("/settings", response_class=HTMLResponse)
    async def settings_page(request: Request):
        return HTMLResponse(content=open("templates/settings.html").read())

    @app.get("/")
    async def read_root():
        return RedirectResponse(url="/queries")

    return app


app = create_app()