# 📁 Estrutura Laravel - Clip Editor API

## Nova Organização

```
app/
├── Http/
│   ├── Controllers/          # Controllers (antes: application/controllers)
│   │   ├── AuthController.py
│   │   ├── UserController.py
│   │   ├── MusicController.py
│   │   ├── VideoController.py
│   │   ├── VideoEditController.py
│   │   ├── PublicationQueueController.py
│   │   └── TemplateController.py
│   ├── Middleware/           # Middleware (antes: application/middleware)
│   │   ├── RateLimiter.py
│   │   └── AuthMiddleware.py
│   ├── Requests/             # Request DTOs (antes: application/dto - requests)
│   │   ├── Auth/
│   │   │   └── LoginRequest.py
│   │   ├── User/
│   │   │   ├── CreateUserRequest.py
│   │   │   └── UpdateUserRequest.py
│   │   ├── Music/
│   │   │   ├── CreateMusicRequest.py
│   │   │   └── UpdateMusicRequest.py
│   │   └── Video/
│   │       └── ProcessVideoRequest.py
│   └── Resources/            # Response DTOs (antes: application/dto - responses)
│       ├── UserResource.py
│       ├── MusicResource.py
│       ├── VideoResource.py
│       └── PublicationResource.py
├── Models/                   # Models (antes: infrastructure/database/models)
│   ├── User.py
│   ├── Music.py
│   ├── VideoEdit.py
│   ├── PublicationQueue.py
│   └── Template.py
├── Services/                 # Services (antes: domain/services)
│   ├── AuthService.py
│   ├── UserService.py
│   ├── MusicService.py
│   ├── VideoService.py
│   ├── VideoEditService.py
│   ├── PublicationService.py
│   └── PublicationSchedulerService.py
├── Repositories/             # Repositories (antes: infrastructure/repositories)
│   ├── UserRepository.py
│   ├── MusicRepository.py
│   ├── VideoEditRepository.py
│   ├── PublicationQueueRepository.py
│   └── TemplateRepository.py
├── Jobs/                     # Jobs/Workers (antes: application/workers)
│   ├── PublicationJob.py
│   └── CleanupJob.py
├── Events/                   # Events (novo)
│   ├── VideoApproved.py
│   └── PublicationScheduled.py
├── Exceptions/               # Exceptions (antes: application/exceptions)
│   ├── Handler.py
│   ├── ValidationException.py
│   └── NotFoundException.py
├── Providers/                # Service Providers (novo)
│   ├── AppServiceProvider.py
│   └── DatabaseServiceProvider.py
└── Helpers/                  # Helpers/Utils (antes: application/utils)
    └── FFmpegHelper.py

config/                       # Config (mantém)
├── app.py
├── database.py
├── jwt.py
└── storage.py

database/
├── migrations/               # Migrations (mantém alembic/versions)
└── seeders/                  # Seeders (novo)
    └── UserSeeder.py

routes/                       # Routes (novo)
├── api.php                   # API routes
├── web.php                   # Web routes (se necessário)
└── __init__.py

tests/                        # Tests (mantém)
├── Unit/
│   ├── Services/
│   └── Repositories/
├── Feature/
│   ├── AuthTest.py
│   └── VideoTest.py
└── Integration/

scripts/                      # Scripts (mantém)
├── download.py
├── edit.py
└── create_admin.py

storage/                      # Storage (novo)
├── app/
│   ├── music/
│   ├── videos/
│   └── processed/
└── logs/

bootstrap/                    # Bootstrap (novo)
└── app.py                    # Inicialização da aplicação
```

## Mapeamento de Arquivos

### Controllers
- `app/application/controllers/auth_controller.py` → `app/Http/Controllers/AuthController.py`
- `app/application/controllers/user_controller.py` → `app/Http/Controllers/UserController.py`
- `app/application/controllers/music_controller.py` → `app/Http/Controllers/MusicController.py`
- `app/application/controllers/video_controller.py` → `app/Http/Controllers/VideoController.py`
- `app/application/controllers/video_edit_controller.py` → `app/Http/Controllers/VideoEditController.py`
- `app/application/controllers/publication_queue_controller.py` → `app/Http/Controllers/PublicationQueueController.py`
- `app/application/controllers/template_controller.py` → `app/Http/Controllers/TemplateController.py`

### DTOs → Requests/Resources
- `app/application/dto/user_dto.py` → `app/Http/Requests/User/` + `app/Http/Resources/UserResource.py`
- `app/application/dto/music_dto.py` → `app/Http/Requests/Music/` + `app/Http/Resources/MusicResource.py`
- `app/application/dto/video_edit_dto.py` → `app/Http/Requests/Video/` + `app/Http/Resources/VideoResource.py`

### Models
- `app/infrastructure/database/models/user_model.py` → `app/Models/User.py`
- `app/infrastructure/database/models/music_model.py` → `app/Models/Music.py`
- `app/infrastructure/database/models/video_edit_model.py` → `app/Models/VideoEdit.py`
- `app/infrastructure/database/models/publication_queue_model.py` → `app/Models/PublicationQueue.py`
- `app/infrastructure/database/models/template_model.py` → `app/Models/Template.py`

### Services
- `app/domain/services/user_service.py` → `app/Services/UserService.py`
- `app/domain/services/music_service.py` → `app/Services/MusicService.py`
- `app/domain/services/video_edit_service.py` → `app/Services/VideoEditService.py`
- `app/domain/services/publication_service.py` → `app/Services/PublicationService.py`
- `app/domain/services/publication_scheduler_service.py` → `app/Services/PublicationSchedulerService.py`

### Repositories
- `app/infrastructure/repositories/user_repository.py` → `app/Repositories/UserRepository.py`
- `app/infrastructure/repositories/music_repository.py` → `app/Repositories/MusicRepository.py`
- `app/infrastructure/repositories/video_edit_repository.py` → `app/Repositories/VideoEditRepository.py`
- `app/infrastructure/repositories/publication_queue_repository.py` → `app/Repositories/PublicationQueueRepository.py`
- `app/infrastructure/repositories/template_repository.py` → `app/Repositories/TemplateRepository.py`

### Workers → Jobs
- `app/application/workers/publication_worker.py` → `app/Jobs/PublicationJob.py`
- `app/application/workers/cleanup_worker.py` → `app/Jobs/CleanupJob.py`

### Exceptions
- `app/application/exceptions/handlers.py` → `app/Exceptions/Handler.py`

### Middleware
- `app/application/middleware/rate_limiter.py` → `app/Http/Middleware/RateLimiter.py`

### Utils → Helpers
- `app/application/utils/ffmpeg_utils.py` → `app/Helpers/FFmpegHelper.py`

### Config
- `app/config/settings.py` → `config/app.py`, `config/database.py`, `config/jwt.py`, `config/storage.py`

### Main
- `app/application/main.py` → `bootstrap/app.py` + `routes/api.py`

