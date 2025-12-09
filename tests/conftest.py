"""
Configuração global para testes
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.infrastructure.database.base import Base, get_db
from app.application.main import app
from app.config import settings

# Database de teste (SQLite em memória para testes rápidos)
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Cria banco de teste para cada teste"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Cliente de teste FastAPI"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user_data():
    """Dados de usuário admin para testes"""
    return {
        "email": "admin@test.com",
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "webhook_url": "https://test.webhook.com"
    }


@pytest.fixture
def user_data():
    """Dados de usuário comum para testes"""
    return {
        "email": "user@test.com",
        "username": "user",
        "password": "user123",
        "role": "user",
        "webhook_url": "https://user.webhook.com"
    }

