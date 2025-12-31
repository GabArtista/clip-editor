#!/usr/bin/env python3
"""
Script de teste simples para o endpoint de upload de músicas.
Pode ser executado diretamente sem pytest.
"""
import os
import sys
import requests
import time
from pathlib import Path

# Configuração
API_BASE_URL = os.getenv("API_URL", "http://localhost:8060")
TEST_MUSIC_NAME = "test_upload_api"

def test_health():
    """Testa o endpoint de health."""
    print("🔍 Testando /health...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        print("✅ Health check OK")
        return True
    except Exception as e:
        print(f"❌ Health check falhou: {e}")
        return False


def test_list_music():
    """Testa listagem de músicas."""
    print("\n🔍 Testando /list-music...")
    try:
        response = requests.get(f"{API_BASE_URL}/list-music", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert "musics" in data
        print(f"✅ Listagem OK - {data['count']} músicas encontradas")
        return True
    except Exception as e:
        print(f"❌ Listagem falhou: {e}")
        return False


def test_upload_music():
    """Testa upload de música."""
    print(f"\n🔍 Testando /upload-music com música '{TEST_MUSIC_NAME}'...")
    
    # Procura uma música existente para usar como teste
    music_dir = "music"
    test_file = None
    
    if os.path.exists(music_dir):
        for arquivo in os.listdir(music_dir):
            if arquivo.lower().endswith('.mp3'):
                test_file = os.path.join(music_dir, arquivo)
                break
    
    if not test_file or not os.path.exists(test_file):
        print("⚠️  Nenhuma música encontrada em music/ para usar como teste")
        print("   Pulando teste de upload (precisa de arquivo MP3 real)")
        return None
    
    try:
        # Verifica se já existe
        list_response = requests.get(f"{API_BASE_URL}/list-music", timeout=10)
        if list_response.status_code == 200:
            existing = [m for m in list_response.json().get("musics", []) if m["name"] == TEST_MUSIC_NAME]
            if existing:
                print(f"⚠️  Música '{TEST_MUSIC_NAME}' já existe, deletando primeiro...")
                delete_response = requests.delete(f"{API_BASE_URL}/delete-music/{TEST_MUSIC_NAME}", timeout=10)
                time.sleep(1)
        
        # Faz upload
        with open(test_file, "rb") as f:
            files = {"file": (os.path.basename(test_file), f, "audio/mpeg")}
            data = {"music_name": TEST_MUSIC_NAME}
            response = requests.post(f"{API_BASE_URL}/upload-music", files=files, data=data, timeout=60)
        
        assert response.status_code == 200, f"Status {response.status_code}: {response.text}"
        result = response.json()
        assert result["ok"] is True
        assert result["music_name"] == TEST_MUSIC_NAME
        assert "duration" in result
        assert result["duration"] > 0
        
        print(f"✅ Upload OK")
        print(f"   - Nome: {result['music_name']}")
        print(f"   - Duração: {result['duration']:.2f}s")
        print(f"   - Tamanho: {result['size_bytes']} bytes")
        print(f"   - Codec: {result['codec']}")
        
        # Verifica se aparece na listagem
        list_response = requests.get(f"{API_BASE_URL}/list-music", timeout=10)
        if list_response.status_code == 200:
            musics = list_response.json().get("musics", [])
            found = [m for m in musics if m["name"] == TEST_MUSIC_NAME]
            if found:
                print(f"✅ Música aparece na listagem")
            else:
                print(f"⚠️  Música não aparece na listagem")
        
        return True
        
    except AssertionError as e:
        print(f"❌ Upload falhou (assertion): {e}")
        if response.status_code != 200:
            print(f"   Resposta: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Upload falhou: {e}")
        return False


def test_delete_music():
    """Testa deleção de música."""
    print(f"\n🔍 Testando /delete-music...")
    
    try:
        # Tenta deletar a música de teste
        response = requests.delete(f"{API_BASE_URL}/delete-music/{TEST_MUSIC_NAME}", timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Deleção OK - Música '{TEST_MUSIC_NAME}' removida")
            return True
        elif response.status_code == 404:
            print(f"⚠️  Música '{TEST_MUSIC_NAME}' não existe (já foi deletada ou nunca foi criada)")
            return True  # Não é erro se não existir
        else:
            print(f"❌ Deleção falhou: Status {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Deleção falhou: {e}")
        return False


def test_upload_duplicate():
    """Testa upload de música duplicada."""
    print(f"\n🔍 Testando upload duplicado...")
    
    music_dir = "music"
    test_file = None
    
    if os.path.exists(music_dir):
        for arquivo in os.listdir(music_dir):
            if arquivo.lower().endswith('.mp3'):
                test_file = os.path.join(music_dir, arquivo)
                break
    
    if not test_file or not os.path.exists(test_file):
        print("⚠️  Pulando teste de duplicata (precisa de arquivo MP3)")
        return None
    
    try:
        # Primeiro upload
        with open(test_file, "rb") as f:
            files = {"file": (os.path.basename(test_file), f, "audio/mpeg")}
            data = {"music_name": TEST_MUSIC_NAME}
            response1 = requests.post(f"{API_BASE_URL}/upload-music", files=files, data=data, timeout=60)
        
        if response1.status_code != 200:
            print(f"⚠️  Primeiro upload falhou, pulando teste de duplicata")
            return None
        
        # Segundo upload (deve falhar)
        with open(test_file, "rb") as f:
            files = {"file": (os.path.basename(test_file), f, "audio/mpeg")}
            data = {"music_name": TEST_MUSIC_NAME}
            response2 = requests.post(f"{API_BASE_URL}/upload-music", files=files, data=data, timeout=60)
        
        assert response2.status_code == 409, f"Esperava 409, recebeu {response2.status_code}"
        assert "já existe" in response2.json()["detail"].lower()
        
        print("✅ Teste de duplicata OK - Upload duplicado foi rejeitado corretamente")
        
        # Limpa
        requests.delete(f"{API_BASE_URL}/delete-music/{TEST_MUSIC_NAME}", timeout=10)
        
        return True
        
    except Exception as e:
        print(f"❌ Teste de duplicata falhou: {e}")
        # Limpa se necessário
        try:
            requests.delete(f"{API_BASE_URL}/delete-music/{TEST_MUSIC_NAME}", timeout=10)
        except:
            pass
        return False


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("🧪 TESTES AUTOMÁTICOS - API DE UPLOAD DE MÚSICAS")
    print("=" * 60)
    print(f"API URL: {API_BASE_URL}\n")
    
    results = []
    
    # Testes básicos
    results.append(("Health Check", test_health()))
    results.append(("List Music", test_list_music()))
    
    # Testes de upload
    upload_result = test_upload_music()
    if upload_result is not None:
        results.append(("Upload Music", upload_result))
    
    # Teste de duplicata
    duplicate_result = test_upload_duplicate()
    if duplicate_result is not None:
        results.append(("Upload Duplicate", duplicate_result))
    
    # Teste de deleção
    results.append(("Delete Music", test_delete_music()))
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, result in results:
        if result is True:
            print(f"✅ {name}: PASSOU")
            passed += 1
        elif result is False:
            print(f"❌ {name}: FALHOU")
            failed += 1
        else:
            print(f"⚠️  {name}: PULADO")
            skipped += 1
    
    print("=" * 60)
    print(f"Total: {len(results)} | ✅ {passed} | ❌ {failed} | ⚠️  {skipped}")
    print("=" * 60)
    
    if failed > 0:
        print("\n❌ Alguns testes falharam!")
        sys.exit(1)
    else:
        print("\n✅ Todos os testes passaram!")
        sys.exit(0)


if __name__ == "__main__":
    main()

