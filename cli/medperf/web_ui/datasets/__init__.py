from fastapi import APIRouter
from .routes import router as ui_router

router = APIRouter()

router.include_router(ui_router)
