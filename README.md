# FALA Clip Editor

Ferramentas para automatizar a edição de vídeos de música.

## Executando localmente (modo sandbox)

1. Copie `.env.dev` para `.env` e ajuste variáveis se necessário.
2. Instale dependências Python:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Suba a stack de desenvolvimento (API + Postgres + MinIO):
   ```bash
   docker compose -f docker-compose.dev.yml up --build
   ```
4. Aplique migrações para provisionar o schema:
   ```bash
   alembic upgrade head
   ```
5. Para desenvolvimento rápido é possível definir `JOB_EXECUTION_MODE=sync` no `.env` e processar jobs inline. Para o fluxo assíncrono padrão, inicialize o worker RQ:
   ```bash
   rq worker video-edit
   ```
6. A API FastAPI ficará disponível em `http://localhost:8060`.

### Endpoints principais

- `POST /music` — upload de músicas (multipart) com metadados e disparo da análise automática.
- `GET /music/{music_id}` — consulta detalhes da análise (transcrição placeholder, batidas e embeddings simulados).
- `POST /videos` — registra vídeo a partir do link, gera análise placeholder e modelos de clipes (2 variações por música sugerida ou 3 quando uma música é informada).
- `GET /videos/{video_id}` — retorna detalhes do vídeo analisado e todos os modelos de clipe salvos.
- `POST /render/{video_id}` — renderiza, de forma sequencial, os modelos selecionados e devolve os arquivos gerados.
- `POST /feedback/music/{music_id}` — registra feedback textual específico da música e alimenta o aprendizado global.
- `POST /feedback/artist` — registra feedback geral do artista (ou contextual de uma música) para personalização.
- `POST /learning-centers` / `PUT /learning-centers/{id}` / `DELETE /learning-centers/{id}` — gerenciam centros de aprendizado versionados (global, artista ou música).
- `GET /metrics` — exporta métricas em formato Prometheus (requisições, jobs, tokens estimados, etc.).

Documentação adicional:

- `docs/platform-overview.md`: visão geral da arquitetura.
- `docs/schema/dbdiagram.dbml`: modelo do banco para o dbdiagram.
- `docs/migrations.md`: guia de uso do Alembic.
- `mobile/README.md`: roadmap do app React Native.
