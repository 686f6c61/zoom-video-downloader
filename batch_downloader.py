#!/usr/bin/env python3
"""
Zoom Video Downloader - Batch Processing
========================================

Este proyecto permite descargar grabaciones de Zoom en diferentes formatos:
- Videos (MP4)
- Audios (MP3) 
- Transcripciones (SRT/VTT)

El script batch_downloader.py procesa múltiples URLs desde archivos CSV o TXT
y descarga el contenido especificado utilizando yt-dlp como herramienta principal.

Características:
- Soporte para descarga masiva desde archivos
- Conversión automática de video a audio MP3
- Extracción de transcripciones cuando están disponibles
- Nombres de archivo personalizados desde CSV
- Instalación automática de dependencias (yt-dlp, ffmpeg)

Formatos de entrada soportados:
- TXT: una URL de Zoom por línea
- CSV: titulo,url (dos columnas separadas por coma)

Uso: python3 batch_downloader.py <archivo_urls> [tipo]
Tipos: video, audio, transcript, all

Author: 686f6c61
Project: zoom-video-downloader
"""
"""
Zoom Video Downloader - Batch Processing
========================================

Este proyecto permite descargar grabaciones de Zoom en diferentes formatos:
- Videos (MP4)
- Audios (MP3) 
- Transcripciones (SRT/VTT)

El script batch_downloader.py procesa múltiples URLs desde archivos CSV o TXT
y descarga el contenido especificado utilizando yt-dlp como herramienta principal.

Características:
- Soporte para descarga masiva desde archivos
- Conversión automática de video a audio MP3
- Extracción de transcripciones cuando están disponibles
- Nombres de archivo personalizados desde CSV
- Instalación automática de dependencias (yt-dlp, ffmpeg)

Formatos de entrada soportados:
- TXT: una URL de Zoom por línea
- CSV: titulo,url (dos columnas separadas por coma)

Uso: python3 batch_downloader.py <archivo_urls> [tipo]
Tipos: video, audio, transcript, all

Author: 686f6c61
Project: zoom-video-downloader
"""

import requests
import re
import os
import sys
import subprocess
import csv
from urllib.parse import urlparse, parse_qs

def create_directories():
    """
    Crear estructura de directorios para organizar las descargas.
    
    Crea los siguientes directorios si no existen:
    - downloads/: Directorio principal
    - downloads/MP4/: Para archivos de video
    - downloads/MP3/: Para archivos de audio
    - downloads/SRT/: Para transcripciones
    
    Returns:
        None
    """
    directories = ['downloads', 'downloads/MP4', 'downloads/MP3', 'downloads/SRT']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def sanitize_filename(filename):
    """
    Sanitizar nombre de archivo para que sea válido en todos los sistemas operativos.
    
    Args:
        filename (str): Nombre de archivo original
        
    Returns:
        str: Nombre de archivo sanitizado
        
    Proceso:
    1. Reemplaza caracteres inválidos por guiones bajos
    2. Limita la longitud a 50 caracteres para evitar problemas
    """
    import re
    # Reemplazar caracteres inválidos en Windows/Linux/Mac
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limitar longitud para evitar problemas de sistema de archivos
    if len(filename) > 50:
        filename = filename[:50]
    return filename

def extract_video_id(zoom_url):
    """
    Extraer el ID único de la grabación desde la URL de Zoom.
    
    Args:
        zoom_url (str): URL completa de la grabación de Zoom
        
    Returns:
        str or None: ID de la grabación o None si no se encuentra
        
    Ejemplo:
    Input:  https://zoom.us/rec/play/gD5HiYaP4SvEo7ILjkl6BaVa8_S5vyP0e7HatLxbx7SlXuykhw_-89F8sWXTTQGQBJXhi7o-S1bSdKc.VDINYMvBrp8hB9at
    Output: gD5HiYaP4SvEo7ILjkl6BaVa8_S5vyP0e7HatLxbx7SlXuykhw_-89F8sWXTTQGQBJXhi7o-S1bSdKc.VDINYMvBrp8hB9at
    """
    match = re.search(r'/rec/play/([^?]+)', zoom_url)
    return match.group(1) if match else None

def install_ffmpeg():
    """
    Verificar e instalar ffmpeg si no está disponible en el sistema.
    
    ffmpeg es necesario para convertir videos MP4 a audio MP3.
    Esta función intenta instalarlo automáticamente en sistemas Debian/Ubuntu.
    
    Returns:
        bool: True si ffmpeg está disponible o se instaló correctamente, False en caso contrario
        
    Nota:
    - Requiere privilegios de sudo para instalación
    - Solo compatible con sistemas basados en Debian/Ubuntu
    - Para otros sistemas, instalar manualmente: apt install ffmpeg
    """
    try:
        # Verificar si ffmpeg ya está instalado
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Instalando ffmpeg...")
        try:
            # Actualizar lista de paquetes e instalar ffmpeg
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'ffmpeg'], check=True)
            return True
        except subprocess.CalledProcessError:
            print("No se pudo instalar ffmpeg automáticamente")
            print("Por favor, instálalo manualmente: sudo apt install ffmpeg")
            return False

def convert_to_mp3(input_file, output_file):
    """
    Convertir archivo de video MP4 a audio MP3 usando ffmpeg.
    
    Args:
        input_file (str): Ruta del archivo de video de entrada
        output_file (str): Ruta del archivo de audio de salida
        
    Returns:
        bool: True si la conversión fue exitosa, False en caso contrario
        
    Proceso:
    1. Verifica que ffmpeg esté disponible
    2. Ejecuta ffmpeg con parámetros optimizados para calidad
    3. Extrae solo el stream de audio del video
    
    Parámetros ffmpeg:
    - -q:a 0: Calidad de audio máxima (VBR 0)
    - -map a: Seleccionar solo el stream de audio
    """
    try:
        if not install_ffmpeg():
            return False
            
        print(f"Convirtiendo {input_file} a MP3...")
        cmd = [
            'ffmpeg',
            '-i', input_file,        # Archivo de entrada
            '-q:a', '0',             # Calidad de audio máxima
            '-map', 'a',             # Mapear solo el stream de audio
            output_file              # Archivo de salida
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Conversión completada: {output_file}")
            return True
        else:
            print(f"Error en conversión: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error convirtiendo a MP3: {e}")
        return False

def download_with_yt_dlp(zoom_url, download_type='video', custom_name=None):
    """
    Descargar contenido de Zoom utilizando yt-dlp como herramienta principal.
    
    yt-dlp es un fork de youtube-dl con soporte mejorado para Zoom y otras plataformas.
    
    Args:
        zoom_url (str): URL de la grabación de Zoom
        download_type (str): Tipo de descarga ('video', 'audio', 'transcript', 'all')
        custom_name (str, optional): Nombre personalizado para el archivo
        
    Returns:
        bool: True si la descarga fue exitosa, False en caso contrario
        
    Proceso:
    1. Verificar/instalar yt-dlp si no está disponible
    2. Extraer ID del video para generar nombre de archivo
    3. Construir comando yt-dlp según tipo de descarga
    4. Ejecutar descarga y manejar errores
    5. Si es 'all', convertir video a audio adicionalmente
    
    Tipos de descarga soportados:
    - video: Descargar solo el archivo MP4
    - audio: Extraer y descargar solo audio MP3
    - transcript: Descargar subtítulos/transcripción SRT/VTT
    - all: Descargar video + audio + transcripción
    """
    try:
        # Extraer ID para mostrar en progreso
        video_id = extract_video_id(zoom_url)
        safe_id = video_id[:20] if video_id else "recording"
        display_name = custom_name or safe_id
        print(f"  Descargando {display_name}...")
        
        # Verificar si yt-dlp está instalado, instalar si no
        try:
            subprocess.run(['yt-dlp', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  Instalando yt-dlp...")
            subprocess.run(['pip', 'install', 'yt-dlp'], check=True)
        
        # Generar nombre base para archivos
        base_name = custom_name if custom_name else safe_id
        
        output_template = None
        cmd = None
        
        # Construir comando según tipo de descarga
        if download_type == 'video':
            output_template = f"downloads/MP4/{base_name}.mp4"
            cmd = [
                'yt-dlp',
                '--no-warnings',                    # Ocultar advertencias
                '--format', 'best[ext=mp4]/best', # Preferir MP4 de mejor calidad
                '--output', output_template,
                zoom_url
            ]
        elif download_type == 'audio':
            output_template = f"downloads/MP3/{base_name}.mp3"
            cmd = [
                'yt-dlp',
                '--no-warnings',
                '--extract-audio',                # Extraer solo audio
                '--audio-format', 'mp3',           # Formato de salida MP3
                '--audio-quality', '0',            # Calidad máxima
                '--output', f"downloads/MP3/{base_name}.%(ext)s",
                zoom_url
            ]
        elif download_type == 'transcript':
            output_template = f"downloads/SRT/{base_name}"
            cmd = [
                'yt-dlp',
                '--no-warnings',
                '--write-subs',                   # Escribir subtítulos
                '--write-auto-subs',              # Incluir subtítulos automáticos
                '--sub-langs', 'all',             # Todos los idiomas disponibles
                '--skip-download',                 # No descargar video
                '--output', output_template,
                zoom_url
            ]
        elif download_type == 'all':
            output_template = f"downloads/MP4/{base_name}.mp4"
            cmd = [
                'yt-dlp',
                '--no-warnings',
                '--format', 'best[ext=mp4]/best',
                '--write-subs',                   # Incluir subtítulos
                '--write-auto-subs',
                '--sub-langs', 'all',
                '--output', output_template,
                zoom_url
            ]
        
        # Validar que se construyó el comando correctamente
        if not cmd or not output_template:
            print(f"  Tipo de descarga no válido: {download_type}")
            return False
        
        # Ejecutar descarga
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  Descarga completada: {base_name}")
            
            # Si se descargó video y se pidió 'all', convertir también a MP3
            if download_type == 'all':
                video_file = f"downloads/MP4/{base_name}.mp4"
                if os.path.exists(video_file):
                    audio_file = f"downloads/MP3/{base_name}.mp3"
                    convert_to_mp3(video_file, audio_file)
            
            return True
        else:
            print(f"  Error con yt-dlp: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  Error con yt-dlp: {e}")
        return False
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"  Descarga completada: {base_name}")
            
            # Si se descargó video y se pidió 'all', convertir también a MP3
            if download_type == 'all':
                video_file = f"downloads/MP4/{base_name}.mp4"
                if os.path.exists(video_file):
                    audio_file = f"downloads/MP3/{base_name}.mp3"
                    convert_to_mp3(video_file, audio_file)
            
            return True
        else:
            print(f"  Error con yt-dlp: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  Error con yt-dlp: {e}")
        return False

def read_urls_from_file(file_path):
    """
    Leer y procesar URLs de Zoom desde archivos TXT o CSV.
    
    Soporta dos formatos:
    1. TXT: Una URL de Zoom por línea
    2. CSV: titulo,url (dos columnas separadas por coma)
    
    Args:
        file_path (str): Ruta al archivo a procesar
        
    Returns:
        list: Lista de tuplas (title, url) con las URLs válidas encontradas
        
    Formatos soportados:
    
    TXT:
    https://zoom.us/rec/play/abc123...
    https://zoom.us/rec/play/def456...
    
    CSV:
    Clase Matemáticas,https://zoom.us/rec/play/abc123...
    Clase Física,https://zoom.us/rec/play/def456...
    
    Proceso:
    1. Leer archivo con codificación UTF-8
    2. Detectar formato automáticamente (CSV vs TXT)
    3. Validar que las URLs sean de Zoom
    4. Sanitizar nombres de archivo
    5. Retornar lista procesada
    """
    urls = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
            
        if not content:
            print("El archivo está vacío")
            return []
        
        # Detectar formato automáticamente por presencia de comas
        if ',' in content:
            # Formato CSV: titulo,url
            lines = content.split('\n')
            for line in lines:
                if ',' in line:
                    # Dividir solo en la primera coma para permitir comas en títulos
                    parts = line.split(',', 1)
                    if len(parts) >= 2:
                        title = sanitize_filename(parts[0].strip())
                        url = parts[1].strip()
                        # Validar que sea URL de Zoom válida
                        if url.startswith('https://zoom.us/rec/'):
                            urls.append((title, url))
        else:
            # Formato TXT: una URL por línea
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('https://zoom.us/rec/'):
                    # Generar nombre automático si no hay título
                    title = f"video_{i+1}"
                    urls.append((title, line))
        
        return urls
        
    except FileNotFoundError:
        print(f"No se encontró el archivo: {file_path}")
        return []
    except Exception as e:
        print(f"Error leyendo el archivo: {e}")
        return []

def get_user_choice():
    """
    Mostrar menú interactivo para seleccionar tipo de descarga.
    
    Returns:
        str: Tipo de descarga seleccionado ('video', 'audio', 'transcript', 'all')
        
    Comportamiento:
    - En modo interactivo: muestra menú y espera entrada del usuario
    - En modo no interactivo (pipelines, scripts): retorna 'all' por defecto
    
    Opciones disponibles:
    1. video: Solo archivos MP4
    2. audio: Solo archivos MP3 (extraídos del video)
    3. transcript: Solo archivos SRT/VTT de transcripción
    4. all: Video + audio + transcripción
    """
    print("\n¿Qué deseas descargar?")
    print("1. Solo videos (MP4)")
    print("2. Solo audios (MP3)")
    print("3. Solo transcripciones (SRT)")
    print("4. Todo (video + audio + transcripción)")
    
    # Verificar si estamos en modo no interactivo (pipelines, automatización)
    if not sys.stdin.isatty():
        print("Modo no interactivo detectado, usando 'all' por defecto")
        return 'all'
    
    while True:
        try:
            choice = input("Elige una opción (1-4): ").strip()
            if choice == '1':
                return 'video'
            elif choice == '2':
                return 'audio'
            elif choice == '3':
                return 'transcript'
            elif choice == '4':
                return 'all'
            else:
                print("Opción no válida. Por favor, elige 1, 2, 3 o 4.")
        except EOFError:
            print("Modo no interactivo detectado, usando 'all' por defecto")
            return 'all'

def main():
    """
    Función principal del descargador masivo de Zoom.
    
    Uso:
    python3 batch_downloader.py <archivo_urls> [tipo]
    
    Args:
    - archivo_urls: Ruta al archivo TXT o CSV con URLs de Zoom
    - tipo (opcional): video, audio, transcript, all
    
    Flujo de ejecución:
    1. Validar argumentos de línea de comandos
    2. Verificar existencia del archivo
    3. Crear estructura de directorios
    4. Leer y procesar URLs del archivo
    5. Mostrar resumen de URLs encontradas
    6. Seleccionar tipo de descarga (interactivo o argumento)
    7. Confirmar descarga (modo interactivo)
    8. Procesar descargas una por una
    9. Mostrar estadísticas finales
    
    Ejemplos de uso:
    python3 batch_downloader.py input/urls.csv all
    python3 batch_downloader.py input/urls.txt video
    python3 batch_downloader.py input/urls.csv  # Interactivo
    """
    # Validar argumentos mínimos
    if len(sys.argv) < 2:
        print("Uso: python3 batch_downloader.py <archivo_urls> [tipo]")
        print("Formatos de archivo:")
        print("  TXT: una URL por línea")
        print("  CSV: titulo,url (dos columnas)")
        print("\nTipos disponibles: video, audio, transcript, all")
        print("Si no especificas tipo, se te preguntará interactivamente")
        sys.exit(1)
    
    file_path = sys.argv[1]
    download_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Verificar existencia del archivo
    if not os.path.exists(file_path):
        print(f"El archivo no existe: {file_path}")
        sys.exit(1)
    
    # Preparar entorno
    create_directories()
    
    # Leer URLs del archivo
    print(f"Leyendo URLs desde: {file_path}")
    urls = read_urls_from_file(file_path)
    
    if not urls:
        print("No se encontraron URLs válidas en el archivo")
        sys.exit(1)
    
    print(f"Se encontraron {len(urls)} URLs válidas")
    
    # Mostrar resumen de URLs (limitado para no saturar la salida)
    print("\nResumen de URLs encontradas:")
    for i, (title, url) in enumerate(urls[:5]):  # Mostrar solo las primeras 5
        video_id = extract_video_id(url)
        if video_id:
            print(f"  {i+1}. {title} -> {video_id[:20]}...")
        else:
            print(f"  {i+1}. {title} -> URL inválida")
    
    if len(urls) > 5:
        print(f"  ... y {len(urls) - 5} más")
    
    # Determinar tipo de descarga
    if not download_type:
        download_type = get_user_choice()
    elif download_type not in ['video', 'audio', 'transcript', 'all']:
        print(f"Error: tipo '{download_type}' no válido. Usa: video, audio, transcript, all")
        sys.exit(1)
    
    # Confirmar descarga en modo interactivo
    print(f"\nSe descargarán {len(urls)} archivos en formato: {download_type}")
    
    if not sys.stdin.isatty():
        print("Iniciando descarga automática (modo no interactivo)...")
    else:
        try:
            confirm = input("¿Continuar? (s/N): ").strip().lower()
            if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
                print("Descarga cancelada")
                sys.exit(0)
        except EOFError:
            print("Iniciando descarga automática (modo no interactivo)...")
    
    # Ejecutar descargas masivas
    print(f"\nIniciando descarga masiva ({download_type})...")
    print("=" * 50)
    
    successful = 0
    failed = 0
    
    for i, (title, url) in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Procesando: {title}")
        
        if download_with_yt_dlp(url, download_type, title):
            successful += 1
        else:
            failed += 1
            print(f"  Falló la descarga de: {title}")
    
    # Mostrar estadísticas finales
    print("\n" + "=" * 50)
    print("RESUMEN DE DESCARGA:")
    print(f"  Exitosas: {successful}")
    print(f"  Fallidas: {failed}")
    print(f"  Total procesadas: {len(urls)}")
    
    if successful > 0:
        print(f"\nLos archivos se guardaron en:")
        if download_type in ['video', 'all']:
            print(f"  Videos: downloads/MP4/")
        if download_type in ['audio', 'all']:
            print(f"  Audios: downloads/MP3/")
        if download_type in ['transcript', 'all']:
            print(f"  Transcripciones: downloads/SRT/")

if __name__ == "__main__":
    main()