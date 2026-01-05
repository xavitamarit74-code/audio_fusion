#!/bin/bash

# ============================================
# Audio Fusion - Ejecutar Tests
# ============================================

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo ""
echo -e "${PURPLE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                                           ║${NC}"
echo -e "${PURPLE}║   🧪  ${BLUE}Audio Fusion${PURPLE} - Tests               ║${NC}"
echo -e "${PURPLE}║                                           ║${NC}"
echo -e "${PURPLE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}✗${NC} Por favor, ejecuta este script desde el directorio del proyecto"
    exit 1
fi

# Verificar entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠${NC} Entorno virtual no encontrado. Ejecuta primero:"
    echo -e "   ${YELLOW}./setup.sh${NC}"
    exit 1
fi

PY="$PWD/venv/bin/python"
if [ ! -x "$PY" ]; then
    echo -e "${RED}✗${NC} No se encuentra el intérprete en $PY"
    echo -e "${YELLOW}⚠${NC} Recomendado: ./setup.sh"
    exit 1
fi

# Verificar pytest
if ! "$PY" -c 'import pytest' >/dev/null 2>&1; then
    echo -e "${BLUE}▶${NC} Instalando pytest..."
    "$PY" -m pip install pytest --quiet
fi

# Ejecutar tests
echo -e "${BLUE}▶${NC} Ejecutando tests..."
echo ""

TEST_EXIT=0

# Opciones de ejecución según argumentos
if [ "$1" == "-v" ] || [ "$1" == "--verbose" ]; then
    set +e
    "$PY" -m pytest -v --tb=long
    TEST_EXIT=$?
    set -e
elif [ "$1" == "-q" ] || [ "$1" == "--quiet" ]; then
    set +e
    "$PY" -m pytest -q
    TEST_EXIT=$?
    set -e
elif [ "$1" == "--coverage" ]; then
    "$PY" -m pip install pytest-cov --quiet
    set +e
    "$PY" -m pytest --cov=backend --cov-report=term-missing
    TEST_EXIT=$?
    set -e
elif [ "$1" == "--help" ]; then
    echo "Uso: ./run_tests.sh [opción]"
    echo ""
    echo "Opciones:"
    echo "  (sin opción)   Ejecutar tests con salida normal"
    echo "  -v, --verbose  Ejecutar con salida detallada"
    echo "  -q, --quiet    Ejecutar con salida mínima"
    echo "  --coverage     Ejecutar con reporte de cobertura"
    echo "  --help         Mostrar esta ayuda"
    exit 0
else
    set +e
    "$PY" -m pytest
    TEST_EXIT=$?
    set -e
fi

# Resultado
echo ""
if [ $TEST_EXIT -eq 0 ]; then
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✓ Todos los tests pasaron               ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
else
    echo -e "${RED}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ✗ Algunos tests fallaron                ║${NC}"
    echo -e "${RED}╚═══════════════════════════════════════════╝${NC}"
fi
echo ""

exit $TEST_EXIT
