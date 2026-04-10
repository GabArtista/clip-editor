# Fluxo atual da FALA Viral API

Este resumo agrupa os endpoints por fluxo para facilitar o teste manual (use com a nova coleção do Postman).

## 1. Autenticação
1. `POST /auth/register` – cria usuário e carteira.
2. `POST /auth/login` – devolve novo `access_token`.
3. `GET /me` – mostra status e saldo (`wallet_balance` + `currency`).

## 2. Carteira
1. `POST /wallet/deposit` – adiciona créditos (R$). Use antes de consumir IA.
2. `GET /wallet/transactions` – últimas movimentações (depósitos/consumos).

## 3. Biblioteca de músicas
1. `POST /music` – upload multipart (`title`, `duration_seconds`, `audio_file`).
2. `GET /music` – lista do usuário autenticado.
3. `GET /music/{music_id}` – detalhes + transcrição atual (se existir).
4. `POST /music/{music_id}/transcribe` – dispara a IA determinística e debita o custo calculado.

## 4. IA de vídeo
1. `POST /videos/suggestions`
   - Entrada: `video_url`, `video_duration_seconds`, `notes`, `music_ids`.
   - Saída: 3 sugestões com `music_id`, `start_time_seconds`, `prompt`, etc.
2. `POST /videos/variations`
   - Entrada: `video_url`, `video_duration_seconds`, `notes`, `music_id`.
   - Saída: 3 variações com descrições e blocos de segmentos.

Não há mais persistência de vídeos/feedbacks – tudo é calculado na hora e retornado em JSON.

## 5. Observabilidade
1. `GET /health` – status rápido.
2. `GET /metrics` – métricas em formato Prometheus (requisições, custos estimados, etc.).

## Boas práticas
- Grave `access_token` e `music_id` como variáveis no Postman.
- Verifique sempre o saldo (`GET /me` ou `/wallet/transactions`) antes de acionar as rotas de IA.
- Para resetar o ambiente, rode `docker compose -f docker-compose.dev.yml down -v` e `alembic upgrade head`.
