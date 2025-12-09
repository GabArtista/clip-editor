#!/usr/bin/env python3
"""
Script para reorganizar a estrutura do projeto seguindo padrão Laravel
"""
import os
import shutil
import re
from pathlib import Path

# Mapeamento de arquivos antigos para novos
FILE_MAPPINGS = {
    # Database Base
    "app/infrastructure/database/base.py": "app/Providers/DatabaseServiceProvider.py",
    
    # Models
    "app/infrastructure/database/models/user_model.py": "app/Models/User.py",
    "app/infrastructure/database/models/music_model.py": "app/Models/Music.py",
    "app/infrastructure/database/models/video_edit_model.py": "app/Models/VideoEdit.py",
    "app/infrastructure/database/models/publication_queue_model.py": "app/Models/PublicationQueue.py",
    "app/infrastructure/database/models/template_model.py": "app/Models/Template.py",
    
    # Services
    "app/domain/services/user_service.py": "app/Services/UserService.py",
    "app/domain/services/music_service.py": "app/Services/MusicService.py",
    "app/domain/services/video_edit_service.py": "app/Services/VideoEditService.py",
    "app/domain/services/publication_service.py": "app/Services/PublicationService.py",
    "app/domain/services/publication_scheduler_service.py": "app/Services/PublicationSchedulerService.py",
    
    # Repositories
    "app/infrastructure/repositories/user_repository.py": "app/Repositories/UserRepository.py",
    "app/infrastructure/repositories/music_repository.py": "app/Repositories/MusicRepository.py",
    "app/infrastructure/repositories/video_edit_repository.py": "app/Repositories/VideoEditRepository.py",
    "app/infrastructure/repositories/publication_queue_repository.py": "app/Repositories/PublicationQueueRepository.py",
    "app/infrastructure/repositories/template_repository.py": "app/Repositories/TemplateRepository.py",
    
    # Controllers
    "app/application/controllers/auth_controller.py": "app/Http/Controllers/AuthController.py",
    "app/application/controllers/user_controller.py": "app/Http/Controllers/UserController.py",
    "app/application/controllers/music_controller.py": "app/Http/Controllers/MusicController.py",
    "app/application/controllers/video_controller.py": "app/Http/Controllers/VideoController.py",
    "app/application/controllers/video_edit_controller.py": "app/Http/Controllers/VideoEditController.py",
    "app/application/controllers/publication_queue_controller.py": "app/Http/Controllers/PublicationQueueController.py",
    "app/application/controllers/template_controller.py": "app/Http/Controllers/TemplateController.py",
    
    # Middleware
    "app/application/middleware/rate_limiter.py": "app/Http/Middleware/RateLimiter.py",
    
    # Workers -> Jobs
    "app/application/workers/publication_worker.py": "app/Jobs/PublicationJob.py",
    "app/application/workers/cleanup_worker.py": "app/Jobs/CleanupJob.py",
    
    # Exceptions
    "app/application/exceptions/handlers.py": "app/Exceptions/Handler.py",
    
    # Utils -> Helpers
    "app/application/utils/ffmpeg_utils.py": "app/Helpers/FFmpegHelper.py",
    
    # Auth
    "app/application/auth/jwt_handler.py": "app/Http/Middleware/AuthMiddleware.py",
    "app/application/auth/password.py": "app/Helpers/PasswordHelper.py",
}

# Mapeamento de imports
IMPORT_MAPPINGS = {
    # Database
    "from app.infrastructure.database.base import": "from app.Providers.DatabaseServiceProvider import",
    "from app.infrastructure.database.models": "from app.Models",
    "app.infrastructure.database.models": "app.Models",
    
    # Services
    "from app.domain.services": "from app.Services",
    "app.domain.services": "app.Services",
    
    # Repositories
    "from app.infrastructure.repositories": "from app.Repositories",
    "app.infrastructure.repositories": "app.Repositories",
    
    # Controllers
    "from app.application.controllers": "from app.Http.Controllers",
    "app.application.controllers": "app.Http.Controllers",
    
    # Middleware
    "from app.application.middleware": "from app.Http.Middleware",
    "app.application.middleware": "app.Http.Middleware",
    
    # Workers -> Jobs
    "from app.application.workers": "from app.Jobs",
    "app.application.workers": "app.Jobs",
    
    # Exceptions
    "from app.application.exceptions": "from app.Exceptions",
    "app.application.exceptions": "app.Exceptions",
    
    # Utils -> Helpers
    "from app.application.utils": "from app.Helpers",
    "app.application.utils": "app.Helpers",
    
    # Auth
    "from app.application.auth": "from app.Http.Middleware",
    "app.application.auth": "app.Http.Middleware",
    
    # Config
    "from app.config": "from config",
    "app.config": "config",
}

def update_imports_in_file(file_path: Path):
    """Atualiza imports em um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Aplica mapeamentos de imports
        for old_import, new_import in IMPORT_MAPPINGS.items():
            content = content.replace(old_import, new_import)
        
        # Atualiza nomes de classes (UserModel -> User, etc)
        content = re.sub(r'UserModel', 'User', content)
        content = re.sub(r'MusicModel', 'Music', content)
        content = re.sub(r'VideoEditModel', 'VideoEdit', content)
        content = re.sub(r'PublicationQueueModel', 'PublicationQueue', content)
        content = re.sub(r'TemplateModel', 'Template', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✓ Atualizado: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"  ✗ Erro ao atualizar {file_path}: {e}")
        return False

def move_file(old_path: str, new_path: str):
    """Move arquivo e atualiza imports"""
    old = Path(old_path)
    new = Path(new_path)
    
    if not old.exists():
        print(f"  ⚠ Arquivo não encontrado: {old_path}")
        return False
    
    # Cria diretório destino
    new.parent.mkdir(parents=True, exist_ok=True)
    
    # Copia arquivo
    shutil.copy2(old, new)
    print(f"  ✓ Movido: {old_path} -> {new_path}")
    
    # Atualiza imports no arquivo movido
    update_imports_in_file(new)
    
    return True

def main():
    """Executa reorganização"""
    print("🚀 Iniciando reorganização Laravel...\n")
    
    base_dir = Path(__file__).parent.parent
    
    # Move arquivos
    moved = 0
    for old_path, new_path in FILE_MAPPINGS.items():
        old_full = base_dir / old_path
        new_full = base_dir / new_path
        
        if move_file(old_path, new_path):
            moved += 1
    
    print(f"\n✅ {moved}/{len(FILE_MAPPINGS)} arquivos movidos")
    print("\n⚠️  IMPORTANTE: Revise os imports manualmente!")
    print("⚠️  Alguns imports podem precisar de ajustes adicionais.")

if __name__ == "__main__":
    main()

