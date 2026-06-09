from django.contrib import admin
from .models import Sala, Reservacion


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ["nombre", "ubicacion", "capacidad", "activa"]
    list_filter = ["activa"]


@admin.register(Reservacion)
class ReservacionAdmin(admin.ModelAdmin):
    list_display = ["sala", "usuario", "fecha", "hora_inicio", "hora_fin", "estado"]
    list_filter = ["estado", "fecha"]
    readonly_fields = ["fecha_creacion", "fecha_cancelacion"]
