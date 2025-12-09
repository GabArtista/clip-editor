"""
Rotas da API
"""
from fastapi import APIRouter
from app.Http.Controllers import (
    AuthController,
    UserController,
    MusicController,
    VideoController,
    VideoEditController,
    PublicationQueueController,
    TemplateController
)

# Router principal da API
api_router = APIRouter(prefix="/api/v1")

# Inclui todos os routers
api_router.include_router(AuthController.router)
api_router.include_router(UserController.router)
api_router.include_router(MusicController.router)
api_router.include_router(VideoController.router)
api_router.include_router(VideoEditController.router)
api_router.include_router(PublicationQueueController.router)
api_router.include_router(TemplateController.router)

