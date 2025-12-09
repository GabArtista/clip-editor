# Clip Editor API v2.0 - New Editor

Sistema completo de edição automática de clips de música com fila de publicações inteligente.

## 🚀 Funcionalidades

### Autenticação e Usuários
- Sistema de autenticação JWT
- Roles: Admin e User
- Gerenciamento completo de usuários (criação, atualização, bloqueio)
- Webhook URL personalizado por usuário

### Músicas
- Upload de músicas MP3 por usuário
- Gerenciamento completo (CRUD)
- Detecção automática de duração

### Edição de Vídeos
- Download automático de Reels do Instagram
- Sincronização de música com vídeo (pontos de impacto)
- Processamento com FFmpeg
- Múltiplos formatos de retorno (URL, Base64, Path, File)

### Fila de Publicações
- **Sistema inteligente de agendamento:**
  - Máximo 10 publicações por mês por usuário
  - Distribuição automática ao longo do mês
  - Horários fixos: 10h, 13h, 17h (rotacionando)
  - Processamento apenas do mês atual
  - Realocação automática de datas vencidas

- **Worker assíncrono:**
  - Execução diária às 00:00 (horário SP)
  - Processamento em lotes (máx 10 por vez)
  - Pausas entre lotes para não sobrecarregar servidor
  - Tratamento de erros robusto

## 📋 Arquitetura

### Padrão MVC/DDD (inspirado no Laravel 12)

```
app/
├── domain/              # Camada de Domínio (DDD)
│   ├── entities/        # Entidades de domínio
│   ├── repositories/    # Interfaces de repositórios
│   └── services/        # Serviços de domínio
├── infrastructure/      # Camada de Infraestrutura
│   ├── database/        # Models SQLAlchemy, migrations
│   ├── repositories/    # Implementações de repositórios
│   └── external/        # Integrações externas (N8N)
├── application/         # Camada de Aplicação
│   ├── controllers/     # Controllers (MVC)
│   ├── dto/             # Data Transfer Objects
│   ├── workers/         # Workers assíncronos
│   ├── scheduler/       # Agendamento de tarefas
│   └── exceptions/      # Tratamento de erros
└── config/              # Configurações
```

## 🛠️ Tecnologias

- **FastAPI** - Framework web assíncrono
- **PostgreSQL** - Banco de dados relacional
- **SQLAlchemy** - ORM
- **Alembic** - Migrations
- **APScheduler** - Agendamento de tarefas
- **JWT** - Autenticação
- **FFmpeg** - Processamento de vídeo/áudio
- **yt-dlp** - Download de vídeos
- **Docker** - Containerização

## 📦 Instalação

### Pré-requisitos
- Docker e Docker Compose
- Python 3.11+ (para desenvolvimento local)

### Setup

1. Clone o repositório e entre na branch:
```bash
git checkout neweditor
```

2. Configure variáveis de ambiente:
```bash
cp env.example .env
# Edite .env com suas configurações
```

3. Inicie com Docker Compose:
```bash
docker-compose up -d
```

4. Execute migrations:
```bash
docker-compose exec app alembic upgrade head
```

5. Acesse a documentação:
```
http://localhost:8060/docs
```

## 🔧 Configuração

### Variáveis de Ambiente

```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_USER=clip_editor
DB_PASSWORD=clip_editor_pass
DB_NAME=clip_editor_db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# App
APP_HOST=0.0.0.0
APP_PORT=8060
```

## 📚 API Endpoints

### Autenticação
- `POST /api/v1/auth/login` - Login e obtenção de token

### Usuários
- `POST /api/v1/users` - Criar usuário (admin)
- `GET /api/v1/users` - Listar usuários (admin)
- `GET /api/v1/users/me` - Meu perfil
- `PUT /api/v1/users/me` - Atualizar meu perfil
- `PUT /api/v1/users/{id}` - Atualizar usuário (admin)
- `POST /api/v1/users/{id}/block` - Bloquear usuário (admin)
- `DELETE /api/v1/users/{id}` - Deletar usuário (admin)

### Músicas
- `POST /api/v1/musics` - Upload de música
- `GET /api/v1/musics` - Listar minhas músicas
- `GET /api/v1/musics/{id}` - Obter música
- `PUT /api/v1/musics/{id}` - Atualizar música
- `DELETE /api/v1/musics/{id}` - Deletar música

### Vídeos
- `POST /api/v1/videos/process` - Processar vídeo (download + edição)
- `GET /api/v1/videos/files/{filename}` - Baixar vídeo processado

### Publicações
- `POST /api/v1/publications` - Adicionar publicação na fila
- `GET /api/v1/publications` - Listar minhas publicações
- `DELETE /api/v1/publications/{id}` - Cancelar publicação

## 🔄 Fluxo de Publicação

1. **Usuário processa vídeo:**
   - Faz upload de música (se necessário)
   - Processa vídeo com música
   - Sistema automaticamente adiciona na fila (se `auto_queue=true`)

2. **Sistema agenda publicação:**
   - Calcula próxima data disponível
   - Respeita limite de 10/mês
   - Distribui ao longo do mês
   - Usa horários 10h, 13h, 17h

3. **Worker processa diariamente:**
   - Executa às 00:00 (SP)
   - Processa apenas publicações do mês atual
   - Realoca datas vencidas
   - Publica via webhook do usuário

## ⚡ Otimizações de Performance

- **Processamento assíncrono:** Worker usa async/await
- **Lotes limitados:** Máximo 10 publicações por vez
- **Pausas entre lotes:** 2 segundos para não sobrecarregar
- **Singleton worker:** Uma instância por aplicação
- **Queries otimizadas:** Índices no banco de dados
- **Connection pooling:** SQLAlchemy com pool de conexões

## 🧪 Testes

```bash
pytest --cov=app tests/
```

## 📝 Migrations

```bash
# Criar nova migration
alembic revision --autogenerate -m "descrição"

# Aplicar migrations
alembic upgrade head

# Reverter migration
alembic downgrade -1
```

## 🐳 Docker

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f app

# Stop
docker-compose down
```

## 📄 Licença

Este projeto é privado.

