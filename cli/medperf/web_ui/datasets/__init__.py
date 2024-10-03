from fastapi import APIRouter
from .routes_submit import router as submit_router
from .routes_prepare import router as prepare_router
from .routes_operational import router as operational_router
from .routes import router as ui_router

router = APIRouter()

router.include_router(submit_router)
router.include_router(prepare_router)
router.include_router(operational_router)
router.include_router(ui_router)
