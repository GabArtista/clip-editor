import os
from glob import glob

def ultimo_video(diretorio="videos/"):
    arquivos = glob(os.path.join(diretorio, "*.mp4"))
    if not arquivos:
        return None
    return max(arquivos, key=os.path.getctime)
