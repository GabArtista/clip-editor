# Guia rápido de testes automatizados

Com a refatoração para o fluxo simplificado, mantivemos apenas um arquivo de testes funcional: `tests/test_api.py`. Ele cobre:

1. Registro/login + depósito (`test_register_and_wallet_flow`);
2. Upload + transcrição (`test_music_transcription_flow`);
3. Geração de sugestões e variações (`test_video_suggestions_and_variations`).

## Como rodar

```bash
source .venv/bin/activate
pytest          # roda tudo
pytest -k wallet  # roda apenas o fluxo de carteira
```

Os testes usam SQLite em arquivo (definido no `tests/conftest.py`) e um modo determinístico de IA, então não é necessário subir o Postgres/MinIO para validar a suite.

## Dicas

- Tenha certeza de que nada está rodando em `runtime/test_db.sqlite3` antes de iniciar (o teste já faz o drop/create automaticamente).
- Para testar manualmente o fluxo completo depois do `pytest`, siga o roteiro descrito em `docs/local-manual-testing.md`.
