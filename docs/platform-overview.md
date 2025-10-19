# Plataforma FALA – Visão Geral Inicial

Este documento descreve os componentes planejados para evoluir o editor automático de vídeos em uma plataforma SaaS com app mobile (iOS/Android) e backend escalável.

## Módulos Principais

- **Backend API (FastAPI):** expõe endpoints para ingestão de Reels, gerenciamento de cookies por usuário, catálogo de músicas e orquestração do pipeline de edição.
- **Workers / Pipeline de IA:** executa downloads, análise de vídeo, transcrição de áudio, alinhamento com a música e geração do resultado. Pode ser a mesma codebase executando tarefas assíncronas via Celery/RQ.
- **Banco de Dados (PostgreSQL):** persiste usuários, contas sociais, assets de áudio, transcrições e histórico de edições.
- **Object Storage (MinIO/S3):** armazena músicas originais, previews e artefatos temporários do pipeline. Os vídeos finais são servidos ao usuário através de URLs com expiração controlada.
- **Aplicativo Mobile (React Native):** interface para artistas se autenticarem, gerirem suas músicas e submeterem novos Reels/remixes.

## Fluxo Alto Nível

1. Usuário autentica no app e vincula sua conta do Instagram. Cookies são criptografados e persistidos.
2. Usuário faz upload de uma música (ou utiliza uma existente). O backend armazena o áudio e inicia a transcrição automática.
3. Ao informar o link do Reel, o backend baixa o vídeo autenticado com os cookies do usuário, executa análise visual e relaciona com as seções da música transcrita.
4. O pipeline gera o vídeo editado, publica em storage temporário e devolve ao usuário para validação.
5. Feedbacks (aprovado, aprovado com ideias, rejeitado) alimentam o módulo de aprendizado personalizado.

## Próximos Passos Técnicos

1. **Modelagem de banco:** implementar as tabelas discutidas no DBML (ver `docs/schema/dbdiagram.dbml`).
2. **Infra local:** utilizar `docker-compose.dev.yml` para subir API + Postgres + MinIO. Criar jobs de limpeza para artefatos temporários.
3. **Organização do backend:** separar módulos (`core`, `auth`, `reels`, `music`, `edits`) e configurar migrations (Alembic) apontando para o Postgres.
4. **Aplicativo React Native:** inicializar projeto em `mobile/` com Expo ou CLI, implementar fluxo de login, upload de música e submissão de links.
5. **CI/CD:** configurar pipelines (GitHub Actions/GitLab CI) para rodar testes, lint e builds mobile.
