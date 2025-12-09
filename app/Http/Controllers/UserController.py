from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.Providers.DatabaseServiceProvider import get_db
from app.Repositories.UserRepository import UserRepository
from app.Services.UserService import UserService
from app.domain.entities.user import User
from app.Http.Middleware.AuthMiddleware import get_current_user, get_current_admin_user
    UserCreateDTO,
    UserUpdateDTO,
    UserResponseDTO
)
from app.application.validators import validate_webhook_url

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.post("", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Cria um novo usuário (apenas admin)"""
    try:
        # Valida webhook URL se fornecido
        webhook_url = None
        if user_data.webhook_url:
            try:
                webhook_url = validate_webhook_url(user_data.webhook_url)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
        
        user = user_service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            role=user_data.role,
            webhook_url=webhook_url
        )
        
        return UserResponseDTO(
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao criar usuário: {str(e)}"
        )


@router.get("", response_model=List[UserResponseDTO])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Lista todos os usuários (apenas admin)"""
    try:
        user_repo = UserRepository(db)
        users = user_repo.get_all(skip=skip, limit=limit)
        
        return [
            UserResponseDTO(
                id=user.id,
                email=user.email,
                username=user.username,
                role=user.role,
                is_active=user.is_active,
                is_blocked=user.is_blocked,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            for user in users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar usuários: {str(e)}"
        )


@router.get("/me", response_model=UserResponseDTO)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtém informações do usuário atual"""
    return UserResponseDTO(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        is_blocked=current_user.is_blocked,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.get("/{user_id}", response_model=UserResponseDTO)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Obtém um usuário por ID (apenas admin)"""
    try:
        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
        
        return UserResponseDTO(
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar usuário: {str(e)}"
        )


@router.put("/me", response_model=UserResponseDTO)
def update_current_user(
    user_data: UserUpdateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza o próprio usuário"""
    try:
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
        
        update_data = user_data.dict(exclude_unset=True)
        # Remove campos que usuário comum não pode alterar
        update_data.pop("role", None)
        update_data.pop("is_active", None)
        update_data.pop("is_blocked", None)
        
        # Valida webhook URL se fornecido
        if "webhook_url" in update_data and update_data["webhook_url"]:
            try:
                update_data["webhook_url"] = validate_webhook_url(update_data["webhook_url"])
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        if "password" in update_data:
            update_data["password"] = update_data["password"]
        
        user = user_service.update_user(current_user.id, **update_data)
        
        return UserResponseDTO(
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserResponseDTO)
def update_user(
    user_id: int,
    user_data: UserUpdateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Atualiza um usuário (apenas admin)"""
    try:
        # Valida webhook URL se fornecido
        if "webhook_url" in user_data.dict(exclude_unset=True) and user_data.webhook_url:
            try:
                user_data.webhook_url = validate_webhook_url(user_data.webhook_url)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
        
        update_data = user_data.dict(exclude_unset=True)
        if "password" in update_data:
            update_data["password"] = update_data["password"]
        
        user = user_service.update_user(user_id, **update_data)
        
        return UserResponseDTO(
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )


@router.post("/{user_id}/block", response_model=UserResponseDTO)
def block_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Bloqueia um usuário (apenas admin)"""
    try:
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
        
        user = user_service.block_user(user_id)
        
        return UserResponseDTO(
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao bloquear usuário: {str(e)}"
        )


@router.post("/{user_id}/unblock", response_model=UserResponseDTO)
def unblock_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Desbloqueia um usuário (apenas admin)"""
    try:
        user_repo = UserRepository(db)
        user_service = UserService(user_repo)
        
        user = user_service.unblock_user(user_id)
        
        return UserResponseDTO(
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao desbloquear usuário: {str(e)}"
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deleta um usuário (apenas admin)"""
    try:
        if user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível deletar seu próprio usuário"
            )
        
        user_repo = UserRepository(db)
        success = user_repo.delete(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar usuário: {str(e)}"
        )

