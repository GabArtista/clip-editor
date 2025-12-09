"""
Controllers - Laravel Style
"""
from app.Http.Controllers.AuthController import router as auth_router
from app.Http.Controllers.UserController import router as user_router
from app.Http.Controllers.MusicController import router as music_router
from app.Http.Controllers.VideoController import router as video_router
from app.Http.Controllers.VideoEditController import router as video_edit_router
from app.Http.Controllers.PublicationQueueController import router as publication_router
from app.Http.Controllers.TemplateController import router as template_router

# Aliases para compatibilidade
AuthController = type('AuthController', (), {'router': auth_router})
UserController = type('UserController', (), {'router': user_router})
MusicController = type('MusicController', (), {'router': music_router})
VideoController = type('VideoController', (), {'router': video_router})
VideoEditController = type('VideoEditController', (), {'router': video_edit_router})
PublicationQueueController = type('PublicationQueueController', (), {'router': publication_router})
TemplateController = type('TemplateController', (), {'router': template_router})

__all__ = [
    "AuthController",
    "UserController",
    "MusicController",
    "VideoController",
    "VideoEditController",
    "PublicationQueueController",
    "TemplateController",
]

