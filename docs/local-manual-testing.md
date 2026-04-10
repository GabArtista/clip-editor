# Guia atualizado de execução local

Este tutorial cobre o fluxo atual do backend simplificado (auth, carteira, músicas e IA determinística). Use-o quando quiser rodar a API na sua máquina e testar as chamadas com o Postman ou `curl`.

## 1. Pré-requisitos

- Python 3.12 com `venv`.
- Docker + Docker Compose (para Postgres/MinIO opcionais).
- Arquivo `.env` baseado em `.env.dev` com as variáveis de banco e diretórios ajustadas.

## 2. Preparação do ambiente

1. **Criar virtualenv e instalar dependências**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Subir o Postgres** (opcionalmente também o MinIO):
   ```bash
   docker compose -f docker-compose.dev.yml up -d postgres
   ```
   Por padrão o serviço fica disponível em `127.0.0.1:55432`.

3. **Rodar migrações**
   ```bash
   alembic upgrade head
   ```

4. **Iniciar a API**
   ```bash
   uvicorn api.app:app --reload --port 8060
   ```
   A API responde em `http://localhost:8060`.

## 3. Postman / Coleção

Importe somente `postmans/fala-viral-api.postman_collection.json`. Ela já contém todos os fluxos:

- Auth (`/auth/register`, `/auth/login`, `/me`);
- Wallet (`/wallet/deposit`, `/wallet/transactions`);
- Music (`/music`, `/music/{id}`, `/music/{id}/transcribe`);
- Video IA (`/videos/suggestions`, `/videos/variations`).

Configure o ambiente do Postman com:

| Variável | Exemplo |
| --- | --- |
| `baseUrl` | `http://localhost:8060` |
| `accessToken` | preencha após registrar/login |
| `musicId` | atualizado após o upload |

## 4. Roteiro rápido de testes manuais

1. **Auth:** `POST /auth/register` → copiar `access_token`. Se necessário, `POST /auth/login`.
2. **Wallet:** `POST /wallet/deposit` com valores em reais (créditos). Verificar em `GET /wallet/transactions`.
3. **Música:** `POST /music` (multipart) e guardar o `id`. Conferir com `GET /music`.
4. **Transcrição:** `POST /music/{id}/transcribe` → verifica se os créditos foram debitados e se a transcrição foi salva.
5. **Sugestões de vídeo:** `POST /videos/suggestions` passando `video_url`, duração e a lista `music_ids`.
6. **Variações:** `POST /videos/variations` com o `music_id` escolhido na etapa anterior.

## 5. Debug / Logs

- **API local:** os logs aparecem no terminal do `uvicorn`.
- **API via Docker Compose:** `docker compose -f docker-compose.dev.yml logs -f api`.
- **Postgres:** `docker compose -f docker-compose.dev.yml logs -f postgres`.

## 6. Encerramento

```bash
docker compose -f docker-compose.dev.yml down
deactivate  # sai do virtualenv
```

Se quiser limpar tudo, use `docker compose -f docker-compose.dev.yml down -v` para remover volumes e começar do zero.
