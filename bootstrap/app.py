"""
Bootstrap da aplicação - Laravel Style
"""
import os
import atexit
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes.api import api_router
from app.Exceptions.Handler import setup_exception_handlers
from app.Providers.SchedulerProvider import setup_scheduler, start_scheduler, shutdown_scheduler
from app.Providers.DatabaseServiceProvider import SessionLocal
from app.Repositories.UserRepository import UserRepository
from app.Services.UserService import UserService
from app.domain.entities.user import UserRole

logger = logging.getLogger(__name__)

# Cria diretórios necessários
os.makedirs(settings.VIDEOS_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.MUSIC_DIR, exist_ok=True)
os.makedirs(settings.COOKIES_DIR, exist_ok=True)

# Cria aplicação FastAPI
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

# Exception handlers
setup_exception_handlers(app)

# Inclui rotas da API
app.include_router(api_router)


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
    ensure_default_admin()
    # Inicia scheduler em background
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de encerramento da aplicação"""
    shutdown_scheduler()


# Garante que scheduler seja parado ao encerrar
atexit.register(shutdown_scheduler)


def ensure_default_admin():
    """
    Garante que exista um usuário admin padrão.
    Se não existir username 'admin', cria com a senha definida.
    """
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
        existing = user_repo.get_by_username("admin")
        if existing:
            return

        user_service.create_user(
            email="gabrielw.dev@gmail.com",
            username="admin",
            password="0102G@briel",
            role=UserRole.ADMIN,
            webhook_url=None,
        )
        logger.info("Usuário admin padrão criado (username: admin, email: gabrielw.dev@gmail.com)")
    except Exception as exc:
        logger.error(f"Falha ao garantir admin padrão: {exc}")
    finally:
        db.close()

