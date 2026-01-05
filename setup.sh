#!/bin/bash

# ============================================
# Audio Fusion - Script de Instalación macOS
# ============================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Banner
echo ""
echo -e "${PURPLE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                           ║${NC}"
echo -e "${PURPLE}║   🎵  ${BLUE}Audio Fusion${PURPLE} - Instalación         ║${NC}"
echo -e "${PURPLE}║                                           ║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Función para imprimir pasos
step() {
    echo -e "${BLUE}▶${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    error "Por favor, ejecuta este script desde el directorio del proyecto"
    exit 1
fi

# 1. Verificar Python
step "Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    success "Python $PYTHON_VERSION encontrado"
else
    error "Python 3 no está instalado"
    echo "  Instálalo con: brew install python3"
    exit 1
fi

# 2. Verificar/Instalar ffmpeg
step "Verificando ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    success "ffmpeg encontrado"
else
    warning "ffmpeg no encontrado, intentando instalar..."
    
    if command -v brew &> /dev/null; then
        echo "  Instalando con Homebrew..."
        brew install ffmpeg
        success "ffmpeg instalado"
    else
        error "Homebrew no está instalado"
        echo "  Instala Homebrew primero:"
        echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        echo "  Luego ejecuta: brew install ffmpeg"
        exit 1
    fi
fi

# 3. Crear entorno virtual
VENV_DIR="venv"

step "Creando entorno virtual..."
if [ -d "$VENV_DIR" ]; then
    warning "El entorno virtual ya existe, recreando..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
success "Entorno virtual creado en ./$VENV_DIR"

# 4. Activar entorno virtual e instalar dependencias
step "Instalando dependencias..."
source "$VENV_DIR/bin/activate"

# Actualizar pip
pip install --upgrade pip --quiet

# Instalar dependencias
pip install -r requirements.txt --quiet

success "Dependencias instaladas"

# 5. Crear directorios necesarios
step "Creando directorios..."
mkdir -p backend/storage/files backend/storage/jobs
success "Directorios creados"

# Resumen final
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                           ║${NC}"
echo -e "${GREEN}║   ✓ Instalación completada                ║${NC}"
echo -e "${GREEN}║                                           ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${PURPLE}Para ejecutar la aplicación:${NC}"
echo ""
echo -e "  ${BLUE}1.${NC} Activa el entorno virtual:"
echo -e "     ${YELLOW}source venv/bin/activate${NC}"
echo ""
echo -e "  ${BLUE}2.${NC} Inicia la aplicación:"
echo -e "     ${YELLOW}uvicorn backend.app:app --reload --port 8000${NC}"
echo ""
echo -e "  ${BLUE}3.${NC} Abre en tu navegador:"
echo -e "     ${YELLOW}http://localhost:8000${NC}"
echo ""
echo -e "${PURPLE}Para desactivar el entorno virtual:${NC}"
echo -e "     ${YELLOW}deactivate${NC}"
echo ""
