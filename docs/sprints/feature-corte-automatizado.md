# Plano da Feature `feature/corte-automatizado-main`

Este documento fornece contexto completo para continuação do desenvolvimento por qualquer pessoa/IA. Ele descreve ambiente, banco dedicado, organização das sprints, branches e testes esperados.

## Ambiente e Banco de Dados

- **Banco dedicado**: criar um banco exclusivo para esta feature (ex.: `fala_clip_ai`). Não alterar bancos existentes do servidor.
- **Credenciais PG Admin**: configurar o novo banco manualmente usando o acesso informado pelo proprietário. Não versionar credenciais.
- **Migrations**: cada sprint que introduz mudanças em dados deve incluir migrations Alembic apontando para o novo banco.
- **Limpeza de artefatos**: após entregar versões finais dos vídeos, remover arquivos temporários (`videos/`, `processed/`) e manter apenas metadados persistidos.

## Sprints e Branches

Todas as branches partem de `feature/corte-automatizado-main`, criada diretamente de `main` (estado atual do microserviço de edição). Cada sprint abre um PR independente com testes automatizados e integrações revisadas com o core já existente.

### Sprint 1 – Controle de Infra e Filas
- **Branch**: `feature/infra-job-control-main`
- **Objetivos**:
  - Introduzir orquestração (Celery/RQ ou Dramatiq) com limite de 1 worker pesado.
  - State machine de jobs: `queued → analyzing → rendering → done/failed`.
  - Rate limit no endpoint de upload para evitar saturação.
  - Serviço de limpeza automática após entrega.
- **Tarefas**:
  - Criar módulo `jobs/` com definição dos workers e estados.
  - Expor endpoint `GET /jobs/{id}` no FastAPI.
  - Implementar job cleaner e agendamento (cron/worker leve).
  - Ajustar `scripts/edit.py`/`scripts/download.py` para usarem diretórios temporários configuráveis.
- **Testes**:
  - Testes unitários para fila (mock de broker) garantindo limite de concorrência.
  - Teste API de criação/consulta de job.
  - Teste do cleanup verificando remoção de arquivos.

### Sprint 2 – Processamento de Música e Gênero
- **Branch**: `feature/music-processing-main`
- **Objetivos**:
  - Endpoint `POST /music` com upload e metadados.
  - Worker `analyze_music` (transcrição única, batidas, embeddings).
  - Detecção de gênero: `declared`, `inferred`, score.
  - Persistência em tabelas novas (`music_assets`, `music_analysis`, `music_beats`, `music_embeddings`).
- **Tarefas**:
  - Implementar storage (MinIO ou filesystem isolado).
  - Criar migrations Alembic correspondentes.
  - Cache de resultados para não reprocesar.
  - Notificar status via eventos/jobs.
- **Testes**:
  - API upload (fixtures de áudio sintético).
  - Pipeline de análise (unitário com mocks para Whisper/OpenAI).
  - Verificação de migrations (pytest + banco temporário).

### Sprint 3 – Análise de Vídeo e Sugestões
- **Branch**: `feature/video-suggestion-engine-main`
- **Objetivos**:
  - Reutilizar download atual (`scripts/download.py`) e extrair frames/embeddings.
  - Worker `analyze_video` com CLIP/MoViNet + detecção de impactos.
  - Motor de sugestão que combina camadas global/artista/música e perfis por gênero.
  - Garantir diversidade: 2 modelos (sem música) ou 3 (com música fornecida), no mínimo 5s de diferença.
- **Tarefas**:
  - Criar tabelas `video_ingests`, `video_analysis`, `video_clip_models`.
  - Implementar serviço `suggest_clips` consumindo o aprendizado acumulado.
  - Persistir resultados e anexar ao job para renderização posterior.
- **Testes**:
  - Pipelines de vídeo com amostra local (curto MP4).
  - Testes determinísticos do ranking (fixtures de embeddings).
  - Verificação da regra de diversidade ≥5s.

### Sprint 4 – Renderização e Feedback de Aprendizado
- **Branches**: `feature/render-limited-main` e `feature/feedback-learning-main`
- **Objetivos**:
  - Renderizar variantes de forma sequencial controlada (respeitando limites do servidor).
  - Expor progresso no job (ex.: `rendering_variant`, `completed_variants`).
  - Endpoints de feedback textual:
    - `POST /feedback/music/{music_id}`
    - `POST /feedback/artist`
  - Atualizar camadas de aprendizado (global/artista/música) e perfis por gênero.
  - Permitir que o artista crie/edite/pausa centros de aprendizado (global, artista, música) com rótulos “experimental” para testes e opção de reverter para baseline.
- **Tarefas**:
  - Adaptar `scripts/edit.py` para múltiplos segmentos e logs por etapa.
  - Criar tabelas `music_feedback`, `artist_feedback`, `ai_learning_events`, `global_genre_profiles`.
  - Workers que consumam feedback e recalculem pesos.
  - Endpoints `POST/PUT/DELETE /learning-centers/...` com versionamento e histórico.
  - Implementado nas branches `feature/render-limited-main` e `feature/feedback-learning-main` (2025-10-18).
- **Testes**:
  - Verificação de sincronização áudio/vídeo (comparação de timestamps).
  - Testes API de feedback com autenticação.
  - Testes de atualização dos perfis (mock de dados e assertions nos pesos).
  - Testes garantindo isolamento entre centros de aprendizado e rollback controlado.

### Sprint 5 – Observabilidade e Custos
- **Branch**: `feature/metrics-costs-main`
- **Objetivos**:
  - Instrumentar métricas (Prometheus/Grafana) para CPU/RAM, tempo das etapas, tamanho de fila.
  - Contabilizar tokens OpenAI por request e associar ao usuário/música.
  - Alertas básicos quando SLA > 15 min ou CPU > 80%.
- **Tarefas**:
  - Implementar middleware/logging estruturado.
  - Expor endpoint `/metrics`.
  - Criar relatórios ou dashboards mínimos.
  - Entregue via `feature/metrics-costs-main` com middleware HTTP, métricas de jobs/feedback e contagem de tokens simulada (2025-10-18).
- **Testes**:
  - Testes unitários para contadores e agregações.
  - Smoke test validando `/metrics`.
  - Teste que simula consumo de tokens e verifica armazenamento.

## Estratégia de Testes

- Utilizar `pytest` com bancos temporários (fixtures Postgres) e storage fake (MinIO local ou mock).
- Para pipelines com IA, mocar chamadas pesadas ou usar dados sintéticos determinísticos.
- Rodar suíte completa a cada sprint e garantir compatibilidade com job limit.
- Documentar comandos em `docs/tests.md` (a criar) para facilitar reprodução.

## Próximos Passos

1. Criar o banco dedicado via PG Admin antes de rodar migrations.
2. Abrir a branch `feature/corte-automatizado-main` a partir de `main` (já criado) e, sequencialmente, iniciar pela Sprint 1 garantindo controle de carga para proteger outros serviços.
3. Manter este documento atualizado ao término de cada sprint com versões e links de PR, anotando alterações em centros de aprendizado.
