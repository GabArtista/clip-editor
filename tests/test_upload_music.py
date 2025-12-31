"""
Testes automáticos para o endpoint de upload de músicas.
"""
import os
import pytest
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from api.app import app

# Configuração de testes
TEST_MUSIC_DIR = "test_music"
TEST_PROCESSED_DIR = "test_processed"


@pytest.fixture(scope="function")
def client():
    """Cria um cliente de teste."""
    return TestClient(app)


@pytest.fixture(scope="function")
def setup_test_dirs():
    """Cria diretórios de teste e limpa após."""
    # Backup dos diretórios originais
    original_music = "music"
    original_processed = "processed"
    
    # Cria diretórios de teste
    os.makedirs(TEST_MUSIC_DIR, exist_ok=True)
    os.makedirs(TEST_PROCESSED_DIR, exist_ok=True)
    
    # Backup temporário
    music_backup = None
    processed_backup = None
    
    if os.path.exists(original_music):
        music_backup = original_music + ".backup"
        if os.path.exists(music_backup):
            shutil.rmtree(music_backup)
        shutil.copytree(original_music, music_backup)
    
    yield
    
    # Restaura diretórios originais
    if music_backup and os.path.exists(music_backup):
        if os.path.exists(original_music):
            shutil.rmtree(original_music)
        shutil.move(music_backup, original_music)
    
    # Limpa diretórios de teste
    if os.path.exists(TEST_MUSIC_DIR):
        shutil.rmtree(TEST_MUSIC_DIR)
    if os.path.exists(TEST_PROCESSED_DIR):
        shutil.rmtree(TEST_PROCESSED_DIR)


@pytest.fixture
def sample_audio_file():
    """Cria um arquivo de áudio de teste válido (MP3 simulado)."""
    # Cria um arquivo temporário que será usado como "MP3"
    # Em um teste real, você usaria um arquivo MP3 real
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    # Escreve alguns bytes para simular um arquivo
    temp_file.write(b'fake mp3 content for testing')
    temp_file.close()
    yield temp_file.name
    if os.path.exists(temp_file.name):
        os.remove(temp_file.name)


def test_health_endpoint(client):
    """Testa o endpoint de health check."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_music_success(client, setup_test_dirs, sample_audio_file):
    """Testa upload bem-sucedido de música."""
    # Usa uma música real do sistema se existir
    music_path = os.path.join("music", "Fala.mp3")
    
    if not os.path.exists(music_path):
        pytest.skip("Música de teste não encontrada")
    
    with open(music_path, "rb") as f:
        files = {"file": ("test_music.mp3", f, "audio/mpeg")}
        data = {"music_name": "test_upload_music"}
        
        response = client.post("/upload-music", files=files, data=data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "music_name" in data
    assert "file_path" in data
    assert "duration" in data
    assert data["duration"] > 0
    
    # Verifica se o arquivo foi salvo
    saved_path = data["file_path"]
    assert os.path.exists(saved_path)
    assert saved_path.endswith(".mp3")
    
    # Limpa após teste
    if os.path.exists(saved_path):
        os.remove(saved_path)


def test_upload_music_without_name(client, setup_test_dirs):
    """Testa upload usando nome do arquivo."""
    music_path = os.path.join("music", "Fala.mp3")
    
    if not os.path.exists(music_path):
        pytest.skip("Música de teste não encontrada")
    
    with open(music_path, "rb") as f:
        files = {"file": ("minha_musica.mp3", f, "audio/mpeg")}
        
        response = client.post("/upload-music", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["music_name"] == "minha_musica"
    
    # Limpa após teste
    saved_path = data["file_path"]
    if os.path.exists(saved_path):
        os.remove(saved_path)


def test_upload_music_duplicate(client, setup_test_dirs):
    """Testa upload de música duplicada."""
    music_path = os.path.join("music", "Fala.mp3")
    
    if not os.path.exists(music_path):
        pytest.skip("Música de teste não encontrada")
    
    music_name = "test_duplicate"
    
    # Primeiro upload
    with open(music_path, "rb") as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        data = {"music_name": music_name}
        response1 = client.post("/upload-music", files=files, data=data)
    
    assert response1.status_code == 200
    
    # Segundo upload (deve falhar)
    with open(music_path, "rb") as f:
        files = {"file": ("test2.mp3", f, "audio/mpeg")}
        data = {"music_name": music_name}
        response2 = client.post("/upload-music", files=files, data=data)
    
    assert response2.status_code == 409
    assert "já existe" in response2.json()["detail"].lower()
    
    # Limpa após teste
    saved_path = response1.json()["file_path"]
    if os.path.exists(saved_path):
        os.remove(saved_path)


def test_upload_music_empty_file(client):
    """Testa upload de arquivo vazio."""
    files = {"file": ("empty.mp3", b"", "audio/mpeg")}
    response = client.post("/upload-music", files=files)
    
    assert response.status_code == 400
    assert "vazio" in response.json()["detail"].lower()


def test_upload_music_invalid_audio(client):
    """Testa upload de arquivo que não é áudio válido."""
    # Cria um arquivo de texto como se fosse áudio
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    temp_file.write(b'This is not a valid audio file')
    temp_file.close()
    
    try:
        with open(temp_file.name, "rb") as f:
            files = {"file": ("invalid.mp3", f, "audio/mpeg")}
            response = client.post("/upload-music", files=files)
        
        # Deve falhar na validação com ffprobe
        assert response.status_code in [400, 500]
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)


def test_list_music(client):
    """Testa listagem de músicas."""
    response = client.get("/list-music")
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "musics" in data
    assert "count" in data
    assert isinstance(data["musics"], list)
    assert data["count"] == len(data["musics"])


def test_delete_music(client, setup_test_dirs):
    """Testa deleção de música."""
    music_path = os.path.join("music", "Fala.mp3")
    
    if not os.path.exists(music_path):
        pytest.skip("Música de teste não encontrada")
    
    music_name = "test_delete"
    
    # Primeiro faz upload
    with open(music_path, "rb") as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        data = {"music_name": music_name}
        upload_response = client.post("/upload-music", files=files, data=data)
    
    assert upload_response.status_code == 200
    saved_path = upload_response.json()["file_path"]
    
    # Depois deleta
    delete_response = client.delete(f"/delete-music/{music_name}")
    
    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True
    assert not os.path.exists(saved_path)


def test_delete_music_not_found(client):
    """Testa deleção de música inexistente."""
    response = client.delete("/delete-music/musica_que_nao_existe")
    
    assert response.status_code == 404
    assert "não encontrada" in response.json()["detail"].lower()


def test_upload_music_sanitize_name(client, setup_test_dirs):
    """Testa sanitização de nome de música."""
    music_path = os.path.join("music", "Fala.mp3")
    
    if not os.path.exists(music_path):
        pytest.skip("Música de teste não encontrada")
    
    # Nome com caracteres especiais
    with open(music_path, "rb") as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        data = {"music_name": "música com espaços e @#$%"}
        
        response = client.post("/upload-music", files=files, data=data)
    
    assert response.status_code == 200
    data = response.json()
    # Nome deve ser sanitizado
    assert " " not in data["music_name"] or "_" in data["music_name"]
    
    # Limpa após teste
    saved_path = data["file_path"]
    if os.path.exists(saved_path):
        os.remove(saved_path)

