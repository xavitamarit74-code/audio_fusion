"""Core de procesamiento de audio (reutilizable por la API).

Mantiene la API del módulo original, pero vive en backend.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

from pydub import AudioSegment


def _configure_ffmpeg() -> None:
    """Configura ffmpeg/ffprobe para pydub.

    Prioridad:
    - binarios del sistema en PATH
    - fallback portable de imageio-ffmpeg
    """

    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")

    if ffmpeg and ffprobe:
        AudioSegment.converter = ffmpeg
        AudioSegment.ffprobe = ffprobe
        return

    try:
        import imageio_ffmpeg

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe:
            AudioSegment.converter = exe
            AudioSegment.ffprobe = exe
    except Exception:
        # Si no hay ffmpeg (ni sistema ni fallback), pydub fallará al exportar/importar.
        # Preferimos no romper el import; el error será más claro cuando se use.
        return


_configure_ffmpeg()


FORMATOS_SOPORTADOS = {
    ".mp3": "mp3",
    ".m4r": "m4a",
    ".m4a": "m4a",
    ".mp4": "mp4",
    ".wav": "wav",
    ".ogg": "ogg",
    ".flac": "flac",
    ".aac": "aac",
    ".mov": "mov",
}


def detectar_formato(filepath: str) -> str:
    """Detecta el formato basándose en la extensión."""
    extension = Path(filepath).suffix.lower()
    return FORMATOS_SOPORTADOS.get(extension, "mp3")


def cargar_audio(filepath: str) -> AudioSegment:
    """Carga un archivo de audio (o contenedor de vídeo con pista de audio)."""
    formato = detectar_formato(filepath)
    return AudioSegment.from_file(filepath, format=formato)


def normalizar_audio(audio: AudioSegment, target_dbfs: float = -14.0) -> AudioSegment:
    """Normaliza el volumen del audio a un nivel objetivo (dBFS)."""
    diferencia = target_dbfs - audio.dBFS
    return audio.apply_gain(diferencia)


def fusionar_dos_audios(
    audio1: AudioSegment,
    audio2: AudioSegment,
    crossfade_ms: int = 2000,
) -> tuple[AudioSegment, int]:
    """Fusiona dos segmentos de audio con crossfade."""
    max_crossfade = min(len(audio1), len(audio2), crossfade_ms)
    resultado = audio1.append(audio2, crossfade=max_crossfade)
    return resultado, max_crossfade


def _export_audio(resultado: AudioSegment, ruta_salida: str) -> None:
    """Exporta con parámetros razonables según formato."""
    formato_salida = detectar_formato(ruta_salida)
    export_params: dict = {}

    if formato_salida == "mp3":
        export_params = {"bitrate": "320k"}
    elif formato_salida in ["m4a", "m4r", "mp4", "aac"]:
        # En contenedores MP4/M4A, AAC es lo más compatible (iOS/Safari).
        export_params = {"codec": "aac", "bitrate": "256k"}

    Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
    resultado.export(ruta_salida, format=formato_salida, **export_params)


def fusionar_multiples_audios(
    rutas_audios: list[str],
    ruta_salida: str,
    crossfade_ms: int = 2000,
    fade_in_ms: int = 0,
    fade_out_ms: int = 0,
    normalizar: bool = False,
    volumenes: Optional[list[float]] = None,
) -> dict:
    if len(rutas_audios) < 2:
        return {"exito": False, "mensaje": "Se necesitan al menos 2 archivos de audio"}

    try:
        audios: list[AudioSegment] = []
        duraciones_originales: list[float] = []

        for i, ruta in enumerate(rutas_audios):
            audio = cargar_audio(ruta)
            duraciones_originales.append(len(audio) / 1000)

            if volumenes and i < len(volumenes) and volumenes[i] != 0:
                audio = audio.apply_gain(volumenes[i])

            audios.append(audio)

        resultado = audios[0]
        crossfades_aplicados: list[int] = []

        for i in range(1, len(audios)):
            resultado, crossfade_real = fusionar_dos_audios(resultado, audios[i], crossfade_ms)
            crossfades_aplicados.append(crossfade_real)

        if fade_in_ms > 0:
            resultado = resultado.fade_in(min(fade_in_ms, len(resultado)))
        if fade_out_ms > 0:
            resultado = resultado.fade_out(min(fade_out_ms, len(resultado)))

        if normalizar:
            resultado = normalizar_audio(resultado)

        _export_audio(resultado, ruta_salida)

        return {
            "exito": True,
            "num_archivos": len(rutas_audios),
            "duraciones_originales": duraciones_originales,
            "duracion_resultado": len(resultado) / 1000,
            "crossfades_aplicados": crossfades_aplicados,
            "ruta_salida": ruta_salida,
            "mensaje": f"¡Fusión de {len(rutas_audios)} archivos completada!",
        }

    except FileNotFoundError as e:
        return {"exito": False, "mensaje": f"Archivo no encontrado: {e}"}
    except Exception as e:
        return {"exito": False, "mensaje": f"Error al procesar: {str(e)}"}


def fusionar_audios(
    ruta_audio1: str,
    ruta_audio2: str,
    ruta_salida: str,
    crossfade_ms: int = 2000,
    fade_in_ms: int = 0,
    fade_out_ms: int = 0,
    normalizar: bool = False,
    volumen_audio1: float = 0.0,
    volumen_audio2: float = 0.0,
) -> dict:
    """Compatibilidad con la API anterior (fusiona 2 audios)."""
    resultado = fusionar_multiples_audios(
        rutas_audios=[ruta_audio1, ruta_audio2],
        ruta_salida=ruta_salida,
        crossfade_ms=crossfade_ms,
        fade_in_ms=fade_in_ms,
        fade_out_ms=fade_out_ms,
        normalizar=normalizar,
        volumenes=[volumen_audio1, volumen_audio2],
    )

    if resultado.get("exito"):
        resultado["duracion_audio1"] = resultado["duraciones_originales"][0]
        resultado["duracion_audio2"] = resultado["duraciones_originales"][1]
        resultado["crossfade_aplicado"] = (
            resultado["crossfades_aplicados"][0] if resultado["crossfades_aplicados"] else 0
        )
    return resultado


def fusionar_multiples_audios_con_progreso(
    rutas_audios: list[str],
    ruta_salida: str,
    crossfade_ms: int = 2000,
    fade_in_ms: int = 0,
    fade_out_ms: int = 0,
    normalizar: bool = False,
    volumenes: Optional[list[float]] = None,
):
    if len(rutas_audios) < 2:
        yield {"exito": False, "mensaje": "Se necesitan al menos 2 archivos de audio"}
        return

    try:
        yield {"tipo": "progreso", "progreso": 0, "etapa": "Iniciando"}

        audios: list[AudioSegment] = []
        duraciones_originales: list[float] = []
        total = len(rutas_audios)

        for i, ruta in enumerate(rutas_audios):
            nombre = Path(ruta).name
            yield {"tipo": "progreso", "progreso": int((i / total) * 40), "etapa": f"Cargando {nombre}"}
            audio = cargar_audio(ruta)
            duraciones_originales.append(len(audio) / 1000)

            if volumenes and i < len(volumenes) and volumenes[i] != 0:
                audio = audio.apply_gain(volumenes[i])

            audios.append(audio)
            yield {"tipo": "progreso", "progreso": int(((i + 1) / total) * 40), "etapa": f"Cargado {i + 1}/{total}"}

        resultado = audios[0]
        crossfades_aplicados: list[int] = []
        pasos_fusion = max(1, total - 1)

        for paso, idx in enumerate(range(1, total), start=1):
            yield {"tipo": "progreso", "progreso": 40 + int(((paso - 1) / pasos_fusion) * 40), "etapa": f"Fusionando {paso}/{pasos_fusion}"}
            resultado, crossfade_real = fusionar_dos_audios(resultado, audios[idx], crossfade_ms)
            crossfades_aplicados.append(crossfade_real)

        yield {"tipo": "progreso", "progreso": 82, "etapa": "Aplicando fades"}
        if fade_in_ms > 0:
            resultado = resultado.fade_in(min(fade_in_ms, len(resultado)))
        if fade_out_ms > 0:
            resultado = resultado.fade_out(min(fade_out_ms, len(resultado)))

        if normalizar:
            yield {"tipo": "progreso", "progreso": 86, "etapa": "Normalizando"}
            resultado = normalizar_audio(resultado)

        yield {"tipo": "progreso", "progreso": 90, "etapa": "Exportando"}
        _export_audio(resultado, ruta_salida)

        yield {"tipo": "progreso", "progreso": 100, "etapa": "Completado"}
        yield {
            "exito": True,
            "num_archivos": len(rutas_audios),
            "duraciones_originales": duraciones_originales,
            "duracion_resultado": len(resultado) / 1000,
            "crossfades_aplicados": crossfades_aplicados,
            "ruta_salida": ruta_salida,
            "mensaje": f"¡Fusión de {len(rutas_audios)} archivos completada!",
        }

    except FileNotFoundError as e:
        yield {"exito": False, "mensaje": f"Archivo no encontrado: {e}"}
    except Exception as e:
        yield {"exito": False, "mensaje": f"Error al procesar: {str(e)}"}


def obtener_info_audio(ruta: str) -> Optional[dict]:
    try:
        audio = cargar_audio(ruta)
        return {
            "duracion": len(audio) / 1000,
            "canales": audio.channels,
            "sample_rate": audio.frame_rate,
            "formato": detectar_formato(ruta),
        }
    except Exception:
        return None


def crear_preview(
    rutas_audios: list[str],
    ruta_salida: str,
    crossfade_ms: int = 2000,
    fade_in_ms: int = 0,
    fade_out_ms: int = 0,
    normalizar: bool = False,
    volumenes: Optional[list[float]] = None,
    max_duracion_ms: int = 30000,
) -> dict:
    if len(rutas_audios) < 2:
        return {"exito": False, "mensaje": "Se necesitan al menos 2 archivos de audio"}

    try:
        num_audios = len(rutas_audios)
        tiempo_crossfades = crossfade_ms * (num_audios - 1)
        tiempo_disponible = max_duracion_ms + tiempo_crossfades
        tiempo_por_audio = tiempo_disponible // num_audios

        audios: list[AudioSegment] = []
        duraciones_preview: list[float] = []

        for i, ruta in enumerate(rutas_audios):
            audio = cargar_audio(ruta)

            if len(audio) > tiempo_por_audio:
                if i == 0:
                    inicio = max(0, len(audio) - tiempo_por_audio)
                    audio = audio[inicio:]
                elif i == num_audios - 1:
                    audio = audio[:tiempo_por_audio]
                else:
                    centro = len(audio) // 2
                    inicio = max(0, centro - tiempo_por_audio // 2)
                    audio = audio[inicio : inicio + tiempo_por_audio]

            duraciones_preview.append(len(audio) / 1000)

            if volumenes and i < len(volumenes) and volumenes[i] != 0:
                audio = audio.apply_gain(volumenes[i])

            audios.append(audio)

        resultado = audios[0]
        for i in range(1, len(audios)):
            max_crossfade = min(len(resultado), len(audios[i]), crossfade_ms)
            resultado = resultado.append(audios[i], crossfade=max_crossfade)

        if fade_in_ms > 0:
            resultado = resultado.fade_in(min(fade_in_ms, len(resultado)))
        if fade_out_ms > 0:
            resultado = resultado.fade_out(min(fade_out_ms, len(resultado)))

        if normalizar:
            resultado = normalizar_audio(resultado)

        if len(resultado) > max_duracion_ms:
            resultado = resultado[:max_duracion_ms]
            resultado = resultado.fade_out(500)

        Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
        # Preview siempre MP3 128k (compatibilidad iOS/Safari)
        resultado.export(ruta_salida, format="mp3", bitrate="128k")

        return {
            "exito": True,
            "duracion_preview": len(resultado) / 1000,
            "duraciones_segmentos": duraciones_preview,
            "ruta_salida": ruta_salida,
            "mensaje": "Preview generada correctamente",
        }

    except Exception as e:
        return {"exito": False, "mensaje": f"Error al crear preview: {str(e)}"}


def crear_preview_con_progreso(
    rutas_audios: list[str],
    ruta_salida: str,
    crossfade_ms: int = 2000,
    fade_in_ms: int = 0,
    fade_out_ms: int = 0,
    normalizar: bool = False,
    volumenes: Optional[list[float]] = None,
    max_duracion_ms: int = 30000,
):
    if len(rutas_audios) < 2:
        yield {"exito": False, "mensaje": "Se necesitan al menos 2 archivos de audio"}
        return

    try:
        yield {"tipo": "progreso", "progreso": 0, "etapa": "Iniciando"}

        num_audios = len(rutas_audios)
        tiempo_crossfades = crossfade_ms * (num_audios - 1)
        tiempo_disponible = max_duracion_ms + tiempo_crossfades
        tiempo_por_audio = tiempo_disponible // num_audios

        audios: list[AudioSegment] = []
        duraciones_preview: list[float] = []

        for i, ruta in enumerate(rutas_audios):
            nombre = Path(ruta).name
            yield {"tipo": "progreso", "progreso": int((i / num_audios) * 60), "etapa": f"Preparando {nombre}"}
            audio = cargar_audio(ruta)

            if len(audio) > tiempo_por_audio:
                if i == 0:
                    inicio = max(0, len(audio) - tiempo_por_audio)
                    audio = audio[inicio:]
                elif i == num_audios - 1:
                    audio = audio[:tiempo_por_audio]
                else:
                    centro = len(audio) // 2
                    inicio = max(0, centro - tiempo_por_audio // 2)
                    audio = audio[inicio : inicio + tiempo_por_audio]

            duraciones_preview.append(len(audio) / 1000)

            if volumenes and i < len(volumenes) and volumenes[i] != 0:
                audio = audio.apply_gain(volumenes[i])

            audios.append(audio)
            yield {"tipo": "progreso", "progreso": int(((i + 1) / num_audios) * 60), "etapa": f"Segmentos listos {i + 1}/{num_audios}"}

        resultado = audios[0]
        pasos = max(1, num_audios - 1)
        for paso, idx in enumerate(range(1, len(audios)), start=1):
            yield {"tipo": "progreso", "progreso": 60 + int(((paso - 1) / pasos) * 20), "etapa": f"Fusionando {paso}/{pasos}"}
            max_crossfade = min(len(resultado), len(audios[idx]), crossfade_ms)
            resultado = resultado.append(audios[idx], crossfade=max_crossfade)

        yield {"tipo": "progreso", "progreso": 82, "etapa": "Aplicando efectos"}
        if fade_in_ms > 0:
            resultado = resultado.fade_in(min(fade_in_ms, len(resultado)))
        if fade_out_ms > 0:
            resultado = resultado.fade_out(min(fade_out_ms, len(resultado)))
        if normalizar:
            yield {"tipo": "progreso", "progreso": 86, "etapa": "Normalizando"}
            resultado = normalizar_audio(resultado)

        if len(resultado) > max_duracion_ms:
            resultado = resultado[:max_duracion_ms]
            resultado = resultado.fade_out(500)

        yield {"tipo": "progreso", "progreso": 90, "etapa": "Exportando"}
        Path(ruta_salida).parent.mkdir(parents=True, exist_ok=True)
        resultado.export(ruta_salida, format="mp3", bitrate="128k")

        yield {"tipo": "progreso", "progreso": 100, "etapa": "Completado"}
        yield {
            "exito": True,
            "duracion_preview": len(resultado) / 1000,
            "duraciones_segmentos": duraciones_preview,
            "ruta_salida": ruta_salida,
            "mensaje": "Preview generada correctamente",
        }

    except Exception as e:
        yield {"exito": False, "mensaje": f"Error al crear preview: {str(e)}"}
