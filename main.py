#!/usr/bin/env python3
"""
Zoom Video Downloader - Interactive Interface
=============================================

Interfaz interactiva para descargar grabaciones de Zoom.
Reemplaza al script start.sh con una experiencia más amigable.

Características:
- Menú interactivo con navegación por números
- Explorador de archivos en carpeta input/
- Vista previa de URLs antes de descargar
- Selección de tipo de descarga (video, audio, transcript, all)
- Monitoreo de descargas en tiempo real
- Estadísticas de descargas completadas

Author: 686f6c61
Project: zoom-video-downloader
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

class ZoomDownloaderInterface:
    def __init__(self):
        self.input_dir = "input"
        self.downloads_dir = "downloads"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Crear directorios necesarios si no existen"""
        for directory in [self.input_dir, self.downloads_dir, "downloads/MP4", "downloads/MP3", "downloads/SRT"]:
            os.makedirs(directory, exist_ok=True)
    
    def clear_screen(self):
        """Limpiar pantalla para mejor experiencia"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_header(self):
        """Mostrar encabezado del programa"""
        print("=" * 60)
        print("     ZOOM VIDEO DOWNLOADER - INTERFAZ INTERACTIVA")
        print("=" * 60)
        print("Descarga grabaciones de Zoom de forma sencilla")
        print()
    
    def show_main_menu(self):
        """Mostrar menú principal"""
        print("MENÚ PRINCIPAL:")
        print("1. Descargar URL individual")
        print("2. Descargar desde archivo (masivo)")
        print("3. Ver archivos en carpeta input/")
        print("4. Ver estado de descargas")
        print("5. Limpiar archivos temporales")
        print("6. Ayuda")
        print("0. Salir")
        print()
    
    def get_user_choice(self, max_option):
        """Obtener elección del usuario con validación"""
        while True:
            try:
                choice = input("Selecciona una opción: ").strip()
                if choice.isdigit():
                    choice_num = int(choice)
                    if 0 <= choice_num <= max_option:
                        return choice_num
                    else:
                        print(f"Por favor, ingresa un número entre 0 y {max_option}")
                else:
                    print("Por favor, ingresa un número válido")
            except KeyboardInterrupt:
                print("\n\nSaliendo del programa...")
                sys.exit(0)
    
    def list_input_files(self):
        """Listar archivos disponibles en carpeta input/"""
        print("\nARCHIVOS DISPONIBLES EN input/:")
        print("-" * 40)
        
        files = []
        extensions = ['*.txt', '*.csv']
        
        for ext in extensions:
            files.extend(glob.glob(os.path.join(self.input_dir, ext)))
        
        if not files:
            print("No hay archivos .txt o .csv en la carpeta input/")
            print("Puedes crear archivos con URLs de Zoom para descargar")
            return []
        
        for i, file in enumerate(files, 1):
            file_size = os.path.getsize(file)
            print(f"{i}. {os.path.basename(file)} ({file_size} bytes)")
        
        return files
    
    def preview_file_content(self, file_path):
        """Mostrar vista previa del contenido del archivo"""
        print(f"\nVISTA PREVIA DE {os.path.basename(file_path)}:")
        print("-" * 50)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            print(f"Total de líneas: {len(lines)}")
            print("\nPrimeras 5 líneas:")
            for i, line in enumerate(lines[:5], 1):
                print(f"{i}. {line.strip()}")
            
            if len(lines) > 5:
                print(f"... y {len(lines) - 5} líneas más")
                
        except Exception as e:
            print(f"Error leyendo el archivo: {e}")
    
    def download_individual(self):
        """Descargar una URL individual"""
        print("\nDESCARGA INDIVIDUAL")
        print("-" * 30)
        
        url = input("Ingresa la URL de Zoom: ").strip()
        if not url:
            print("URL no válida")
            return
        
        if not url.startswith('https://zoom.us/rec/'):
            print("Error: La URL debe ser de Zoom (https://zoom.us/rec/...)")
            return
        
        print("\nTIPO DE DESCARGA:")
        print("1. Video (MP4)")
        print("2. Audio (MP3)")
        print("3. Transcripción (SRT)")
        print("4. Todo (video + audio + transcripción)")
        
        choice = self.get_user_choice(4)
        types = {1: 'video', 2: 'audio', 3: 'transcript', 4: 'all'}
        download_type = types[choice]
        
        custom_name = input("Nombre personalizado (opcional): ").strip()
        if not custom_name:
            custom_name = None
        
        print(f"\nIniciando descarga...")
        self.run_simple_downloader(url, download_type, custom_name)
    
    def download_from_file(self):
        """Descargar desde archivo"""
        print("\nDESCARGA MASIVA DESDE ARCHIVO")
        print("-" * 40)
        
        files = self.list_input_files()
        if not files:
            return
        
        print(f"\nSelecciona un archivo (1-{len(files)}):")
        choice = self.get_user_choice(len(files))
        
        if choice == 0:
            return
        
        selected_file = files[choice - 1]
        
        # Mostrar vista previa
        self.preview_file_content(selected_file)
        
        confirm = input("\n¿Deseas continuar con este archivo? (s/N): ").strip().lower()
        if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
            return
        
        print("\nTIPO DE DESCARGA:")
        print("1. Video (MP4)")
        print("2. Audio (MP3)")
        print("3. Transcripción (SRT)")
        print("4. Todo (video + audio + transcripción)")
        
        choice = self.get_user_choice(4)
        types = {1: 'video', 2: 'audio', 3: 'transcript', 4: 'all'}
        download_type = types[choice]
        
        print(f"\nIniciando descarga masiva...")
        self.run_batch_downloader(selected_file, download_type)
    
    def show_download_status(self):
        """Mostrar estado de descargas"""
        print("\nESTADO DE DESCARGAS")
        print("-" * 30)
        
        if not os.path.exists(self.downloads_dir):
            print("No hay descargas realizadas")
            return
        
        # Contar archivos por tipo
        mp4_count = len(glob.glob("downloads/MP4/*.mp4"))
        mp3_count = len(glob.glob("downloads/MP3/*.mp3"))
        srt_count = len(glob.glob("downloads/SRT/*.{srt,vtt}"))
        
        print(f"Videos (MP4): {mp4_count} archivos")
        print(f"Audios (MP3): {mp3_count} archivos")
        print(f"Transcripciones: {srt_count} archivos")
        
        # Calcular tamaño total
        try:
            total_size = subprocess.check_output(['du', '-sh', self.downloads_dir], 
                                               stderr=subprocess.DEVNULL).decode().split()[0]
            print(f"Tamaño total: {total_size}")
        except:
            pass
        
        # Mostrar archivos recientes
        print("\nARCHIVOS RECIENTES:")
        try:
            result = subprocess.run(['find', self.downloads_dir, '-type', 'f', '-printf', '%TY-%Tm-%Td %TH:%TM %p\n'], 
                                  capture_output=True, text=True)
            if result.stdout:
                lines = result.stdout.strip().split('\n')[:5]
                for line in lines:
                    print(f"  {line}")
        except:
            pass
    
    def clean_temp_files(self):
        """Limpiar archivos temporales"""
        print("\nLIMPIEZA DE ARCHIVOS")
        print("-" * 25)
        
        confirm = input("¿Eliminar archivos temporales? (s/N): ").strip().lower()
        if confirm not in ['s', 'si', 'sí', 'y', 'yes']:
            return
        
        # Eliminar archivos .part
        part_files = glob.glob("downloads/**/*.part", recursive=True)
        for file in part_files:
            os.remove(file)
        
        print(f"Eliminados {len(part_files)} archivos .part")
        
        # Eliminar entorno virtual si existe
        if os.path.exists("venv"):
            subprocess.run(['rm', '-rf', 'venv'])
            print("Eliminado entorno virtual")
        
        print("Limpieza completada")
    
    def show_help(self):
        """Mostrar ayuda"""
        print("\nAYUDA - ZOOM VIDEO DOWNLOADER")
        print("=" * 40)
        print()
        print("FORMATOS DE ARCHIVO SOPORTADOS:")
        print("- TXT: una URL de Zoom por línea")
        print("- CSV: titulo,url (dos columnas separadas por coma)")
        print()
        print("EJEMPLOS:")
        print("Archivo TXT:")
        print("  https://zoom.us/rec/play/abc123...")
        print("  https://zoom.us/rec/play/def456...")
        print()
        print("Archivo CSV:")
        print("  Clase Matemáticas,https://zoom.us/rec/play/abc123...")
        print("  Clase Física,https://zoom.us/rec/play/def456...")
        print()
        print("TIPOS DE DESCARGA:")
        print("- video: Solo el archivo de video (MP4)")
        print("- audio: Solo el archivo de audio (MP3)")
        print("- transcript: Solo la transcripción (SRT/VTT)")
        print("- all: Video + audio + transcripción")
        print()
        print("DEPENDENCIAS:")
        print("El programa instalará automáticamente:")
        print("- yt-dlp: para descargar desde Zoom")
        print("- ffmpeg: para convertir video a audio")
        print()
    
    def run_simple_downloader(self, url, download_type, custom_name=None):
        """Ejecutar descargador individual"""
        cmd = ['python3', 'simple_zoom_downloader.py', url, download_type]
        if custom_name:
            cmd.append(custom_name)
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print("Error en la descarga")
        except FileNotFoundError:
            print("Error: No se encuentra simple_zoom_downloader.py")
    
    def run_batch_downloader(self, file_path, download_type):
        """Ejecutar descargador masivo"""
        cmd = ['python3', 'batch_downloader.py', file_path, download_type]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print("Error en la descarga masiva")
        except FileNotFoundError:
            print("Error: No se encuentra batch_downloader.py")
    
    def run(self):
        """Ejecutar interfaz principal"""
        while True:
            self.clear_screen()
            self.show_header()
            self.show_main_menu()
            
            choice = self.get_user_choice(6)
            
            if choice == 0:
                print("\n¡Gracias por usar Zoom Video Downloader!")
                break
            elif choice == 1:
                self.download_individual()
            elif choice == 2:
                self.download_from_file()
            elif choice == 3:
                self.list_input_files()
            elif choice == 4:
                self.show_download_status()
            elif choice == 5:
                self.clean_temp_files()
            elif choice == 6:
                self.show_help()
            
            if choice != 0:
                input("\nPresiona Enter para continuar...")

def main():
    """Función principal"""
    try:
        interface = ZoomDownloaderInterface()
        interface.run()
    except KeyboardInterrupt:
        print("\n\nPrograma interrumpido. ¡Hasta pronto!")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()