# 🎵 Audio Fusion

Aplicación web para fusionar **múltiples archivos de audio** con crossfade.

- **Frontend**: estático (HTML + CSS/SCSS BEM + JS vanilla)
- **Backend**: FastAPI (sirve el frontend y expone una API en `/v1/*`)
- **Procesamiento**: `pydub` + `ffmpeg`

![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)

## ✨ Características

- **Múltiples archivos**: Fusiona de 2 a 10 archivos de audio
- **Previsualización**: Escucha una muestra antes de exportar
- **Crossfade suave**: Transiciones profesionales entre audios
- **Reordenar**: Cambia el orden arrastrando o con botones
- **Fade in/out**: Efectos de entrada y salida graduales
- **Control de volumen**: Ajusta el volumen de cada pista independientemente
- **Normalización**: Iguala el volumen del resultado automáticamente
- **Múltiples formatos**: MP3, M4R, M4A, MP4, WAV, OGG, FLAC, AAC
- **Interfaz responsive**: Funciona en móvil, tablet y desktop

---

## ✅ Requisitos

- macOS 10.15+ (o cualquier sistema con Python y ffmpeg)
- Python 3.9+
- `ffmpeg` instalado (el `setup.sh` intenta instalarlo con Homebrew en macOS)

Notas de compatibilidad:

- En **Python 3.13+**, la librería estándar `audioop` ya no existe. Este proyecto lo cubre con `audioop-lts` y un shim `pyaudioop.py` para que `pydub` funcione correctamente.

---

## 🚀 Instalación rápida (macOS)

### Paso 1: Descarga el proyecto

Coloca la carpeta `audio_fusion` donde prefieras (por ejemplo, en tu carpeta de proyectos).

### Paso 2: Abre Terminal

Puedes abrir Terminal de varias formas:
- Spotlight (`Cmd + Espacio`) → escribe "Terminal"
- Finder → Aplicaciones → Utilidades → Terminal

### Paso 3: Navega al proyecto

```bash
cd /ruta/a/audio_fusion
```

Por ejemplo, si lo pusiste en Documentos:
```bash
cd ~/Documents/audio_fusion
```

### Paso 4: Ejecuta el instalador

```bash
chmod +x setup.sh
./setup.sh
```

Este script automáticamente:
- ✓ Verifica que tienes Python 3
- ✓ Instala ffmpeg si no lo tienes (necesita Homebrew)
- ✓ Crea un entorno virtual aislado
- ✓ Instala todas las dependencias
- ✓ Crea directorios de almacenamiento del backend

---

## ▶️ Arranque (recomendado)

Para arrancar en **un solo comando** (activa venv, levanta el servidor y abre el navegador):

```bash
./run_app.sh
```

Detalles útiles:

- Por defecto usa el puerto `8000`.
- Si `8000` está ocupado, intenta elegir un puerto libre entre `8000` y `8010`.
- Puedes forzar el puerto con `PORT`:

```bash
PORT=8005 ./run_app.sh
```

Si algún día sirves el frontend en otro puerto/dominio (origen distinto), puedes activar CORS:

```bash
ENABLE_CORS=1 ./run_app.sh
```

---

## 🎮 Uso

### Iniciar la aplicación

Cada vez que quieras usar la aplicación:

```bash
# 1. Navega al proyecto
cd /ruta/a/audio_fusion

# 2. Activa el entorno virtual
source venv/bin/activate

# 3. Inicia la aplicación
uvicorn backend.app:app --reload --port 8000
```

### Abrir en el navegador

Una vez iniciada, abre tu navegador y ve a:

```
http://localhost:8000
```

### Usar la aplicación

1. **Sube los archivos**: Arrastra o haz clic para seleccionar (hasta 10)
2. **Reordena si necesitas**: Usa las flechas ↑↓ o arrastra
3. **Ajusta los parámetros**:
   - **Crossfade**: Duración de la transición entre audios
   - **Fade In**: Entrada gradual al inicio
   - **Fade Out**: Salida gradual al final
   - **Normalizar**: Iguala el volumen final
   - **Formato**: Elige el formato de salida
4. **Previsualiza**: Haz clic en "Previsualizar" para escuchar una muestra
5. **Fusiona**: Cuando estés satisfecho, haz clic en "Fusionar"
6. **Descarga**: Escucha el resultado y descárgalo

### Botones de limpieza

En el panel **Acciones** hay dos botones para “volver a cero”:

- **Limpiar archivos/resultados**: borra los archivos subidos y los resultados en el servidor, y limpia la UI de previews/resultados. **No cambia** los parámetros (crossfade, fades, normalizar, formato).
- **RESET** (reset fuerte): hace lo anterior y además **restaura los parámetros** a sus valores por defecto. También está diseñado para ser robusto si había una preview/fusión en curso (evita que un job antiguo vuelva a “revivir” tras el reset). **Requiere confirmación**.

### Detener la aplicación

En la terminal, presiona `Ctrl + C`

### Desactivar el entorno virtual

```bash
deactivate
```

---

## 📁 Estructura del Proyecto

```
audio_fusion/
├── backend/                # API (FastAPI) + procesamiento
│   ├── app.py              # Servidor (API + sirve el frontend)
│   ├── audio_processor.py  # Lógica de procesamiento
│   └── storage/            # Archivos subidos y resultados de jobs
├── frontend/               # UI estática
│   ├── index.html
│   └── assets/
│       ├── js/app.js
│       ├── scss/main.scss
│       └── css/main.css
├── tests/                  # Tests automatizados
│   ├── conftest.py         # Fixtures
│   ├── test_audio_processor.py   # Tests de procesamiento
├── venv/                   # Entorno virtual (creado por setup)
├── run_app.sh               # Arranque en 1 comando (abre navegador)
├── requirements.txt        # Dependencias Python
├── pytest.ini             # Configuración de tests
├── setup.sh               # Script de instalación
├── run_tests.sh           # Script para ejecutar tests
└── README.md              # Este archivo
```

---

## ⚙️ Parámetros Disponibles

| Parámetro | Descripción | Rango |
|-----------|-------------|-------|
| **Archivos** | Número de archivos de audio a fusionar | 2 - 10 |
| **Crossfade** | Duración de la transición suave entre cada par de audios | 0 - 10 segundos |
| **Fade In** | Entrada gradual al inicio del audio resultante | 0 - 5 segundos |
| **Fade Out** | Salida gradual al final del audio resultante | 0 - 5 segundos |
| **Volumen** | Ajuste de ganancia individual por archivo | -20 a +20 dB |
| **Normalizar** | Ajusta el volumen final a -14 dBFS (estándar streaming) | On/Off |
| **Formato** | Formato del archivo de salida | MP3, M4A, WAV, OGG, FLAC |

### Funciones especiales

- **Previsualización**: Genera una muestra de ~30 segundos para probar la configuración sin procesar todo el audio
- **Reordenamiento**: Cambia el orden de los archivos con los botones ↑↓
- **Duración estimada**: Muestra la duración aproximada del resultado final

---

## 🔧 Requisitos del Sistema

- **macOS** 10.15 (Catalina) o superior
- **Python** 3.9 o superior
- **ffmpeg** (se instala automáticamente con el script)
- **Homebrew** (para instalar ffmpeg)

### Instalar Homebrew (si no lo tienes)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

---

## 🐛 Solución de Problemas

### "command not found: uvicorn"

Faltan dependencias dentro del entorno virtual:
```bash
./setup.sh
```

Nota: `./run_app.sh` y `./run_tests.sh` usan `venv/bin/python` directamente (no dependen de `source venv/bin/activate`), lo que evita problemas si mueves la carpeta del proyecto.

### "No module named pydub"

Reinstala las dependencias:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### "ffmpeg not found"

Instala ffmpeg:
```bash
brew install ffmpeg
```

Si no tienes `ffmpeg` instalado, el proyecto incluye un fallback portable vía `imageio-ffmpeg` (lo configura automáticamente el backend al importar `pydub`).

### El puerto 8000 está ocupado

Usa otro puerto:
```bash
uvicorn backend.app:app --reload --port 8001
```

Si usas `./run_app.sh`, intenta automáticamente un puerto libre entre `8000` y `8010`.

### Error al procesar audio

Verifica que el archivo de audio no esté corrupto y sea un formato soportado.

---

## 📝 Notas

- El backend guarda uploads y resultados en `backend/storage/`.
- El frontend se sirve desde `frontend/` (sin build obligatorio; ya hay CSS compilado).
- Los resultados de jobs se almacenan en `backend/storage/jobs/<epoch>/<job_id>/...`.

---

## 🔌 API

La API vive bajo `/v1/*` y se sirve en el mismo origen que el frontend.

### Subida

`POST /v1/uploads` (multipart form-data con `files`)

Devuelve una lista de archivos con `file_id` (IDs que se usan para preview/merge).

### Preview

- `POST /v1/previews` crea un job de preview.
- `GET /v1/jobs/{job_id}` consulta el progreso.
- `GET /v1/jobs/{job_id}/preview` devuelve el audio de preview cuando el job termina.

### Merge

- `POST /v1/merges` crea un job de fusión.
- `GET /v1/jobs/{job_id}` consulta el progreso.
- `GET /v1/jobs/{job_id}/download` devuelve el resultado cuando el job termina.

### Reset

Además de los botones, existe un endpoint de API para automatizar la limpieza:

### `POST /v1/reset`

Body JSON:

```json
{ "mode": "soft" }
```

Modos:

- `soft`: borra uploads/resultados y limpia jobs en memoria.
- `hard`: igual que `soft`, pero además hace un “reset fuerte” (incrementa un epoch interno) para que jobs iniciados antes del reset no puedan reescribir estado tras el reset.

Respuesta:

```json
{ "ok": true, "mode": "soft" }
```

---

## 🧰 Ejemplos con `curl`

Asumiendo que el servidor está corriendo en `http://127.0.0.1:8000`.

Tip: puedes arrancarlo con:

```bash
./run_app.sh
```

### 1) Subir archivos

Sube 2 archivos (mínimo para preview/merge):

```bash
curl -sS -X POST \
  -F "files=@/ruta/a/uno.mp3" \
  -F "files=@/ruta/a/dos.mp3" \
  http://127.0.0.1:8000/v1/uploads
```

Respuesta (ejemplo):

```json
{
  "files": [
    {"file_id":"abc123...","filename":"uno.mp3","duration":3.0,"format":"mp3"},
    {"file_id":"def456...","filename":"dos.mp3","duration":3.0,"format":"mp3"}
  ]
}
```

Guarda los `file_id` para los siguientes pasos.

### 2) Crear una preview

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/previews \
  -H 'Content-Type: application/json' \
  -d '{
    "file_ids": ["abc123...", "def456..."],
    "params": {
      "crossfade_ms": 2000,
      "fade_in_ms": 0,
      "fade_out_ms": 0,
      "normalizar": false,
      "volumenes": [0, 0]
    }
  }'
```

Respuesta (ejemplo):

```json
{
  "job_id": "<job_id>",
  "status_url": "/v1/jobs/<job_id>",
  "preview_url": "/v1/jobs/<job_id>/preview"
}
```

### 3) Consultar estado del job

```bash
curl -sS http://127.0.0.1:8000/v1/jobs/<job_id>
```

Campos típicos: `state` (`queued|running|done|error`), `progress` (0-100), `stage`.

### 4) Descargar/escuchar la preview

Cuando el estado sea `done`:

```bash
curl -L -o preview.mp3 http://127.0.0.1:8000/v1/jobs/<job_id>/preview
```

### 5) Crear una fusión (merge)

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/merges \
  -H 'Content-Type: application/json' \
  -d '{
    "file_ids": ["abc123...", "def456..."],
    "params": {
      "crossfade_ms": 2000,
      "fade_in_ms": 0,
      "fade_out_ms": 0,
      "normalizar": false,
      "volumenes": [0, 0]
    },
    "output": {"format": "mp3"}
  }'
```

Respuesta (ejemplo):

```json
{
  "job_id": "<job_id>",
  "status_url": "/v1/jobs/<job_id>",
  "download_url": "/v1/jobs/<job_id>/download"
}
```

Descarga cuando `state=done`:

```bash
curl -L -o audio_fusion.mp3 http://127.0.0.1:8000/v1/jobs/<job_id>/download
```

### 6) Limpiar / resetear servidor

Limpieza (soft):

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/reset \
  -H 'Content-Type: application/json' \
  -d '{"mode":"soft"}'
```

Reset fuerte (hard):

```bash
curl -sS -X POST http://127.0.0.1:8000/v1/reset \
  -H 'Content-Type: application/json' \
  -d '{"mode":"hard"}'
```

---

## 🧪 Tests

El proyecto incluye una suite de tests para verificar que todo funciona correctamente.

### Ejecutar tests

```bash
# Activar entorno virtual primero
source venv/bin/activate

# Ejecutar todos los tests
./run_tests.sh

# O con pytest directamente
pytest
```

### Opciones de ejecución

```bash
# Tests con salida detallada
./run_tests.sh -v

# Tests con salida mínima
./run_tests.sh -q

# Tests con reporte de cobertura
./run_tests.sh --coverage

# Ejecutar solo tests específicos
pytest tests/test_audio_processor.py -v

# Ejecutar un test concreto
pytest tests/test_audio_processor.py::TestFusionarAudios::test_fusion_basica -v
```

### Qué comprueban los tests

- `tests/test_audio_processor.py`: Tests del procesamiento de audio
  - Detección de formatos
  - Carga de archivos
  - Normalización de volumen
  - Fusión de 2 archivos (compatibilidad)
  - Fusión de múltiples archivos (3, 4, ...)
  - Generación de previews
  - Manejo de errores
  - Casos límite (archivos muy cortos, crossfade excesivo, etc.)

---

## 🤝 Créditos

- **pydub**: Procesamiento de audio
- **ffmpeg**: Backend de codificación de audio

---

¡Disfruta fusionando tus audios! 🎶
# audio_fusion
