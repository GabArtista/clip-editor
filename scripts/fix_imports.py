#!/usr/bin/env python3
"""
Script para corrigir imports após reorganização Laravel
"""
import os
import re
from pathlib import Path

# Mapeamento de correções de imports
IMPORT_FIXES = [
    # DatabaseServiceProvider
    (r'from app\.Providers\.DatabaseServiceProvider import Base', 'from app.Providers.DatabaseServiceProvider import Base'),
    (r'from app\.Providers\.DatabaseServiceProvider import get_db', 'from app.Providers.DatabaseServiceProvider import get_db'),
    
    # Repositories - corrigir imports
    (r'from app\.Repositories import (\w+)', r'from app.Repositories.\1 import \1'),
    
    # Services - corrigir imports
    (r'from app\.Services\.(\w+_service) import (\w+)', r'from app.Services.\2 import \2'),
    (r'from app\.Services import (\w+)', r'from app.Services.\1 import \1'),
    
    # Middleware - AuthMiddleware
    (r'from app\.Http\.Middleware import (create_access_token|verify_password|get_current_user|get_current_admin_user)', r'from app.Http.Middleware.AuthMiddleware import \1'),
    
    # Entities - manter como está
    (r'from app\.domain\.entities', 'from app.domain.entities'),
    
    # DTOs - ainda precisa mover
    (r'from app\.application\.dto', 'from app.Http.Requests'),  # Temporário, depois moveremos
    
    # Config
    (r'from config import settings', 'from config import settings'),
    (r'from app\.config import settings', 'from config import settings'),
    (r'from app\.config\.settings import', 'from config.app import'),
]

def fix_imports_in_file(file_path: Path):
    """Corrige imports em um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Aplica correções
        for pattern, replacement in IMPORT_FIXES:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  ✗ Erro ao corrigir {file_path}: {e}")
        return False

def main():
    """Executa correção de imports"""
    print("🔧 Corrigindo imports...\n")
    
    base_dir = Path(__file__).parent.parent
    
    # Arquivos para corrigir
    files_to_fix = [
        "app/Models/*.py",
        "app/Services/*.py",
        "app/Repositories/*.py",
        "app/Http/Controllers/*.py",
        "app/Http/Middleware/*.py",
        "app/Jobs/*.py",
        "app/Exceptions/*.py",
        "app/Helpers/*.py",
        "app/Providers/*.py",
    ]
    
    fixed = 0
    for pattern in files_to_fix:
        for file_path in base_dir.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.py':
                if fix_imports_in_file(file_path):
                    print(f"  ✓ {file_path.relative_to(base_dir)}")
                    fixed += 1
    
    print(f"\n✅ {fixed} arquivos corrigidos")

if __name__ == "__main__":
    main()

