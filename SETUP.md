# Guia de Setup - Clip Editor API v2.0

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.11+ (para desenvolvimento local)
- Git

## 🚀 Instalação Rápida

### 1. Clone e entre na branch

```bash
git checkout neweditor
```

### 2. Configure variáveis de ambiente

```bash
cp env.example .env
```

Edite o arquivo `.env` com suas configurações:

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

# N8N Webhook (opcional, padrão já configurado)
N8N_WEBHOOK_URL=https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76
```

### 3. Inicie os serviços

```bash
docker-compose up -d
```

Isso irá:
- Criar container do PostgreSQL
- Criar container da aplicação
- Aguardar PostgreSQL ficar pronto

### 4. Execute as migrations

```bash
docker-compose exec app alembic upgrade head
```

### 5. Crie o primeiro usuário admin

```bash
docker-compose exec app python scripts/create_admin.py
```

Ou localmente (se tiver Python configurado):

```bash
python scripts/create_admin.py
```

Siga as instruções para criar o admin.

### 6. Acesse a API

- **Swagger UI**: http://localhost:8060/docs
- **ReDoc**: http://localhost:8060/redoc
- **Health Check**: http://localhost:8060/health

## 🔧 Comandos Úteis

### Ver logs

```bash
docker-compose logs -f app
```

### Parar serviços

```bash
docker-compose down
```

### Parar e remover volumes (limpar banco)

```bash
docker-compose down -v
```

### Executar migrations

```bash
docker-compose exec app alembic upgrade head
```

### Reverter migration

```bash
docker-compose exec app alembic downgrade -1
```

### Criar nova migration

```bash
docker-compose exec app alembic revision --autogenerate -m "descrição"
```

### Acessar shell do container

```bash
docker-compose exec app bash
```

### Acessar banco de dados

```bash
docker-compose exec postgres psql -U clip_editor -d clip_editor_db
```

## 🧪 Testando a API

### 1. Fazer login

```bash
curl -X POST "http://localhost:8060/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "sua_senha"
  }'
```

### 2. Usar o token nas requisições

```bash
TOKEN="seu_token_aqui"

curl -X GET "http://localhost:8060/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

## 📝 Estrutura do Projeto

```
clip-editor/
├── app/                    # Código da aplicação
│   ├── application/        # Camada de aplicação (controllers, DTOs)
│   ├── domain/             # Camada de domínio (entities, services)
│   ├── infrastructure/     # Camada de infraestrutura (database, external)
│   └── config/             # Configurações
├── alembic/                # Migrations do banco
├── scripts/                # Scripts utilitários
├── docker-compose.yml      # Configuração Docker
├── Dockerfile             # Imagem Docker
└── requirements.txt       # Dependências Python
```

## 🐛 Troubleshooting

### Erro: "Connection refused" ao conectar no banco

- Verifique se o PostgreSQL está rodando: `docker-compose ps`
- Verifique os logs: `docker-compose logs postgres`
- Aguarde alguns segundos após iniciar os containers

### Erro: "Table already exists" nas migrations

- O banco já tem as tabelas. Você pode:
  - Dropar e recriar: `docker-compose down -v && docker-compose up -d`
  - Ou marcar a migration como aplicada: `alembic stamp head`

### Erro: "Module not found"

- Verifique se todas as dependências estão instaladas
- Reconstrua a imagem: `docker-compose build --no-cache`

### Worker não está processando publicações

- Verifique os logs: `docker-compose logs app | grep scheduler`
- O worker executa apenas às 00:00 (horário SP)
- Para testar manualmente, você pode chamar a função diretamente

## 📚 Próximos Passos

1. Configure seu webhook URL no perfil do usuário
2. Faça upload de músicas
3. Processe vídeos
4. Acompanhe a fila de publicações

## 🔒 Segurança

⚠️ **IMPORTANTE**: Em produção:

1. Altere `JWT_SECRET_KEY` para um valor seguro
2. Configure CORS adequadamente
3. Use HTTPS
4. Configure rate limiting
5. Mantenha dependências atualizadas

## 📞 Suporte

Para dúvidas ou problemas, consulte:
- Documentação da API: `/docs`
- Logs da aplicação: `docker-compose logs app`

