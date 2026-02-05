#!/usr/bin/env python3
"""
Nucleo comun de Zoom Video Downloader
=====================================

Este modulo contiene funciones compartidas por todos los scripts
de descarga de grabaciones de Zoom.

Funcionalidades:
- Instalacion automatica de dependencias
- Conversion de video a audio
- Sanitizacion de nombres de archivo
- Extraccion de IDs de video
- Validacion de URLs
- Sistema de logging
- Reintentos con backoff exponencial
- Barra de progreso visual
- Conversiones de formato

Autor: Zoom Video Downloader
Version: 2.0.0
"""

import os
import sys
import re
import time
import yaml
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
from urllib.parse import urlparse


def cargar_configuracion(ruta_archivo: str = "config.yaml") -> Dict[str, Any]:
    """
    Cargar configuracion desde archivo YAML.

    Args:
        ruta_archivo: Ruta al archivo de configuracion (por defecto config.yaml)

    Returns:
        Dict con la configuracion cargada o valores por defecto si no existe
    """
    config_predeterminada = {
        "descargas": {
            "directorio_base": "downloads",
            "video": "MP4",
            "audio": "MP3",
            "transcripcion": "SRT",
        },
        "video": {
            "formato_preferido": "mp4",
            "calidad": "best",
            "convertir_audio": True,
            "formato_audio": "mp3",
            "calidad_audio": "0",
        },
        "transcripcion": {"idiomas": "all", "formatos_salida": ["vtt", "srt"]},
        "reintentos": {
            "maximos": 3,
            "intervalo_segundos": 5,
            "tiempo_espera_porcentaje": 0.1,
        },
        "logging": {
            "archivo": "downloads/descargas.log",
            "nivel": "INFO",
            "formato": "[%(asctime)s] %(levelname)s: %(message)s",
        },
        "interfaz": {"colores": True, "barra_progreso": True},
        "descarga": {
            "timeout_segundos": 300,
            "tamano_buffer": 8192,
            "reintentar_descargas_fallidas": True,
        },
    }

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config:
                config_predeterminada.update(config)
            return config_predeterminada
    except FileNotFoundError:
        return config_predeterminada
    except Exception as e:
        print(f"Error cargando configuracion: {e}")
        return config_predeterminada


def inicializar_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Inicializar sistema de logging.

    Args:
        config: Diccionario de configuracion

    Returns:
        Logger configurado
    """
    logger = logging.getLogger("zoom_downloader")

    nivel_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    nivel = nivel_map.get(config.get("logging", {}).get("nivel", "INFO"), logging.INFO)
    logger.setLevel(nivel)

    archivo_log = config.get("logging", {}).get("archivo", "downloads/descargas.log")
    formato = config.get("logging", {}).get(
        "formato", "[%(asctime)s] %(levelname)s: %(message)s"
    )

    fh = logging.FileHandler(archivo_log, encoding="utf-8")
    fh.setLevel(nivel)

    ch = logging.StreamHandler()
    ch.setLevel(nivel)

    formatter = logging.Formatter(formato)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


class Colores:
    """
    Codes de color para salida en terminal.
    """

    RESET = "\033[0m"
    NEGRITA = "\033[1m"
    SUBRAYADO = "\033[4m"

    NEGRO = "\033[30m"
    ROJO = "\033[31m"
    VERDE = "\033[32m"
    AMARILLO = "\033[33m"
    AZUL = "\033[34m"
    MAGENTA = "\033[35m"
    CIAN = "\033[36m"
    BLANCO = "\033[37m"

    FONDO_ROJO = "\033[41m"
    FONDO_VERDE = "\033[42m"
    FONDO_AMARILLO = "\033[43m"


def imprimir_texto(
    texto: str, color: str = "", logger: Optional[logging.Logger] = None
) -> None:
    """
    Imprimir texto con opcion de color.

    Args:
        texto: Texto a imprimir
        color: Code de color (opcional)
        logger: Logger para registrar (opcional)
    """
    print(f"{color}{texto}{Colores.RESET}")
    if logger:
        logger.info(texto)


def crear_directorios(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Crear estructura de directorios para descargas.

    Args:
        config: Diccionario de configuracion

    Returns:
        Dict con rutas de directorios creados
    """
    base = Path(config["descargas"]["directorio_base"])
    dirs = {
        "base": base,
        "video": base / config["descargas"]["video"],
        "audio": base / config["descargas"]["audio"],
        "transcripcion": base / config["descargas"]["transcripcion"],
    }

    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)

    return dirs


def sanitizar_nombre_archivo(nombre: str, limite: int = 50) -> str:
    """
    Sanitizar nombre de archivo para que sea valido en todos los sistemas operativos.

    Args:
        nombre: Nombre original
        limite: Longitud maxima permitida

    Returns:
        Nombre sanitizado
    """
    nombre_sanitizado = re.sub(r'[<>:"/\\|?*]', "_", nombre)
    nombre_sanitizado = re.sub(r"\s+", " ", nombre_sanitizado).strip()

    if len(nombre_sanitizado) > limite:
        nombre_sanitizado = nombre_sanitizado[:limite].strip()

    return nombre_sanitizado if nombre_sanitizado else "archivo_descarga"


def extraer_id_video(zoom_url: str) -> Optional[str]:
    """
    Extraer el ID unico de la grabacion desde la URL de Zoom.

    Args:
        zoom_url: URL completa de la grabacion de Zoom

    Returns:
        ID de la grabacion o None si no se encuentra
    """
    match = re.search(r"/rec/play/([^?]+)", zoom_url)
    return match.group(1) if match else None


def validar_url_zoom(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validar que la URL sea de Zoom y este accesible.

    Args:
        url: URL a validar

    Returns:
        Tupla (es_valida, id_video)
    """
    if not url.startswith("https://zoom.us/rec/"):
        return False, None

    video_id = extraer_id_video(url)
    if not video_id:
        return False, None

    return True, video_id


def verificar_sudo() -> bool:
    """
    Verificar si el comando sudo esta disponible y funciona.

    Returns:
        True si sudo esta disponible
    """
    try:
        subprocess.run(
            ["sudo", "-n", "true"], check=True, capture_output=True, timeout=5
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def instalar_dependencias(logger: logging.Logger) -> bool:
    """
    Instalar yt-dlp si no esta disponible.

    Args:
        logger: Logger para registrar eventos

    Returns:
        True si se instalo correctamente o ya existia
    """
    try:
        subprocess.run(["yt-dlp", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.info("Instalando yt-dlp...")
        try:
            resultado = subprocess.run(
                [sys.executable, "-m", "pip", "install", "yt-dlp"],
                capture_output=True,
                text=True,
            )
            if resultado.returncode == 0:
                logger.info("yt-dlp instalado correctamente")
                return True
            else:
                logger.error(f"Error instalando yt-dlp: {resultado.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error instalando yt-dlp: {e}")
            return False


def verificar_ffmpeg(logger: logging.Logger) -> bool:
    """
    Verificar si ffmpeg esta instalado.

    Args:
        logger: Logger para registrar eventos

    Returns:
        True si esta disponible
    """
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("ffmpeg no encontrado, intentando instalar...")
        return instalar_ffmpeg(logger)


def instalar_ffmpeg(logger: logging.Logger) -> bool:
    """
    Instalar ffmpeg si no esta disponible.

    Args:
        logger: Logger para registrar eventos

    Returns:
        True si se instalo correctamente o sudo no esta disponible
    """
    if not verificar_sudo():
        logger.warning(
            "sudo no disponible, no se puede instalar ffmpeg automaticamente"
        )
        logger.info("Por favor, instala ffmpeg manualmente: sudo apt install ffmpeg")
        return False

    try:
        logger.info("Instalando ffmpeg...")
        subprocess.run(["sudo", "apt", "update"], check=True, capture_output=True)
        subprocess.run(
            ["sudo", "apt", "install", "-y", "ffmpeg"], check=True, capture_output=True
        )
        logger.info("ffmpeg instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error instalando ffmpeg: {e}")
        logger.info("Por favor, instala ffmpeg manualmente: sudo apt install ffmpeg")
        return False


def convertir_a_mp3(
    video_path: str, audio_path: str, logger: logging.Logger, config: Dict[str, Any]
) -> bool:
    """
    Convertir archivo de video MP4 a audio MP3 usando ffmpeg.

    Args:
        video_path: Ruta del archivo de video de entrada
        audio_path: Ruta del archivo de audio de salida
        logger: Logger para registrar eventos
        config: Configuracion del programa

    Returns:
        True si la conversion fue exitosa
    """
    if not verificar_ffmpeg(logger):
        return False

    calidad_audio = config.get("video", {}).get("calidad_audio", "0")

    try:
        logger.info(f"Convirtiendo {video_path} a MP3...")
        cmd = [
            "ffmpeg",
            "-i",
            video_path,
            "-q:a",
            calidad_audio,
            "-map",
            "a",
            "-y",
            audio_path,
        ]

        resultado = subprocess.run(cmd, capture_output=True, text=True)

        if resultado.returncode == 0:
            logger.info(f"Conversion completada: {audio_path}")
            return True
        else:
            logger.error(f"Error en conversion: {resultado.stderr}")
            return False

    except Exception as e:
        logger.error(f"Error convirtiendo a MP3: {e}")
        return False


def reintentar_con_backoff(
    func,
    max_reintentos: int = 3,
    intervalo_base: float = 5.0,
    logger: Optional[logging.Logger] = None,
) -> Tuple[bool, Any]:
    """
    Ejecutar funcion con reintentos y backoff exponencial.

    Args:
        func: Funcion a ejecutar
        max_reintentos: Numero maximo de reintentos
        intervalo_base: Intervalo base entre reintentos (segundos)
        logger: Logger para registrar eventos

    Returns:
        Tupla (exito, resultado)
    """
    intervalo = float(intervalo_base)

    for intento in range(1, max_reintentos + 1):
        try:
            resultado = func()
            return True, resultado
        except Exception as e:
            if logger:
                logger.warning(f"Intento {intento}/{max_reintentos} fallido: {e}")

            if intento < max_reintentos:
                if logger:
                    logger.info(f"Reintentando en {intervalo:.1f} segundos...")
                time.sleep(intervalo)
                intervalo *= 2
            else:
                if logger:
                    logger.error(f"Todos los reintentos fallaron")
                return False, None

    return False, None


class BarraProgreso:
    """
    Barra de progreso visual en terminal.
    """

    def __init__(
        self,
        total: int,
        prefix: str = "",
        longitud: int = 40,
        fill: str = "█",
        vacio: str = "░",
    ):
        self.total = total
        self.prefix = prefix
        self.longitud = longitud
        self.fill = fill
        self.vacio = vacio
        self.completado = 0
        self.inicio = time.time()

    def actualizar(self, completado: int, info: str = "") -> None:
        """
        Actualizar el estado de la barra de progreso.

        Args:
            completado: Numero de elementos completados
            info: Informacion adicional a mostrar
        """
        self.completado = completado

        porcentaje = self.completado / self.total
        bloques = int(porcentaje * self.longitud)
        barra = self.fill * bloques + self.vacio * (self.longitud - bloques)

        elapsed = time.time() - self.inicio
        velocidad = self.completado / elapsed if elapsed > 0 else 0

        if velocidad > 0:
            restante = (self.total - self.completado) / velocidad
            tiempo_restante = f"{restante:.0f}s"
        else:
            tiempo_restante = "?"

        print(
            f"\r{self.prefix} |{barra}| "
            f"{porcentaje:.0%} "
            f"({self.completado}/{self.total}) "
            f"- {tiempo_restante} {info}",
            end="",
            flush=True,
        )

    def finalizar(self, mensaje: str = "") -> None:
        """
        Finalizar la barra de progreso.

        Args:
            mensaje: Mensaje final a mostrar
        """
        print()
        if mensaje:
            print(mensaje)


def convertir_vtt_a_srt(ruta_vtt: str, logger: logging.Logger) -> Optional[str]:
    """
    Convertir archivo VTT a SRT.

    Args:
        ruta_vtt: Ruta del archivo VTT de entrada
        logger: Logger para registrar eventos

    Returns:
        Ruta del archivo SRT creado o None si hubo error
    """
    try:
        ruta_srt = ruta_vtt.replace(".vtt", ".srt")

        with open(ruta_vtt, "r", encoding="utf-8") as f:
            contenido = f.read()

        contenido = contenido.replace("WEBVTT", "")
        contenido = contenido.replace(".000", ".000")
        contenido = re.sub(r"(\d{2}:\d{2}:\d{2})\.(\d{3})", r"\1,\2", contenido)

        contenido = re.sub(r"-->\s*", " --> ", contenido)

        with open(ruta_srt, "w", encoding="utf-8") as f:
            f.write(contenido)

        logger.info(f"Convertido: {ruta_vtt} -> {ruta_srt}")
        return ruta_srt

    except Exception as e:
        logger.error(f"Error convirtiendo VTT a SRT: {e}")
        return None


def obtener_tamano_archivo(ruta: str) -> Optional[int]:
    """
    Obtener tamano de un archivo en bytes.

    Args:
        ruta: Ruta del archivo

    Returns:
        Tamano en bytes o None si no existe
    """
    try:
        return os.path.getsize(ruta)
    except OSError:
        return None


def formatear_tamano(tamano_bytes: float) -> str:
    """
    Formatear tamano de archivo a formato legible.

    Args:
        tamano_bytes: Tamano en bytes

    Returns:
        Cadena formateada (KB, MB, GB)
    """
    for unidad in ["B", "KB", "MB", "GB"]:
        if abs(tamano_bytes) < 1024.0:
            return f"{tamano_bytes:.1f} {unidad}"
        tamano_bytes /= 1024.0

    return f"{tamano_bytes:.1f} TB"


def guardar_metadatos(
    nombre: str,
    url: str,
    tipo: str,
    rutas_archivos: Dict[str, str],
    logger: logging.Logger,
) -> None:
    """
    Guardar metadatos de la descarga en archivo JSON.

    Args:
        nombre: Nombre del video
        url: URL de la grabacion
        tipo: Tipo de descarga (video, audio, transcript, all)
        rutas_archivos: Dict con rutas de archivos descargados
        logger: Logger para registrar eventos
    """
    import json

    archivo_metadatos = Path("downloads/metadatos.json")

    metadatos = {}
    try:
        if archivo_metadatos.exists():
            with open(archivo_metadatos, "r", encoding="utf-8") as f:
                metadatos = json.load(f)
    except Exception as e:
        logger.warning(f"No se pudieron leer metadatos anteriores: {e}")

    entrada = {
        "nombre": nombre,
        "url": url,
        "tipo": tipo,
        "archivos": {},
        "fecha_descarga": datetime.now().isoformat(),
    }

    for tipo_archivo, ruta in rutas_archivos.items():
        tamano = obtener_tamano_archivo(ruta)
        entrada["archivos"][tipo_archivo] = {
            "ruta": ruta,
            "tamano_bytes": tamano,
            "tamano_formateado": formatear_tamano(tamano) if tamano else "desconocido",
        }

    if "descargas" not in metadatos:
        metadatos["descargas"] = []

    metadatos["descargas"].append(entrada)

    try:
        with open(archivo_metadatos, "w", encoding="utf-8") as f:
            json.dump(metadatos, f, indent=2, ensure_ascii=False)
        logger.info("Metadatos guardados")
    except Exception as e:
        logger.error(f"Error guardando metadatos: {e}")


def leer_urls_desde_archivo(
    ruta_archivo: str, logger: logging.Logger
) -> List[Tuple[str, str]]:
    """
    Leer y procesar URLs de Zoom desde archivos TXT o CSV.

    Args:
        ruta_archivo: Ruta al archivo a procesar
        logger: Logger para registrar eventos

    Returns:
        Lista de tuplas (nombre, url)
    """
    urls = []

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            contenido = f.read().strip()

        if not contenido:
            logger.warning("El archivo esta vacio")
            return []

        if "," in contenido:
            lineas = contenido.split("\n")
            for i, linea in enumerate(lineas):
                if "," in linea:
                    partes = linea.split(",", 1)
                    if len(partes) >= 2:
                        nombre = sanitizar_nombre_archivo(partes[0].strip())
                        url = partes[1].strip()
                        es_valida, _ = validar_url_zoom(url)
                        if es_valida:
                            urls.append((nombre, url))
        else:
            lineas = contenido.split("\n")
            for i, linea in enumerate(lineas):
                linea = linea.strip()
                es_valida, _ = validar_url_zoom(linea)
                if es_valida:
                    nombre = f"video_{i + 1}"
                    urls.append((nombre, linea))

        logger.info(f"Leidas {len(urls)} URLs validas de {ruta_archivo}")
        return urls

    except FileNotFoundError:
        logger.error(f"No se encontro el archivo: {ruta_archivo}")
        return []
    except Exception as e:
        logger.error(f"Error leyendo archivo: {e}")
        return []
