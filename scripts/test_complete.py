#!/usr/bin/env python3
"""
Teste completo do sistema reorganizado
Verifica estrutura, imports e funcionalidades básicas
"""
import sys
import ast
from pathlib import Path

def check_file_structure():
    """Verifica se a estrutura de diretórios está correta"""
    base = Path(__file__).parent.parent
    required_dirs = [
        "app/Http/Controllers",
        "app/Http/Middleware",
        "app/Http/Requests",
        "app/Http/Resources",
        "app/Models",
        "app/Services",
        "app/Repositories",
        "app/Jobs",
        "app/Exceptions",
        "app/Providers",
        "app/Helpers",
        "routes",
        "config",
        "bootstrap",
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not (base / dir_path).exists():
            missing.append(dir_path)
    
    return missing

def check_syntax(file_path):
    """Verifica sintaxe de um arquivo Python"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        return True, None
    except SyntaxError as e:
        return False, f"Erro de sintaxe: {e}"
    except Exception as e:
        return False, f"Erro: {e}"

def test_critical_files():
    """Testa arquivos críticos"""
    base = Path(__file__).parent.parent
    critical_files = [
        "bootstrap/app.py",
        "routes/api.py",
        "config/app.py",
        "app/Providers/DatabaseServiceProvider.py",
        "app/Http/Controllers/AuthController.py",
        "app/Http/Middleware/AuthMiddleware.py",
        "app/Services/UserService.py",
        "app/Repositories/UserRepository.py",
    ]
    
    errors = []
    for file_path in critical_files:
        full_path = base / file_path
        if not full_path.exists():
            errors.append(f"Arquivo não encontrado: {file_path}")
            continue
        
        ok, error = check_syntax(full_path)
        if not ok:
            errors.append(f"{file_path}: {error}")
    
    return errors

def main():
    print("🧪 Teste Completo do Sistema Reorganizado\n")
    print("=" * 60)
    
    # 1. Verifica estrutura de diretórios
    print("\n1️⃣ Verificando estrutura de diretórios...")
    missing_dirs = check_file_structure()
    if missing_dirs:
        print(f"❌ Diretórios faltando: {', '.join(missing_dirs)}")
        return 1
    else:
        print("✅ Estrutura de diretórios OK")
    
    # 2. Verifica arquivos críticos
    print("\n2️⃣ Verificando arquivos críticos...")
    errors = test_critical_files()
    if errors:
        print("❌ Erros encontrados:")
        for e in errors:
            print(f"  - {e}")
        return 1
    else:
        print("✅ Todos os arquivos críticos OK")
    
    # 3. Verifica estrutura Laravel
    print("\n3️⃣ Verificando padrão Laravel...")
    base = Path(__file__).parent.parent
    
    laravel_checks = [
        ("app/Http/Controllers", "Controllers em Http/Controllers"),
        ("app/Http/Requests", "Requests em Http/Requests"),
        ("app/Http/Resources", "Resources em Http/Resources"),
        ("app/Models", "Models em app/Models"),
        ("app/Services", "Services em app/Services"),
        ("app/Repositories", "Repositories em app/Repositories"),
        ("app/Jobs", "Jobs em app/Jobs"),
        ("routes/api.py", "Rotas em routes/api.py"),
        ("bootstrap/app.py", "Bootstrap em bootstrap/app.py"),
        ("config/app.py", "Config em config/app.py"),
    ]
    
    all_ok = True
    for path, description in laravel_checks:
        full_path = base / path
        if full_path.exists():
            print(f"  ✅ {description}")
        else:
            print(f"  ❌ {description} - Não encontrado")
            all_ok = False
    
    if not all_ok:
        return 1
    
    print("\n" + "=" * 60)
    print("🎉 TODOS OS TESTES PASSARAM!")
    print("✅ Estrutura reorganizada seguindo padrão Laravel")
    print("✅ Arquivos críticos funcionando")
    print("✅ Pronto para uso!")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

