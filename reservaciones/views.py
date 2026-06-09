from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReservacionForm
from .models import Reservacion
from .services import ReservacionError, cancelar_reservacion, registrar_reservacion


@login_required
def lista_reservaciones(request):
    reservaciones = Reservacion.objects.filter(
        usuario=request.user
    ).select_related("sala").order_by("-fecha", "-hora_inicio")
    return render(
        request,
        "reservaciones/lista.html",
        {"reservaciones": reservaciones},
    )


@login_required
def nueva_reservacion(request):
    if request.method == "POST":
        form = ReservacionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            try:
                registrar_reservacion(
                    usuario=request.user,
                    sala_id=data["sala"].pk,
                    fecha=data["fecha"],
                    hora_inicio=data["hora_inicio"],
                    hora_fin=data["hora_fin"],
                    asistentes=data["asistentes"],
                    proposito=data["proposito"],
                )
                messages.success(request, "Reservación registrada exitosamente.")
                return redirect("lista_reservaciones")
            except ReservacionError as e:
                messages.error(request, str(e))
    else:
        form = ReservacionForm()
    return render(request, "reservaciones/nueva.html", {"form": form})


@login_required
def cancelar_reservacion_view(request, pk):
    reservacion = get_object_or_404(Reservacion, pk=pk)
    if request.method == "POST":
        try:
            cancelar_reservacion(request.user, pk)
            messages.success(request, "Reservación cancelada exitosamente.")
        except ReservacionError as e:
            messages.error(request, str(e))
        return redirect("lista_reservaciones")
    return render(
        request,
        "reservaciones/cancelar_confirmar.html",
        {"reservacion": reservacion},
    )
