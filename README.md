# Sistema de Reservación de Salas de Estudio

Aplicación web Django para reservar salas de estudio. Desarrollada con TDD y BDD.

## Requisitos

- Python 3.10+
- pip
- Google Chrome + ChromeDriver (para pruebas BDD con Selenium)
- Apache JMeter 5.6+ (para pruebas de rendimiento)

## Instalación

```bash
git clone <url-del-repositorio>
cd salas_estudio
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```

## Variables de entorno

Crea un archivo `.env` o exporta las variables:

```bash
export DJANGO_SETTINGS_MODULE=salas_estudio.settings
export SECRET_KEY=clave-secreta-segura
```

## Migraciones y datos iniciales

```bash
python manage.py migrate
python manage.py loaddata reservaciones/fixtures/salas_iniciales.json
python manage.py crear_usuarios_prueba
```

Esto crea las 4 salas del sistema y los siguientes usuarios de prueba:

| Usuario  | Contraseña      |
|----------|-----------------|
| alumno1  | TestPass123!    |
| alumno2  | TestPass123!    |

Para crear un superusuario de administración:

```bash
python manage.py createsuperuser
```

## Ejecutar la aplicación

```bash
python manage.py runserver
```

Accede en: http://127.0.0.1:8000/

## Ejecutar pruebas unitarias

```bash
python manage.py test reservaciones --verbosity=2
```

## Cobertura de código

```bash
coverage run --source=reservaciones --omit="*/migrations/*,*/management/*" manage.py test reservaciones
coverage report -m
coverage html    # genera carpeta htmlcov/
```

Archivos excluidos de cobertura:
- `*/migrations/*` — código generado automáticamente por Django.
- `*/management/*` — comando utilitario sin lógica de negocio.

## PEP 8

```bash
flake8 reservaciones/ --exclude=reservaciones/migrations/ --max-line-length=100
```

## Complejidad ciclomática

```bash
radon cc reservaciones/ -s -a --exclude "*/migrations/*"
```

Todas las funciones y métodos tienen complejidad ≤ 10 (promedio A).

## Pruebas BDD (Behave + Selenium)

Requiere Google Chrome y ChromeDriver instalados y en el PATH.

```bash
cd salas_estudio
behave features/reservaciones.feature
behave features/cancelaciones.feature
# O ejecutar todos:
behave
```

Los escenarios cubren CA-01 a CA-11. Selenium corre en modo headless.

## Pruebas de rendimiento (JMeter)

```bash
# Levantar la aplicación con datos iniciales
python manage.py runserver 0.0.0.0:8000

# Ejecutar el plan de pruebas
jmeter -n -t jmeter/plan_reservaciones.jmx \
       -l jmeter/resultados.jtl \
       -e -o jmeter/reporte_html/
```

Consulta `jmeter/README_jmeter.md` para la interpretación de resultados.

## Estructura del proyecto

```
salas_estudio/
├── reservaciones/
│   ├── models.py          # Entidades: Sala, Reservacion
│   ├── services.py        # Lógica de negocio reutilizable
│   ├── forms.py           # Validaciones de formulario
│   ├── views.py           # Controladores HTTP
│   ├── urls.py            # Rutas de la app
│   ├── admin.py           # Registro en panel admin
│   ├── fixtures/          # Datos iniciales (salas)
│   └── tests.py           # Pruebas unitarias UT-01 a UT-20
├── features/
│   ├── reservaciones.feature   # Escenarios BDD HU-01
│   ├── cancelaciones.feature   # Escenarios BDD HU-02
│   ├── environment.py          # Configuración Behave + Selenium
│   └── steps/
│       ├── autenticacion_steps.py
│       ├── reservacion_steps.py
│       └── cancelacion_steps.py
├── templates/             # Plantillas HTML (Bootstrap 5)
├── jmeter/                # Plan JMeter y reportes
├── htmlcov/               # Reporte HTML de cobertura
└── README.md
```
