# Guia de execução local e testes manuais

Este tutorial descreve como subir a stack do editor de vídeo localmente, popular os serviços auxiliares e validar os fluxos principais da API sem depender do antigo app mobile.

## Pré-requisitos

- Python 3.11+ com `venv`.
- Docker e Docker Compose.
- `make` opcional para atalhos (todos os comandos abaixo usam apenas `bash`).
- 1 arquivo `.env` configurado (baseado em `env.example` ou `.env.dev`).

## Passo a passo para subir o ambiente

1. **Copie o arquivo de variáveis:**
   ```bash
   cp env.example .env
   ```
   Ajuste portas ou diretórios caso precise. Para execução rápida em modo síncrono, defina `JOB_EXECUTION_MODE=sync` e `FAKE_REDIS=1`.

2. **Crie o virtualenv e instale dependências:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Suba os serviços Docker (API, Postgres e MinIO):**
   ```bash
   docker compose -f docker-compose.dev.yml up --build
   ```
   A API ficará acessível em `http://localhost:8060`. O painel do MinIO pode ser acessado em `http://localhost:9001` (user: `minioadmin`, senha: `minioadmin`).

4. **Aplicar migrações (em outro terminal com o virtualenv ativo):**
   ```bash
   alembic upgrade head
   ```

5. **Executar o worker RQ (opcional quando `JOB_EXECUTION_MODE=async`):**
   ```bash
   rq worker video-edit
   ```
   No modo síncrono (`JOB_EXECUTION_MODE=sync`) o worker externo não é necessário; os jobs são processados inline.

6. **Validar saúde do serviço:**
   ```bash
   curl http://localhost:8060/health
   ```
7. **Registrar usuário e obter token:**
   ```bash
   curl -X POST http://localhost:8060/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "artist@example.com", "password": "Secret123!"}'
   ```
   Anote o `access_token` retornado (ou faça login em `/auth/login`). Use esse token Bearer nas requisições subsequentes.

## Roteiro de testes manuais

1. **Autenticação & Sessões**
   - Importe `postmans/00-auth-sessions.postman_collection.json`.
   - Ajuste `base_url`, cadastre/login com `email`/`password` e copie o `access_token` para o ambiente do Postman.
   - Execute `Atualizar Sessão` informando o JSON de cookies exportado (para jobs que dependem do Instagram).

2. **Biblioteca de músicas**
   - Importe `postmans/01-music-library.postman_collection.json`.
   - Faça upload de um MP3/M4A real para gerar um novo `music_id`.
   - Valide o retorno da transcrição fake e dos metadados com `GET /music/{music_id}`.

3. **Ingestão de vídeos**
   - Importe `postmans/02-video-ingestion.postman_collection.json`.
   - Use o `music_id` gerado anteriormente (ou deixe em branco para sugestões genéricas).
   - Capture o `video_id` retornado para as etapas seguintes.

4. **Jobs de renderização**
   - Utilize `postmans/03-video-jobs.postman_collection.json`.
   - Em `/render/{video_id}` informe os `clip_ids` retornados ao consultar `/videos/{video_id}`.
   - Acompanhe o job pelo `GET /jobs/{job_id}`.

5. **Feedbacks e centros de aprendizado**
   - Importe `postmans/04-feedback-learning.postman_collection.json`.
   - Reutilize um `music_id` válido (quando necessário).
   - Crie um centro de aprendizado, atualize e depois arquive para percorrer todo o ciclo.

6. **Observabilidade**
   - Em `postmans/05-observability.postman_collection.json` execute `GET /metrics` e confirme a exposição no formato Prometheus.

## Encerrando o ambiente

- Pare os containers:
  ```bash
  docker compose -f docker-compose.dev.yml down
  ```
- Opcional: limpe volumes com `docker volume rm fala_db_data fala_object_storage fala_media_cache`.
- Desative o virtualenv com `deactivate`.

> Dica: mantenha os `postmans/*.json` importados no Postman e salve um ambiente local com `base_url`, `user_id`, `music_id`, etc. Assim você reaproveita os mesmos fluxos ao validar correções futuras.
