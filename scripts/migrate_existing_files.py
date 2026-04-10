#!/usr/bin/env python3
"""
Script para migrar arquivos existentes (músicas e vídeos) para o banco de dados
Registra arquivos que já existem nas pastas mas não estão no banco
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.Providers.DatabaseServiceProvider import SessionLocal
from app.Repositories.MusicRepository import MusicRepository
from app.Services.MusicService import MusicService
from app.Helpers.FFmpegHelper import get_audio_duration
from config import settings

def find_music_files() -> List[Tuple[int, str, str]]:
    """
    Encontra arquivos de música nas pastas music/{user_id}/
    Retorna: [(user_id, file_path, filename), ...]
    """
    music_files = []
    music_dir = Path(settings.MUSIC_DIR)
    
    if not music_dir.exists():
        return music_files
    
    # Itera sobre pastas de usuários
    for user_dir in music_dir.iterdir():
        if not user_dir.is_dir():
            continue
        
        try:
            user_id = int(user_dir.name)
        except ValueError:
            print(f"⚠ Pasta inválida ignorada: {user_dir.name}")
            continue
        
        # Busca arquivos MP3 na pasta do usuário
        for file_path in user_dir.glob("*.mp3"):
            music_files.append((user_id, str(file_path), file_path.name))
    
    return music_files

def register_music_file(user_id: int, file_path: str, filename: str, db) -> bool:
    """Registra um arquivo de música no banco"""
    try:
        music_repo = MusicRepository(db)
        music_service = MusicService(music_repo)
        
        # Verifica se já existe registro para este arquivo
        musics = music_repo.get_by_user_id(user_id)
        for music in musics:
            if music.file_path == file_path:
                print(f"  ✓ Já registrado: {filename}")
                return False
        
        # Obtém informações do arquivo
        file_size = os.path.getsize(file_path)
        
        # Tenta obter duração
        try:
            duration = get_audio_duration(file_path)
        except Exception as e:
            print(f"  ⚠ Não foi possível obter duração: {e}")
            duration = None
        
        # Gera nome baseado no filename
        name = os.path.splitext(filename)[0]
        # Remove UUID se presente (formato: uuid_nome.mp3)
        if len(name) > 32 and name[32] == '_':
            name = name[33:]
        
        # Cria registro
        music = music_service.create_music(
            user_id=user_id,
            name=name or "Música sem nome",
            filename=filename,
            file_path=file_path,
            duration=duration,
            file_size=file_size
        )
        
        print(f"  ✓ Registrado: {music.name} (ID: {music.id})")
        return True
        
    except ValueError as e:
        if "Já existe uma música com este nome" in str(e):
            print(f"  ⚠ Já existe música com este nome, tentando nome alternativo...")
            # Tenta com nome único
            try:
                name = f"{os.path.splitext(filename)[0]}_{user_id}"
                music = music_service.create_music(
                    user_id=user_id,
                    name=name,
                    filename=filename,
                    file_path=file_path,
                    duration=duration,
                    file_size=file_size
                )
                print(f"  ✓ Registrado com nome alternativo: {music.name} (ID: {music.id})")
                return True
            except Exception as e2:
                print(f"  ✗ Erro ao registrar: {e2}")
                return False
        else:
            print(f"  ✗ Erro: {e}")
            return False
    except Exception as e:
        print(f"  ✗ Erro ao registrar: {e}")
        return False

def main():
    print("=" * 60)
    print("  MIGRAÇÃO DE ARQUIVOS EXISTENTES")
    print("=" * 60)
    print()
    
    # Encontra arquivos de música
    print("🔍 Buscando arquivos de música...")
    music_files = find_music_files()
    
    if not music_files:
        print("  ℹ Nenhum arquivo de música encontrado")
        print()
        print("💡 Você pode fazer upload manualmente via API:")
        print("   POST /api/v1/musics")
        return
    
    print(f"  ✓ Encontrados {len(music_files)} arquivo(s) de música")
    print()
    
    # Registra no banco
    db = SessionLocal()
    registered = 0
    skipped = 0
    errors = 0
    
    try:
        print("📝 Registrando arquivos no banco de dados...")
        print()
        
        for user_id, file_path, filename in music_files:
            print(f"📄 {filename} (usuário {user_id}):")
            
            if not os.path.exists(file_path):
                print(f"  ✗ Arquivo não encontrado: {file_path}")
                errors += 1
                continue
            
            if register_music_file(user_id, file_path, filename, db):
                registered += 1
            else:
                skipped += 1
            print()
        
    finally:
        db.close()
    
    # Resumo
    print("=" * 60)
    print("  RESUMO")
    print("=" * 60)
    print(f"✓ Registrados: {registered}")
    print(f"⚠ Já existiam: {skipped}")
    print(f"✗ Erros: {errors}")
    print()
    
    if registered > 0:
        print("✅ Migração concluída!")
        print()
        print("💡 Os arquivos de vídeo processados não precisam ser migrados,")
        print("   pois são gerados automaticamente quando você processa um vídeo.")
    else:
        print("ℹ Nenhum arquivo novo foi registrado.")
        print()
        print("💡 Você pode fazer upload manualmente via API:")
        print("   POST /api/v1/musics")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Migração interrompida pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ ERRO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


