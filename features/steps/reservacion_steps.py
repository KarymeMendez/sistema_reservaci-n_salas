from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from django.utils import timezone
from datetime import timedelta, time
from reservaciones.models import Sala, Reservacion
from django.contrib.auth.models import User


def get_wait(context, secs=10):
    return WebDriverWait(context.driver, secs)


@given('que existe una sala activa "{nombre}" con capacidad {capacidad:d}')
def step_crear_sala_activa(context, nombre, capacidad):
    Sala.objects.get_or_create(
        nombre=nombre,
        defaults={"capacidad": capacidad, "ubicacion": "Biblioteca, planta baja", "activa": True}
    )


@given('existe una sala inactiva "{nombre}"')
def step_crear_sala_inactiva(context, nombre):
    Sala.objects.get_or_create(
        nombre=nombre,
        defaults={"capacidad": 6, "ubicacion": "Biblioteca, planta alta", "activa": False}
    )


@given('que no existe otra reservación vigente para "{sala_nombre}" en el horario solicitado')
def step_sin_traslape(context, sala_nombre):
    pass


@given('que existe una reservación vigente para "{sala_nombre}" entre las "{h_inicio}" y las "{h_fin}"')
def step_reservacion_existente(context, sala_nombre, h_inicio, h_fin):
    sala = Sala.objects.get(nombre=sala_nombre)
    user, _ = User.objects.get_or_create(username="alumno1")
    user.set_password("TestPass123!")
    user.save()
    fecha = timezone.localdate() + timedelta(days=1)
    hi = time(*[int(x) for x in h_inicio.split(":")])
    hf = time(*[int(x) for x in h_fin.split(":")])
    Reservacion.objects.create(
        usuario=user, sala=sala, fecha=fecha,
        hora_inicio=hi, hora_fin=hf,
        asistentes=2, proposito="Reservación previa de prueba para el sistema",
        estado=Reservacion.VIGENTE,
    )


@when('navega al formulario de nueva reservación')
def step_ir_a_nueva(context):
    context.driver.get(f"{context.base_url}/reservaciones/nueva/")
    get_wait(context).until(
        EC.presence_of_element_located((By.ID, "form-nueva-reservacion"))
    )


@when('selecciona la sala "{sala_nombre}"')
def step_seleccionar_sala(context, sala_nombre):
    sala = Sala.objects.get(nombre=sala_nombre)
    select = Select(context.driver.find_element(By.NAME, "sala"))
    select.select_by_value(str(sala.pk))


@when('captura la fecha de mañana')
def step_capturar_fecha_manana(context):
    fecha = (timezone.localdate() + timedelta(days=1)).strftime("%Y-%m-%d")
    campo = context.driver.find_element(By.NAME, "fecha")
    context.driver.execute_script(
        "arguments[0].value = arguments[1];", campo, fecha
    )
    context._fecha_reservacion = fecha


@when('captura una fecha pasada')
def step_capturar_fecha_pasada(context):
    fecha = (timezone.localdate() - timedelta(days=1)).strftime("%Y-%m-%d")
    campo = context.driver.find_element(By.NAME, "fecha")
    context.driver.execute_script(
        "arguments[0].value = arguments[1];", campo, fecha
    )


@when('captura hora de inicio "{h_inicio}" y hora de fin "{h_fin}"')
def step_capturar_horario(context, h_inicio, h_fin):
    for nombre, valor in [("hora_inicio", h_inicio), ("hora_fin", h_fin)]:
        campo = context.driver.find_element(By.NAME, nombre)
        context.driver.execute_script(
            "arguments[0].value = arguments[1];", campo, valor
        )
    context._hora_inicio = h_inicio
    context._hora_fin = h_fin


@when('captura {asistentes:d} asistentes y propósito "{proposito}"')
def step_capturar_asistentes_proposito(context, asistentes, proposito):
    campo_asist = context.driver.find_element(By.NAME, "asistentes")
    campo_asist.clear()
    campo_asist.send_keys(str(asistentes))
    campo_prop = context.driver.find_element(By.NAME, "proposito")
    campo_prop.clear()
    campo_prop.send_keys(proposito)


@when('envía el formulario de reservación')
def step_enviar_formulario(context):
    context.driver.execute_script(
        "arguments[0].click();",
        context.driver.find_element(By.ID, "btn-guardar")
    )


@when('intenta reservar la sala inactiva "{sala_nombre}"')
def step_verificar_sala_inactiva_no_aparece(context, sala_nombre):
    context._sala_inactiva = sala_nombre


@when('se envían dos solicitudes simultáneas para "{sala_nombre}" en el mismo horario')
def step_solicitudes_concurrentes(context, sala_nombre):
    import threading
    from reservaciones.services import registrar_reservacion, ReservacionError
    sala = Sala.objects.get(nombre=sala_nombre)
    user = User.objects.get(username="alumno1")
    fecha = timezone.localdate() + timedelta(days=2)
    context._resultados_concurrencia = []

    def intentar(idx):
        try:
            r = registrar_reservacion(
                usuario=user, sala_id=sala.pk, fecha=fecha,
                hora_inicio=time(14, 0), hora_fin=time(15, 0),
                asistentes=1, proposito=f"Solicitud concurrente de prueba número {idx}",
            )
            context._resultados_concurrencia.append(("ok", r.pk))
        except Exception:
            context._resultados_concurrencia.append(("error", None))

    threads = [threading.Thread(target=intentar, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    context._sala_concurrencia = sala
    context._fecha_concurrencia = fecha


@then('el sistema registra la reservación con estado "VIGENTE"')
def step_verificar_vigente(context):
    wait = get_wait(context)
    wait.until(EC.url_contains("/reservaciones"))
    from reservaciones.models import Reservacion
    assert Reservacion.objects.filter(estado=Reservacion.VIGENTE).exists(), \
        "No se encontró ninguna reservación VIGENTE"


@then('muestra un mensaje de confirmación')
def step_verificar_mensaje_confirmacion(context):
    wait = get_wait(context)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "alert-success")))
    texto = context.driver.find_element(By.CLASS_NAME, "alert-success").text
    assert "exitosamente" in texto.lower() or "confirmación" in texto.lower() or \
        "registrada" in texto.lower(), f"Mensaje inesperado: {texto}"


@then('la reservación aparece en la lista de reservaciones')
def step_verificar_en_lista(context):
    wait = get_wait(context)
    wait.until(EC.presence_of_element_located((By.ID, "tabla-reservaciones")))
    tabla = context.driver.find_element(By.ID, "tabla-reservaciones").text
    assert "VIGENTE" in tabla, "La reservación no aparece en la tabla"


@then('el sistema no registra la nueva reservación')
def step_verificar_no_registrada(context):
    from reservaciones.models import Reservacion
    count = Reservacion.objects.filter(estado=Reservacion.VIGENTE).count()
    assert count <= 1, f"Se encontraron {count} reservaciones vigentes cuando no debería haber más de 1"


@then('muestra un mensaje de sala no disponible')
def step_verificar_mensaje_no_disponible(context):
    body = context.driver.find_element(By.TAG_NAME, "body").text
    assert "no está disponible" in body.lower() or "horario solicitado" in body.lower(), \
        f"No se encontró mensaje de sala no disponible. Texto: {body[:200]}"


@then('muestra un mensaje de capacidad excedida')
def step_verificar_mensaje_capacidad(context):
    body = context.driver.find_element(By.TAG_NAME, "body").text
    assert "capacidad" in body.lower(), \
        f"No se encontró mensaje de capacidad. Texto: {body[:200]}"


@then('muestra un mensaje de fecha inválida')
def step_verificar_mensaje_fecha(context):
    body = context.driver.find_element(By.TAG_NAME, "body").text
    assert "fecha" in body.lower() and (
        "anterior" in body.lower() or "inválida" in body.lower() or "válida" in body.lower()
    ), f"No se encontró mensaje de fecha inválida. Texto: {body[:200]}"


@then('la sala inactiva no aparece en las opciones del formulario')
def step_verificar_sala_no_aparece(context):
    context.driver.get(f"{context.base_url}/reservaciones/nueva/")
    get_wait(context).until(
        EC.presence_of_element_located((By.NAME, "sala"))
    )
    select = Select(context.driver.find_element(By.NAME, "sala"))
    opciones = [opt.text for opt in select.options]
    assert context._sala_inactiva not in opciones, \
        f"La sala inactiva '{context._sala_inactiva}' no debería aparecer en opciones"


@then('solo una reservación queda registrada como vigente')
def step_verificar_una_vigente(context):
    from reservaciones.models import Reservacion
    vigentes = Reservacion.objects.filter(
        sala=context._sala_concurrencia,
        fecha=context._fecha_concurrencia,
        estado=Reservacion.VIGENTE
    ).count()
    assert vigentes <= 1, \
        f"Se registraron {vigentes} reservaciones vigentes para el mismo horario"
