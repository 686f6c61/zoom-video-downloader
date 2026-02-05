#!/usr/bin/env python3
"""
Zoom Video Downloader - Descarga Masiva
=======================================

Script para procesar múltiples URLs de Zoom desde archivos CSV o TXT.
Ideal para descargas masivas de grabaciones.

Funcionalidades:
- Soporte para descarga masiva desde archivos
- Reintentos automaticos con backoff exponencial
- Barra de progreso visual
- Conversión automatica de video a audio MP3
- Extracción de transcripciones cuando disponibles
- Nombres de archivo personalizados desde CSV
- Logging persistente
- Metadatos de descarga

Formatos de entrada:
- TXT: una URL de Zoom por linea
- CSV: titulo,url (dos columnas separadas por coma)

Uso: python3 batch_downloader.py <archivo_urls> [tipo]
Tipos: video, audio, transcript, all

Autor: Zoom Video Downloader
Version: 2.0.0
"""

import sys
import argparse
import logging
from typing import Dict, Any, Optional, List, Tuple
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
    leer_urls_desde_archivo,
)


def construir_comando_yt_dlp(
    url: str, tipo: str, nombre_salida: str, config: Dict[str, Any]
) -> Tuple[Optional[List[str]], Optional[str], Optional[str]]:
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
    url: str, tipo: str, nombre: str, config: Dict[str, Any], logger: logging.Logger
) -> bool:
    """
    Ejecutar la descarga de una grabacion de Zoom.

    Args:
        url: URL de la grabacion
        tipo: Tipo de descarga
        nombre: Nombre del video
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

    nombre_archivo = sanitizar_nombre_archivo(nombre)

    logger.info(f"Descargando: {nombre_archivo} (tipo: {tipo})")

    crear_directorios(config)

    cmd, ruta_salida, tipo_archivos = construir_comando_yt_dlp(
        url, tipo, nombre_archivo, config
    )

    if not cmd:
        logger.error(f"Tipo de descarga no valido: {tipo}")
        return False

    reintentos = config.get("reintentos", {}).get("maximos", 3)

    exito, resultado = reintentar_con_backoff(
        func=lambda: __import__("subprocess").run(cmd, capture_output=True, text=True),
        max_reintentos=reintentos,
        intervalo_base=config.get("reintentos", {}).get("intervalo_segundos", 5),
        logger=logger,
    )

    if not exito:
        logger.error(f"Descarga fallida: {nombre_archivo}")
        return False

    if resultado.returncode != 0:
        logger.error(f"yt-dlp error: {resultado.stderr}")
        return False

    logger.info(f"Descarga completada: {nombre_archivo}")

    rutas_archivos = {}

    if tipo_archivos in ["video", "all"]:
        if tipo == "all":
            import subprocess

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


def obtener_argumentos() -> argparse.Namespace:
    """
    Parsear argumentos de linea de comandos.

    Returns:
        Namespace con los argumentos parseados
    """
    parser = argparse.ArgumentParser(
        description="Zoom Video Downloader - Descarga masiva de grabaciones",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python3 batch_downloader.py input/urls.txt all
  python3 batch_downloader.py input/urls.csv video
  python3 batch_downloader.py input/urls.txt audio --verbose
        """,
    )

    parser.add_argument(
        "archivo", nargs="?", help="Ruta al archivo TXT o CSV con URLs de Zoom"
    )

    parser.add_argument(
        "tipo",
        nargs="?",
        default="all",
        choices=["video", "audio", "transcript", "all"],
        help="Tipo de descarga (default: all)",
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Archivo de configuracion (default: config.yaml)",
    )

    parser.add_argument("--verbose", action="store_true", help="Modo verboso (debug)")

    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="No pedir confirmacion antes de descargar",
    )

    return parser.parse_args()


def mostrar_resumen(
    total: int, exitosas: int, fallidas: int, logger: logging.Logger
) -> None:
    """
    Mostrar resumen de la descarga masiva.

    Args:
        total: Total de URLs procesadas
        exitosas: Numero de descargas exitosas
        fallidas: Numero de descargas fallidas
        logger: Logger para registrar eventos
    """
    print("\n" + "=" * 50)
    print("RESUMEN DE DESCARGA MASIVA")
    print("=" * 50)
    print(f"  Total procesadas: {total}")
    print(f"  Exitosas: {exitosas}")
    print(f"  Fallidas: {fallidas}")
    print(
        f"  Tasa de exito: {((exitosas / total) * 100):.1f}%"
        if total > 0
        else "  Tasa de exito: 0%"
    )
    print("=" * 50)

    logger.info(f"Resumen: {exitosas}/{total} descargas exitosas")


def main() -> None:
    """
    Funcion principal del descargador masivo.
    """
    args = obtener_argumentos()

    config = cargar_configuracion(args.config)

    if args.verbose:
        config["logging"]["nivel"] = "DEBUG"

    logger = inicializar_logging(config)

    logger.info("Iniciando Zoom Video Downloader - Descarga Masiva")

    if not args.archivo:
        print("Uso: python3 batch_downloader.py <archivo_urls> [tipo]")
        print("Formatos:")
        print("  TXT: una URL por linea")
        print("  CSV: titulo,url (dos columnas)")
        print("\nTipos: video, audio, transcript, all")
        sys.exit(1)

    archivo_path = Path(args.archivo)
    if not archivo_path.exists():
        logger.error(f"El archivo no existe: {archivo_path}")
        sys.exit(1)

    urls = leer_urls_desde_archivo(str(archivo_path), logger)

    if not urls:
        logger.error("No se encontraron URLs validas en el archivo")
        sys.exit(1)

    print(f"\nSe procesaran {len(urls)} grabaciones")
    print(f"Tipo de descarga: {args.tipo}")

    for i, (nombre, url) in enumerate(urls[:5], 1):
        print(f"  {i}. {nombre}: {url[:50]}...")

    if len(urls) > 5:
        print(f"  ... y {len(urls) - 5} mas")

    if not args.no_confirm:
        confirm = input("\nContinuar? (s/N): ").strip().lower()
        if confirm not in ["s", "si", "yes"]:
            print("Descarga cancelada")
            sys.exit(0)

    crear_directorios(config)

    barra = BarraProgreso(len(urls), prefix="Descargando", longitud=40)

    exitosas = 0
    fallidas = 0
    fallidas_detalles = []

    for i, (nombre, url) in enumerate(urls, 1):
        barra.actualizar(i, f"{nombre}")

        if ejecutar_descarga(url, args.tipo, nombre, config, logger):
            exitosas += 1
        else:
            fallidas += 1
            fallidas_detalles.append((nombre, url))

    barra.finalizar()

    mostrar_resumen(len(urls), exitosas, fallidas, logger)

    if fallidas_detalles and config.get("descarga", {}).get(
        "reintentar_descargas_fallidas", False
    ):
        print("\nReintentando descargas fallidas...")
        reintentos_fallidos = []
        for nombre, url in fallidas_detalles:
            if ejecutar_descarga(url, args.tipo, nombre, config, logger):
                exitosas += 1
                fallidas -= 1
            else:
                reintentos_fallidos.append((nombre, url))

        if reintentos_fallidos:
            print(f"\nDescargas que siguen fallando: {len(reintentos_fallidos)}")
            for nombre, url in reintentos_fallidos:
                logger.error(f"No se pudo descargar: {nombre} ({url})")

    if exitosas > 0:
        logger.info("Descarga masiva completada")
        sys.exit(0)
    else:
        logger.error("Descarga masiva fallida")
        sys.exit(1)


if __name__ == "__main__":
    main()
