# Pruebas de Rendimiento — JMeter

## Requisitos

- Apache JMeter 5.6+
- Aplicación corriendo en `localhost:8000` con datos iniciales cargados
- Usuarios `alumno1` y `alumno2` creados (`manage.py crear_usuarios_prueba`)

## Ejecutar las pruebas

```bash
# Desde la carpeta raíz del proyecto
python manage.py runserver 0.0.0.0:8000 &

# Ejecutar el plan completo (modo no-GUI)
jmeter -n -t jmeter/plan_reservaciones.jmx \
       -l jmeter/resultados.jtl \
       -e -o jmeter/reporte_html/

# Ver el reporte
open jmeter/reporte_html/index.html
```

## Escenarios

| ID      | Descripción                   | Usuarios | Iteraciones | Criterio            |
|---------|-------------------------------|----------|-------------|---------------------|
| PERF-01 | Consulta de reservaciones     | 50       | 5           | P95 ≤ 1500ms, <1% error |
| PERF-02 | Registro de reservaciones     | 30       | 3           | P95 ≤ 2000ms, <1% error |
| PERF-03 | Control de concurrencia       | 10       | 10          | 0 duplicados vigentes |

## Verificación post PERF-03

Después de ejecutar PERF-03, verificar en la base de datos:

```bash
python manage.py shell -c "
from reservaciones.models import Reservacion
from datetime import date
vigentes = Reservacion.objects.filter(
    sala_id=1,
    fecha=date(2027, 3, 15),
    hora_inicio='09:00:00',
    hora_fin='10:00:00',
    estado='VIGENTE'
).count()
print(f'Reservaciones vigentes para el horario concurrente: {vigentes}')
assert vigentes <= 1, 'ERROR: Hay duplicados'
print('OK: Control de concurrencia correcto')
"
```

## Interpretación de resultados esperados

- **Tasa de errores < 1%**: el servidor maneja la carga sin fallos.
- **P95 ≤ 1500ms (PERF-01)**: el listado responde rápido incluso con 50 usuarios.
- **P95 ≤ 2000ms (PERF-02)**: el POST de reservación (con validaciones + BD) es aceptable.
- **PERF-03**: `SELECT FOR UPDATE` en SQLite limita la concurrencia real; en producción
  usar PostgreSQL para mejor rendimiento bajo carga concurrente.

## Posibles cuellos de botella

- SQLite no es adecuado para alta concurrencia; migrar a PostgreSQL en producción.
- Las consultas de disponibilidad pueden optimizarse con índices en `(sala, fecha, estado)`.
- El login por cada iteración genera overhead; en producción usar tokens de sesión reutilizables.
