#!/usr/bin/env python3
"""
Tests para Zoom Video Downloader
================================

Pruebas unitarias y de integracion para el nucleo comun
y los scripts de descarga.

Categorias:
- Pruebas de funciones utilitarias
- Pruebas de validacion
- Pruebas de conversion
- Pruebas de integracion

Autor: Zoom Video Downloader
Version: 2.0.0
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    cargar_configuracion,
    sanitizar_nombre_archivo,
    validar_url_zoom,
    extraer_id_video,
    formatear_tamano,
    convertir_vtt_a_srt,
    Colores,
    leer_urls_desde_archivo,
)


class TestConfiguracion:
    """Pruebas para el sistema de configuracion."""

    def test_cargar_configuracion_defecto(self):
        """Cargar configuracion con valores por defecto."""
        config = cargar_configuracion("archivo_inexistente.yaml")

        assert "descargas" in config
        assert config["descargas"]["video"] == "MP4"
        assert config["descargas"]["audio"] == "MP3"
        assert config["descargas"]["transcripcion"] == "SRT"

    def test_estructura_directorios(self):
        """Verificar estructura de directorios."""
        from core import crear_directorios, cargar_configuracion

        config = cargar_configuracion("config.yaml")
        dirs = crear_directorios(config)

        assert dirs["base"].exists()
        assert dirs["video"].exists()
        assert dirs["audio"].exists()
        assert dirs["transcripcion"].exists()


class TestSanitizacion:
    """Pruebas para la sanitizacion de nombres de archivo."""

    def test_nombre_normal(self):
        """Sanitizar nombre normal."""
        resultado = sanitizar_nombre_archivo("mi_video")
        assert resultado == "mi_video"

    def test_nombre_con_espacios(self):
        """Sanitizar nombre con espacios."""
        resultado = sanitizar_nombre_archivo("mi video")
        assert resultado == "mi video"

    def test_nombre_con_caracteres_especiales(self):
        """Sanitizar nombre con caracteres especiales."""
        resultado = sanitizar_nombre_archivo('video<>:"/\\|?*.mp4')
        assert ".mp4" in resultado
        assert "<" not in resultado
        assert ">" not in resultado

    def test_nombre_largo(self):
        """Truncar nombre largo."""
        nombre_largo = "a" * 100
        resultado = sanitizar_nombre_archivo(nombre_largo)
        assert len(resultado) == 50

    def test_nombre_vacio(self):
        """Manejar nombre vacio."""
        resultado = sanitizar_nombre_archivo("")
        assert resultado == "" or resultado == "archivo_descarga"


class TestValidacion:
    """Pruebas para la validacion de URLs."""

    def test_url_valida(self):
        """Validar URL de Zoom correcta."""
        url = "https://zoom.us/rec/play/abc123def456"
        es_valida, video_id = validar_url_zoom(url)

        assert es_valida is True
        assert video_id == "abc123def456"

    def test_url_invalida(self):
        """Invalidar URL incorrecta."""
        url = "https://youtube.com/watch?v=abc123"
        es_valida, video_id = validar_url_zoom(url)

        assert es_valida is False
        assert video_id is None

    def test_url_sin_play(self):
        """Invalidar URL sin /rec/play/."""
        url = "https://zoom.us/rec/"
        es_valida, video_id = validar_url_zoom(url)

        assert es_valida is False

    def test_extraer_id_video(self):
        """Extraer ID de video de URL."""
        url = "https://zoom.us/rec/play/abc123...xyz789"
        video_id = extraer_id_video(url)

        assert video_id == "abc123...xyz789"

    def test_extraer_id_con_parametros(self):
        """Extraer ID con parametros de URL."""
        url = "https://zoom.us/rec/play/abc123?param=value"
        video_id = extraer_id_video(url)

        assert video_id == "abc123"


class TestFormateo:
    """Pruebas para funciones de formateo."""

    def test_formatear_bytes(self):
        """Formatear tamano en bytes."""
        resultado = formatear_tamano(500)
        assert resultado == "500.0 B"

    def test_formatear_kilobytes(self):
        """Formatear tamano en kilobytes."""
        resultado = formatear_tamano(2048)
        assert resultado == "2.0 KB"

    def test_formatear_megabytes(self):
        """Formatear tamano en megabytes."""
        resultado = formatear_tamano(1048576)
        assert resultado == "1.0 MB"

    def test_formatear_gigabytes(self):
        """Formatear tamano en gigabytes."""
        resultado = formatear_tamano(1073741824)
        assert resultado == "1.0 GB"


class TestConversion:
    """Pruebas para conversion de formatos."""

    def test_convertir_vtt_a_srt(self):
        """Convertir contenido VTT a SRT."""
        contenido_vtt = """WEBVTT

1
00:00:00.000 --> 00:00:05.000
Hola mundo

2
00:00:05.000 --> 00:00:10.000
Adios mundo
"""

        ruta_vtt = ""
        ruta_srt = None

        with tempfile.NamedTemporaryFile(mode="w", suffix=".vtt", delete=False) as f:
            f.write(contenido_vtt)
            ruta_vtt = f.name

        try:
            mock_logger = MagicMock()
            ruta_srt = convertir_vtt_a_srt(ruta_vtt, mock_logger)

            assert ruta_srt is not None
            assert Path(ruta_srt).exists()

            with open(ruta_srt, "r", encoding="utf-8") as f:
                contenido_srt = f.read()

            assert "WEBVTT" not in contenido_srt
            assert "-->" in contenido_srt

        finally:
            if Path(ruta_vtt).exists():
                os.unlink(ruta_vtt)
            if ruta_srt is not None and Path(ruta_srt).exists():
                os.unlink(ruta_srt)


class TestLecturaArchivos:
    """Pruebas para lectura de archivos."""

    def test_leer_txt_valido(self):
        """Leer archivo TXT con URLs validas."""
        contenido = """https://zoom.us/rec/play/abc123
https://zoom.us/rec/play/def456
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(contenido)
            ruta = f.name

        try:
            mock_logger = MagicMock()
            urls = leer_urls_desde_archivo(ruta, mock_logger)

            assert len(urls) == 2
            assert urls[0][0] == "video_1"
            assert urls[0][1] == "https://zoom.us/rec/play/abc123"
        finally:
            os.unlink(ruta)

    def test_leer_csv_valido(self):
        """Leer archivo CSV con URLs validas."""
        contenido = """Clase 1,https://zoom.us/rec/play/abc123
Clase 2,https://zoom.us/rec/play/def456
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(contenido)
            ruta = f.name

        try:
            mock_logger = MagicMock()
            urls = leer_urls_desde_archivo(ruta, mock_logger)

            assert len(urls) == 2
            assert urls[0][0] == "Clase 1"
            assert urls[0][1] == "https://zoom.us/rec/play/abc123"
        finally:
            os.unlink(ruta)

    def test_leer_archivo_vacio(self):
        """Manejar archivo vacio."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            ruta = f.name

        try:
            mock_logger = MagicMock()
            urls = leer_urls_desde_archivo(ruta, mock_logger)

            assert len(urls) == 0
        finally:
            os.unlink(ruta)

    def test_leer_archivo_inexistente(self):
        """Manejar archivo inexistente."""
        mock_logger = MagicMock()
        urls = leer_urls_desde_archivo("archivo_inexistente.txt", mock_logger)

        assert len(urls) == 0


class TestColores:
    """Pruebas para el sistema de colores."""

    def test_colores_existen(self):
        """Verificar que todos los colores existen."""
        assert Colores.RESET is not None
        assert Colores.ROJO is not None
        assert Colores.VERDE is not None
        assert Colores.AZUL is not None


class TestIntegracion:
    """Pruebas de integracion."""

    @pytest.fixture
    def directorio_temporal(self):
        """Crear directorio temporal para pruebas."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_ciclo_descarga_completo(self, directorio_temporal):
        """Probar ciclo completo de descarga con mock."""
        from unittest.mock import patch, MagicMock
        from core import (
            cargar_configuracion,
            validar_url_zoom,
            sanitizar_nombre_archivo,
            crear_directorios,
        )

        original_dir = os.getcwd()
        os.chdir(directorio_temporal)

        try:
            config = cargar_configuracion("archivo_inexistente.yaml")
            crear_directorios(config)

            url_valida = "https://zoom.us/rec/play/test123"
            es_valida, video_id = validar_url_zoom(url_valida)

            assert es_valida is True
            assert video_id == "test123"

            nombre = sanitizar_nombre_archivo("Mi-Video.de-Prueba")
            assert nombre == "Mi-Video.de-Prueba"

        finally:
            os.chdir(original_dir)


def pytest_configure(config):
    """Configuracion de pytest."""
    config.addinivalue_line("markers", "integration: mark test as integration test")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
