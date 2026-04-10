#!/usr/bin/env python3
"""Script para testar a API completa"""
import httpx
import json

API_URL = "http://127.0.0.1:8000"

print("=== 1. Login Admin ===")
with httpx.Client() as client:
    login_response = client.post(
        f"{API_URL}/api/v1/auth/login",
        json={"username": "admin", "password": "0102G@briel"}
    )
    print(f"Status: {login_response.status_code}")
    login_data = login_response.json()
    print(json.dumps(login_data, indent=2, ensure_ascii=False))

    if login_response.status_code != 200:
        print("ERRO: Falha no login")
        exit(1)

    admin_token = login_data["access_token"]
    print(f"\n✓ Token admin obtido: {admin_token[:50]}...\n")

    print("=== 2. Criar Usuário ===")
    create_user_response = client.post(
        f"{API_URL}/api/v1/users",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "email": "c1a9x9a9@gmail.com",
            "username": "caxa12",
            "password": "0102G@briel",
            "webhook_url": "https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76",
            "role": "user"
        }
    )
    print(f"Status: {create_user_response.status_code}")
    response_data = create_user_response.json()
    print(json.dumps(response_data, indent=2, ensure_ascii=False))

    if create_user_response.status_code == 400 and "já está em uso" in str(response_data.get("detail", "")):
        print("\n⚠ Usuário já existe, continuando com login...\n")
    elif create_user_response.status_code not in [200, 201]:
        print("ERRO: Falha ao criar usuário")
        exit(1)
    else:
        print("\n✓ Usuário criado com sucesso!\n")

    print("=== 3. Login como Usuário Criado ===")
    user_login_response = client.post(
        f"{API_URL}/api/v1/auth/login",
        json={"username": "caxa12", "password": "0102G@briel"}
    )
    print(f"Status: {user_login_response.status_code}")
    user_login_data = user_login_response.json()
    print(json.dumps(user_login_data, indent=2, ensure_ascii=False))

    if user_login_response.status_code != 200:
        print("ERRO: Falha no login do usuário")
        exit(1)

    user_token = user_login_data["access_token"]
    print(f"\n✓ Token usuário obtido: {user_token[:50]}...\n")

    print("=== 4. Listar Fila de Publicações (upcoming) ===")
    queue_response = client.get(
        f"{API_URL}/api/v1/publications/upcoming",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    print(f"Status: {queue_response.status_code}")
    print(json.dumps(queue_response.json(), indent=2, ensure_ascii=False))

    print("\n=== 5. Listar Todas as Publicações ===")
    all_queue_response = client.get(
        f"{API_URL}/api/v1/publications",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    print(f"Status: {all_queue_response.status_code}")
    print(json.dumps(all_queue_response.json(), indent=2, ensure_ascii=False))

    print("\n=== Teste Completo! ===")
    print(f"Token do usuário para uso: {user_token}")

