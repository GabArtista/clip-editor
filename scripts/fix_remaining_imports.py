#!/usr/bin/env python3
"""
Corrige imports que ainda referenciam estrutura antiga
"""
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """Corrige imports em um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Corrige imports de validators
        content = re.sub(
            r'from app\.application\.validators import',
            'from app.application.validators import',
            content
        )
        
        # Corrige imports de storage
        content = re.sub(
            r'from app\.infrastructure\.storage import',
            'from app.infrastructure.storage import',
            content
        )
        
        # Corrige imports de entities (mantém como está, ainda são usados)
        # content = re.sub(...) - não precisa, entities ainda está em app/domain
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  ✗ Erro: {file_path}: {e}")
        return False

def main():
    base = Path(__file__).parent.parent
    
    # Arquivos que podem ter imports antigos
    files_to_check = [
        "app/Http/Controllers/*.py",
        "app/Http/Resources/*.py",
        "app/Http/Requests/**/*.py",
    ]
    
    fixed = 0
    for pattern in files_to_check:
        for file_path in base.glob(pattern):
            if file_path.is_file() and file_path.suffix == '.py':
                if fix_imports_in_file(file_path):
                    print(f"  ✓ {file_path.relative_to(base)}")
                    fixed += 1
    
    print(f"\n✅ {fixed} arquivos verificados/corrigidos")

if __name__ == "__main__":
    main()

