#!/usr/bin/env python3
"""
Interfaz interactiva de Zoom Video Downloader
==============================================

Menu grafico en terminal para descargar grabaciones de Zoom.
Esta interfaz proporciona una experiencia de usuario amigable
sin necesidad de usar la linea de comandos.

Caracteristicas:
- Menu interactivo con navegacion por numeros
- Explorador de archivos en carpeta input/
- Vista previa de URLs antes de descargar
- Seleccion de tipo de descarga (video, audio, transcript, all)
- Monitoreo de descargas en tiempo real
- Estadisticas de descargas completadas
- Limpieza de archivos temporales

Uso:
    python3 main.py

Dependencias:
    - core.py: nucleo con funciones compartidas
    - simple_zoom_downloader.py: descarga individual
    - batch_downloader.py: descarga masiva

Autor: Zoom Video Downloader
Version: 2.0.0
Licencia: MIT
"""

import os
import sys
import subprocess
import glob
from pathlib import Path


class ZoomDownloaderInterface:
    """
    Clase principal de la interfaz interactiva.

    Maneja toda la interaccion con el usuario a traves
    de menus en terminal, incluyendo navegacion,
    seleccion de opciones y visualizacion de resultados.

    Atributos:
        input_dir (str): Carpeta con archivos de entrada (URLs)
        downloads_dir (str): Carpeta principal de descargas

    Ejemplo:
        interface = ZoomDownloaderInterface()
        interface.run()
    """

    def __init__(self):
        """Inicializar la interfaz y crear directorios necesarios."""
        self.input_dir = "input"
        self.downloads_dir = "downloads"
        self.ensure_directories()

    def ensure_directories(self):
        """
        Crear estructura de directorios si no existen.

        Crea los siguientes directorios:
        - input/: archivos de entrada (URLs)
        - downloads/: carpeta principal
        - downloads/MP4/: videos descargados
        - downloads/MP3/: audios extraidos
        - downloads/SRT/: transcripciones
        """
        for directory in [
            self.input_dir,
            self.downloads_dir,
            "downloads/MP4",
            "downloads/MP3",
            "downloads/SRT",
        ]:
            os.makedirs(directory, exist_ok=True)

    def clear_screen(self):
        """Limpiar pantalla para mejor experiencia visual."""
        os.system("cls" if os.name == "nt" else "clear")

    def show_header(self):
        """Mostrar encabezado del programa."""
        print("=" * 60)
        print("     ZOOM VIDEO DOWNLOADER - INTERFAZ INTERACTIVA")
        print("=" * 60)
        print("Descarga grabaciones de Zoom de forma sencilla")
        print()

    def show_main_menu(self):
        """Mostrar menu principal con opciones disponibles."""
        print("MENU PRINCIPAL:")
        print("1. Descargar URL individual")
        print("2. Descargar desde archivo (masivo)")
        print("3. Ver archivos en carpeta input/")
        print("4. Ver estado de descargas")
        print("5. Limpiar archivos temporales")
        print("6. Ayuda")
        print("0. Salir")
        print()

    def get_user_choice(self, max_option):
        """
        Obtener eleccion del usuario con validacion.

        Args:
            max_option (int): Numero maximo de opcion valida

        Returns:
            int: Opcion seleccionada por el usuario

        Raises:
            KeyboardInterrupt: Si el usuario presiona Ctrl+C
        """
        while True:
            try:
                choice = input("Selecciona una opcion: ").strip()
                if choice.isdigit():
                    choice_num = int(choice)
                    if 0 <= choice_num <= max_option:
                        return choice_num
                    else:
                        print(f"Por favor, ingresa un numero entre 0 y {max_option}")
                else:
                    print("Por favor, ingresa un numero valido")
            except KeyboardInterrupt:
                print("\n\nSaliendo del programa...")
                sys.exit(0)

    def list_input_files(self):
        """
        Listar archivos disponibles en carpeta input/.

        Busca archivos con extension .txt y .csv que contengan
        URLs de Zoom para descarga masiva.

        Returns:
            list: Lista de rutas de archivos encontrados
        """
        print("\nARCHIVOS DISPONIBLES EN input/:")
        print("-" * 40)

        files = []
        extensions = ["*.txt", "*.csv"]

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
        """
        Mostrar vista previa del contenido del archivo.

        Args:
            file_path (str): Ruta del archivo a previsualizar
        """
        print(f"\nVISTA PREVIA DE {os.path.basename(file_path)}:")
        print("-" * 50)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            print(f"Total de lineas: {len(lines)}")
            print("\nPrimeras 5 lineas:")
            for i, line in enumerate(lines[:5], 1):
                print(f"{i}. {line.strip()}")

            if len(lines) > 5:
                print(f"... y {len(lines) - 5} lineas mas")

        except Exception as e:
            print(f"Error leyendo el archivo: {e}")

    def download_individual(self):
        """
        Menu para descargar una URL individual.

        Solicita al usuario:
        - URL de la grabacion de Zoom
        - Tipo de descarga (video, audio, transcript, all)
        - Nombre personalizado (opcional)
        """
        print("\nDESCARGA INDIVIDUAL")
        print("-" * 30)

        url = input("Ingresa la URL de Zoom: ").strip()
        if not url:
            print("URL no valida")
            return

        if not url.startswith("https://zoom.us/rec/"):
            print("Error: La URL debe ser de Zoom (https://zoom.us/rec/)")
            return

        print("\nTIPO DE DESCARGA:")
        print("1. Video (MP4)")
        print("2. Audio (MP3)")
        print("3. Transcripcion (SRT)")
        print("4. Todo (video + audio + transcripcion)")

        choice = self.get_user_choice(4)
        types = {1: "video", 2: "audio", 3: "transcript", 4: "all"}
        download_type = types[choice]

        custom_name = input("Nombre personalizado (opcional): ").strip()
        if not custom_name:
            custom_name = None

        print(f"\nIniciando descarga...")
        self.run_simple_downloader(url, download_type, custom_name)

    def download_from_file(self):
        """
        Menu para descargar desde archivo (batch).

        Permite seleccionar un archivo de la carpeta input/
        y descargar todas las URLs contenidas.
        """
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

        self.preview_file_content(selected_file)

        confirm = input("\nDeseas continuar con este archivo? (s/N): ").strip().lower()
        if confirm not in ["s", "si", "si", "y", "yes"]:
            return

        print("\nTIPO DE DESCARGA:")
        print("1. Video (MP4)")
        print("2. Audio (MP3)")
        print("3. Transcripcion (SRT)")
        print("4. Todo (video + audio + transcripcion)")

        choice = self.get_user_choice(4)
        types = {1: "video", 2: "audio", 3: "transcript", 4: "all"}
        download_type = types[choice]

        print(f"\nIniciando descarga masiva...")
        self.run_batch_downloader(selected_file, download_type)

    def show_download_status(self):
        """
        Mostrar estado actual de las descargas.

        Presenta:
        - Numero de archivos por tipo (MP4, MP3, SRT)
        - Tamano total de descargas
        - Archivos mas recientes
        """
        print("\nESTADO DE DESCARGAS")
        print("-" * 30)

        if not os.path.exists(self.downloads_dir):
            print("No hay descargas realizadas")
            return

        mp4_count = len(glob.glob("downloads/MP4/*.mp4"))
        mp3_count = len(glob.glob("downloads/MP3/*.mp3"))
        srt_count = len(glob.glob("downloads/SRT/*.{srt,vtt}"))

        print(f"Videos (MP4): {mp4_count} archivos")
        print(f"Audios (MP3): {mp3_count} archivos")
        print(f"Transcripciones: {srt_count} archivos")

        try:
            total_size = (
                subprocess.check_output(
                    ["du", "-sh", self.downloads_dir], stderr=subprocess.DEVNULL
                )
                .decode()
                .split()[0]
            )
            print(f"Tamano total: {total_size}")
        except Exception:
            pass

        print("\nARCHIVOS RECIENTES:")
        try:
            result = subprocess.run(
                [
                    "find",
                    self.downloads_dir,
                    "-type",
                    "f",
                    "-printf",
                    "%TY-%Tm-%Td %TH:%TM %p\n",
                ],
                capture_output=True,
                text=True,
            )
            if result.stdout:
                lines = result.stdout.strip().split("\n")[:5]
                for line in lines:
                    print(f"  {line}")
        except Exception:
            pass

    def clean_temp_files(self):
        """
        Menu para limpiar archivos temporales.

        Elimina:
        - Archivos .part (descargas incompletas)
        - Entorno virtual si existe
        """
        print("\nLIMPIEZA DE ARCHIVOS")
        print("-" * 25)

        confirm = input("Eliminar archivos temporales? (s/N): ").strip().lower()
        if confirm not in ["s", "si", "si", "y", "yes"]:
            return

        part_files = glob.glob("downloads/**/*.part", recursive=True)
        for file in part_files:
            os.remove(file)

        print(f"Eliminados {len(part_files)} archivos .part")

        if os.path.exists("venv"):
            subprocess.run(["rm", "-rf", "venv"])
            print("Eliminado entorno virtual")

        print("Limpieza completada")

    def show_help(self):
        """
        Mostrar ayuda con informacion de uso.

        Incluye:
        - Formatos de archivo soportados
        - Ejemplos de archivos de entrada
        - Tipos de descarga disponibles
        - Dependencias del sistema
        """
        print("\nAYUDA - ZOOM VIDEO DOWNLOADER")
        print("=" * 40)
        print()
        print("FORMATOS DE ARCHIVO SOPORTADOS:")
        print("- TXT: una URL de Zoom por linea")
        print("- CSV: titulo,url (dos columnas separadas por coma)")
        print()
        print("EJEMPLOS:")
        print("Archivo TXT:")
        print("  https://zoom.us/rec/play/abc123...")
        print("  https://zoom.us/rec/play/def456...")
        print()
        print("Archivo CSV:")
        print("  Clase Matematicas,https://zoom.us/rec/play/abc123...")
        print("  Clase Fisica,https://zoom.us/rec/play/def456...")
        print()
        print("TIPOS DE DESCARGA:")
        print("- video: Solo el archivo de video (MP4)")
        print("- audio: Solo el archivo de audio (MP3)")
        print("- transcript: Solo la transcripcion (SRT/VTT)")
        print("- all: Video + audio + transcripcion")
        print()
        print("DEPENDENCIAS:")
        print("El programa instalara automaticamente:")
        print("- yt-dlp: para descargar desde Zoom")
        print("- ffmpeg: para convertir video a audio")
        print()

    def run_simple_downloader(self, url, download_type, custom_name=None):
        """
        Ejecutar el descargador individual.

        Args:
            url (str): URL de la grabacion de Zoom
            download_type (str): Tipo de descarga
            custom_name (str, optional): Nombre personalizado
        """
        cmd = ["python3", "simple_zoom_downloader.py", url, download_type]
        if custom_name:
            cmd.append(custom_name)

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print("Error en la descarga")
        except FileNotFoundError:
            print("Error: No se encuentra simple_zoom_downloader.py")

    def run_batch_downloader(self, file_path, download_type):
        """
        Ejecutar el descargador masivo.

        Args:
            file_path (str): Ruta del archivo con URLs
            download_type (str): Tipo de descarga
        """
        cmd = ["python3", "batch_downloader.py", file_path, download_type]

        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            print("Error en la descarga masiva")
        except FileNotFoundError:
            print("Error: No se encuentra batch_downloader.py")

    def run(self):
        """
        Bucle principal de la interfaz.

        Maneja el ciclo de menu:
        1. Mostrar menu
        2. Obtener eleccion
        3. Ejecutar accion
        4. Esperar Enter para continuar
        """
        while True:
            self.clear_screen()
            self.show_header()
            self.show_main_menu()

            choice = self.get_user_choice(6)

            if choice == 0:
                print("\nGracias por usar Zoom Video Downloader!")
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
    """
    Funcion principal de entrada.

    Inicializa la interfaz y maneja excepciones globales.

    Excepciones manejadas:
        KeyboardInterrupt: Ctrl+C para salir
        Exception: Cualquier otro error inesperado
    """
    try:
        interface = ZoomDownloaderInterface()
        interface.run()
    except KeyboardInterrupt:
        print("\n\nPrograma interrumpido. Hasta pronto!")
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
