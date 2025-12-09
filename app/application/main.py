from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.application.controllers import (
    auth_controller,
    user_controller,
    music_controller,
    publish_controller,
    video_controller,
    publication_queue_controller,
    template_controller,
    video_edit_controller
)
from app.application.exceptions import setup_exception_handlers
from app.application.scheduler import setup_scheduler, start_scheduler, shutdown_scheduler
import os
import atexit

# Cria diretórios necessários
os.makedirs(settings.VIDEOS_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.MUSIC_DIR, exist_ok=True)
os.makedirs(settings.COOKIES_DIR, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## API para Edição Automática de Clips de Música
    
    Sistema completo de edição de vídeos com sincronização de música e fila inteligente de publicações.
    
    ### Funcionalidades Principais:
    
    - 🔐 **Autenticação JWT**: Sistema seguro com roles (Admin/User)
    - 🎵 **Gerenciamento de Músicas**: Upload e gerenciamento de arquivos MP3
    - 🎬 **Edição de Vídeos**: Download de Reels do Instagram e sincronização com música
    - 📅 **Fila de Publicações**: Agendamento automático (10/mês, horários 10h/13h/17h)
    - 🔗 **Integração N8N**: Publicação automática via webhook
    
    ### Como Usar:
    
    1. Faça login em `/api/v1/auth/login`
    2. Configure seu webhook URL no perfil
    3. Faça upload de músicas em `/api/v1/musics`
    4. Processe vídeos em `/api/v1/videos/process`
    5. Acompanhe publicações em `/api/v1/publications`
    
    ### Documentação Completa:
    
    - Swagger UI: `/docs`
    - ReDoc: `/redoc`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Clip Editor API",
        "email": "support@clipeditor.com",
    },
    license_info={
        "name": "Proprietary",
    },
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar origens
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files - removido mount direto para permitir controle de acesso por usuário
# Os arquivos são servidos via endpoint com validação de usuário

# Exception handlers
setup_exception_handlers(app)

# Routers
app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(music_controller.router)
app.include_router(publish_controller.router)
app.include_router(video_controller.router)
app.include_router(publication_queue_controller.router)
app.include_router(template_controller.router)
app.include_router(video_edit_controller.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "service": settings.APP_NAME
    }


@app.get("/", tags=["Root"])
def root():
    """Root endpoint"""
    return {
        "message": f"Bem-vindo à {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.on_event("startup")
async def startup_event():
    """Evento de inicialização da aplicação"""
    # Inicia scheduler em background (não bloqueia)
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de encerramento da aplicação"""
    shutdown_scheduler()


# Garante que scheduler seja parado ao encerrar
atexit.register(shutdown_scheduler)

