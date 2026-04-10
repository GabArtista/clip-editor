# 🚀 Como Iniciar o Servidor

## Método 1: Iniciar Manualmente

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Iniciar servidor
uvicorn bootstrap.app:app --host 0.0.0.0 --port 8060
```

## Método 2: Em Background

```bash
# Iniciar em background
uvicorn bootstrap.app:app --host 0.0.0.0 --port 8060 > /tmp/clip_editor_server.log 2>&1 &

# Ver logs
tail -f /tmp/clip_editor_server.log
```

## Método 3: Com Reload (Desenvolvimento)

```bash
uvicorn bootstrap.app:app --host 0.0.0.0 --port 8060 --reload
```

## Verificar se está rodando

```bash
curl http://127.0.0.1:8060/docs
```

Se retornar HTML, está funcionando! ✅

## Parar o servidor

```bash
# Encontrar processo
ps aux | grep uvicorn

# Matar processo (substitua PID)
kill PID_DO_PROCESSO
```


