#!/usr/bin/env python3
"""
Script para criar usuário admin inicial
Uso: python scripts/create_admin.py
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.infrastructure.database.base import SessionLocal, engine
from app.infrastructure.database.models import UserModel
from app.domain.entities.user import UserRole
from app.application.auth.password import get_password_hash
from getpass import getpass


def create_admin():
    """Cria usuário admin inicial"""
    db: Session = SessionLocal()
    
    try:
        print("=" * 50)
        print("Criação de Usuário Admin")
        print("=" * 50)
        
        # Verifica se já existe admin
        existing_admin = db.query(UserModel).filter(UserModel.role == UserRole.ADMIN).first()
        if existing_admin:
            print(f"\n⚠️  Já existe um usuário admin: {existing_admin.email}")
            response = input("Deseja criar outro? (s/N): ").strip().lower()
            if response != 's':
                print("Operação cancelada.")
                return
        
        # Coleta dados
        print("\nInforme os dados do administrador:")
        email = input("Email: ").strip()
        
        if not email:
            print("❌ Email é obrigatório!")
            return
        
        # Verifica se email já existe
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            print(f"❌ Email {email} já está em uso!")
            return
        
        username = input("Username: ").strip()
        if not username:
            print("❌ Username é obrigatório!")
            return
        
        # Verifica se username já existe
        existing = db.query(UserModel).filter(UserModel.username == username).first()
        if existing:
            print(f"❌ Username {username} já está em uso!")
            return
        
        password = getpass("Senha: ")
        if len(password) < 6:
            print("❌ Senha deve ter no mínimo 6 caracteres!")
            return
        
        password_confirm = getpass("Confirme a senha: ")
        if password != password_confirm:
            print("❌ Senhas não coincidem!")
            return
        
        webhook_url = input("Webhook URL (opcional, pode deixar em branco): ").strip()
        if not webhook_url:
            webhook_url = None
        
        # Cria usuário
        admin = UserModel(
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            webhook_url=webhook_url,
            role=UserRole.ADMIN,
            is_active=True,
            is_blocked=False
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("\n✅ Usuário admin criado com sucesso!")
        print(f"   ID: {admin.id}")
        print(f"   Email: {admin.email}")
        print(f"   Username: {admin.username}")
        print(f"   Role: {admin.role}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erro ao criar admin: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()

