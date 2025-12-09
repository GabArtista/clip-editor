# Changelog - Clip Editor API v2.0

## [2.0.0] - 2025-01-09

### 🎉 Nova Versão Completa

Refatoração completa da API seguindo padrões MVC/DDD inspirados no Laravel 12.

### ✨ Funcionalidades Adicionadas

#### Autenticação e Usuários
- Sistema de autenticação JWT completo
- Roles: Admin e User
- Gerenciamento completo de usuários (CRUD)
- Webhook URL personalizado por usuário
- Validação de webhook URL

#### Músicas
- Upload de músicas MP3 por usuário
- Gerenciamento completo (CRUD)
- Detecção automática de duração
- Validação de formato e tamanho de arquivo
- Isolamento por usuário

#### Edição de Vídeos
- Download automático de Reels do Instagram
- Sincronização de música com vídeo (pontos de impacto)
- Processamento com FFmpeg
- Múltiplos formatos de retorno (URL, Base64, Path, File)
- Integração automática com fila de publicação

#### Fila de Publicações
- Sistema inteligente de agendamento
  - Máximo 10 publicações por mês por usuário
  - Distribuição automática ao longo do mês
  - Horários fixos: 10h, 13h, 17h (rotacionando)
  - Processamento apenas do mês atual
  - Realocação automática de datas vencidas
- Worker assíncrono
  - Execução diária às 00:00 (horário SP)
  - Processamento em lotes (máx 10 por vez)
  - Pausas entre lotes para não sobrecarregar servidor
  - Tratamento de erros robusto

#### Integração N8N
- Cliente para webhook
- Publicação automática via fila
- Webhook personalizado por usuário

### 🏗️ Arquitetura

- **Padrão MVC/DDD**: Separação clara de responsabilidades
- **Camadas bem definidas**: Domain, Infrastructure, Application
- **Repositórios**: Abstração de acesso a dados
- **Serviços de domínio**: Lógica de negócio isolada
- **DTOs**: Validação e serialização de dados

### 🔧 Melhorias Técnicas

- PostgreSQL como banco de dados
- Migrations com Alembic
- Tratamento global de erros
- Validações robustas (Pydantic)
- Docker Compose para desenvolvimento
- Scheduler em background (APScheduler)
- Processamento assíncrono

### 📝 Documentação

- Swagger/OpenAPI completo
- ReDoc disponível
- Guia de setup detalhado
- README atualizado

### 🛠️ Scripts

- `scripts/create_admin.py`: Criação de usuário admin inicial

### 🔒 Segurança

- Hash de senhas com bcrypt
- JWT com expiração configurável
- Validação de inputs
- Tratamento seguro de erros

### ⚡ Performance

- Processamento assíncrono
- Lotes limitados
- Connection pooling
- Queries otimizadas

### 📦 Dependências

- FastAPI 0.112.0
- SQLAlchemy 2.0.23
- Alembic 1.13.1
- APScheduler 3.10.4
- E outras...

### 🐛 Correções

- Tratamento de erros melhorado
- Validações mais robustas
- Melhor isolamento de usuários

### 📚 Migração da Versão Anterior

A versão 2.0 é uma refatoração completa. Para migrar:

1. Faça backup dos dados antigos
2. Configure novo banco PostgreSQL
3. Execute migrations
4. Crie usuário admin
5. Reconfigure webhooks

---

## [1.0.0] - Versão Anterior

Versão inicial com funcionalidades básicas de edição de vídeo.

