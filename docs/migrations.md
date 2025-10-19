# Migrations (Alembic)

## Pré-requisitos

- Ambiente virtual ativo (`python -m venv .venv && source .venv/bin/activate`)
- Dependências instaladas: `pip install -r requirements.txt`
- Containers de desenvolvimento ativos: `docker compose -f docker-compose.dev.yml up -d postgres`
  - O arquivo `.env.dev` já contém as credenciais padrão (`fala:fala@postgres:5432/fala`).

## Variáveis de ambiente

Alembic monta a URL do banco automaticamente a partir de:

```
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
```

ou da variável `DATABASE_URL` (`postgresql+psycopg://user:pass@host:port/db`).  
No ambiente local, basta copiar `.env.dev` para `.env` ou exportar as variáveis antes de rodar os comandos.

## Rodar migrações

Aplicar todas as migrações pendentes:

```bash
alembic upgrade head
```

Reverter para uma revisão específica:

```bash
alembic downgrade <revision_id>
```

Gerar uma nova revisão vazia (preencher manualmente com alterações):

```bash
alembic revision -m "descricao da mudanca"
```

As revisões são armazenadas em `alembic/versions/`. Para facilitar, mantenha as alterações de schema sincronizadas com o arquivo `docs/schema/dbdiagram.dbml`.
