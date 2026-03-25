# FITKIT — Sistema de Gimnasio

Proyecto web para la gestión integral de un gimnasio: membresías, cursos, clases, asistencia y foro de clase. Incluye paneles para **Admin**, **Trainer** y **Cliente**, además de un módulo de calendario con las clases programadas.

## Tecnologías
- **Backend:** Django 6.0.3 + Django REST Framework
- **Frontend:** Templates Django + Tailwind CSS + CSS propio
- **Base de datos:** PostgreSQL (Supabase) o SQLite en modo desarrollo

## Funcionalidades principales
- Gestión de miembros, planes, cursos y clases.
- Inscripción a clases con validación de membresía activa y cupo máximo.
- Asistencia por clase.
- Publicaciones y comentarios por clase (foro).
- Paneles diferenciados por rol (Admin, Trainer, Cliente).
- Calendario de clases por usuario.

## Requisitos
- Python 3.10+
- pip
- PostgreSQL (Supabase) si se desea cumplir el entorno obligatorio

## Instalación
1. Crear y activar un entorno virtual.
2. Instalar dependencias:
```bash
pip install Django==6.0.3 djangorestframework psycopg2-binary Pillow
```
3. Crear el archivo `.env` en la raíz (basado en `.env.example`) y configurar variables.
4. Ejecutar migraciones:
```bash
python manage.py migrate
```
5. Iniciar el servidor:
```bash
python manage.py runserver
```

## Variables de entorno
El proyecto usa `.env` en la raíz. Si no se activa PostgreSQL, usará SQLite como respaldo.

Variables soportadas:
- `USE_SUPABASE_DB` (obligatorio para forzar PostgreSQL): `true` / `1`
- `SUPABASE_DATABASE_URL` (recomendado)  
- `SUPABASE_DB_NAME`
- `SUPABASE_DB_USER`
- `SUPABASE_DB_PASSWORD`
- `SUPABASE_DB_HOST`
- `SUPABASE_DB_PORT` (por defecto `5432`)
- `SUPABASE_DB_SSLMODE` (por defecto `require`)

Ejemplo mínimo:
```
USE_SUPABASE_DB=true
SUPABASE_DATABASE_URL=postgresql://usuario:password@host:5432/postgres
SUPABASE_DB_SSLMODE=require
```

## API REST (DRF)
Base URL: `/api/`

| Método | Endpoint | Descripción | Auth |
|---|---|---|---|
| POST | `/api/auth/registro/` | Registro de miembros | No |
| POST | `/api/auth/login/` | Login y entrega de token | No |
| GET | `/api/auth/me/` | Perfil del miembro autenticado | Sí |
| POST | `/api/auth/logout/` | Cierre de sesión y revocación de token | Sí |

**Header de autenticación**
```
Authorization: Token <uuid>
```

## Rutas Web principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/index/` | Landing |
| GET | `/roles/` | Selección de rol |
| GET | `/membresia/` | Planes de membresía |
| GET | `/admin-home/` | Panel admin |
| GET | `/trainer.html` | Panel trainer |
| GET | `/cliente.html` | Panel cliente |
| GET | `/trainer/cursos/` | Cursos del trainer |
| GET | `/trainer/clases/` | Clases del trainer |
| GET | `/cliente/clases/` | Clases disponibles para cliente |
| GET | `/cliente/mis-clases/` | Clases inscritas del cliente |

## Estructura del proyecto
- `config/`: configuración Django
- `gym/`: app principal (modelos, vistas, serializers, templates)
- `gym/templates/`: vistas HTML (cliente, trainer, admin)
- `gym/static/`: CSS y JS

## Notas importantes
- El archivo `.env` **no debe** subirse a GitHub (ya está en `.gitignore`).
- Para cumplir el requisito de PostgreSQL en Supabase, asegúrate de tener `USE_SUPABASE_DB=true` y las variables correctas.
- El archivo `db.sqlite3` es solo para desarrollo local si no se usa Supabase.

