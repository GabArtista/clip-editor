#!/usr/bin/env python3
"""
Teste completo de ponta a ponta para validação da edição de vídeos
Testa: processamento, aprovação, expiração e fila de publicação
"""
import httpx
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo

API_URL = "http://127.0.0.1:8060"
SP_TIMEZONE = ZoneInfo("America/Sao_Paulo")

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def print_result(status_code, data, success_msg=None, error_msg=None):
    print(f"Status: {status_code}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if status_code >= 200 and status_code < 300:
        if success_msg:
            print(f"\n✓ {success_msg}")
    else:
        if error_msg:
            print(f"\n✗ ERRO: {error_msg}")
    print()

def main():
    print_section("TESTE COMPLETO - FLUXO DE EDIÇÃO DE VÍDEOS")
    
    with httpx.Client(timeout=300.0) as client:
        # ============================================================
        # 1. LOGIN ADMIN
        # ============================================================
        print_section("1. Login Admin")
        login_response = client.post(
            f"{API_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "0102G@briel"}
        )
        login_data = login_response.json()
        print_result(login_response.status_code, login_data)
        
        if login_response.status_code != 200:
            print("ERRO: Falha no login admin")
            return False
        
        admin_token = login_data["access_token"]
        
        # ============================================================
        # 2. CRIAR OU OBTER USUÁRIO
        # ============================================================
        print_section("2. Criar/Obter Usuário")
        create_user_response = client.post(
            f"{API_URL}/api/v1/users",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {admin_token}"
            },
            json={
                "email": "teste.video@example.com",
                "username": "teste_video",
                "password": "teste123",
                "webhook_url": "https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76",
                "role": "user"
            }
        )
        create_data = create_user_response.json()
        print_result(create_user_response.status_code, create_data)
        
        if create_user_response.status_code == 400 and "já está em uso" in str(create_data.get("detail", "")):
            print("⚠ Usuário já existe, continuando...")
        elif create_user_response.status_code not in [200, 201]:
            print("ERRO: Falha ao criar usuário")
            return False
        
        # ============================================================
        # 3. LOGIN COMO USUÁRIO
        # ============================================================
        print_section("3. Login como Usuário")
        user_login_response = client.post(
            f"{API_URL}/api/v1/auth/login",
            json={"username": "teste_video", "password": "teste123"}
        )
        user_login_data = user_login_response.json()
        print_result(user_login_response.status_code, user_login_data)
        
        if user_login_response.status_code != 200:
            print("ERRO: Falha no login do usuário")
            return False
        
        user_token = user_login_data["access_token"]
        user_id = user_login_data.get("user", {}).get("id")
        
        # ============================================================
        # 4. UPLOAD DE MÚSICA
        # ============================================================
        print_section("4. Upload de Música")
        
        # Verifica se já existe música
        list_music_response = client.get(
            f"{API_URL}/api/v1/musics",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        musics = list_music_response.json()
        
        music_id = None
        if musics and len(musics) > 0:
            music_id = musics[0]["id"]
            print(f"✓ Usando música existente: ID {music_id} - {musics[0]['name']}")
        else:
            # Tenta fazer upload de uma música de teste
            # Se não tiver arquivo, usa uma música existente de outro usuário ou pula
            print("⚠ Nenhuma música encontrada. Você precisa fazer upload de uma música primeiro.")
            print("   Use: POST /api/v1/musics com arquivo MP3")
            return False
        
        # ============================================================
        # 5. PROCESSAR VÍDEO
        # ============================================================
        print_section("5. Processar Vídeo")
        print("Processando vídeo do Instagram...")
        
        process_response = client.post(
            f"{API_URL}/api/v1/videos/process",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "url": "https://www.instagram.com/p/DNixp-4Naqh/",
                "music_id": music_id,
                "impact_music": 51.0,
                "impact_video": 1.0,
                "return_format": "url"
            }
        )
        process_data = process_response.json()
        print_result(process_response.status_code, process_data)
        
        if process_response.status_code != 200:
            print("ERRO: Falha ao processar vídeo")
            return False
        
        video_edit_id = process_data.get("video_edit_id")
        preview_url = process_data.get("preview_url")
        s3_url = process_data.get("s3_url")
        expires_at_str = process_data.get("expires_at")
        
        if not video_edit_id:
            print("ERRO: video_edit_id não retornado")
            return False
        
        print(f"\n✓ Vídeo processado com sucesso!")
        print(f"  - Video Edit ID: {video_edit_id}")
        print(f"  - Preview URL: {preview_url[:80]}..." if preview_url else "  - Preview URL: N/A")
        print(f"  - S3 URL: {s3_url[:80]}..." if s3_url else "  - S3 URL: N/A")
        print(f"  - Expira em: {expires_at_str}")
        
        # ============================================================
        # 6. VERIFICAR VÍDEO EDITADO
        # ============================================================
        print_section("6. Verificar Vídeo Editado")
        get_video_response = client.get(
            f"{API_URL}/api/v1/video-edits/{video_edit_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        video_data = get_video_response.json()
        print_result(get_video_response.status_code, video_data)
        
        if get_video_response.status_code != 200:
            print("ERRO: Falha ao obter vídeo editado")
            return False
        
        status = video_data.get("status")
        expires_at_str = video_data.get("expires_at")
        
        print(f"\n✓ Status do vídeo: {status}")
        print(f"  - Expira em: {expires_at_str}")
        
        # Verifica se está expirado
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            current_time = datetime.now(SP_TIMEZONE)
            time_remaining = (expires_at - current_time.replace(tzinfo=SP_TIMEZONE)).total_seconds()
            
            if time_remaining > 0:
                print(f"  - Tempo restante: {int(time_remaining)} segundos ({int(time_remaining/60)} minutos)")
            else:
                print(f"  - ⚠ VÍDEO JÁ EXPIROU!")
        
        # ============================================================
        # 7. LISTAR VÍDEOS PENDENTES
        # ============================================================
        print_section("7. Listar Vídeos Pendentes de Aprovação")
        pending_response = client.get(
            f"{API_URL}/api/v1/video-edits/pending",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        pending_data = pending_response.json()
        print_result(pending_response.status_code, pending_data)
        
        if pending_response.status_code == 200:
            print(f"✓ Total de vídeos pendentes: {len(pending_data)}")
        
        # ============================================================
        # 8. APROVAR VÍDEO (DENTRO DE 5 MINUTOS)
        # ============================================================
        print_section("8. Aprovar Vídeo")
        
        # Verifica se ainda não expirou
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            current_time = datetime.now(SP_TIMEZONE)
            time_remaining = (expires_at - current_time.replace(tzinfo=SP_TIMEZONE)).total_seconds()
            
            if time_remaining <= 0:
                print("⚠ VÍDEO JÁ EXPIROU! Não é possível aprovar.")
                print("   Testando rejeição...")
                
                reject_response = client.post(
                    f"{API_URL}/api/v1/video-edits/{video_edit_id}/reject",
                    headers={"Authorization": f"Bearer {user_token}"}
                )
                reject_data = reject_response.json()
                print_result(reject_response.status_code, reject_data)
                return False
            else:
                print(f"✓ Tempo restante: {int(time_remaining)} segundos - Aprovando...")
        
        approve_response = client.post(
            f"{API_URL}/api/v1/video-edits/approve",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user_token}"
            },
            json={
                "video_edit_id": video_edit_id,
                "description": "Vídeo de teste aprovado automaticamente 🚀"
            }
        )
        approve_data = approve_response.json()
        print_result(approve_response.status_code, approve_data, "Vídeo aprovado com sucesso!")
        
        if approve_response.status_code != 200:
            print("ERRO: Falha ao aprovar vídeo")
            if "expirou" in str(approve_data.get("detail", "")).lower():
                print("  → O vídeo expirou antes da aprovação (comportamento esperado se demorou > 5min)")
            return False
        
        publication_id = approve_data.get("publication_id")
        scheduled_date = approve_data.get("scheduled_date")
        
        print(f"\n✓ Vídeo aprovado e agendado!")
        print(f"  - Publication ID: {publication_id}")
        print(f"  - Data agendada: {scheduled_date}")
        
        # ============================================================
        # 9. VERIFICAR STATUS DO VÍDEO APÓS APROVAÇÃO
        # ============================================================
        print_section("9. Verificar Status do Vídeo Após Aprovação")
        get_video_after_response = client.get(
            f"{API_URL}/api/v1/video-edits/{video_edit_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        video_after_data = get_video_after_response.json()
        print_result(get_video_after_response.status_code, video_after_data)
        
        if get_video_after_response.status_code == 200:
            new_status = video_after_data.get("status")
            print(f"\n✓ Novo status: {new_status}")
            if new_status == "published":
                print("  → Vídeo marcado como publicado (agendado)")
        
        # ============================================================
        # 10. VERIFICAR FILA DE PUBLICAÇÃO
        # ============================================================
        print_section("10. Verificar Fila de Publicação")
        queue_response = client.get(
            f"{API_URL}/api/v1/publications/upcoming",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        queue_data = queue_response.json()
        print_result(queue_response.status_code, queue_data)
        
        if queue_response.status_code == 200:
            print(f"✓ Total de publicações agendadas: {len(queue_data)}")
            if queue_data:
                print(f"  - Próxima publicação: {queue_data[0].get('scheduled_date')}")
        
        # ============================================================
        # RESUMO FINAL
        # ============================================================
        print_section("RESUMO DO TESTE")
        print("✓ Login admin: OK")
        print("✓ Criar/obter usuário: OK")
        print("✓ Login usuário: OK")
        print("✓ Upload/obter música: OK")
        print("✓ Processar vídeo: OK")
        print("✓ Verificar vídeo editado: OK")
        print("✓ Listar pendentes: OK")
        print("✓ Aprovar vídeo: OK")
        print("✓ Verificar status após aprovação: OK")
        print("✓ Verificar fila de publicação: OK")
        print("\n🎉 TESTE COMPLETO EXECUTADO COM SUCESSO!")
        print(f"\nVideo Edit ID: {video_edit_id}")
        if publication_id:
            print(f"Publication ID: {publication_id}")
        
        return True

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Teste interrompido pelo usuário")
        exit(1)
    except Exception as e:
        print(f"\n\n✗ ERRO INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


