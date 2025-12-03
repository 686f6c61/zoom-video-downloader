# Zoom video downloader

Herramienta para descargar grabaciones de Zoom en diferentes formatos: video (MP4), audio (MP3) y transcripciones (SRT/VTT).

## Caracteristicas

- Descarga individual o masiva de grabaciones
- Soporte para video, audio y transcripciones
- Interfaz interactiva por terminal
- Conversion automatica de video a audio
- Instalacion automatica de dependencias (yt-dlp, ffmpeg)
- Soporte para archivos TXT y CSV con URLs

## Requisitos

- Python 3.x
- ffmpeg (se instala automaticamente en sistemas Debian/Ubuntu)

## Instalacion

```bash
git clone <tu-repositorio>
cd zoom-video-downloader
chmod +x start.sh
```

## Uso

### Interfaz interactiva

```bash
./start.sh
```

Esto abre un menu interactivo donde puedes:
1. Descargar una URL individual
2. Descargar desde archivo (masivo)
3. Ver archivos en carpeta input/
4. Ver estado de descargas
5. Limpiar archivos temporales

### Descarga individual (linea de comandos)

```bash
python3 simple_zoom_downloader.py <URL> [tipo] [nombre]
```

Tipos disponibles:
- `video` - Solo video MP4
- `audio` - Solo audio MP3
- `transcript` - Solo transcripcion SRT/VTT
- `all` - Todo (video + audio + transcripcion)

Ejemplo:
```bash
python3 simple_zoom_downloader.py "https://zoom.us/rec/play/..." video "mi_clase"
```

### Descarga masiva

```bash
python3 batch_downloader.py <archivo> [tipo]
```

Ejemplo:
```bash
python3 batch_downloader.py input/urls.txt all
```

## Formatos de archivo de entrada

### Archivo TXT

Una URL por linea:
```
https://zoom.us/rec/play/abc123...
https://zoom.us/rec/play/def456...
```

### Archivo CSV

Titulo y URL separados por coma:
```
Clase Matematicas,https://zoom.us/rec/play/abc123...
Clase Fisica,https://zoom.us/rec/play/def456...
```

## Estructura del proyecto

```
zoom-video-downloader/
├── main.py                  # Interfaz interactiva principal
├── simple_zoom_downloader.py # Descarga individual
├── batch_downloader.py       # Descarga masiva
├── start.sh                  # Script de inicio
├── input/                    # Carpeta para archivos con URLs
│   └── ejemplo_urls.txt      # Ejemplo de archivo de entrada
└── downloads/                # Carpeta de descargas (se crea automaticamente)
    ├── MP4/                  # Videos descargados
    ├── MP3/                  # Audios extraidos
    └── SRT/                  # Transcripciones
```

## Dependencias

El proyecto instala automaticamente:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Descarga de videos
- ffmpeg - Conversion de video a audio

## Licencia

MIT
