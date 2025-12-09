FROM python:3.11-slim

# Sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Dependências Python
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip wheel \
    && pip install --no-cache-dir -r requirements.txt

# Código
COPY . .

# Healthcheck (FastAPI docs)
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD curl -fsS http://127.0.0.1:8060/health >/dev/null || exit 1

EXPOSE 8060
CMD ["uvicorn", "bootstrap.app:app", "--host", "0.0.0.0", "--port", "8060"]
