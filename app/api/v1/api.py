from fastapi import APIRouter

from features.users import api as users_api
from features.tables import api as tables_api

api_router = APIRouter()
api_router.include_router(users_api.router, prefix="/users", tags=["users"])
api_router.include_router(tables_api.router, prefix="/tables", tags=["tables"])
