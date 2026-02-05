#!/usr/bin/env python3
"""
Zoom Video Downloader - Descarga Individual
==========================================

Script para descargar grabaciones individuales de Zoom.
Ideal para descargas unicas o pruebas rapidas.

Funcionalidades:
- Descarga de URLs individuales de Zoom
- Soporte para video (MP4), audio (MP3) y transcripciones (SRT/VTT)
- Nombres de archivo personalizados
- Sistema de reintentos con backoff exponencial
- Barra de progreso visual
- Conversion automatica video -> audio
- Metadatos de descarga

Uso: python3 simple_zoom_downloader.py <URL_ZOOM> [tipo] [nombre]
Tipos: video, audio, transcript, all
Nombre: opcional, para personalizar el archivo de salida

Autor: Zoom Video Downloader
Version: 2.0.0
"""

import sys
import subprocess
import argparse
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from core import (
    cargar_configuracion,
    inicializar_logging,
    crear_directorios,
    sanitizar_nombre_archivo,
    validar_url_zoom,
    instalar_dependencias,
    verificar_ffmpeg,
    convertir_a_mp3,
    convertir_vtt_a_srt,
    BarraProgreso,
    reintentar_con_backoff,
    guardar_metadatos,
    formatear_tamano,
    Colores,
    imprimir_texto,
)


def construir_comando_yt_dlp(
    url: str, tipo: str, nombre_salida: str, config: Dict[str, Any]
) -> tuple:
    """
    Construir comando de yt-dlp segun el tipo de descarga.

    Args:
        url: URL de la grabacion de Zoom
        tipo: Tipo de descarga (video, audio, transcript, all)
        nombre_salida: Nombre base para el archivo de salida
        config: Configuracion del programa

    Returns:
        Tupla (comando, ruta_salida, tipo_archivos)
    """
    dirs = config["descargas"]
    video_config = config.get("video", {})
    transcript_config = config.get("transcripcion", {})

    if tipo == "video":
        ruta_salida = str(
            Path(dirs["directorio_base"]) / dirs["video"] / f"{nombre_salida}.mp4"
        )
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--format",
            f"best[ext={video_config.get('formato_preferido', 'mp4')}]/best",
            "--output",
            ruta_salida,
            url,
        ]
        return cmd, ruta_salida, "video"

    elif tipo == "audio":
        ruta_salida = str(
            Path(dirs["directorio_base"]) / dirs["audio"] / f"{nombre_salida}.mp3"
        )
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--extract-audio",
            "--audio-format",
            video_config.get("formato_audio", "mp3"),
            "--audio-quality",
            str(video_config.get("calidad_audio", "0")),
            "--output",
            str(
                Path(dirs["directorio_base"])
                / dirs["audio"]
                / f"{nombre_salida}.%(ext)s"
            ),
            url,
        ]
        return cmd, ruta_salida, "audio"

    elif tipo == "transcript":
        ruta_base = str(
            Path(dirs["directorio_base"]) / dirs["transcripcion"] / nombre_salida
        )
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            transcript_config.get("idiomas", "all"),
            "--skip-download",
            "--output",
            ruta_base,
            url,
        ]
        return cmd, ruta_base, "transcript"

    elif tipo == "all":
        ruta_video = str(
            Path(dirs["directorio_base"]) / dirs["video"] / f"{nombre_salida}.mp4"
        )
        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--format",
            f"best[ext={video_config.get('formato_preferido', 'mp4')}]/best",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            transcript_config.get("idiomas", "all"),
            "--output",
            ruta_video,
            url,
        ]
        return cmd, ruta_video, "all"

    return None, None, None


def ejecutar_descarga(
    url: str,
    tipo: str,
    nombre: Optional[str],
    config: Dict[str, Any],
    logger: logging.Logger,
) -> bool:
    """
    Ejecutar la descarga de una grabacion de Zoom.

    Args:
        url: URL de la grabacion
        tipo: Tipo de descarga
        nombre: Nombre personalizado (opcional)
        config: Configuracion del programa
        logger: Logger para registrar eventos

    Returns:
        True si la descarga fue exitosa
    """
    es_valida, video_id = validar_url_zoom(url)
    if not es_valida:
        logger.error(f"URL invalida: {url}")
        return False

    if not instalar_dependencias(logger):
        logger.error("No se pudo instalar yt-dlp")
        return False

    if nombre:
        nombre_archivo = sanitizar_nombre_archivo(nombre)
    else:
        nombre_base = video_id[:20] if video_id else "video_descarga"
        nombre_archivo = sanitizar_nombre_archivo(nombre_base)

    logger.info(f"Iniciando descarga: {nombre_archivo} (tipo: {tipo})")

    crear_directorios(config)

    cmd, ruta_salida, tipo_archivos = construir_comando_yt_dlp(
        url, tipo, nombre_archivo, config
    )

    if not cmd:
        logger.error(f"Tipo de descarga no valido: {tipo}")
        return False

    reintentos = config.get("reintentos", {}).get("maximos", 3)

    exito, resultado = reintentar_con_backoff(
        func=lambda: subprocess.run(cmd, capture_output=True, text=True),
        max_reintentos=reintentos,
        intervalo_base=config.get("reintentos", {}).get("intervalo_segundos", 5),
        logger=logger,
    )

    if not exito:
        logger.error("Descarga fallida despues de todos los reintentos")
        return False

    resultado_final = resultado

    if resultado_final.returncode != 0:
        logger.error(f"yt-dlp error: {resultado_final.stderr}")
        return False

    logger.info(f"Descarga completada: {nombre_archivo}")

    rutas_archivos = {}

    if tipo_archivos in ["video", "all"]:
        if tipo == "all":
            video_file = str(
                Path(config["descargas"]["directorio_base"])
                / config["descargas"]["video"]
                / f"{nombre_archivo}.mp4"
            )
            audio_file = str(
                Path(config["descargas"]["directorio_base"])
                / config["descargas"]["audio"]
                / f"{nombre_archivo}.mp3"
            )

            if Path(video_file).exists():
                convertir_a_mp3(video_file, audio_file, logger, config)
                rutas_archivos["audio"] = audio_file

        rutas_archivos["video"] = ruta_salida

    if tipo_archivos in ["transcript", "all"]:
        import glob

        archivos_vtt = glob.glob(
            str(
                Path(config["descargas"]["directorio_base"])
                / config["descargas"]["transcripcion"]
                / f"{nombre_archivo}*.vtt"
            )
        )

        convertir_srt = "srt" in config.get("transcripcion", {}).get(
            "formatos_salida", []
        )

        for vtt in archivos_vtt:
            rutas_archivos["transcripcion"] = vtt
            if convertir_srt:
                convertir_vtt_a_srt(vtt, logger)

    if rutas_archivos:
        guardar_metadatos(nombre_archivo, url, tipo, rutas_archivos, logger)

    return True


def mostrar_resumen_descarga(
    nombre: str, tipo: str, rutas: Dict[str, str], logger: logging.Logger
) -> None:
    """
    Mostrar resumen de la descarga completada.

    Args:
        nombre: Nombre del video
        tipo: Tipo de descarga
        rutas: Rutas de archivos descargados
        logger: Logger para registrar eventos
    """
    imprimir_texto(f"\n{'=' * 50}", Colores.VERDE)
    imprimir_texto(f"  DESCARGA COMPLETADA: {nombre}", Colores.VERDE)
    imprimir_texto(f"{'=' * 50}\n", Colores.VERDE)

    for tipo_archivo, ruta in rutas.items():
        tamano = formatear_tamano(
            Path(ruta).stat().st_size if Path(ruta).exists() else 0
        )
        logger.info(f"  {tipo_archivo}: {ruta} ({tamano})")
        print(f"  [{tipo_archivo.upper()}]: {ruta}")
        print(f"    Tamano: {tamano}")

    logger.info("Descarga finalizada correctamente")


def obtener_argumentos() -> argparse.Namespace:
    """
    Parsear argumentos de linea de comandos.

    Returns:
        Namespace con los argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="Zoom Video Downloader - Descarga individual de grabaciones",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 simple_zoom_downloader.py "https://zoom.us/rec/play/..." video
  python3 simple_zoom_downloader.py "https://zoom.us/rec/play/..." audio "mi_clase"
  python3 simple_zoom_downloader.py "https://zoom.us/rec/play/..." all
        """,
    )

    parser.add_argument("url", nargs="?", help="URL de la grabacion de Zoom")

    parser.add_argument(
        "tipo",
        nargs="?",
        default="all",
        choices=["video", "audio", "transcript", "all"],
        help="Tipo de descarga (default: all)",
    )

    parser.add_argument(
        "nombre", nargs="?", default=None, help="Nombre personalizado para el archivo"
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Archivo de configuracion (default: config.yaml)",
    )

    parser.add_argument("--verbose", action="store_true", help="Modo verboso (debug)")

    return parser.parse_args()


def menu_interactivo() -> tuple:
    """
    Mostrar menu interactivo para seleccion de tipo de descarga.

    Returns:
        Tupla (url, tipo, nombre)
    """
    print("\nZoom Video Downloader - Descarga Individual")
    print("-" * 45)

    url = input("Ingresa la URL de Zoom: ").strip()
    if not url:
        return "", "", ""

    if not url.startswith("https://zoom.us/rec/"):
        print("Error: La URL debe ser de Zoom (https://zoom.us/rec/...)")
        return "", "", ""

    print("\nTipo de descarga:")
    print("1. Video (MP4)")
    print("2. Audio (MP3)")
    print("3. Transcripcion (SRT)")
    print("4. Todo (video + audio + transcripcion)")

    while True:
        opcion = input("Elige una opcion (1-4): ").strip()
        if opcion in ["1", "2", "3", "4"]:
            tipos = {"1": "video", "2": "audio", "3": "transcript", "4": "all"}
            tipo = tipos[opcion]
            break
        print("Opcion no valida")

    nombre = input("Nombre personalizado (opcional): ").strip()

    return url, tipo, nombre


def main() -> None:
    """
    Funcion principal del descargador individual.
    """
    args = obtener_argumentos()

    config = cargar_configuracion(args.config)

    if args.verbose:
        config["logging"]["nivel"] = "DEBUG"

    logger = inicializar_logging(config)

    logger.info("Iniciando Zoom Video Downloader - Descarga Individual")

    if args.url:
        url, tipo, nombre = args.url, args.tipo, args.nombre
    else:
        url, tipo, nombre = menu_interactivo()
        if not url:
            print("URL requerida")
            sys.exit(1)

    exito = ejecutar_descarga(url, tipo, nombre, config, logger)

    if exito:
        logger.info("Descarga completada exitosamente")
        sys.exit(0)
    else:
        logger.error("Descarga fallida")
        sys.exit(1)


if __name__ == "__main__":
    main()
