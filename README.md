# 📚 MooviDump Enhanced

Descargador inteligente de contenidos de plataformas Moodle con interfaz amigable y avisos detallados de progreso.

## 🎯 Características

- ✅ **Descarga automática** de cursos completos desde Moodle
- ✅ **Estructura organizada** por curso → sección → módulo → archivo
- ✅ **Avisos detallados** en terminal para monitorear progreso
- ✅ **Sanitización de nombres** de archivos (evita caracteres inválidos)
- ✅ **Manejo robusto de errores** con continuidad de descarga
- ✅ **Aliases de cursos** para nombres personalizados
- ✅ **Snapshots JSON** opcionales (DUMP_ALL)
- ✅ **Timeout configurado** (30 segundos por archivo)

## 🚀 Instalación Rápida

### 1. Requisitos Previos
- Python 3.6 o superior
- Acceso a una plataforma Moodle con servicio web habilitado

### 2. Configurar Credenciales
```bash
# Copiar archivo de ejemplo
cp example.env .env

# Editar con tus credenciales
# MOODLE_SITE=https://tu-moodle.com
# MOODLE_USERNAME=tu_usuario
# MOODLE_PASSWORD=tu_contraseña
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar
```bash
python main.py
```

## 📊 Salida de Consola

El programa muestra un progreso detallado:

```
============================================================
📚 MooviDump Enhanced - Iniciando descarga...
============================================================

🔐 Iniciando sesión...
✅ Sesión iniciada correctamente
📡 Obteniendo información del sitio...
✅ Usuario ID: 12345
📥 Obteniendo lista de cursos...
✅ Se encontraron 3 curso(s)
📁 Directorio de descarga: C:\...\dumps

━━━ CURSO 1 ━━━
📂 [Fundamentos de Matemática] ID: 1678
   📍 Ubicación: dumps\FMI
   ⏳ Obteniendo contenidos...
   📋 Total de secciones: 8

   📑 [1/8] Sección: Tema 1
       ├─ Recurso de lectura (2 archivos)
           └─ ⬇️  apuntes.pdf... ✅ (245.3 KB)
           └─ ⬇️  ejercicios.pdf... ✅ (128.5 KB)
```

## ⚙️ Configuración

Edita `main.py` para personalizar:

### `DUMP_ALL = False`
- `False` (por defecto): Solo descarga archivos
- `True`: Incluye snapshots JSON de estructura

### `FULL_SANITIZER = False`
- `False` (por defecto): Mantiene espacios en nombres
- `True`: Reemplaza espacios con guiones bajos

### `COURSE_ALIASES`
```python
COURSE_ALIASES = {
    1678: "FMI",           # ID: 1678 → carpeta "FMI"
    1679: "AM",            # ID: 1679 → carpeta "AM"
    1680: "PROI",          # ID: 1680 → carpeta "PROI"
}
```

## 📁 Estructura de Salida

```
dumps/
├── FMI/                          # Curso (nombre o alias)
│   ├── Tema 1/                   # Sección
│   │   ├── Recurso de lectura/   # Módulo
│   │   │   ├── apuntes.pdf
│   │   │   └── ejercicios.pdf
│   │   └── Tareas/
│   │       └── tarea1.zip
│   ├── Tema 2/
│   │   └── ...
│   └── contents.json             # (si DUMP_ALL=True)
└── AM/
    └── ...
```

## 🔑 Variables de Entorno (.env)

```ini
MOODLE_SITE=https://moodle.ejemplo.com
MOODLE_USERNAME=tu_usuario
MOODLE_PASSWORD=tu_contraseña
```

## 📋 Dependencias

```
python-dotenv>=0.19.0
requests>=2.25.0
```

Instala todas con:
```bash
pip install -r requirements.txt
```

## 🛠️ Solución de Problemas

### Error: "Missing MOODLE_SITE in environment"
- Verifica que `.env` existe en la raíz del proyecto
- Comprueba que contiene `MOODLE_SITE=...`

### Error: "login failed!"
- Verifica credenciales en `.env`
- Confirma que el usuario tiene acceso al sitio Moodle
- Verifica que el servicio web está habilitado en Moodle

### Error: "Faltan MOODLE_USERNAME o MOODLE_PASSWORD"
- Asegúrate de tener ambas variables en `.env`
- No deben estar vacías

### Archivos no se descargan
- Verifica que tienes permisos en Moodle
- Algunos archivos pueden estar restringidos
- El programa continuará con otros cursos/archivos

## 🎨 Símbolos Usados

| Símbolo | Significado |
|---------|-------------|
| 📚 | MooviDump |
| 🔐 | Autenticación |
| 📡 | Obtención de datos |
| 📥 | Descarga de cursos |
| 📂 | Carpeta/Curso |
| 📍 | Ubicación |
| 📋 | Total de items |
| 📑 | Sección |
| ⏳ | Cargando/Esperando |
| ⬇️ | Descargando archivo |
| ✅ | Éxito |
| ❌ | Error |
| ⚠️ | Advertencia |

## 📝 Notas Importantes

- Los archivos ocultos en Moodle **no se descargan**
- La estructura de carpetas respeta la jerarquía del curso
- Los nombres de archivo se sanitizan automáticamente
- Se usa timeout de 30 segundos por archivo
- El programa es resistente a errores (continúa si uno falla)

## 🔄 Versión Optimizada

Este código incluye mejoras sobre la versión original:
- Avisos de progreso detallados
- Mejor estructura visual en terminal
- Manejo robusto de errores
- Información de tamaño de archivo
- Contadores de progreso

Ver [CHANGELOG.md](CHANGELOG.md) para detalles técnicos.

## 📧 Soporte

Para reportar problemas o sugerencias, verifica:
1. Que tus credenciales de Moodle sean correctas
2. Que tienes permisos suficientes
3. Que el servicio web de Moodle está disponible

## 📄 Licencia

Este proyecto es un descendiente mejorado de MooviDump original.

---

**Última actualización:** Enero 2026

