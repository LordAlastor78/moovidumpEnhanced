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

