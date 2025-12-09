"""
Testes de autenticação
"""
import pytest
from app.infrastructure.repositories import UserRepository
from app.domain.services.user_service import UserService
from app.domain.entities.user import UserRole


def test_create_user(db, user_data):
    """Testa criação de usuário"""
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    
    user = user_service.create_user(
        email=user_data["email"],
        username=user_data["username"],
        password=user_data["password"],
        role=UserRole.USER
    )
    
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.username == user_data["username"]
    assert user.role == UserRole.USER


def test_authenticate_user(db, user_data):
    """Testa autenticação de usuário"""
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    
    # Cria usuário
    user_service.create_user(
        email=user_data["email"],
        username=user_data["username"],
        password=user_data["password"]
    )
    
    # Autentica
    authenticated = user_service.authenticate_user(
        user_data["username"],
        user_data["password"]
    )
    
    assert authenticated is not None
    assert authenticated.email == user_data["email"]
    
    # Testa senha incorreta
    failed = user_service.authenticate_user(
        user_data["username"],
        "wrong_password"
    )
    assert failed is None


def test_login_endpoint(client, db, user_data):
    """Testa endpoint de login"""
    from app.infrastructure.repositories import UserRepository
    from app.domain.services.user_service import UserService
    
    # Cria usuário
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)
    user_service.create_user(
        email=user_data["email"],
        username=user_data["username"],
        password=user_data["password"]
    )
    
    # Testa login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": user_data["username"],
            "password": user_data["password"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    
    # Testa login com credenciais inválidas
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": user_data["username"],
            "password": "wrong_password"
        }
    )
    assert response.status_code == 401

