# language: es
Característica: Registrar una reservación (HU-01)
  Como usuario autenticado
  Quiero seleccionar una sala disponible y registrar una reservación
  Para asegurar el uso exclusivo de la sala durante un periodo determinado

  Antecedentes:
    Dado que existe una sala activa "Sala A" con capacidad 4
    Y existe una sala inactiva "Sala de mantenimiento"
    Y el usuario "alumno1" ha iniciado sesión

  Escenario: CA-01 Registrar una reservación válida
    Dado que no existe otra reservación vigente para "Sala A" en el horario solicitado
    Cuando navega al formulario de nueva reservación
    Y selecciona la sala "Sala A"
    Y captura la fecha de mañana
    Y captura hora de inicio "10:00" y hora de fin "11:00"
    Y captura 2 asistentes y propósito "Sesión de estudio grupal para examen"
    Y envía el formulario de reservación
    Entonces el sistema registra la reservación con estado "VIGENTE"
    Y muestra un mensaje de confirmación
    Y la reservación aparece en la lista de reservaciones

  Escenario: CA-02 Rechazar una reservación con horario traslapado
    Dado que existe una reservación vigente para "Sala A" entre las "10:00" y las "11:00"
    Cuando navega al formulario de nueva reservación
    Y selecciona la sala "Sala A"
    Y captura la fecha de mañana
    Y captura hora de inicio "10:30" y hora de fin "11:30"
    Y captura 2 asistentes y propósito "Sesión de estudio grupal para examen"
    Y envía el formulario de reservación
    Entonces el sistema no registra la nueva reservación
    Y muestra un mensaje de sala no disponible

  Escenario: CA-03 Rechazar una reservación que exceda la capacidad
    Cuando navega al formulario de nueva reservación
    Y selecciona la sala "Sala A"
    Y captura la fecha de mañana
    Y captura hora de inicio "10:00" y hora de fin "11:00"
    Y captura 5 asistentes y propósito "Sesión de estudio grupal para examen"
    Y envía el formulario de reservación
    Entonces el sistema no registra la nueva reservación
    Y muestra un mensaje de capacidad excedida

  Escenario: CA-04 Rechazar una fecha anterior al día actual
    Cuando navega al formulario de nueva reservación
    Y selecciona la sala "Sala A"
    Y captura una fecha pasada
    Y captura hora de inicio "10:00" y hora de fin "11:00"
    Y captura 2 asistentes y propósito "Sesión de estudio grupal para examen"
    Y envía el formulario de reservación
    Entonces el sistema no registra la nueva reservación
    Y muestra un mensaje de fecha inválida

  Escenario: CA-05 Rechazar una sala inactiva
    Cuando navega al formulario de nueva reservación
    Y intenta reservar la sala inactiva "Sala de mantenimiento"
    Entonces la sala inactiva no aparece en las opciones del formulario

  Escenario: CA-06 Evitar doble reservación ante solicitudes concurrentes
    Dado que no existe otra reservación vigente para "Sala A" en el horario solicitado
    Cuando se envían dos solicitudes simultáneas para "Sala A" en el mismo horario
    Entonces solo una reservación queda registrada como vigente
