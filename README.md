# Zoom Video Downloader

Herramienta mejorada para descargar grabaciones de Zoom en diferentes formatos: video (MP4), audio (MP3) y transcripciones (SRT/VTT).

## Caracteristicas

- **Descarga individual o masiva** de grabaciones
- **Soporte para video, audio y transcripciones**
- **Interfaz interactiva** por terminal
- **Conversion automatica** de video a audio
- **Sistema de reintentos** con backoff exponencial
- **Barra de progreso** visual
- **Logging persistente** en archivo
- **Metadatos** de descarga en JSON
- **Conversion VTT a SRT** para transcripciones
- **Configuracion externa** via YAML
- **Tests unitarios** con pytest

## Requisitos

- Python 3.8+
- ffmpeg (se instala automaticamente en sistemas Debian/Ubuntu)
- yt-dlp (se instala automaticamente)

## Instalacion

```bash
git clone <tu-repositorio>
cd zoom-video-downloader
pip install -e .
chmod +x start.sh
```

O con dependencias de desarrollo:

```bash
pip install -e ".[dev]"
```

## Uso

### Interfaz interactiva

```bash
./start.sh
```

Menu interactivo con opciones:
1. Descargar URL individual
2. Descargar desde archivo (masivo)
3. Ver archivos en carpeta input/
4. Ver estado de descargas
5. Limpiar archivos temporales
6. Ayuda

### Descarga individual (linea de comandos)

```bash
python3 simple_zoom_downloader.py <URL> [tipo] [nombre]
```

Tipos disponibles:
- `video` - Solo video MP4
- `audio` - Solo audio MP3
- `transcript` - Solo transcripcion SRT/VTT
- `all` - Todo (video + audio + transcripcion)

Ejemplos:
```bash
python3 simple_zoom_downloader.py "https://zoom.us/rec/play/..." video
python3 simple_zoom_downloader.py "https://zoom.us/rec/play/..." all "mi_clase"
python3 simple_zoom_downloader.py "https://zoom.us/rec/play/..." transcript --verbose
```

### Descarga masiva

```bash
python3 batch_downloader.py <archivo> [tipo] [--no-confirm] [--verbose]
```

Ejemplos:
```bash
python3 batch_downloader.py input/urls.txt all
python3 batch_downloader.py input/urls.csv video --no-confirm
python3 batch_downloader.py input/urls.txt audio --verbose
```

Argumentos disponibles:
- `--config`: Archivo de configuracion (default: config.yaml)
- `--verbose`: Modo verboso (debug)
- `--no-confirm`: No pedir confirmacion antes de descargar

## Configuracion

Edita `config.yaml` para personalizar:

```yaml
descargas:
  directorio_base: downloads
  video: MP4
  audio: MP3
  transcripcion: SRT

video:
  formato_preferido: mp4
  calidad: best
  convertir_audio: true
  formato_audio: mp3
  calidad_audio: "0"

reintentos:
  maximos: 3
  intervalo_segundos: 5

logging:
  archivo: downloads/descargas.log
  nivel: INFO
```

## Formatos de archivo de entrada

### TXT

Una URL por linea:
```
https://zoom.us/rec/play/abc123...
https://zoom.us/rec/play/def456...
```

### CSV

Titulo y URL separados por coma:
```
Clase Matematicas,https://zoom.us/rec/play/abc123...
Clase Fisica,https://zoom.us/rec/play/def456...
```

## Estructura del proyecto

```
zoom-video-downloader/
├── core.py                    # Nucleo comun (funciones compartidas)
├── simple_zoom_downloader.py   # Descarga individual
├── batch_downloader.py         # Descarga masiva
├── main.py                     # Interfaz interactiva
├── start.sh                    # Script de inicio
├── config.yaml                 # Configuracion
├── requirements.txt            # Dependencias
├── input/                      # Carpeta para archivos con URLs
├── downloads/                  # Carpeta de descargas
│   ├── MP4/                   # Videos descargados
│   ├── MP3/                   # Audios extraidos
│   ├── SRT/                   # Transcripciones
│   ├── descargas.log          # Log de descargas
│   └── metadatos.json         # Metadatos de descargas
└── tests/
    └── test_core.py           # Tests unitarios
```

## Dependencias

El proyecto instala automaticamente:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Descarga de videos
- ffmpeg - Conversion de video a audio
- PyYAML - Configuracion

## Dependencias

El proyecto usa `pyproject.toml` para gestion de dependencias (estandar moderno de Python).

**Dependencias principales:**
- yt-dlp - Descarga de videos
- PyYAML - Configuracion

**Instalacion basica:**
```bash
pip install -e .
```

**Con dependencias de desarrollo (tests):**
```bash
pip install -e ".[dev]"
```

## Tests

```bash
python3 -m pytest tests/ -v
```

## Registro de cambios

### Version 2.0.0

- Nucleo comun refactorizado (`core.py`)
- Sistema de configuracion YAML
- Sistema de logging persistente
- Reintentos con backoff exponencial
- Barra de progreso visual
- Conversion VTT a SRT
- Exportacion de metadatos JSON
- Tests unitarios completos
- Argumentos con argparse
- Mejora de manejo de errores
- Colores en terminal

## Licencia

MIT
