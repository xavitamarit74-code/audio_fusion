from __future__ import annotations

import os
import shutil
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .audio_processor import (
    crear_preview_con_progreso,
    fusionar_multiples_audios_con_progreso,
    obtener_info_audio,
)

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
FRONTEND_BUILD_DIR = FRONTEND_DIR / "build"
STORAGE_DIR = Path(__file__).resolve().parent / "storage"
FILES_DIR = STORAGE_DIR / "files"
JOBS_DIR = STORAGE_DIR / "jobs"

FILES_DIR.mkdir(parents=True, exist_ok=True)
JOBS_DIR.mkdir(parents=True, exist_ok=True)


JobState = Literal["queued", "running", "done", "error"]
JobKind = Literal["preview", "merge"]


@dataclass
class Job:
    id: str
    kind: JobKind
    epoch: int = 0
    state: JobState = "queued"
    progress: int = 0
    stage: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    result_path: str | None = None
    result_filename: str | None = None
    result_content_type: str | None = None
    error: str | None = None


_JOBS: dict[str, Job] = {}
_LOCK = threading.Lock()
_RESET_EPOCH = 0


def _now() -> float:
    return time.time()


def _current_epoch() -> int:
    with _LOCK:
        return _RESET_EPOCH


def _set_job(job: Job) -> None:
    with _LOCK:
        # Si se ha hecho reset fuerte, ignoramos actualizaciones de jobs antiguos.
        if job.epoch != _RESET_EPOCH:
            return
        _JOBS[job.id] = job


def _get_job(job_id: str) -> Job:
    with _LOCK:
        job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return job


def _guess_content_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return {
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".m4r": "audio/mp4",
        ".mp4": "audio/mp4",
        ".wav": "audio/wav",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".aac": "audio/aac",
    }.get(ext, "application/octet-stream")


_ALLOWED_OUTPUT_FORMATS = {"mp3", "m4a", "m4r", "mp4", "flac", "ogg", "wav", "aac"}


def _normalize_output_format(value: Any) -> str:
    # Acepta: "mp3", ".mp3", " audio_fusion.mp3 ", etc.
    if value is None:
        return "mp3"
    s = str(value).strip().lower()
    if "." in s:
        s = s.split(".")[-1]
    s = s.lstrip(".").strip()
    return s or "mp3"


def _job_dir(epoch: int, job_id: str) -> Path:
    d = JOBS_DIR / str(epoch) / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _file_path(file_id: str) -> Path:
    # Guardamos por id + extensión al subir; buscamos el primer match.
    direct = FILES_DIR / file_id
    if direct.exists():
        return direct

    matches = sorted(FILES_DIR.glob(f"{file_id}.*"))
    if not matches:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    return matches[0]


def _run_preview_job(job_id: str, file_ids: list[str], params: dict[str, Any]) -> None:
    try:
        job = _get_job(job_id)
    except HTTPException:
        return

    job_epoch = job.epoch
    job.state = "running"
    job.created_at = job.created_at or _now()
    job.updated_at = _now()
    _set_job(job)

    rutas = [str(_file_path(fid)) for fid in file_ids]
    out_dir = _job_dir(job_epoch, job_id)
    out_path = out_dir / "preview.mp3"  # siempre mp3 por compatibilidad

    try:
        for evento in crear_preview_con_progreso(
            rutas_audios=rutas,
            ruta_salida=str(out_path),
            crossfade_ms=int(params.get("crossfade_ms", 2000)),
            fade_in_ms=int(params.get("fade_in_ms", 0)),
            fade_out_ms=int(params.get("fade_out_ms", 0)),
            normalizar=bool(params.get("normalizar", False)),
            volumenes=params.get("volumenes", None),
        ):
            if _current_epoch() != job_epoch:
                return
            if evento.get("tipo") == "progreso":
                job.progress = int(evento.get("progreso", 0))
                job.stage = str(evento.get("etapa", ""))
                job.updated_at = _now()
                _set_job(job)
            else:
                if not evento.get("exito"):
                    raise RuntimeError(str(evento.get("mensaje", "Error")))

        job.state = "done"
        job.progress = 100
        job.stage = "Completado"
        job.result_path = str(out_path)
        job.result_filename = "preview.mp3"
        job.result_content_type = "audio/mpeg"
        job.updated_at = _now()
        _set_job(job)

    except Exception as e:
        if _current_epoch() != job_epoch:
            return
        job.state = "error"
        job.error = str(e)
        job.updated_at = _now()
        _set_job(job)


def _run_merge_job(job_id: str, file_ids: list[str], params: dict[str, Any], output_format: str) -> None:
    try:
        job = _get_job(job_id)
    except HTTPException:
        return

    job_epoch = job.epoch
    job.state = "running"
    job.created_at = job.created_at or _now()
    job.updated_at = _now()
    _set_job(job)

    rutas = [str(_file_path(fid)) for fid in file_ids]
    out_dir = _job_dir(job_epoch, job_id)
    ext = _normalize_output_format(output_format)
    filename = f"audio_fusion.{ext}"
    out_path = out_dir / filename

    try:
        for evento in fusionar_multiples_audios_con_progreso(
            rutas_audios=rutas,
            ruta_salida=str(out_path),
            crossfade_ms=int(params.get("crossfade_ms", 2000)),
            fade_in_ms=int(params.get("fade_in_ms", 0)),
            fade_out_ms=int(params.get("fade_out_ms", 0)),
            normalizar=bool(params.get("normalizar", False)),
            volumenes=params.get("volumenes", None),
        ):
            if _current_epoch() != job_epoch:
                return
            if evento.get("tipo") == "progreso":
                job.progress = int(evento.get("progreso", 0))
                job.stage = str(evento.get("etapa", ""))
                job.updated_at = _now()
                _set_job(job)
            else:
                if not evento.get("exito"):
                    raise RuntimeError(str(evento.get("mensaje", "Error")))

        job.state = "done"
        job.progress = 100
        job.stage = "Completado"
        job.result_path = str(out_path)
        job.result_filename = filename
        job.result_content_type = _guess_content_type(filename)
        job.updated_at = _now()
        _set_job(job)

    except Exception as e:
        if _current_epoch() != job_epoch:
            return
        job.state = "error"
        job.error = str(e)
        job.updated_at = _now()
        _set_job(job)


app = FastAPI(title="Audio Fusion API", version="1.0")

# CORS: en dev permitimos localhost; en prod, fija el dominio del frontend.
_ENABLE_CORS = os.environ.get("ENABLE_CORS", "").strip().lower() in {"1", "true", "yes", "on"}

if _ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )


@app.get("/favicon.ico")
async def favicon():
    for ico in (FRONTEND_BUILD_DIR / "favicon.ico", FRONTEND_DIR / "favicon.ico"):
        if ico.exists():
            return FileResponse(str(ico), media_type="image/x-icon")
    return Response(status_code=204)


@app.post("/v1/uploads")
async def upload(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No se han enviado archivos")
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Máximo 10 archivos")

    uploaded: list[dict[str, Any]] = []

    for f in files:
        ext = Path(f.filename).suffix.lower()
        file_id = uuid.uuid4().hex[:10]
        dest = FILES_DIR / f"{file_id}{ext}"

        with dest.open("wb") as out:
            while True:
                chunk = await f.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)

        info = obtener_info_audio(str(dest))
        if not info:
            dest.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=f"No se pudo leer el audio: {f.filename}")

        uploaded.append(
            {
                "file_id": file_id,
                "filename": f.filename,
                "duration": info["duracion"],
                "format": info["formato"],
            }
        )

    return {"files": uploaded}


@app.post("/v1/previews")
async def create_preview(payload: dict[str, Any], background: BackgroundTasks):
    file_ids = payload.get("file_ids")
    params = payload.get("params", {})

    if not isinstance(file_ids, list) or len(file_ids) < 2:
        raise HTTPException(status_code=400, detail="Necesitas al menos 2 archivos")

    epoch = _current_epoch()
    job_id = uuid.uuid4().hex
    job = Job(id=job_id, kind="preview", epoch=epoch, created_at=_now(), updated_at=_now(), stage="En cola")
    _set_job(job)

    background.add_task(_run_preview_job, job_id, file_ids, params)

    return {
        "job_id": job_id,
        "status_url": f"/v1/jobs/{job_id}",
        "preview_url": f"/v1/jobs/{job_id}/preview",
    }


@app.post("/v1/merges")
async def create_merge(payload: dict[str, Any], background: BackgroundTasks):
    file_ids = payload.get("file_ids")
    params = payload.get("params", {})
    output = payload.get("output", {})
    output_format = _normalize_output_format(output.get("format", "mp3"))

    if output_format not in _ALLOWED_OUTPUT_FORMATS:
        raise HTTPException(status_code=400, detail="Formato de salida no soportado")

    if not isinstance(file_ids, list) or len(file_ids) < 2:
        raise HTTPException(status_code=400, detail="Necesitas al menos 2 archivos")

    epoch = _current_epoch()
    job_id = uuid.uuid4().hex
    job = Job(id=job_id, kind="merge", epoch=epoch, created_at=_now(), updated_at=_now(), stage="En cola")
    _set_job(job)

    background.add_task(_run_merge_job, job_id, file_ids, params, output_format)

    return {
        "job_id": job_id,
        "status_url": f"/v1/jobs/{job_id}",
        "download_url": f"/v1/jobs/{job_id}/download",
    }


@app.get("/v1/jobs/{job_id}")
async def job_status(job_id: str):
    job = _get_job(job_id)
    return {
        "job_id": job.id,
        "kind": job.kind,
        "state": job.state,
        "progress": job.progress,
        "stage": job.stage,
        "result": {
            "filename": job.result_filename,
            "content_type": job.result_content_type,
            "url": (
                f"/v1/jobs/{job_id}/preview"
                if job.kind == "preview"
                else f"/v1/jobs/{job_id}/download"
            )
            if job.state == "done"
            else None,
        },
        "error": job.error,
    }


@app.get("/v1/jobs/{job_id}/preview")
async def job_preview(job_id: str):
    job = _get_job(job_id)
    if job.kind != "preview":
        raise HTTPException(status_code=400, detail="Job no es de preview")
    if job.state != "done" or not job.result_path:
        raise HTTPException(status_code=404, detail="Preview no disponible")

    return FileResponse(
        job.result_path,
        media_type=job.result_content_type or "audio/mpeg",
        filename=job.result_filename or "preview.mp3",
    )


@app.get("/v1/jobs/{job_id}/download")
async def job_download(job_id: str):
    job = _get_job(job_id)
    if job.kind != "merge":
        raise HTTPException(status_code=400, detail="Job no es de merge")
    if job.state != "done" or not job.result_path:
        raise HTTPException(status_code=404, detail="Resultado no disponible")

    return FileResponse(
        job.result_path,
        media_type=job.result_content_type or "application/octet-stream",
        filename=job.result_filename or "audio_fusion",
    )


@app.post("/v1/cleanup")
async def cleanup():
    """Limpieza simple de jobs antiguos (MVP)."""
    ttl_seconds = 6 * 3600
    now = _now()

    removed = 0
    with _LOCK:
        job_ids = list(_JOBS.keys())

    for job_id in job_ids:
        job = _get_job(job_id)
        if now - job.updated_at > ttl_seconds:
            with _LOCK:
                _JOBS.pop(job_id, None)
            shutil.rmtree(_job_dir(job.epoch, job_id), ignore_errors=True)
            removed += 1

    return {"removed": removed}


@app.post("/v1/reset")
async def reset(payload: dict[str, Any] | None = None):
    """Resetea el estado del servidor.

    - mode=soft: borra uploads/resultados y limpia jobs en memoria.
    - mode=hard: lo mismo + incrementa epoch para que jobs en curso no reescriban estado tras el reset.
    """

    mode = "soft"
    if isinstance(payload, dict) and payload.get("mode") is not None:
        mode = str(payload.get("mode") or "soft").lower().strip()

    if mode not in {"soft", "hard"}:
        raise HTTPException(status_code=400, detail="mode debe ser soft o hard")

    # Marcar reset (hard) y vaciar jobs de memoria de forma atómica.
    global _RESET_EPOCH
    with _LOCK:
        if mode == "hard":
            _RESET_EPOCH += 1
        _JOBS.clear()

    # Borrar storage en disco (best-effort). Los workers antiguos podrían recrear carpetas,
    # pero sus updates quedarán ignorados en memoria tras un hard reset.
    shutil.rmtree(FILES_DIR, ignore_errors=True)
    shutil.rmtree(JOBS_DIR, ignore_errors=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    JOBS_DIR.mkdir(parents=True, exist_ok=True)

    return {"ok": True, "mode": mode}


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("backend.app:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    main()


# Servir frontend estático (dev/prod simple)
# Debe ir al final para no interceptar rutas de la API (/v1/*).
if FRONTEND_BUILD_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_BUILD_DIR), html=True), name="frontend")
