#!/bin/bash

# DESCARGADOR DE ZOOM - INTERFAZ INTERACTIVA
# Inicia automáticamente la interfaz gráfica interactiva

# Verificar si Python3 está disponible
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 no está instalado"
    echo "Por favor, instala Python3 para usar el descargador"
    exit 1
fi

# Verificar si main.py existe
if [ ! -f "main.py" ]; then
    echo "Error: No se encuentra main.py"
    echo "Asegúrate de estar en el directorio correcto del proyecto"
    exit 1
fi

# Iniciar la interfaz interactiva
echo "Iniciando Zoom Video Downloader - Interfaz Interactiva..."
echo ""

# Ejecutar main.py
python3 main.py

# Función para verificar dependencias
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
echo "Error: Python3 no está instalado"
        exit 1
    fi
    
    # Crear entorno virtual si no existe
    if [ ! -d "venv" ]; then
        echo "Creando entorno virtual..."
        python3 -m venv venv
    fi
    
    # Activar entorno virtual
    source venv/bin/activate
    
    # Instalar dependencias
    pip install requests yt-dlp --quiet 2>/dev/null
}

# Función para descarga individual
download_individual() {
    local url="$1"
    local type="$2"
    local name="$3"
    
    if [ -z "$url" ]; then
        echo "Error: Se requiere una URL"
        echo "Uso: $0 individual <URL> [tipo] [nombre]"
        exit 1
    fi
    
    check_dependencies
    
    echo "Descarga individual"
    echo "URL: $url"
    [ -n "$type" ] && echo "Tipo: $type"
    [ -n "$name" ] && echo "Nombre: $name"
    echo ""
    
    # Ejecutar descarga individual
    if [ -n "$type" ] && [ -n "$name" ]; then
        python simple_zoom_downloader.py "$url" "$type" "$name"
    elif [ -n "$type" ]; then
        python simple_zoom_downloader.py "$url" "$type"
    else
        python simple_zoom_downloader.py "$url"
    fi
    
    show_status
}

# Función para descarga masiva
download_batch() {
    local file="$1"
    local type="$2"
    
    if [ -z "$file" ]; then
        echo "Error: Se requiere un archivo"
        echo "Uso: $0 masivo <archivo> [tipo]"
        exit 1
    fi
    
    if [ ! -f "$file" ]; then
        echo "Error: El archivo no existe: $file"
        echo ""
        echo "Archivos disponibles en input/:"
        if [ -d "input" ]; then
            ls -la input/ 2>/dev/null || echo "  (vacío)"
        else
            echo "  (directorio input/ no existe)"
        fi
        exit 1
    fi
    
    check_dependencies
    
    echo "Descarga masiva"
    echo "Archivo: $file"
    [ -n "$type" ] && echo "Tipo: $type"
    echo ""
    
    # Ejecutar descarga masiva
    if [ -n "$type" ]; then
        python batch_downloader.py "$file" "$type"
    else
        python batch_downloader.py "$file"
    fi
    
    show_status
}

# Función para mostrar estado
show_status() {
    echo ""
    echo "ESTADO DE DESCARGAS:"
    echo "======================="
    
    if [ -d "downloads" ]; then
        echo "Directorio downloads/"
        
        # Contar archivos
        local mp4_count=0
        local mp3_count=0
        local srt_count=0
        
        if [ -d "downloads/MP4" ]; then
            mp4_count=$(find downloads/MP4/ -name "*.mp4" -not -name "*.part" 2>/dev/null | wc -l)
        fi
        
        if [ -d "downloads/MP3" ]; then
            mp3_count=$(find downloads/MP3/ -name "*.mp3" 2>/dev/null | wc -l)
        fi
        
        if [ -d "downloads/SRT" ]; then
            srt_count=$(find downloads/SRT/ -name "*.srt" -o -name "*.vtt" 2>/dev/null | wc -l)
        fi
        
        echo "  📹 Videos (MP4): $mp4_count archivos"
        echo "  Audios (MP3): $mp3_count archivos"
        echo "  Transcripciones (SRT/VTT): $srt_count archivos"
        
        # Calcular tamaño total
        local total_size=0
        if [ -d "downloads" ]; then
            total_size=$(du -sh downloads/ 2>/dev/null | cut -f1)
            echo "  💾 Tamaño total: $total_size"
        fi
        
        # Mostrar archivos recientes (últimos 5)
        echo ""
        echo "Archivos recientes:"
        find downloads/ -type f -not -name "*.part" -printf "%TY-%Tm-%Td %TH:%TM %p\n" 2>/dev/null | sort -r | head -5 | while read line; do
            echo "  $line"
        done
        
    else
        echo "  📭 No hay descargas realizadas"
    fi
}

# Función para limpiar
clean_files() {
    echo "Limpiando archivos temporales..."
    
    # Eliminar archivos .part (descargas incompletas)
    find downloads/ -name "*.part" -type f -delete 2>/dev/null
    echo "  Archivos .part eliminados"
    
    # Eliminar entorno virtual si existe
    if [ -d "venv" ]; then
        rm -rf venv
        echo "  Entorno virtual eliminado"
    fi
    
    # Eliminar archivos de log temporales
    find . -name "*.log" -type f -delete 2>/dev/null
    echo "  Archivos de log eliminados"
    
    echo "Limpieza completada"
}

# Si se proporcionan argumentos, mostrar ayuda y salir
if [ $# -gt 0 ]; then
    echo "⚠️  Este script ahora inicia la interfaz interactiva automáticamente"
    echo "   Si quieres usar la línea de comandos, ejecuta directamente:"
    echo "   python3 simple_zoom_downloader.py <URL> [tipo] [nombre]"
    echo "   python3 batch_downloader.py <archivo> [tipo]"
    echo ""
    echo "🎯 Para la interfaz interactiva, simplemente ejecuta:"
    echo "   ./start.sh"
    echo ""
    exit 1
fi