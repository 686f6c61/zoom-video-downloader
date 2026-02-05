#!/bin/bash

# ============================================================================
# ZOOM VIDEO DOWNLOADER - Script de Inicio
# ============================================================================
#
# Este script verifica las dependencias necesarias y ejecuta la interfaz
# interactiva de Zoom Video Downloader.
#
# Funciones del script:
# 1. Verificar que Python3 este instalado
# 2. Verificar que todos los archivos del proyecto existan
# 3. Instalar dependencias automaticamente si es necesario
# 4. Ejecutar la interfaz interactiva (main.py)
#
# Requisitos:
# - Python 3.8 o superior
# - pip3
# - Conexion a internet (para instalar dependencias)
#
# Uso:
#   ./start.sh
#
# El script creara automaticamente los siguientes directorios si no existen:
#   - downloads/
#   - downloads/MP4/
#   - downloads/MP3/
#   - downloads/SRT/
#   - log/
#
# ============================================================================

set -e

echo "Iniciando Zoom Video Downloader..."
echo ""

# Verificar que Python3 este instalado
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 no esta instalado"
    echo "Por favor, instala Python3 para usar el descargador"
    exit 1
fi

# Verificar archivos necesarios del proyecto
ARCHIVOS_REQUERIDOS=(
    "main.py"
    "core.py"
    "simple_zoom_downloader.py"
    "batch_downloader.py"
    "pyproject.toml"
)

for archivo in "${ARCHIVOS_REQUERIDOS[@]}"; do
    if [ ! -f "$archivo" ]; then
        echo "Error: No se encuentra $archivo"
        echo "Asegurate de estar en el directorio correcto del proyecto"
        exit 1
    fi
done

echo "Archivos del proyecto verificados correctamente."

# Verificar e instalar dependencias
# ============================================================================
# Las dependencias se definen en pyproject.toml e incluyen:
#   - yt-dlp: para descargar videos de Zoom
#   - PyYAML: para leer archivos de configuracion
#
# El script intentara importar los modulos y si fallan,
# instalara las dependencias automaticamente.
# ============================================================================

echo "Verificando dependencias..."

python3 -c "
import yaml
import subprocess
import sys

# Verificar yt-dlp
try:
    subprocess.run(['yt-dlp', '--version'], check=True, capture_output=True)
except (subprocess.CalledProcessError, FileNotFoundError):
    print('yt-dlp no encontrado, instalando...')
    sys.exit(1)

# Verificar PyYAML
try:
    import yaml
except ImportError:
    print('PyYAML no encontrado, instalando...')
    sys.exit(1)

print('Todas las dependencias estan disponibles.')
" 2>/dev/null || {
    echo "Instalando dependencias desde pyproject.toml..."
    pip3 install -e . --break-system-packages 2>/dev/null || pip3 install -e .
    echo "Dependencias instaladas correctamente."
}

echo ""
echo "Listo! Iniciando interfaz..."
echo ""

# Ejecutar la interfaz interactiva
# ============================================================================
# main.py proporciona un menu grafico en terminal con las siguientes opciones:
#   1. Descargar URL individual
#   2. Descargar desde archivo (masivo)
#   3. Ver archivos en carpeta input/
#   4. Ver estado de descargas
#   5. Limpiar archivos temporales
#   6. Ayuda
#   0. Salir
# ============================================================================

python3 main.py

echo ""
echo "Gracias por usar Zoom Video Downloader!"
