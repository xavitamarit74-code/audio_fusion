"""
Tests para el módulo de procesamiento de audio.
"""

import pytest
from pathlib import Path
import sys
import shutil
import subprocess

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.audio_processor import (
    detectar_formato,
    cargar_audio,
    normalizar_audio,
    fusionar_audios,
    fusionar_multiples_audios,
    crear_preview,
    obtener_info_audio,
    FORMATOS_SOPORTADOS,
)


def _ffmpeg_available() -> bool:
    """Devuelve True si hay un ffmpeg ejecutable disponible."""
    try:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            try:
                import imageio_ffmpeg

                ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                ffmpeg = None

        if not ffmpeg:
            return False

        proc = subprocess.run(
            [ffmpeg, "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
        return proc.returncode == 0
    except Exception:
        return False


class TestDetectarFormato:
    """Tests para la función detectar_formato."""
    
    def test_detectar_mp3(self):
        """Debe detectar correctamente archivos MP3."""
        assert detectar_formato("audio.mp3") == "mp3"
        assert detectar_formato("audio.MP3") == "mp3"
        assert detectar_formato("/ruta/completa/audio.mp3") == "mp3"
    
    def test_detectar_m4r(self):
        """Debe detectar M4R como M4A (son el mismo formato)."""
        assert detectar_formato("tono.m4r") == "m4a"
        assert detectar_formato("tono.M4R") == "m4a"
    
    def test_detectar_m4a(self):
        """Debe detectar correctamente archivos M4A."""
        assert detectar_formato("audio.m4a") == "m4a"
    
    def test_detectar_wav(self):
        """Debe detectar correctamente archivos WAV."""
        assert detectar_formato("audio.wav") == "wav"
    
    def test_detectar_ogg(self):
        """Debe detectar correctamente archivos OGG."""
        assert detectar_formato("audio.ogg") == "ogg"
    
    def test_detectar_flac(self):
        """Debe detectar correctamente archivos FLAC."""
        assert detectar_formato("audio.flac") == "flac"
    
    def test_formato_desconocido_default_mp3(self):
        """Debe devolver MP3 como formato por defecto para extensiones desconocidas."""
        assert detectar_formato("audio.xyz") == "mp3"
        assert detectar_formato("audio.unknown") == "mp3"
    
    def test_formatos_soportados_completos(self):
        """Verifica que todos los formatos esperados están soportados."""
        formatos_esperados = ['.mp3', '.m4r', '.m4a', '.wav', '.ogg', '.flac', '.aac']
        for formato in formatos_esperados:
            assert formato in FORMATOS_SOPORTADOS


class TestCargarAudio:
    """Tests para la función cargar_audio."""
    
    def test_cargar_audio_mp3(self, sample_audio_files):
        """Debe cargar correctamente un archivo MP3."""
        audio = cargar_audio(sample_audio_files["audio1"])
        assert audio is not None
        assert len(audio) > 0  # Tiene duración
    
    def test_cargar_audio_duracion_correcta(self, sample_audio_files):
        """El audio cargado debe tener la duración esperada (~3 segundos)."""
        audio = cargar_audio(sample_audio_files["audio1"])
        duracion_segundos = len(audio) / 1000
        assert 2.9 <= duracion_segundos <= 3.1
    
    def test_cargar_archivo_inexistente(self):
        """Debe lanzar excepción para archivos que no existen."""
        with pytest.raises(Exception):
            cargar_audio("/ruta/inexistente/audio.mp3")


class TestNormalizarAudio:
    """Tests para la función normalizar_audio."""
    
    def test_normalizar_audio(self, sample_audio_files):
        """Debe normalizar el audio al nivel objetivo."""
        audio = cargar_audio(sample_audio_files["audio1"])
        normalizado = normalizar_audio(audio, target_dbfs=-14.0)
        
        # El volumen debe estar cerca del objetivo
        assert -15.0 <= normalizado.dBFS <= -13.0
    
    def test_normalizar_diferentes_niveles(self, sample_audio_files):
        """Debe normalizar a diferentes niveles objetivo."""
        audio = cargar_audio(sample_audio_files["audio1"])
        
        normalizado_alto = normalizar_audio(audio, target_dbfs=-10.0)
        normalizado_bajo = normalizar_audio(audio, target_dbfs=-20.0)
        
        assert normalizado_alto.dBFS > normalizado_bajo.dBFS


class TestObtenerInfoAudio:
    """Tests para la función obtener_info_audio."""
    
    def test_obtener_info_audio(self, sample_audio_files):
        """Debe obtener información correcta del audio."""
        info = obtener_info_audio(sample_audio_files["audio1"])
        
        assert info is not None
        assert "duracion" in info
        assert "canales" in info
        assert "sample_rate" in info
        assert "formato" in info
    
    def test_info_duracion_correcta(self, sample_audio_files):
        """La duración reportada debe ser correcta."""
        info = obtener_info_audio(sample_audio_files["audio1"])
        assert 2.9 <= info["duracion"] <= 3.1
    
    def test_info_formato_correcto(self, sample_audio_files):
        """El formato reportado debe ser correcto."""
        info = obtener_info_audio(sample_audio_files["audio1"])
        assert info["formato"] == "mp3"
    
    def test_info_archivo_inexistente(self):
        """Debe devolver None para archivos inexistentes."""
        info = obtener_info_audio("/ruta/inexistente/audio.mp3")
        assert info is None


class TestFusionarAudios:
    """Tests para la función fusionar_audios."""
    
    def test_fusion_basica(self, sample_audio_files, output_path):
        """Debe fusionar dos audios correctamente."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=1000,
        )
        
        assert resultado["exito"] is True
        assert Path(output_path).exists()
        assert resultado["duracion_resultado"] > 0
    
    def test_fusion_sin_crossfade(self, sample_audio_files, output_path):
        """Debe fusionar sin crossfade (concatenar)."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=0,
        )
        
        assert resultado["exito"] is True
        # Sin crossfade, la duración debe ser aproximadamente la suma
        duracion_esperada = resultado["duracion_audio1"] + resultado["duracion_audio2"]
        assert abs(resultado["duracion_resultado"] - duracion_esperada) < 0.2
    
    def test_fusion_con_crossfade(self, sample_audio_files, output_path):
        """Con crossfade, la duración debe ser menor que la suma."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=2000,
        )
        
        assert resultado["exito"] is True
        duracion_sin_crossfade = resultado["duracion_audio1"] + resultado["duracion_audio2"]
        # Con 2 segundos de crossfade, debe ser ~2 segundos menor
        assert resultado["duracion_resultado"] < duracion_sin_crossfade
    
    def test_fusion_con_fade_in(self, sample_audio_files, output_path):
        """Debe aplicar fade-in correctamente."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=500,
            fade_in_ms=1000,
        )
        
        assert resultado["exito"] is True
        assert Path(output_path).exists()
    
    def test_fusion_con_fade_out(self, sample_audio_files, output_path):
        """Debe aplicar fade-out correctamente."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=500,
            fade_out_ms=1000,
        )
        
        assert resultado["exito"] is True
        assert Path(output_path).exists()
    
    def test_fusion_con_fade_in_y_out(self, sample_audio_files, output_path):
        """Debe aplicar fade-in y fade-out juntos."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=500,
            fade_in_ms=500,
            fade_out_ms=500,
        )
        
        assert resultado["exito"] is True
    
    def test_fusion_con_normalizacion(self, sample_audio_files, output_path):
        """Debe normalizar el audio resultante."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=500,
            normalizar=True,
        )
        
        assert resultado["exito"] is True
        assert Path(output_path).exists()
    
    def test_fusion_ajuste_volumen_audio1(self, sample_audio_files, output_path):
        """Debe ajustar el volumen del primer audio."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=500,
            volumen_audio1=-6.0,  # Reducir 6 dB
        )
        
        assert resultado["exito"] is True
    
    def test_fusion_ajuste_volumen_audio2(self, sample_audio_files, output_path):
        """Debe ajustar el volumen del segundo audio."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=500,
            volumen_audio2=6.0,  # Aumentar 6 dB
        )
        
        assert resultado["exito"] is True
    
    def test_fusion_todos_los_parametros(self, sample_audio_files, output_path):
        """Debe funcionar con todos los parámetros activados."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=1000,
            fade_in_ms=500,
            fade_out_ms=500,
            normalizar=True,
            volumen_audio1=-3.0,
            volumen_audio2=3.0,
        )
        
        assert resultado["exito"] is True
        assert Path(output_path).exists()
        assert resultado["duracion_resultado"] > 0
    
    def test_fusion_archivo_inexistente(self, sample_audio_files, output_path):
        """Debe manejar archivos inexistentes correctamente."""
        resultado = fusionar_audios(
            ruta_audio1="/ruta/inexistente/audio.mp3",
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=1000,
        )
        
        assert resultado["exito"] is False
        assert "mensaje" in resultado


class TestFusionarAudiosFormatos:
    """Tests para fusión con diferentes formatos de salida."""
    
    def test_fusion_salida_mp3(self, sample_audio_files, temp_dir):
        """Debe exportar correctamente a MP3."""
        output = str(temp_dir / "output.mp3")
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output,
            crossfade_ms=500,
        )
        
        assert resultado["exito"] is True
        assert Path(output).exists()
        assert Path(output).suffix == ".mp3"
    
    def test_fusion_salida_wav(self, sample_audio_files, temp_dir):
        """Debe exportar correctamente a WAV."""
        output = str(temp_dir / "output.wav")
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output,
            crossfade_ms=500,
        )
        
        assert resultado["exito"] is True
        assert Path(output).exists()
        assert Path(output).suffix == ".wav"
    
    def test_fusion_salida_ogg(self, sample_audio_files, temp_dir):
        """Debe exportar correctamente a OGG."""
        output = str(temp_dir / "output.ogg")
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output,
            crossfade_ms=500,
        )
        
        assert resultado["exito"] is True
        assert Path(output).exists()


class TestExportFormatosMp4Family:
    """Tests para exportar formatos que antes fallaban (m4a/m4r/mp4)."""

    @pytest.mark.parametrize("ext", ["m4a", "m4r", "mp4"])
    def test_export_y_recarga(self, sample_audio_files, temp_dir, ext):
        if not _ffmpeg_available():
            pytest.skip("ffmpeg no disponible; export m4a/m4r/mp4 se omite")

        output = str(temp_dir / f"output.{ext}")
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output,
            crossfade_ms=500,
        )

        assert resultado["exito"] is True
        assert Path(output).exists()
        assert Path(output).stat().st_size > 0

        recargado = cargar_audio(output)
        assert recargado is not None
        assert len(recargado) > 0


class TestExportMuxerMap:
    """Tests unitarios del mapeo extensión->muxer sin invocar ffmpeg."""

    @pytest.mark.parametrize(
        "ruta_salida,expected_format",
        [
            ("/tmp/out.m4a", "ipod"),
            ("/tmp/out.m4r", "ipod"),
            ("/tmp/out.mp4", "mp4"),
        ],
    )
    def test__export_audio_no_usa_m4a_como_muxer(self, monkeypatch, temp_dir, ruta_salida, expected_format):
        from pydub import AudioSegment
        from backend import audio_processor

        called = {"format": None, "kwargs": None, "out": None}

        def fake_export(self, out_f, format=None, **kwargs):
            called["format"] = format
            called["kwargs"] = kwargs
            called["out"] = out_f
            # Crear un archivo dummy para no depender de ffmpeg
            out_path = Path(out_f)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(b"dummy")
            return None

        monkeypatch.setattr(AudioSegment, "export", fake_export, raising=True)

        salida_real = str(temp_dir / Path(ruta_salida).name)
        audio_processor._export_audio(AudioSegment.silent(duration=500), salida_real)

        assert called["format"] == expected_format
        assert called["format"] != "m4a"


class TestCargarMediosRealesOpcional:
    """Tests opcionales: usan archivos en pruebas/ si existen (repo ligero)."""

    def test_cargar_m4a_real_si_existe(self, project_root):
        ruta = project_root / "pruebas" / "mis-gaviotas_Episodio_01.m4a"
        if not ruta.exists():
            pytest.skip("No existe pruebas/mis-gaviotas_Episodio_01.m4a")
        if not _ffmpeg_available():
            pytest.skip("ffmpeg no disponible")

        audio = cargar_audio(str(ruta))
        assert audio is not None
        assert len(audio) > 0

    def test_cargar_mp4_real_si_existe(self, project_root):
        ruta = project_root / "pruebas" / "VIDEO-2026-01-03-17-36-54.mp4"
        if not ruta.exists():
            pytest.skip("No existe pruebas/VIDEO-2026-01-03-17-36-54.mp4")
        if not _ffmpeg_available():
            pytest.skip("ffmpeg no disponible")

        audio = cargar_audio(str(ruta))
        assert audio is not None
        assert len(audio) > 0

    def test_cargar_mov_real_si_existe(self, project_root):
        ruta = project_root / "pruebas" / "copy_B7D6413A-3E0C-40EA-A165-75736A6B9AE9.mov"
        if not ruta.exists():
            pytest.skip("No existe pruebas/copy_....mov")
        if not _ffmpeg_available():
            pytest.skip("ffmpeg no disponible")

        audio = cargar_audio(str(ruta))
        assert audio is not None
        assert len(audio) > 0


class TestFusionarAudiosEdgeCases:
    """Tests para casos límite."""
    
    def test_crossfade_mayor_que_audio(self, short_audio_files, temp_dir):
        """El crossfade debe ajustarse si es mayor que los audios."""
        output = str(temp_dir / "output_short.mp3")
        resultado = fusionar_audios(
            ruta_audio1=short_audio_files["audio1"],
            ruta_audio2=short_audio_files["audio2"],
            ruta_salida=output,
            crossfade_ms=10000,  # 10 segundos, más que los audios
        )
        
        assert resultado["exito"] is True
        # El crossfade se debe haber ajustado
        assert resultado["crossfade_aplicado"] <= 500
    
    def test_fade_in_mayor_que_resultado(self, short_audio_files, temp_dir):
        """El fade-in debe manejarse aunque sea muy largo."""
        output = str(temp_dir / "output_fade.mp3")
        resultado = fusionar_audios(
            ruta_audio1=short_audio_files["audio1"],
            ruta_audio2=short_audio_files["audio2"],
            ruta_salida=output,
            crossfade_ms=100,
            fade_in_ms=10000,  # Más largo que el audio resultante
        )
        
        assert resultado["exito"] is True


class TestFusionarMultiplesAudios:
    """Tests para la fusión de múltiples archivos."""
    
    def test_fusion_tres_archivos(self, sample_audio_files, temp_dir):
        """Debe fusionar correctamente 3 archivos."""
        # Crear un tercer archivo
        from pydub.generators import Sine
        tone3 = Sine(660).to_audio_segment(duration=3000)
        audio3_path = temp_dir / "test_audio3.mp3"
        tone3.export(str(audio3_path), format="mp3")
        
        output = str(temp_dir / "output_multi.mp3")
        resultado = fusionar_multiples_audios(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
                str(audio3_path),
            ],
            ruta_salida=output,
            crossfade_ms=1000,
        )
        
        assert resultado["exito"] is True
        assert resultado["num_archivos"] == 3
        assert len(resultado["duraciones_originales"]) == 3
        assert len(resultado["crossfades_aplicados"]) == 2
        assert Path(output).exists()
    
    def test_fusion_cuatro_archivos(self, sample_audio_files, temp_dir):
        """Debe fusionar correctamente 4 archivos."""
        from pydub.generators import Sine
        
        audios = [sample_audio_files["audio1"], sample_audio_files["audio2"]]
        
        for freq in [660, 550]:
            tone = Sine(freq).to_audio_segment(duration=2000)
            path = temp_dir / f"audio_{freq}.mp3"
            tone.export(str(path), format="mp3")
            audios.append(str(path))
        
        output = str(temp_dir / "output_4files.mp3")
        resultado = fusionar_multiples_audios(
            rutas_audios=audios,
            ruta_salida=output,
            crossfade_ms=500,
        )
        
        assert resultado["exito"] is True
        assert resultado["num_archivos"] == 4
        assert len(resultado["crossfades_aplicados"]) == 3
    
    def test_fusion_multiples_con_volumenes(self, sample_audio_files, temp_dir):
        """Debe aplicar volúmenes diferentes a cada archivo."""
        from pydub.generators import Sine
        tone3 = Sine(660).to_audio_segment(duration=2000)
        audio3_path = temp_dir / "audio3.mp3"
        tone3.export(str(audio3_path), format="mp3")
        
        output = str(temp_dir / "output_vol.mp3")
        resultado = fusionar_multiples_audios(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
                str(audio3_path),
            ],
            ruta_salida=output,
            crossfade_ms=500,
            volumenes=[-6.0, 0.0, 6.0],
        )
        
        assert resultado["exito"] is True
    
    def test_fusion_multiples_con_todos_parametros(self, sample_audio_files, temp_dir):
        """Debe funcionar con todos los parámetros activados."""
        from pydub.generators import Sine
        tone3 = Sine(660).to_audio_segment(duration=2000)
        audio3_path = temp_dir / "audio3.mp3"
        tone3.export(str(audio3_path), format="mp3")
        
        output = str(temp_dir / "output_full.mp3")
        resultado = fusionar_multiples_audios(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
                str(audio3_path),
            ],
            ruta_salida=output,
            crossfade_ms=1000,
            fade_in_ms=500,
            fade_out_ms=500,
            normalizar=True,
            volumenes=[-3.0, 0.0, 3.0],
        )
        
        assert resultado["exito"] is True
        assert Path(output).exists()
    
    def test_fusion_un_solo_archivo_falla(self, sample_audio_files, temp_dir):
        """Debe fallar si solo hay un archivo."""
        output = str(temp_dir / "output_single.mp3")
        resultado = fusionar_multiples_audios(
            rutas_audios=[sample_audio_files["audio1"]],
            ruta_salida=output,
            crossfade_ms=1000,
        )
        
        assert resultado["exito"] is False
        assert "2 archivos" in resultado["mensaje"].lower() or "al menos" in resultado["mensaje"].lower()
    
    def test_fusion_lista_vacia_falla(self, temp_dir):
        """Debe fallar con lista vacía."""
        output = str(temp_dir / "output_empty.mp3")
        resultado = fusionar_multiples_audios(
            rutas_audios=[],
            ruta_salida=output,
            crossfade_ms=1000,
        )
        
        assert resultado["exito"] is False
    
    def test_fusion_archivo_inexistente_en_lista(self, sample_audio_files, temp_dir):
        """Debe manejar correctamente un archivo inexistente en la lista."""
        output = str(temp_dir / "output_missing.mp3")
        resultado = fusionar_multiples_audios(
            rutas_audios=[
                sample_audio_files["audio1"],
                "/ruta/que/no/existe.mp3",
            ],
            ruta_salida=output,
            crossfade_ms=1000,
        )
        
        assert resultado["exito"] is False


class TestCrearPreview:
    """Tests para la función de previsualización."""
    
    def test_crear_preview_basica(self, sample_audio_files, temp_dir):
        """Debe crear una preview correctamente."""
        output = str(temp_dir / "preview.mp3")
        resultado = crear_preview(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
            ],
            ruta_salida=output,
            crossfade_ms=1000,
        )
        
        assert resultado["exito"] is True
        assert Path(output).exists()
        assert resultado["duracion_preview"] > 0
        assert resultado["duracion_preview"] <= 30  # Máximo 30 segundos por defecto
    
    def test_preview_con_limite_duracion(self, sample_audio_files, temp_dir):
        """La preview debe respetar el límite de duración."""
        output = str(temp_dir / "preview_short.mp3")
        resultado = crear_preview(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
            ],
            ruta_salida=output,
            crossfade_ms=500,
            max_duracion_ms=5000,  # Solo 5 segundos
        )
        
        assert resultado["exito"] is True
        assert resultado["duracion_preview"] <= 5.5  # Pequeño margen
    
    def test_preview_tres_archivos(self, sample_audio_files, temp_dir):
        """Debe crear preview de 3 archivos."""
        from pydub.generators import Sine
        tone3 = Sine(660).to_audio_segment(duration=3000)
        audio3_path = temp_dir / "audio3.mp3"
        tone3.export(str(audio3_path), format="mp3")
        
        output = str(temp_dir / "preview_3.mp3")
        resultado = crear_preview(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
                str(audio3_path),
            ],
            ruta_salida=output,
            crossfade_ms=500,
        )
        
        assert resultado["exito"] is True
        assert len(resultado["duraciones_segmentos"]) == 3
    
    def test_preview_con_efectos(self, sample_audio_files, temp_dir):
        """La preview debe aplicar fade-in y fade-out."""
        output = str(temp_dir / "preview_effects.mp3")
        resultado = crear_preview(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
            ],
            ruta_salida=output,
            crossfade_ms=500,
            fade_in_ms=500,
            fade_out_ms=500,
        )
        
        assert resultado["exito"] is True
    
    def test_preview_con_normalizacion(self, sample_audio_files, temp_dir):
        """La preview debe poder normalizarse."""
        output = str(temp_dir / "preview_norm.mp3")
        resultado = crear_preview(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
            ],
            ruta_salida=output,
            crossfade_ms=500,
            normalizar=True,
        )
        
        assert resultado["exito"] is True
    
    def test_preview_con_volumenes(self, sample_audio_files, temp_dir):
        """La preview debe aplicar ajustes de volumen."""
        output = str(temp_dir / "preview_vol.mp3")
        resultado = crear_preview(
            rutas_audios=[
                sample_audio_files["audio1"],
                sample_audio_files["audio2"],
            ],
            ruta_salida=output,
            crossfade_ms=500,
            volumenes=[-6.0, 6.0],
        )
        
        assert resultado["exito"] is True
    
    def test_preview_un_solo_archivo_falla(self, sample_audio_files, temp_dir):
        """La preview debe fallar con un solo archivo."""
        output = str(temp_dir / "preview_single.mp3")
        resultado = crear_preview(
            rutas_audios=[sample_audio_files["audio1"]],
            ruta_salida=output,
        )
        
        assert resultado["exito"] is False


class TestCompatibilidadAPI:
    """Tests para verificar que la API antigua sigue funcionando."""
    
    def test_fusionar_audios_compatibilidad(self, sample_audio_files, output_path):
        """La función fusionar_audios debe seguir funcionando."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=1000,
        )
        
        assert resultado["exito"] is True
        # Debe tener los campos de compatibilidad
        assert "duracion_audio1" in resultado
        assert "duracion_audio2" in resultado
        assert "crossfade_aplicado" in resultado
    
    def test_fusionar_audios_con_todos_parametros_compatibilidad(
        self, sample_audio_files, output_path
    ):
        """Todos los parámetros de la API antigua deben funcionar."""
        resultado = fusionar_audios(
            ruta_audio1=sample_audio_files["audio1"],
            ruta_audio2=sample_audio_files["audio2"],
            ruta_salida=output_path,
            crossfade_ms=1000,
            fade_in_ms=500,
            fade_out_ms=500,
            normalizar=True,
            volumen_audio1=-3.0,
            volumen_audio2=3.0,
        )
        
        assert resultado["exito"] is True
        assert Path(output_path).exists()
