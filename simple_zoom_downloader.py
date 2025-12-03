#!/usr/bin/env python3
"""
Zoom Video Downloader - Individual Downloads
=============================================

Script para descargar grabaciones individuales de Zoom en diferentes formatos.
Ideal para descargas únicas o pruebas rápidas.

Características:
- Descarga de URLs individuales de Zoom
- Soporte para video (MP4), audio (MP3) y transcripciones (SRT)
- Nombres de archivo personalizados
- Múltiples métodos de descarga (yt-dlp + requests directo)
- Instalación automática de dependencias
- Conversión automática video → audio

Uso: python3 simple_zoom_downloader.py <URL_ZOOM> [tipo] [nombre]
Tipos: video, audio, transcript, all
Nombre: opcional, para personalizar el archivo de salida

Author: 686f6c61
Project: zoom-video-downloader
"""

import requests
import re
import os
import sys
import subprocess
from urllib.parse import urlparse, parse_qs

def install_chrome():
    """
    Verificar e instalar Chrome/Chromium si no está disponible.
    
    Chrome/Chromium puede ser necesario para algunos métodos de descarga
    que requieren renderizado de JavaScript o headers específicos.
    
    Returns:
        bool: True si Chrome/Chromium está disponible o se instaló correctamente
        
    Nota:
    - Esta función es principalmente para métodos alternativos de descarga
    - yt-dlp generalmente no requiere Chrome para Zoom
    - Solo compatible con sistemas basados en Debian/Ubuntu
    """
    try:
        # Verificar si Google Chrome está instalado
        subprocess.run(['google-chrome', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            # Verificar si Chromium está instalado (alternativa open source)
            subprocess.run(['chromium-browser', '--version'], check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Chrome/Chromium no encontrado. Intentando instalar...")
            try:
                # Para Ubuntu/Debian - instalar Chromium
                subprocess.run(['sudo', 'apt', 'update'], check=True)
                subprocess.run(['sudo', 'apt', 'install', '-y', 'chromium-browser'], check=True)
                return True
            except subprocess.CalledProcessError:
                print("No se pudo instalar Chrome/Chromium automáticamente")
                return False

def extract_video_id(zoom_url):
    """
    Extraer el ID único de la grabación desde la URL de Zoom.
    
    Args:
        zoom_url (str): URL completa de la grabación de Zoom
        
    Returns:
        str or None: ID de la grabación o None si no se encuentra
        
    El ID es el identificador único que Zoom asigna a cada grabación
    y se usa para generar nombres de archivo y para el proceso de descarga.
    """
    match = re.search(r'/rec/play/([^?]+)', zoom_url)
    return match.group(1) if match else None

def install_ffmpeg():
    """
    Verificar e instalar ffmpeg si no está disponible en el sistema.
    
    ffmpeg es esencial para convertir videos MP4 a audio MP3 cuando se solicita
    el tipo de descarga 'audio' o 'all'.
    
    Returns:
        bool: True si ffmpeg está disponible o se instaló correctamente
        
    Proceso:
    1. Verificar si ffmpeg ya está instalado
    2. Si no está, intentar instalarlo automáticamente
    3. Requiere privilegios de sudo para la instalación
    """
    try:
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Instalando ffmpeg...")
        try:
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'ffmpeg'], check=True)
            return True
        except subprocess.CalledProcessError:
            print("No se pudo instalar ffmpeg automáticamente")
            return False

def convert_to_mp3(input_file, output_file):
    """
    Convertir archivo de video MP4 a audio MP3 usando ffmpeg.
    
    Esta función se utiliza cuando el usuario solicita descarga de audio
    o cuando selecciona 'all' (descargar todo).
    
    Args:
        input_file (str): Ruta del archivo de video MP4 de entrada
        output_file (str): Ruta del archivo de audio MP3 de salida
        
    Returns:
        bool: True si la conversión fue exitosa, False en caso contrario
        
    Parámetros de ffmpeg utilizados:
    - -q:a 0: Calidad de audio máxima (VBR 0)
    - -map a: Extraer solo el stream de audio, ignorando video
    """
    try:
        if not install_ffmpeg():
            return False
            
        print(f"Convirtiendo {input_file} a MP3...")
        cmd = [
            'ffmpeg',
            '-i', input_file,        # Archivo de entrada
            '-q:a', '0',             # Calidad de audio máxima
            '-map', 'a',             # Mapear solo audio
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
    Descargar contenido de Zoom utilizando yt-dlp como método principal.
    
    yt-dlp es la herramienta más confiable para descargar grabaciones de Zoom
    ya que está específicamente diseñada para extraer contenido de plataformas
    de video y streaming.
    
    Args:
        zoom_url (str): URL de la grabación de Zoom
        download_type (str): Tipo de descarga ('video', 'audio', 'transcript', 'all')
        custom_name (str, optional): Nombre personalizado para el archivo
        
    Returns:
        str or None: Ruta del archivo descargado o None si falló
        
    Estrategia de descarga:
    1. Verificar/instalar yt-dlp si no está disponible
    2. Extraer ID del video para generar nombres de archivo
    3. Construir comando específico según tipo de contenido
    4. Ejecutar yt-dlp con parámetros optimizados
    5. Si es 'all', convertir video a audio adicionalmente
    """
    try:
        print(f"Intentando descargar {download_type} con yt-dlp...")
        
        # Verificar si yt-dlp está instalado
        try:
            subprocess.run(['yt-dlp', '--version'], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Instalando yt-dlp...")
            subprocess.run(['pip', 'install', 'yt-dlp'], check=True)
        
        # Generar nombre base para archivos
        video_id = extract_video_id(zoom_url)
        safe_id = video_id[:20] if video_id else "recording"
        base_name = custom_name if custom_name else safe_id
        
        output_template = None
        cmd = None
        
        # Construir comando según tipo de descarga
        if download_type == 'video':
            output_template = f"downloads/MP4/{base_name}.mp4"
            cmd = [
                'yt-dlp',
                '--no-warnings',
                '--format', 'best[ext=mp4]/best',
                '--output', output_template,
                zoom_url
            ]
        elif download_type == 'audio':
            output_template = f"downloads/MP3/{base_name}.mp3"
            cmd = [
                'yt-dlp',
                '--no-warnings',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--output', f"downloads/MP3/{base_name}.%(ext)s",
                zoom_url
            ]
        elif download_type == 'transcript':
            output_template = f"downloads/SRT/{base_name}"
            cmd = [
                'yt-dlp',
                '--no-warnings',
                '--write-subs',
                '--write-auto-subs',
                '--sub-langs', 'all',
                '--skip-download',
                '--output', output_template,
                zoom_url
            ]
        elif download_type == 'all':
            output_template = f"downloads/MP4/{base_name}.mp4"
            cmd = [
                'yt-dlp',
                '--no-warnings',
                '--format', 'best[ext=mp4]/best',
                '--write-subs',
                '--write-auto-subs',
                '--sub-langs', 'all',
                '--output', output_template,
                zoom_url
            ]
        
        if not cmd or not output_template:
            print(f"Tipo de descarga no válido: {download_type}")
            return None
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"Descarga completada con yt-dlp ({download_type})")
            
            # Si se descargó video y se pidió 'all', convertir también a MP3
            if download_type == 'all':
                video_file = f"downloads/MP4/{base_name}.mp4"
                if os.path.exists(video_file):
                    audio_file = f"downloads/MP3/{base_name}.mp3"
                    convert_to_mp3(video_file, audio_file)
            
            return output_template
        else:
            print(f"Error con yt-dlp: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error con yt-dlp: {e}")
        return None

def download_with_requests(zoom_url, custom_name=None):
    """
    Método alternativo de descarga usando requests directamente.
    
    Este método intenta descargar el video analizando el HTML de la página
    de Zoom y extrayendo las URLs directas de los archivos de video.
    
    Args:
        zoom_url (str): URL de la grabación de Zoom
        custom_name (str, optional): Nombre personalizado para el archivo
        
    Returns:
        str or None: Ruta del archivo descargado o None si falló
        
    Proceso:
    1. Hacer request a la URL de Zoom con headers realistas
    2. Analizar el HTML buscando URLs directas de video
    3. Descargar el video desde la URL encontrada
    4. Guardar en el directorio correspondiente
    
    Nota:
    - Este método es menos confiable que yt-dlp
    - Se usa como fallback cuando yt-dlp falla
    - Solo funciona para descarga de video, no audio o transcripciones
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://zoom.us/'
    }
    
    try:
        print("Intentando descarga directa...")
        response = requests.get(zoom_url, headers=headers)
        response.raise_for_status()
        
        # Patrones para buscar URLs de video en el HTML
        video_patterns = [
            r'https://[^"\s]+\.mp4[^"\s]*',
            r'"url":"([^"]+\.mp4[^"]*)"',
            r'"videoUrl":"([^"]+\.mp4[^"]*)"',
            r'"downloadUrl":"([^"]+\.mp4[^"]*)"',
            r'src=["\']([^"\']*\.mp4[^"\']*)["\']',
            r'data-src=["\']([^"\']*\.mp4[^"\']*)["\']'
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, response.text)
            if matches:
                video_url = matches[0] if isinstance(matches[0], str) else matches[0][0]
                video_url = video_url.replace('\\/', '/').replace('\\', '')
                print(f"URL encontrada: {video_url}")
                
                # Descargar el video directamente
                video_response = requests.get(video_url, headers=headers, stream=True)
                video_response.raise_for_status()
                
                # Generar nombre de archivo
                video_id = extract_video_id(zoom_url)
                safe_id = video_id[:20] if video_id else "recording"
                base_name = custom_name if custom_name else safe_id
                output_filename = f"downloads/MP4/{base_name}.mp4"
                
                # Descargar en chunks para manejar archivos grandes
                with open(output_filename, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                print(f"Video descargado: {output_filename}")
                return output_filename
        
        return None
        
    except Exception as e:
        print(f"Error en descarga directa: {e}")
        return None

def get_user_choice():
    """
    Mostrar menú interactivo para seleccionar tipo de descarga.
    
    Returns:
        str: Tipo de descarga seleccionado ('video', 'audio', 'transcript', 'all')
        
    Este menú se muestra cuando el usuario no especifica el tipo
    de descarga como argumento en la línea de comandos.
    """
    print("\n¿Qué deseas descargar?")
    print("1. Solo el video (MP4)")
    print("2. Solo el audio (MP3)")
    print("3. Solo la transcripción (SRT)")
    print("4. Todo (video + audio + transcripción)")
    
    while True:
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

def create_directories():
    """
    Crear estructura de directorios para organizar las descargas.
    
    Crea los directorios necesarios si no existen:
    - downloads/: Directorio principal
    - downloads/MP4/: Para archivos de video
    - downloads/MP3/: Para archivos de audio  
    - downloads/SRT/: Para transcripciones
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
    2. Limita la longitud para evitar problemas del sistema
    """
    import re
    # Reemplazar caracteres inválidos en Windows/Linux/Mac
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limitar longitud
    if len(filename) > 50:
        filename = filename[:50]
    return filename

def main():
    """
    Función principal del descargador individual de Zoom.
    
    Uso:
    python3 simple_zoom_downloader.py <URL_ZOOM> [tipo] [nombre]
    
    Args:
    - URL_ZOOM: URL completa de la grabación de Zoom
    - tipo (opcional): video, audio, transcript, all
    - nombre (opcional): Nombre personalizado para el archivo
    
    Estrategia de descarga:
    1. Validar argumentos y URL
    2. Crear estructura de directorios
    3. Sanitizar nombre personalizado si se proporciona
    4. Seleccionar tipo de descarga (interactivo o argumento)
    5. Intentar descarga con yt-dlp (método principal)
    6. Si falla, intentar descarga directa con requests
    7. Mostrar resultados y estadísticas
    
    Ejemplos:
    python3 simple_zoom_downloader.py https://zoom.us/rec/play/... video
    python3 simple_zoom_downloader.py https://zoom.us/rec/play/... all "Mi_Clase"
    python3 simple_zoom_downloader.py https://zoom.us/rec/play/...  # Interactivo
    """
    if len(sys.argv) < 2:
        print("Uso: python3 simple_zoom_downloader.py <URL_ZOOM> [tipo] [nombre]")
        print("Tipos disponibles: video, audio, transcript, all")
        print("Si no especificas tipo, se te preguntará interactivamente")
        print("Opcional: puedes especificar un nombre personalizado")
        sys.exit(1)
    
    zoom_url = sys.argv[1]
    download_type = sys.argv[2] if len(sys.argv) > 2 else None
    custom_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Preparar entorno
    create_directories()
    
    # Sanitizar nombre personalizado si se proporcionó
    if custom_name:
        custom_name = sanitize_filename(custom_name)
    
    # Validar URL de Zoom
    if not zoom_url.startswith('https://zoom.us/rec/'):
        print("Error: URL de Zoom no válida")
        sys.exit(1)
    
    # Determinar tipo de descarga
    if not download_type:
        download_type = get_user_choice()
    elif download_type not in ['video', 'audio', 'transcript', 'all']:
        print(f"Error: tipo '{download_type}' no válido. Usa: video, audio, transcript, all")
        sys.exit(1)
    
    print(f"\nIniciando descarga de grabación de Zoom (tipo: {download_type})...")
    
    # Método 1: Intentar con yt-dlp (método principal y más confiable)
    result = download_with_yt_dlp(zoom_url, download_type, custom_name)
    if result:
        print("¡Descarga completada!")
        
        # Mostrar archivos descargados con sus tamaños
        video_id = extract_video_id(zoom_url)
        safe_id = video_id[:20] if video_id else "recording"
        base_name = custom_name if custom_name else safe_id
        
        if download_type in ['video', 'all']:
            video_file = f"downloads/MP4/{base_name}.mp4"
            if os.path.exists(video_file):
                size_mb = os.path.getsize(video_file) / (1024 * 1024)
                print(f"Video: {video_file} ({size_mb:.1f} MB)")
        
        if download_type in ['audio', 'all']:
            audio_file = f"downloads/MP3/{base_name}.mp3"
            if os.path.exists(audio_file):
                size_mb = os.path.getsize(audio_file) / (1024 * 1024)
                print(f"Audio: {audio_file} ({size_mb:.1f} MB)")
        
        if download_type in ['transcript', 'all']:
            # Buscar archivos de transcripción (pueden ser .vtt o .srt)
            import glob
            transcript_files = glob.glob(f"downloads/SRT/{base_name}*.vtt") + glob.glob(f"downloads/SRT/{base_name}*.srt")
            for transcript_file in transcript_files:
                size_kb = os.path.getsize(transcript_file) / 1024
                print(f"Transcripción: {transcript_file} ({size_kb:.1f} KB)")
        
        return
    
    # Método 2: Intentar descarga directa (fallback, solo para video)
    if download_type in ['video', 'all']:
        result = download_with_requests(zoom_url, custom_name)
        if result:
            print("¡Descarga completada!")
            
            # Si se pidió 'all', convertir video a audio
            if download_type == 'all':
                video_id = extract_video_id(zoom_url)
                safe_id = video_id[:20] if video_id else "recording"
                base_name = custom_name if custom_name else safe_id
                video_file = f"downloads/MP4/{base_name}.mp4"
                if os.path.exists(video_file):
                    audio_file = f"downloads/MP3/{base_name}.mp3"
                    convert_to_mp3(video_file, audio_file)
            
            return
    
    # Si ambos métodos fallaron, mostrar sugerencias
    print("No se pudo descargar el contenido con los métodos disponibles.")
    print("Sugerencias:")
    print("1. Verifica que la URL sea correcta y accesible")
    print("2. Asegúrate de tener permisos para acceder a la grabación")
    print("3. Intenta acceder a la URL en tu navegador primero")
    print("4. Si la grabación requiere autenticación, necesitarás iniciar sesión")
    print("5. Para transcripciones, asegúrate de que la grabación tenga subtítulos disponibles")

if __name__ == "__main__":
    main()