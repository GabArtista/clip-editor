#!/usr/bin/env python3
"""
Script para limpar sistema - remove arquivos e pastas não utilizados
"""
import os
import shutil
from pathlib import Path

def remove_if_exists(path):
    """Remove arquivo/pasta se existir"""
    p = Path(path)
    if p.exists():
        if p.is_dir():
            shutil.rmtree(p)
            print(f"  ✅ Removido diretório: {path}")
        else:
            p.unlink()
            print(f"  ✅ Removido arquivo: {path}")
        return True
    return False

def main():
    base = Path(__file__).parent.parent
    print("🧹 Iniciando limpeza do sistema...\n")
    
    removed = []
    
    # 1. Estrutura antiga não utilizada
    print("1️⃣ Removendo estrutura antiga não utilizada...")
    old_structure = [
        "app/application",  # Substituído por app/Http, app/Jobs, etc
        "app/domain",        # Substituído por app/Services, app/Repositories
        "app/infrastructure", # Substituído por app/Models, app/Repositories
        "app/config",        # Movido para config/
        "api",               # Antigo, não usado
    ]
    
    for path in old_structure:
        if remove_if_exists(base / path):
            removed.append(path)
    
    # 2. Arquivos antigos na raiz
    print("\n2️⃣ Removendo arquivos antigos na raiz...")
    old_files = [
        "main.py",           # Antigo, agora é bootstrap/app.py
        "test_edit.py",      # Teste antigo
        "estrutura.txt",     # Arquivo temporário
        "headers.txt",       # Arquivo temporário
    ]
    
    for file in old_files:
        if remove_if_exists(base / file):
            removed.append(file)
    
    # 3. Pasta music antiga (arquivos de teste)
    print("\n3️⃣ Removendo pasta music/ antiga (arquivos agora em music/{user_id}/)...")
    music_dir = base / "music"
    if music_dir.exists():
        # Verifica se tem arquivos diretos (não subpastas de usuário)
        has_direct_files = False
        for item in music_dir.iterdir():
            if item.is_file():
                has_direct_files = True
                break
        
        if has_direct_files:
            # Remove apenas arquivos diretos, mantém estrutura de usuários
            for item in music_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    print(f"  ✅ Removido arquivo antigo: music/{item.name}")
                    removed.append(f"music/{item.name}")
    
    # 4. Arquivos temporários de reorganização
    print("\n4️⃣ Removendo arquivos temporários...")
    temp_files = [
        "app/Http/Requests/User/__temp_user_dto.py",
    ]
    
    for file in temp_files:
        if remove_if_exists(base / file):
            removed.append(file)
    
    # 5. Cache Python
    print("\n5️⃣ Removendo cache Python (__pycache__)...")
    for pycache in base.rglob("__pycache__"):
        if remove_if_exists(pycache):
            removed.append(str(pycache.relative_to(base)))
    
    for pyc in base.rglob("*.pyc"):
        if remove_if_exists(pyc):
            removed.append(str(pyc.relative_to(base)))
    
    print(f"\n✅ Limpeza concluída!")
    print(f"📊 Total de itens removidos: {len(removed)}")
    
    if removed:
        print("\n📋 Itens removidos:")
        for item in removed[:20]:  # Mostra primeiros 20
            print(f"  - {item}")
        if len(removed) > 20:
            print(f"  ... e mais {len(removed) - 20} itens")

if __name__ == "__main__":
    main()

