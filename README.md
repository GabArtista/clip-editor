# FALA Viral Backend

Backend FastAPI responsável por:

- Cadastro e autenticação dos artistas.
- Biblioteca de músicas com upload seguro e armazenamento local.
- Transcrição das faixas via IA (com cálculo automático de custo).
- Geração de sugestões de cortes e variações de edição usando contextos das músicas + anotações do vídeo.
- Carteira de créditos (depósitos e consumo a cada operação que usa IA).

## Executando localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api.app:app --reload --port 8060
```

Variáveis importantes (defina em `.env` ou `.env.dev`):

| Variável | Função |
| --- | --- |
| `DATABASE_URL` | Postgres ou SQLite (fallback `runtime/app.db`). |
| `MUSIC_STORAGE_DIR` | Pasta para os uploads das músicas. |
| `OPENAI_API_KEY` | Chave para uso real da LLM. Sem ela o sistema usa um modo determinístico offline. |
| `IA_*` | Custos por operação (áudio, visão, tokens, taxa extra). |

## Principais endpoints

| Método | Rota | Descrição |
| --- | --- | --- |
| `POST /auth/register` | Cria usuário + carteira e já devolve token. |
| `POST /auth/login` | Login tradicional (retorna token). |
| `GET /me` | Dados do usuário autenticado + saldo. |
| `POST /wallet/deposit` | Depósito manual em créditos (R$). |
| `GET /wallet/transactions` | Últimas movimentações. |
| `POST /music` | Upload da música (multipart). |
| `GET /music` / `GET /music/{id}` | Listagem e detalhes (inclui transcrição). |
| `POST /music/{id}/transcribe` | Dispara a IA de transcrição e debita o custo. |
| `POST /videos/suggestions` | Recebe link + duração do vídeo e retorna 3 sugestões combinando música + visão. |
| `POST /videos/variations` | Gera 3 variações de edição para uma música já escolhida. |

Os endpoints de vídeo não persistem nada: eles apenas retornam as três opções calculadas na hora.

## Custos e carteira

Cada operação que usa IA chama o `CostCalculator`, que:

1. Estima o custo da OpenAI com base na duração ou na quantidade estimada de tokens (sempre arredondando para o pior caso).
2. Soma a taxa fixa interna definida em `IA_PLATFORM_EXTRA_FEE_BRL` (padrão R$ 0,30).
3. Debita o valor total da carteira do usuário antes de executar a IA.

Sem saldo suficiente, o endpoint devolve **402 Payment Required**.

## Testes

```bash
pytest
```

Os testes usam SQLite e um modo determinístico de IA (sem chamar a OpenAI). Para testar contra a API real, basta definir `OPENAI_API_KEY` e remover os limites na infraestrutura.
