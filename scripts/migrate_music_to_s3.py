#!/usr/bin/env python3
"""
Script para migrar arquivos de música do storage local para S3/MinIO.

Uso:
    python scripts/migrate_music_to_s3.py

Certifique-se de ter configurado as variáveis de ambiente antes de executar:
    - MUSIC_STORAGE_DRIVER=s3
    - OBJECT_STORAGE_ENDPOINT
    - OBJECT_STORAGE_BUCKET_MEDIA
    - OBJECT_STORAGE_ACCESS_KEY
    - OBJECT_STORAGE_SECRET_KEY
"""

import sys
from pathlib import Path
from typing import Optional
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.settings import get_database_url
from app.models import AudioFile, MusicAsset
from app.services.storage import S3StorageDriver, LocalStorageDriver


def migrate_audio_files():
    """Migra arquivos de música do storage local para S3."""
    # Carrega variáveis de ambiente
    load_dotenv(".env.dev", override=False)
    load_dotenv(".env", override=True)
    
    # Verifica se está configurado para usar S3
    driver = os.getenv("MUSIC_STORAGE_DRIVER", "local").lower()
    if driver != "s3":
        print(f"⚠️  MUSIC_STORAGE_DRIVER está configurado como '{driver}'. Configure como 's3' para migrar.")
        return
    
    # Conecta ao banco de dados
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Cria drivers
    local_driver = LocalStorageDriver(Path(os.getenv("MUSIC_STORAGE_DIR", "music_storage")))
    
    endpoint = os.getenv("OBJECT_STORAGE_ENDPOINT")
    bucket = os.getenv("OBJECT_STORAGE_BUCKET_MEDIA", "media")
    access_key = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
    secret_key = os.getenv("OBJECT_STORAGE_SECRET_KEY")
    region = os.getenv("OBJECT_STORAGE_REGION", "us-east-1")
    
    if not all([endpoint, access_key, secret_key]):
        print("❌ Erro: Variáveis de ambiente S3 não configuradas.")
        db.close()
        return
    
    s3_driver = S3StorageDriver(endpoint, bucket, access_key, secret_key, region)
    
    # Busca todos os arquivos de áudio
    audio_files = db.query(AudioFile).all()
    print(f"📦 Encontrados {len(audio_files)} arquivos de áudio para migrar.")
    
    migrated_count = 0
    error_count = 0
    
    for audio_file in audio_files:
        try:
            # Extrai o path do arquivo
            file_path = Path(audio_file.storage_path)
            
            # Verifica se o arquivo existe no storage local
            if not file_path.exists():
                print(f"⚠️  Arquivo não encontrado: {file_path}")
                error_count += 1
                continue
            
            # Lê o conteúdo do arquivo
            file_content = file_path.read_bytes()
            
            # Busca o music_asset associado
            music_asset = db.query(MusicAsset).filter_by(audio_file_id=audio_file.id).first()
            if not music_asset:
                print(f"⚠️  MusicAsset não encontrado para audio_file {audio_file.id}")
                error_count += 1
                continue
            
            # Define a chave do objeto
            suffix = file_path.suffix or ".mp3"
            object_key = f"media/{music_asset.user_id}/{music_asset.id}/original{suffix}"
            
            # Faz upload para S3
            print(f"📤 Migrando: {file_path.name} -> s3://{bucket}/{object_key}")
            s3_driver.upload_file(
                file_content=file_content,
                object_key=object_key,
                content_type=audio_file.mime_type,
            )
            
            # Atualiza o storage_path no banco
            s3_url = f"s3://{bucket}/{object_key}"
            audio_file.storage_path = s3_url
            db.add(audio_file)
            
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Erro ao migrar arquivo {audio_file.id}: {e}")
            error_count += 1
    
    # Commit das mudanças
    db.commit()
    db.close()
    
    print(f"\n✅ Migração concluída!")
    print(f"   - Arquivos migrados: {migrated_count}")
    print(f"   - Erros: {error_count}")


if __name__ == "__main__":
    migrate_audio_files()


