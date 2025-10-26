# Tutorial de fluxos da plataforma

Este material agrupa os endpoints por fluxo de negócio e descreve a sequência sugerida para validar o editor automático de vídeos via API. Use em conjunto com a pasta `postmans/`.

## 1. Autenticação & Sessões

1. **`POST /auth/register`** – cria usuário e devolve `access_token`. Use para o primeiro acesso ou para ambientes de desenvolvimento.
2. **`POST /auth/login`** – retorna novo `access_token` (form-urlencoded com `username` e `password`).
3. **`GET /auth/me`** – confirma o usuário autenticado; útil para validar o token atual.
4. **`POST /update-session`** – persiste cookies exportados do navegador para acesso autenticado em jobs (`cookie_string` em JSON). Retorno esperado:
   ```json
   {"status": "ok", "message": "Sessão de cookies atualizada com sucesso e salva em formato Netscape!"}
   ```

## 2. Health Check

1. **`GET /health`** – confirma que a API responde (`{"status": "ok"}`).

## 3. Biblioteca de Músicas

1. **`POST /music`** – multipart com metadados e arquivo de áudio (o usuário é inferido pelo token). Resultado: `201` com `id`, `title`, `transcription`, `beats`, etc.
2. **`GET /music/{music_id}`** – use o ID do passo anterior para validar o armazenamento e os dados derivados (transcrição placeholder, embeddings).

## 4. Ingestão de Vídeos e Sugestões

1. **`POST /videos`** – envie `url` do reel e, opcionalmente, `music_id`. A resposta inclui `options` (modelos de clipe) e o novo `video_id`.
2. **`GET /videos/{video_id}`** – consulta detalhada do vídeo, com status, análise placeholder e lista ordenada de clipes (`option_order`).

## 5. Processamento & Renderização

1. **`POST /processar`** – fluxo legado assíncrono; devolve `job_id`.
2. **`GET /jobs/{job_id}`** – acompanha qualquer job criado (processamento ou render).
3. **`POST /render/{video_id}`** – forneça `clip_ids` (da consulta aos vídeos) para gerar os arquivos finais. Retorna outro `job_id`.
4. **`DELETE /cleanup`** – remove arquivos antigos das pastas `videos/` e `processed/` para economizar disco local.

## 6. Feedbacks e Centros de Aprendizado

1. **`POST /feedback/music/{music_id}`** – captura feedback específico de uma música.
2. **`POST /feedback/artist`** – feedback macro do artista, podendo referenciar uma música.
3. **`POST /learning-centers`** – cria um centro versionado (`scope` = `global`, `artist` ou `music`).
4. **`PUT /learning-centers/{center_id}`** – atualiza parâmetros/estado.
5. **`DELETE /learning-centers/{center_id}`** – arquiva o centro.

## 7. Observabilidade

1. **`GET /metrics`** – retorno em texto para Prometheus, incluindo contadores de requests e jobs.

## 8. Boas práticas gerais

- Defina a variável `base_url` para o ambiente atual (`http://localhost:8060` em desenvolvimento).
- Para requests dependentes (ex.: renderização), armazene os IDs da resposta anterior como variáveis em execução no Postman.
- Mantenha `JOB_EXECUTION_MODE=sync` ao validar fluxos end-to-end manualmente; isso simplifica a inspeção dos resultados sem precisar de worker separado.
- Use `logs/auth.log` e `logs/api.log` (se habilitados) para depurar requisições falhas.

Os arquivos da pasta `postmans/` já seguem essa estrutura, permitindo importar apenas os fluxos necessários durante a depuração.
