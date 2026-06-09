from datetime import datetime
from django.db import transaction
from django.utils import timezone

from .models import Reservacion, Sala

HORA_APERTURA = 8
HORA_CIERRE = 20
DURACION_MINIMA_MINUTOS = 30
DURACION_MAXIMA_MINUTOS = 120
MINUTOS_ANTICIPACION_CANCELACION = 60


class ReservacionError(Exception):
    pass


def hay_traslape(sala, fecha, hora_inicio, hora_fin, excluir_id=None):
    qs = Reservacion.objects.filter(
        sala=sala,
        fecha=fecha,
        estado=Reservacion.VIGENTE,
    )
    if excluir_id:
        qs = qs.exclude(pk=excluir_id)
    for r in qs:
        if hora_inicio < r.hora_fin and hora_fin > r.hora_inicio:
            return True
    return False


def _validar_horario(hora_inicio, hora_fin):
    apertura = datetime.strptime("08:00", "%H:%M").time()
    cierre_inicio = datetime.strptime("19:00", "%H:%M").time()
    cierre_fin = datetime.strptime("20:00", "%H:%M").time()

    if hora_inicio < apertura:
        raise ReservacionError("La hora de inicio no puede ser antes de las 08:00.")

    if hora_inicio >= cierre_inicio:
        raise ReservacionError("La hora de inicio debe ser antes de las 19:00.")

    if hora_fin <= hora_inicio:
        raise ReservacionError("La hora de fin debe ser posterior a la hora de inicio.")

    if hora_fin > cierre_fin:
        raise ReservacionError("La hora de fin no puede exceder las 20:00.")


def _validar_duracion(fecha, hora_inicio, hora_fin):
    inicio_dt = datetime.combine(fecha, hora_inicio)
    fin_dt = datetime.combine(fecha, hora_fin)
    duracion = (fin_dt - inicio_dt).seconds // 60

    if duracion < DURACION_MINIMA_MINUTOS:
        raise ReservacionError("La reservación debe durar al menos 30 minutos.")

    if duracion > DURACION_MAXIMA_MINUTOS:
        raise ReservacionError("La reservación no puede durar más de 2 horas.")


def validar_datos_reservacion(sala, fecha, hora_inicio, hora_fin, asistentes):
    hoy = timezone.localdate()
    if fecha < hoy:
        raise ReservacionError("La fecha no puede ser anterior al día actual.")

    _validar_horario(hora_inicio, hora_fin)
    _validar_duracion(fecha, hora_inicio, hora_fin)

    if not sala.activa:
        raise ReservacionError("La sala no se encuentra disponible para reservación.")

    if asistentes < 1:
        raise ReservacionError("El número de asistentes debe ser al menos 1.")

    if asistentes > sala.capacidad:
        raise ReservacionError(
            "El número de asistentes supera la capacidad de la sala."
        )


@transaction.atomic
def registrar_reservacion(usuario, sala_id, fecha, hora_inicio, hora_fin, asistentes, proposito):
    try:
        sala = Sala.objects.select_for_update().get(pk=sala_id)
    except Sala.DoesNotExist:
        raise ReservacionError("La sala especificada no existe.")

    validar_datos_reservacion(sala, fecha, hora_inicio, hora_fin, asistentes)

    if hay_traslape(sala, fecha, hora_inicio, hora_fin):
        raise ReservacionError(
            "La sala no está disponible en el horario solicitado."
        )

    reservacion = Reservacion.objects.create(
        usuario=usuario,
        sala=sala,
        fecha=fecha,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        asistentes=asistentes,
        proposito=proposito.strip(),
        estado=Reservacion.VIGENTE,
    )
    return reservacion


@transaction.atomic
def cancelar_reservacion(usuario, reservacion_id):
    try:
        reservacion = Reservacion.objects.select_for_update().get(pk=reservacion_id)
    except Reservacion.DoesNotExist:
        raise ReservacionError("La reservación no existe.")

    if reservacion.usuario != usuario:
        raise ReservacionError("No tienes permiso para cancelar esta reservación.")

    if reservacion.estado == Reservacion.CANCELADA:
        raise ReservacionError("La reservación ya fue cancelada.")

    ahora = timezone.localtime(timezone.now())
    inicio_dt = datetime.combine(reservacion.fecha, reservacion.hora_inicio)
    inicio_dt = timezone.make_aware(inicio_dt, timezone.get_current_timezone())
    minutos_restantes = (inicio_dt - ahora).total_seconds() / 60

    if minutos_restantes <= MINUTOS_ANTICIPACION_CANCELACION:
        raise ReservacionError(
            "El periodo de cancelación ha concluido. "
            "Solo se puede cancelar con más de 60 minutos de anticipación."
        )

    reservacion.estado = Reservacion.CANCELADA
    reservacion.fecha_cancelacion = timezone.now()
    reservacion.save()
    return reservacion
