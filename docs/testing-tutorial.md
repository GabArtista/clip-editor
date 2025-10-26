# Guia rápido de testes automatizados

O projeto utiliza `pytest` para validar os fluxos principais da API FastAPI. Este documento resume como executar os testes e interpretar os resultados.

## 1. Preparação do ambiente

1. Ative o virtualenv utilizado no desenvolvimento local:
   ```bash
   source .venv/bin/activate
   ```
2. Garanta que as dependências já estejam instaladas:
   ```bash
   pip install -r requirements.txt
   ```
3. Não é necessário subir o Docker Compose; os testes usam SQLite e storages temporários em diretórios dentro de `tmp_path`.

## 2. Executando toda a suíte

```bash
pytest
```

Por padrão o `pytest` procura arquivos `tests/test_*.py`. Os principais cenários cobertos são:

- `tests/test_music.py`: upload e consulta de músicas com assets fake.
- `tests/test_videos.py`: ingestão de vídeo e geração de opções de clipe.
- `tests/test_jobs.py`: fila RQ e acompanhamento de jobs.
- `tests/test_feedback.py`: feedbacks e centros de aprendizado.
- `tests/test_metrics.py`: exposição de métricas Prometheus.

## 3. Rodando testes específicos

Use filtragem por arquivo ou por expressão:

- Arquivo único:
  ```bash
  pytest tests/test_music.py
  ```
- Por expressão (ex.: somente testes que mencionam `feedback`):
  ```bash
  pytest -k feedback
  ```

## 4. Variáveis de ambiente úteis

Alguns testes configuram automaticamente variáveis como `DATABASE_URL`, `MUSIC_STORAGE_DIR`, `FAKE_REDIS=1` e `JOB_EXECUTION_MODE=sync`. Se quiser simular outro cenário:

- Forçar modo assíncrono:
  ```bash
  JOB_EXECUTION_MODE=async pytest tests/test_jobs.py
  ```
- Usar diretório customizado para storage:
  ```bash
  MUSIC_STORAGE_DIR=/tmp/fala-music pytest -k music
  ```

## 5. Saída e depuração

- Ative logs detalhados:
  ```bash
  pytest -o log_cli=true -o log_cli_level=INFO
  ```
- Gere relatório JUnit (para CI):
  ```bash
  pytest --junitxml=reports/junit.xml
  ```

Em caso de falhas, confira também os utilitários em `tests/utils.py`, responsáveis por isolar módulos e limpar caches entre execuções.
