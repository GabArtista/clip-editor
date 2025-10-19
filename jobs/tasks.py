import base64
import time
from pathlib import Path
from typing import Any, Dict, List

from sqlalchemy.orm import joinedload

from app.database import session_scope
from app.models import AudioFile, MusicAsset, VideoClipModel, VideoIngest
from metrics import increment_counter, observe_histogram
from scripts.download import baixar_reel
from scripts.edit import adicionar_musica

from .cleanup import cleanup_directory
from .config import get_env_float
from .lock import processing_lock
from .state import JobStateRepository

SESSION_FILE_PATH = Path("cookies/session.netscape")
VIDEOS_DIR = Path("videos")
PROCESSED_DIR = Path("processed")
MUSIC_DIR = Path("music")


def _ensure_directories() -> None:
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_music_path(music_name: str) -> Path:
    path = MUSIC_DIR / f"{music_name}.mp3"
    if not path.exists():
        raise FileNotFoundError(f"Música não encontrada: {path}")
    return path


def _build_result(filename: str, output_path: Path, return_format: str) -> Dict[str, Any]:
    if return_format == "url":
        return {"filename": filename, "video_url": f"/videos/{filename}"}
    if return_format == "path":
        return {"filename": filename, "video_path": str(output_path)}
    if return_format == "base64":
        with output_path.open("rb") as fh:
            encoded = base64.b64encode(fh.read()).decode("utf-8")
        return {"filename": filename, "video_base64": encoded}
    raise ValueError("Formato inválido. Use: url, base64 ou path.")


def process_video_job(job_id: str, payload: Dict[str, Any]) -> None:
    """
    Executa pipeline de edição de forma controlada. Atualiza o estado do job em cada fase.
    """
    repo = JobStateRepository()
    start_time = time.perf_counter()
    cleanup_ttl = get_env_float("JOB_CLEANUP_TTL_SECONDS", 3600.0)

    _ensure_directories()

    if payload.get("mode") == "clip_render":
        _process_clip_render_job(job_id, payload, repo)
        cleanup_directory(VIDEOS_DIR, cleanup_ttl)
        cleanup_directory(PROCESSED_DIR, cleanup_ttl)
        return

    repo.update_status(job_id, "analyzing", {"message": "Iniciando análise"})

    if not SESSION_FILE_PATH.exists():
        error_msg = "Arquivo de sessão de cookies não encontrado. Use /update-session primeiro."
        repo.set_error(job_id, error_msg)
        repo.update_status(job_id, "failed", {"message": error_msg})
        raise FileNotFoundError(error_msg)

    try:
        with processing_lock(timeout=5.0):
            repo.update_status(job_id, "analyzing", {"message": "Baixando vídeo"})
            video_path_str = baixar_reel(payload["url"], cookie_file_path=str(SESSION_FILE_PATH))
            if not video_path_str:
                raise RuntimeError("Falha ao baixar o vídeo. Sessão pode estar inválida.")

            video_path = Path(video_path_str)
            if not video_path.exists():
                raise FileNotFoundError(f"Vídeo baixado não encontrado: {video_path}")

            repo.update_status(
                job_id,
                "analyzing",
                {"message": "Vídeo baixado", "video_path": str(video_path)},
            )

            musica_path = _resolve_music_path(payload["music"])
            repo.update_status(
                job_id,
                "rendering",
                {
                    "message": "Renderizando vídeo",
                    "music_path": str(musica_path),
                },
            )

            filename = f"{video_path.stem}_{payload['music']}.mp4"
            output_path = PROCESSED_DIR / filename

            adicionar_musica(
                video_path=str(video_path),
                musica_path=str(musica_path),
                segundo_video=float(payload["impact_video"]),
                output_path=str(output_path),
                music_impact=float(payload["impact_music"]),
            )

            if not output_path.exists():
                raise RuntimeError("Renderização concluída sem gerar arquivo de saída.")

            result = _build_result(filename, output_path, payload.get("return_format", "url"))
            repo.set_result(job_id, result)
            repo.update_status(job_id, "done", {"message": "Processamento concluído"})

            duration = time.perf_counter() - start_time
            labels = {"mode": payload.get("mode", "edit"), "status": "done"}
            increment_counter(
                "video_jobs_total",
                labels=labels,
                help_text="Total de jobs de vídeo processados",
            )
            observe_histogram(
                "video_job_duration_seconds",
                duration,
                labels={"mode": payload.get("mode", "edit")},
                help_text="Duração dos jobs de vídeo",
            )

    except Exception as exc:  # noqa: BLE001
        repo.set_error(job_id, str(exc))
        repo.update_status(job_id, "failed", {"message": str(exc)})
        duration = time.perf_counter() - start_time
        increment_counter(
            "video_jobs_total",
            labels={"mode": payload.get("mode", "edit"), "status": "failed"},
            help_text="Total de jobs de vídeo processados",
        )
        observe_histogram(
            "video_job_duration_seconds",
            duration,
            labels={"mode": payload.get("mode", "edit")},
            help_text="Duração dos jobs de vídeo",
        )
        raise
    finally:
        cleanup_directory(VIDEOS_DIR, cleanup_ttl)
        cleanup_directory(PROCESSED_DIR, cleanup_ttl)


def _process_clip_render_job(job_id: str, payload: Dict[str, Any], repo: JobStateRepository) -> None:
    clip_ids: List[str] = payload.get("clip_ids") or []
    video_ingest_id: str | None = payload.get("video_ingest_id")
    if not clip_ids:
        raise ValueError("Nenhum clip_id informado para renderização.")

    start_time = time.perf_counter()
    with session_scope() as session:
        clips: List[VideoClipModel] = (
            session.query(VideoClipModel)
            .options(
                joinedload(VideoClipModel.video_ingest),
                joinedload(VideoClipModel.music_asset).joinedload(MusicAsset.audio_file),
            )
            .filter(VideoClipModel.id.in_(clip_ids))
            .order_by(VideoClipModel.option_order)
            .all()
        )

        if len(clips) != len(clip_ids):
            found_ids = {clip.id for clip in clips}
            missing = [clip_id for clip_id in clip_ids if clip_id not in found_ids]
            raise ValueError(f"Clipes não encontrados: {', '.join(missing)}")

        ingest_ids = {clip.video_ingest_id for clip in clips}
        if len(ingest_ids) > 1:
            raise ValueError("Todos os clipes devem pertencer ao mesmo vídeo.")
        ingest_id = ingest_ids.pop()
        if video_ingest_id and ingest_id != video_ingest_id:
            raise ValueError("Os clipes selecionados não pertencem ao vídeo solicitado.")

        ingest: VideoIngest | None = session.query(VideoIngest).filter(VideoIngest.id == ingest_id).first()
        if not ingest or not ingest.storage_path:
            raise ValueError("Vídeo original não encontrado para renderização.")

        video_path = Path(ingest.storage_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Arquivo do vídeo de ingest não encontrado: {video_path}")

        outputs: List[Dict[str, Any]] = []

        with processing_lock(timeout=5.0):
            repo.update_status(
                job_id,
                "rendering",
                {"message": "Iniciando renderização de variantes", "total": len(clips)},
            )

            for index, clip in enumerate(clips, start=1):
                repo.update_status(
                    job_id,
                    "rendering",
                    {
                        "message": "Renderizando variante",
                        "clip_id": clip.id,
                        "option_order": clip.option_order,
                        "current": index,
                        "total": len(clips),
                    },
                )

                if not clip.music_asset or not clip.music_asset.audio_file:
                    raise ValueError(f"Cl ipe {clip.id} não possui música associada para renderização.")

                audio_path = Path(clip.music_asset.audio_file.storage_path)
                if not audio_path.exists():
                    raise FileNotFoundError(f"Arquivo de música não encontrado: {audio_path}")

                segment = _first_segment(clip.video_segments)
                trim = None
                music_start = float(segment.get("music_start_seconds", 0.0)) if segment else 0.0
                if segment:
                    start = float(segment["video_start_seconds"])
                    end = float(segment["video_end_seconds"])
                    duration = max(0.1, end - start)
                    trim = {"start": start, "duration": duration}

                filename = f"{ingest.id}_{clip.option_order}_{clip.id[:8]}.mp4"
                output_path = PROCESSED_DIR / filename

                adicionar_musica(
                    video_path=str(video_path),
                    musica_path=str(audio_path),
                    segundo_video=0.0 if trim else float(segment.get("video_start_seconds", 0.0) if segment else 0.0),
                    output_path=str(output_path),
                    music_impact=music_start,
                    video_trim=trim,
                )

                if not output_path.exists():
                    raise RuntimeError(f"Falha ao gerar render final para o clipe {clip.id}.")

                outputs.append(
                    {
                        "clip_id": clip.id,
                        "filename": filename,
                        "video_url": f"/videos/{filename}",
                        "option_order": clip.option_order,
                    }
                )

        repo.set_result(job_id, {"outputs": outputs})
        repo.update_status(job_id, "done", {"message": "Renderização concluída", "count": len(outputs)})
        duration = time.perf_counter() - start_time
        mode_labels = {"mode": "clip_render", "status": "done"}
        increment_counter(
            "video_jobs_total",
            labels=mode_labels,
            help_text="Total de jobs de vídeo processados",
        )
        observe_histogram(
            "video_job_duration_seconds",
            duration,
            labels={"mode": "clip_render"},
            help_text="Duração dos jobs de vídeo",
        )


def _first_segment(segments: Any) -> Dict[str, Any] | None:
    if not segments:
        return None
    if isinstance(segments, list) and segments:
        segment = segments[0]
        if isinstance(segment, dict):
            return segment
    return None
