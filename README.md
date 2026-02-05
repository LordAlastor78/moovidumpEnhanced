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
│   ├── [Tema 1]/
│   │   ├── [Módulo 1]/
│   │   │   └── archivo.pdf
│   │   └── [Módulo 2]/
│   │       └── recurso.zip
│   └── [Tema 2]/
│       └── ...
└── [Curso 2]/
    └── ...
```

## 🔧 Personalización

### Aliases de Cursos

En `main.py`, personaliza los nombres de tus cursos:

```python
COURSE_ALIASES = {
    1678: "FMI",
    1679: "AM",
    1680: "PROI",
    1681: "SD",
    # Añade más...
}
```

Si no añades un alias, se usa el nombre del curso en Moodle.

## ⚙️ Características

- ✅ Login automático con credenciales
- ✅ Descarga de todos los cursos matriculados
- ✅ Organización jerárquica (curso → tema → módulo → archivo)
- ✅ Nombres sanitizados (sin caracteres especiales)
- ✅ Manejo robusto de errores
- ✅ Logging detallado del progreso
- ✅ Timeouts y reintentos

## 🐛 Troubleshooting

**"login failed"** → Verifica usuario/contraseña en `.env`

**"Cannot connect"** → Comprueba la URL en `MOODLE_SITE`

**"No courses found"** → Asegúrate de estar matriculado en al menos un curso

**Archivos no se descargan** → Verifica permisos en Moodle o conectividad de red

## 📝 Notas

- Los archivos duplicados se sobrescriben
- Se ignoran automáticamente los cursos ocultos
- La información de login es local (nunca se envía a servidores externos)
- Requiere conexión a internet estable

## 🔒 Comportamiento respecto a archivos ya descargados

- Ahora el script evita descargar archivos que ya existen en `dumps/` con el mismo nombre. Si un fichero con el mismo nombre está presente, se omitirá la descarga y se registrará en los logs.
- Si quieres forzar la descarga de nuevo, elimina manualmente el archivo en `dumps/` o añade lógica de sobreescritura en `main.py`.

## ⚙️ Modos de ejecución (`run.py`)

- `1` Usar `.env`: usa las credenciales guardadas en `.env` (si existe). Si no existe, te preguntará si quieres crearla.
- `2` Credenciales temporales: introduces las credenciales para esta ejecución únicamente (no se guardan en `.env`).
- `3` Guardar credenciales: introduces las credenciales y se guardan en `.env` para usos futuros.

El password no se imprime en pantalla ni se guarda por defecto a menos que elijas explícitamente la opción 3.

## ✨ UI y flags

- `--force`: fuerza la redescarga de archivos aunque ya existan.
- `--verbose`: activa logging detallado (debug).
- `rich` se usa para una salida más agradable en la terminal; está incluido en `requirements.txt`.

Ejemplo de respuesta testeada:

```INFO: MooviDump Enhanced - Automatic Setup & Execution
INFO:
[1/3] Checking .env file and credential mode...
INFO: Elige modo de credenciales:
INFO:   1) Usar credenciales almacenadas en .env (si existe).
INFO:   2) Introducir credenciales para esta ejecución (no guardar).
INFO:   3) Introducir credenciales y guardarlas en .env.
Modo [1/2/3]: 2
   MOODLE_SITE [https://moovi.uvigo.gal]: 
   MOODLE_USERNAME: UR CREDENTIALS
   MOODLE_PASSWORD: UR CREDENTIALS
INFO: Using temporary credentials for this run (not saved).
INFO: 
[2/3] Installing dependencies...
INFO: ✓ Dependencies installed successfully
INFO: 
[3/3] Running main.py...
INFO: ------------------------------------------------------------
Forzar redescarga de archivos existentes? [y/N]: n
INFO: Launching main.py... 
INFO: Using credentials from environment/.env.
INFO: Attempting login to https://moovi.uvigo.gal...
INFO: Token received: 
INFO: login successful
INFO: Fetching site info...
INFO: User ID: URID
INFO: Private access key available (truncated):
INFO: Fetching courses for user URID...
INFO: Found 11 course(s)
INFO: Cursos disponibles:
┏━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ #    ┃ Course ID  ┃ Name                                ┃
┡━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1    │ 1686       │ Programación II                     │
│ 2    │ 1685       │ Arquitectura de computadoras I      │
│ 3    │ 1684       │ Algoritmos e estruturas de datos I  │
│ 4    │ 1683       │ Álxebra lineal                      │
│ 5    │ 1682       │ Técnicas de comunicación e liderado │
└──────┴────────────┴─────────────────────────────────────┘

Descargar todos los cursos? [y/N]: n
Introduce números (1,2,3) o IDs separados por comas (vacío para cancelar): 
Operación cancelada.
INFO: main.py exited with code 0
```