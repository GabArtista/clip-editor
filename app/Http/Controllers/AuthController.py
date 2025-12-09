from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.Providers.DatabaseServiceProvider import get_db
from app.Repositories.UserRepository import UserRepository
from app.Services.UserService import UserService
from app.Http.Middleware.AuthMiddleware import create_access_token
from app.Helpers.PasswordHelper import verify_password
from app.Http.Requests.Auth.LoginRequest import LoginRequest as UserLoginDTO
from app.Http.Resources.UserResource import TokenResponseResource as TokenResponseDTO, UserResource as UserResponseDTO
from config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Autenticação de usuário",
    description="""
    Autentica um usuário e retorna um token JWT válido por 24 horas.
    
    **Parâmetros:**
    - `username`: Nome de usuário ou email
    - `password`: Senha do usuário
    
    **Retorna:**
    - `access_token`: Token JWT para usar nas requisições autenticadas
    - `token_type`: Tipo do token (sempre "bearer")
    - `user`: Dados do usuário autenticado
    
    **Uso do token:**
    Adicione o header `Authorization: Bearer {access_token}` nas requisições protegidas.
    """
)
def login(credentials: UserLoginDTO, db: Session = Depends(get_db)):
    """Autentica usuário e retorna token JWT"""
    try:
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
        
        user = user_service.authenticate_user(credentials.username, credentials.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas"
            )
        
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id},
            expires_delta=access_token_expires
        )
        
        return TokenResponseDTO(
            access_token=access_token,
            token_type="bearer",
            user=UserResponseDTO(
                id=user.id,
                email=user.email,
                username=user.username,
                webhook_url=user.webhook_url,
                role=user.role,
                is_active=user.is_active,
                is_blocked=user.is_blocked,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao fazer login: {str(e)}"
        )

