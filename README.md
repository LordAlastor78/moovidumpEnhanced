# 📚 MooviDump Enhanced

> Descarga todo el contenido de tus cursos de Moodle de forma automática y organizada.

## 🚀 Inicio Rápido

### 1️⃣ Configuración del Entorno

Copia el archivo de ejemplo y completa tus credenciales:

```bash
copy example.env .env
```

Edita `.env` y rellena:
```env
MOODLE_SITE="https://moovi.uvigo.gal"
MOODLE_USERNAME="tu_usuario"
MOODLE_PASSWORD="tu_contraseña"
```

### 2️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3️⃣ Ejecutar el Dump

```bash
python main.py
```

## 📦 Opciones Avanzadas

Edita estas variables en `main.py` para personalizar el comportamiento:

### `DUMP_ALL = True`
Guarda snapshots JSON de cada sección y módulo. Útil para debugging o análisis.

**Sin activar:**
```
dumps/
└── FMI/
    ├── Tema 1/
    │   ├── Lectura.pdf
    │   └── Video.mp4
```

**Con activar:**
```
dumps/
└── 1678_FMI/
    ├── contents.json
    └── sections/
        ├── 01_Tema 1/
        │   ├── section.json
        │   └── 000_Lectura/
        │       ├── module.json
        │       └── Lectura.pdf
```

### `FULL_SANITIZER = True`
Reemplaza espacios con guiones bajos en los nombres de archivos (útil en sistemas con restricciones).

## 📍 Salida de Archivos

Todos los archivos se guardan en la carpeta `dumps/`:

```
dumps/
├── [Curso 1]/
# 📚 MooviDump Enhanced

> Herramienta para descargar y organizar automáticamente los recursos de tus cursos Moodle.

Una utilidad simple y robusta para exportar los archivos y estructura (tema → módulo → archivo)
de los cursos en los que estás matriculado, guardándolos en una carpeta `dumps/` local.

---

## ✨ Características principales

- Inicio de sesión con credenciales de Moodle (entradas seguras con `getpass`).
- Descarga de los recursos por curso/tema/módulo y organización en carpetas.
- Evita re-descargar ficheros existentes (por nombre) a menos que uses `--force`.
- `rich` para tablas y salida amigable en terminal.
- Reintentos y timeouts para llamadas HTTP con `requests.Session`.
- Modos interactivos para no guardar la contraseña (temporal) o guardarla en `.env`.

---

## Requisitos

- Python 3.8+
- Paquetes (instálalos con):

```bash
python -m pip install -r requirements.txt
```

---

## Instalación rápida

1. Clona o descarga este repositorio.
2. Copia el archivo de ejemplo y rellena tus credenciales (opcional):

```powershell
copy example.env .env
# Luego edita .env con tu editor preferido
```


---

## Uso (rápido)

Modo interactivo y asistente: ejecuta el helper `run.py` y sigue las indicaciones:

```powershell
python run.py
```

También puedes ejecutar directamente `main.py` si ya tienes `MOODLE_SITE`, `MOODLE_USERNAME` y `MOODLE_PASSWORD`
definidos en tu entorno o en un fichero `.env`:

```bash
python main.py [--force] [--verbose]
```

Opciones CLI:
- `--force` : Fuerza la re-descarga de archivos aunque ya existan.
- `--verbose` : Activa logging en nivel `DEBUG`.

### Interfaz gráfica (sin terminal)

Puedes usar la app visual:

```powershell
python run_gui.py
```

Incluye:
- Formulario de credenciales (site, usuario, contraseña).
- Opción para guardar contraseña en `.env` o usarla solo temporalmente.
- Opción de forzar redescarga (`--force`).
- Selección de cursos sin prompts de terminal (todos o lista de IDs).
- Panel de logs en tiempo real.

En ejecución por CLI también puedes evitar prompts con:

```bash
python main.py --all-courses
python main.py --courses 1684,1685,1702
```

### Generar `.exe` (Windows)

Compila la interfaz gráfica como ejecutable con:

```powershell
.\build_exe.ps1
```

Resultado:
- `dist/MooviDumpEnhanced.exe`

Nota:
- El `.exe` ya incluye internamente `main.py` para ejecutar la descarga en modo worker.
- La carpeta `dumps/` y el archivo `.env` se crean junto al propio ejecutable.

---

## Modos de ejecución (`run.py`)

Al ejecutar `run.py` se ofrece un asistente con tres modos:

1) Usar `.env` existente (si existe).
2) Introducir credenciales temporales para esta ejecución (no se guardan).
3) Introducir credenciales y guardarlas en `.env` para usos futuros.

Por seguridad, la contraseña no se imprime en pantalla ni se guarda por defecto a menos que elijas la opción 3.

---

## Estructura de salida

Los archivos se guardan bajo `dumps/` con una estructura anidada por curso → sección → módulo.

Ejemplo:

```
dumps/
└── FMI/
    ├── Tema 1/
    │   ├── Módulo A/
    │   │   └── recurso.pdf
    │   └── Módulo B/
    └── Tema 2/
        └── ...
```

Si `DUMP_ALL = True` en `main.py`, se crean snapshots JSON adicionales por sección y módulo.
---

## Personalización

- `COURSE_ALIASES` en `main.py`: mapea `courseid` → nombre de carpeta deseado.
- `DUMP_ALL` y `FULL_SANITIZER` en `main.py` controlan nivel de detalle y formato de nombres.

---

## Troubleshooting

- `login failed` → Revisa usuario/contraseña y `MOODLE_SITE`.
- `Cannot connect` → Verifica URL y conectividad.
- `No courses found` → Comprueba que tu usuario está matriculado en cursos.
- `Archivos no se descargan` → Revisa permisos en Moodle (algunos recursos pueden requerir roles/fuentes específicas).

Si necesitas más detalle, ejecuta con `--verbose` y comparte el log (recortando cualquier credencial).

---

## Agradecimientos

Gracias a Tyr7z por el código base


---

©️ 2026 — MooviDump Enhanced by Lord_Alastor78
