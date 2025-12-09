#!/usr/bin/env python3
"""
Corrige imports nos controllers para usar Requests/Resources
"""
import re
from pathlib import Path

# Mapeamento de imports antigos para novos
IMPORT_FIXES = {
    # Auth
    r'from app\.Http\.Requests\.user_dto import UserLoginDTO': 'from app.Http.Requests.Auth.LoginRequest import LoginRequest as UserLoginDTO',
    r'from app\.Http\.Requests\.user_dto import.*TokenResponseDTO': 'from app.Http.Resources.UserResource import TokenResponseResource as TokenResponseDTO',
    r'from app\.Http\.Requests\.user_dto import.*UserResponseDTO': 'from app.Http.Resources.UserResource import UserResource as UserResponseDTO',
    
    # User
    r'from app\.Http\.Requests\.user_dto import.*UserCreateDTO': 'from app.Http.Requests.User.CreateUserRequest import CreateUserRequest as UserCreateDTO',
    r'from app\.Http\.Requests\.user_dto import.*UserUpdateDTO': 'from app.Http.Requests.User.UpdateUserRequest import UpdateUserRequest as UserUpdateDTO',
    
    # Music
    r'from app\.Http\.Requests\.music_dto import MusicCreateDTO': 'from app.Http.Requests.Music.CreateMusicRequest import CreateMusicRequest as MusicCreateDTO',
    r'from app\.Http\.Requests\.music_dto import MusicUpdateDTO': 'from app.Http.Requests.Music.UpdateMusicRequest import UpdateMusicRequest as MusicUpdateDTO',
    r'from app\.Http\.Requests\.music_dto import MusicResponseDTO': 'from app.Http.Resources.MusicResource import MusicResource as MusicResponseDTO',
    
    # Video
    r'from app\.Http\.Requests\.video_edit_dto import ApproveVideoEditDTO': 'from app.Http.Requests.Video.ApproveVideoRequest import ApproveVideoRequest as ApproveVideoEditDTO',
    r'from app\.Http\.Requests\.video_edit_dto import VideoEditResponseDTO': 'from app.Http.Resources.VideoResource import VideoEditResource as VideoEditResponseDTO',
}

def fix_file(file_path: Path):
    """Corrige imports em um arquivo"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Aplica correções
        for pattern, replacement in IMPORT_FIXES.items():
            content = re.sub(pattern, replacement, content)
        
        # Corrige imports múltiplos na mesma linha
        # UserController e outros podem ter múltiplos imports
        if 'from app.Http.Requests.user_dto import' in content:
            # Substitui linha completa
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if 'from app.Http.Requests.user_dto import' in line:
                    # Adiciona imports separados
                    if 'UserCreateDTO' in line:
                        new_lines.append('from app.Http.Requests.User.CreateUserRequest import CreateUserRequest as UserCreateDTO')
                    if 'UserUpdateDTO' in line:
                        new_lines.append('from app.Http.Requests.User.UpdateUserRequest import UpdateUserRequest as UserUpdateDTO')
                    if 'UserResponseDTO' in line:
                        new_lines.append('from app.Http.Resources.UserResource import UserResource as UserResponseDTO')
                    if 'TokenResponseDTO' in line:
                        new_lines.append('from app.Http.Resources.UserResource import TokenResponseResource as TokenResponseDTO')
                else:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
        
        if content != original:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"  ✗ Erro: {file_path}: {e}")
        return False

def main():
    base = Path(__file__).parent.parent
    controllers_dir = base / "app/Http/Controllers"
    
    fixed = 0
    for file in controllers_dir.glob("*.py"):
        if file.name != "__init__.py":
            if fix_file(file):
                print(f"  ✓ {file.name}")
                fixed += 1
    
    print(f"\n✅ {fixed} controllers corrigidos")

if __name__ == "__main__":
    main()

