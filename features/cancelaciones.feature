# language: es
Característica: Cancelar una reservación (HU-02)
  Como usuario autenticado propietario de una reservación
  Quiero cancelar una reservación que ya no utilizaré
  Para liberar la sala y permitir que otro usuario pueda reservarla

  Antecedentes:
    Dado que existe una sala activa "Sala B" con capacidad 8
    Y el usuario "alumno1" ha iniciado sesión

  Escenario: CA-07 Cancelar una reservación vigente con anticipación suficiente
    Dado que "alumno1" tiene una reservación vigente con inicio en 3 horas
    Cuando confirma la cancelación de su reservación
    Entonces el sistema cambia el estado a "CANCELADA"
    Y registra la fecha y hora de cancelación
    Y muestra un mensaje de cancelación exitosa
    Y la sala vuelve a estar disponible para ese horario

  Escenario: CA-08 Impedir que un usuario cancele una reservación ajena
    Dado que "alumno2" tiene una reservación vigente con inicio en 3 horas
    Y el usuario "otro_usuario" ha iniciado sesión
    Cuando intenta cancelar la reservación de "alumno2"
    Entonces el sistema rechaza la operación
    Y la reservación permanece en estado "VIGENTE"

  Escenario: CA-09 Impedir cancelación fuera del periodo permitido
    Dado que "alumno1" tiene una reservación vigente con inicio en 30 minutos
    Cuando confirma la cancelación de su reservación
    Entonces el sistema rechaza la operación
    Y muestra un mensaje de periodo de cancelación concluido

  Escenario: CA-10 Impedir cancelar nuevamente una reservación ya cancelada
    Dado que "alumno1" tiene una reservación ya cancelada
    Cuando intenta cancelarla nuevamente
    Entonces el sistema rechaza la operación
    Y muestra un mensaje de reservación ya cancelada

  Escenario: CA-11 Mantener la trazabilidad de la cancelación
    Dado que "alumno1" tiene una reservación vigente con inicio en 3 horas
    Cuando confirma la cancelación de su reservación
    Entonces la reservación aparece en el historial con estado "CANCELADA"
    Y se puede identificar la fecha y hora de cancelación
