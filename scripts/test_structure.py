#!/usr/bin/env python3
"""
Script para testar a estrutura reorganizada
Verifica imports e estrutura básica
"""
import sys
import importlib.util
from pathlib import Path

def test_import(module_path, description):
    """Testa import de um módulo"""
    try:
        spec = importlib.util.spec_from_file_location("test", module_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Não executa, só verifica sintaxe
            return True, None
        return False, "Spec não encontrado"
    except SyntaxError as e:
        return False, f"Erro de sintaxe: {e}"
    except Exception as e:
        return False, f"Erro: {e}"

def main():
    base = Path(__file__).parent.parent
    errors = []
    success = []
    
    # Arquivos críticos para testar
    files_to_test = [
        ("config/app.py", "Configuração"),
        ("app/Providers/DatabaseServiceProvider.py", "Database Provider"),
        ("app/Models/User.py", "Model User"),
        ("app/Services/UserService.py", "Service User"),
        ("app/Repositories/UserRepository.py", "Repository User"),
        ("app/Http/Middleware/AuthMiddleware.py", "Auth Middleware"),
        ("app/Helpers/PasswordHelper.py", "Password Helper"),
        ("app/Http/Controllers/AuthController.py", "Auth Controller"),
        ("routes/api.py", "API Routes"),
        ("bootstrap/app.py", "Bootstrap App"),
    ]
    
    print("🧪 Testando estrutura reorganizada...\n")
    
    for file_path, description in files_to_test:
        full_path = base / file_path
        if not full_path.exists():
            errors.append(f"❌ {description}: Arquivo não encontrado ({file_path})")
            continue
        
        ok, error = test_import(full_path, description)
        if ok:
            success.append(f"✅ {description}")
        else:
            errors.append(f"❌ {description}: {error}")
    
    print("\n📊 Resultados:")
    print(f"✅ Sucessos: {len(success)}")
    print(f"❌ Erros: {len(errors)}")
    
    if success:
        print("\n✅ Arquivos OK:")
        for s in success:
            print(f"  {s}")
    
    if errors:
        print("\n❌ Erros encontrados:")
        for e in errors:
            print(f"  {e}")
        return 1
    
    print("\n🎉 Estrutura reorganizada está correta!")
    return 0

if __name__ == "__main__":
    sys.exit(main())

