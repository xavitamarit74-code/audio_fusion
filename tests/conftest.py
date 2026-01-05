"""
Configuración y fixtures para los tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import os

# Añadir el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def temp_dir():
    """Crea un directorio temporal para los tests."""
    temp_path = tempfile.mkdtemp(prefix="audio_fusion_test_")
    yield Path(temp_path)
    # Limpiar después de todos los tests
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_audio_files(temp_dir):
    """
    Genera archivos de audio de prueba usando pydub.
    Crea dos tonos simples de 3 segundos cada uno.
    """
    from pydub import AudioSegment
    from pydub.generators import Sine
    
    # Generar tono 1: 440Hz (La4) - 3 segundos
    tone1 = Sine(440).to_audio_segment(duration=3000)
    tone1 = tone1.fade_in(100).fade_out(100)
    audio1_path = temp_dir / "test_audio1.mp3"
    tone1.export(str(audio1_path), format="mp3")
    
    # Generar tono 2: 880Hz (La5) - 3 segundos
    tone2 = Sine(880).to_audio_segment(duration=3000)
    tone2 = tone2.fade_in(100).fade_out(100)
    audio2_path = temp_dir / "test_audio2.mp3"
    tone2.export(str(audio2_path), format="mp3")
    
    return {
        "audio1": str(audio1_path),
        "audio2": str(audio2_path),
        "temp_dir": temp_dir,
    }


@pytest.fixture
def short_audio_files(temp_dir):
    """
    Genera archivos de audio muy cortos para probar edge cases.
    """
    from pydub import AudioSegment
    from pydub.generators import Sine
    
    # Audio muy corto: 500ms
    short1 = Sine(440).to_audio_segment(duration=500)
    short1_path = temp_dir / "short_audio1.mp3"
    short1.export(str(short1_path), format="mp3")
    
    short2 = Sine(880).to_audio_segment(duration=500)
    short2_path = temp_dir / "short_audio2.mp3"
    short2.export(str(short2_path), format="mp3")
    
    return {
        "audio1": str(short1_path),
        "audio2": str(short2_path),
        "temp_dir": temp_dir,
    }


@pytest.fixture
def output_path(temp_dir):
    """Genera una ruta para el archivo de salida."""
    return str(temp_dir / "output.mp3")


@pytest.fixture
def project_root():
    """Devuelve la raíz del proyecto."""
    return Path(__file__).parent.parent
