from datetime import datetime
from django import forms
from django.utils import timezone

from .models import Sala


class ReservacionForm(forms.Form):
    sala = forms.ModelChoiceField(
        queryset=Sala.objects.filter(activa=True),
        label="Sala",
        empty_label="-- Selecciona una sala --",
    )
    fecha = forms.DateField(
        label="Fecha",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    hora_inicio = forms.TimeField(
        label="Hora de inicio",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    hora_fin = forms.TimeField(
        label="Hora de fin",
        widget=forms.TimeInput(attrs={"type": "time"}),
    )
    asistentes = forms.IntegerField(
        label="Número de asistentes",
        min_value=1,
    )
    proposito = forms.CharField(
        label="Propósito",
        min_length=10,
        max_length=200,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    def clean_fecha(self):
        fecha = self.cleaned_data.get("fecha")
        hoy = timezone.localdate()
        if fecha and fecha < hoy:
            raise forms.ValidationError("La fecha no puede ser anterior al día actual.")
        return fecha

    def clean_hora_inicio(self):
        hora_inicio = self.cleaned_data.get("hora_inicio")
        if hora_inicio:
            apertura = datetime.strptime("08:00", "%H:%M").time()
            cierre_inicio = datetime.strptime("19:00", "%H:%M").time()
            if hora_inicio < apertura:
                raise forms.ValidationError(
                    "La hora de inicio no puede ser antes de las 08:00."
                )
            if hora_inicio >= cierre_inicio:
                raise forms.ValidationError(
                    "La hora de inicio debe ser antes de las 19:00."
                )
        return hora_inicio

    def clean_hora_fin(self):
        hora_fin = self.cleaned_data.get("hora_fin")
        if hora_fin:
            cierre = datetime.strptime("20:00", "%H:%M").time()
            if hora_fin > cierre:
                raise forms.ValidationError(
                    "La hora de fin no puede exceder las 20:00."
                )
        return hora_fin

    def clean(self):
        cleaned = super().clean()
        hora_inicio = cleaned.get("hora_inicio")
        hora_fin = cleaned.get("hora_fin")
        if hora_inicio and hora_fin:
            if hora_fin <= hora_inicio:
                raise forms.ValidationError(
                    "La hora de fin debe ser posterior a la hora de inicio."
                )
        return cleaned
