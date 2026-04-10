#!/bin/bash
# Script para iniciar servidor e executar teste completo

echo "=========================================="
echo "  TESTE COMPLETO - EDIÇÃO DE VÍDEOS"
echo "=========================================="
echo ""

# Verifica se o servidor já está rodando
if curl -s http://127.0.0.1:8060/docs > /dev/null 2>&1; then
    echo "✓ Servidor já está rodando na porta 8060"
    SERVER_RUNNING=true
else
    echo "→ Iniciando servidor..."
    SERVER_RUNNING=false
    
    # Inicia servidor em background
    cd "$(dirname "$0")"
    source .venv/bin/activate 2>/dev/null || true
    
    # Inicia uvicorn em background
    uvicorn bootstrap.app:app --host 0.0.0.0 --port 8060 --reload > /tmp/clip_editor_server.log 2>&1 &
    SERVER_PID=$!
    
    echo "  Servidor iniciado (PID: $SERVER_PID)"
    echo "  Aguardando servidor ficar pronto..."
    
    # Aguarda servidor ficar pronto (máximo 30 segundos)
    for i in {1..30}; do
        if curl -s http://127.0.0.1:8060/docs > /dev/null 2>&1; then
            echo "  ✓ Servidor pronto!"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    
    if ! curl -s http://127.0.0.1:8060/docs > /dev/null 2>&1; then
        echo "✗ ERRO: Servidor não iniciou corretamente"
        echo "  Verifique os logs em /tmp/clip_editor_server.log"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "  EXECUTANDO TESTE COMPLETO"
echo "=========================================="
echo ""

# Executa o teste
python3 test_video_edit_complete.py
TEST_EXIT_CODE=$?

# Se iniciou o servidor, para ele
if [ "$SERVER_RUNNING" = false ]; then
    echo ""
    echo "→ Parando servidor (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
    echo "  ✓ Servidor parado"
fi

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✓ TESTE CONCLUÍDO COM SUCESSO!"
else
    echo "✗ TESTE FALHOU (código: $TEST_EXIT_CODE)"
fi

exit $TEST_EXIT_CODE


