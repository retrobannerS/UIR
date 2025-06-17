from fastapi import APIRouter

from api.v1.endpoints import auth, users, tables

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tables.router, prefix="/tables", tags=["tables"])
api_router.include_router(auth.router, tags=["auth"])
