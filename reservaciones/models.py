from django.db import models
from django.contrib.auth.models import User


class Sala(models.Model):
    nombre = models.CharField(max_length=100)
    capacidad = models.PositiveIntegerField()
    ubicacion = models.CharField(max_length=200)
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Sala"
        verbose_name_plural = "Salas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Reservacion(models.Model):
    VIGENTE = "VIGENTE"
    CANCELADA = "CANCELADA"
    ESTADOS = [
        (VIGENTE, "Vigente"),
        (CANCELADA, "Cancelada"),
    ]

    usuario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reservaciones"
    )
    sala = models.ForeignKey(
        Sala, on_delete=models.CASCADE, related_name="reservaciones"
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    asistentes = models.PositiveIntegerField()
    proposito = models.CharField(max_length=200)
    estado = models.CharField(max_length=10, choices=ESTADOS, default=VIGENTE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Reservación"
        verbose_name_plural = "Reservaciones"
        ordering = ["fecha", "hora_inicio"]

    def __str__(self):
        return f"{self.sala} - {self.fecha} {self.hora_inicio}-{self.hora_fin}"
