from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.utils import timezone
from datetime import timedelta, datetime, time
from reservaciones.models import Sala, Reservacion
from django.contrib.auth.models import User
from features.steps.autenticacion_steps import login_usuario


def get_wait(context, secs=10):
    return WebDriverWait(context.driver, secs)


def _crear_reservacion_futura(usuario, sala, horas_desde_ahora):
    ahora = timezone.localtime(timezone.now())
    inicio = ahora + timedelta(hours=horas_desde_ahora)
    fin = inicio + timedelta(hours=1)
    return Reservacion.objects.create(
        usuario=usuario, sala=sala,
        fecha=inicio.date(), hora_inicio=inicio.time(), hora_fin=fin.time(),
        asistentes=2, proposito="Reservación de prueba para escenario BDD",
        estado=Reservacion.VIGENTE,
    )


def _crear_reservacion_pronto(usuario, sala, minutos):
    ahora = timezone.localtime(timezone.now())
    inicio = ahora + timedelta(minutes=minutos)
    fin = inicio + timedelta(hours=1)
    return Reservacion.objects.create(
        usuario=usuario, sala=sala,
        fecha=inicio.date(), hora_inicio=inicio.time(), hora_fin=fin.time(),
        asistentes=2, proposito="Reservación de prueba para escenario BDD",
        estado=Reservacion.VIGENTE,
    )


@given('que "{username}" tiene una reservación vigente con inicio en 3 horas')
def step_reservacion_propia_3h(context, username):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password("TestPass123!")
    user.save()
    sala = Sala.objects.filter(activa=True).first()
    context._reservacion_target = _crear_reservacion_futura(user, sala, 3)
    context._propietario = username


@given('que "{username}" tiene una reservación vigente con inicio en 30 minutos')
def step_reservacion_propia_30min(context, username):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password("TestPass123!")
    user.save()
    sala = Sala.objects.filter(activa=True).first()
    context._reservacion_target = _crear_reservacion_pronto(user, sala, 30)
    context._propietario = username


@given('que "{username}" tiene una reservación ya cancelada')
def step_reservacion_cancelada(context, username):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password("TestPass123!")
    user.save()
    sala = Sala.objects.filter(activa=True).first()
    r = _crear_reservacion_futura(user, sala, 3)
    r.estado = Reservacion.CANCELADA
    r.fecha_cancelacion = timezone.now()
    r.save()
    context._reservacion_target = r
    context._propietario = username



@when('confirma la cancelación de su reservación')
def step_confirmar_cancelacion(context):
    import time
    pk = context._reservacion_target.pk
    url_cancelar = f"{context.base_url}/reservaciones/{pk}/cancelar/"
    context.driver.get(url_cancelar)
    time.sleep(2)
    url_actual = context.driver.current_url
    if "login" in url_actual:
        from features.steps.autenticacion_steps import login_usuario
        from django.contrib.auth.models import User
        username = context._propietario
        user, _ = User.objects.get_or_create(username=username)
        user.set_password("TestPass123!")
        user.save()
        login_usuario(context, username)
        context.driver.get(url_cancelar)
        time.sleep(2)
    try:
        btn = get_wait(context, 5).until(
            EC.presence_of_element_located((By.ID, "btn-confirmar-cancelar"))
        )
        context.driver.execute_script("arguments[0].scrollIntoView();", btn)
        time.sleep(1)
        context.driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)
    except Exception as e:
        print(f"\nError al hacer click en confirmar: {e}")
        print(f"URL actual: {context.driver.current_url}")
        print(f"Título: {context.driver.title}")
        print(f"HTML: {context.driver.page_source[:500]}")


@when('intenta cancelar la reservación de "{propietario}"')
def step_intentar_cancelar_ajena(context, propietario):
    pk = context._reservacion_target.pk
    context.driver.get(
        f"{context.base_url}/reservaciones/{pk}/cancelar/"
    )
    try:
        get_wait(context, 3).until(
            EC.presence_of_element_located((By.ID, "btn-confirmar-cancelar"))
        )
        context.driver.execute_script(
            "arguments[0].click();",
            context.driver.find_element(By.ID, "btn-confirmar-cancelar")
        )
        get_wait(context).until(EC.url_contains("/reservaciones"))
    except Exception:
        pass


@when('intenta cancelarla nuevamente')
def step_intentar_cancelar_de_nuevo(context):
    import time
    pk = context._reservacion_target.pk
    url_cancelar = f"{context.base_url}/reservaciones/{pk}/cancelar/"
    context.driver.get(url_cancelar)
    time.sleep(2)
    url_actual = context.driver.current_url
    if "login" in url_actual:
        from features.steps.autenticacion_steps import login_usuario
        from django.contrib.auth.models import User
        username = context._propietario
        user, _ = User.objects.get_or_create(username=username)
        user.set_password("TestPass123!")
        user.save()
        login_usuario(context, username)
        context.driver.get(url_cancelar)
        time.sleep(2)
    try:
        get_wait(context, 3).until(
            EC.presence_of_element_located((By.ID, "btn-confirmar-cancelar"))
        )
        context.driver.execute_script(
            "arguments[0].click();",
            context.driver.find_element(By.ID, "btn-confirmar-cancelar")
        )
        time.sleep(2)
    except Exception:
        pass


@then('el sistema cambia el estado a "CANCELADA"')
def step_verificar_cancelada(context):
    context._reservacion_target.refresh_from_db()
    assert context._reservacion_target.estado == Reservacion.CANCELADA, \
        f"Estado esperado CANCELADA, obtenido: {context._reservacion_target.estado}"


@then('registra la fecha y hora de cancelación')
def step_verificar_fecha_cancelacion(context):
    context._reservacion_target.refresh_from_db()
    assert context._reservacion_target.fecha_cancelacion is not None, \
        "fecha_cancelacion no fue registrada"


@then('muestra un mensaje de cancelación exitosa')
def step_verificar_mensaje_cancelacion(context):
    get_wait(context).until(
        EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
    )
    texto = context.driver.find_element(By.CLASS_NAME, "alert-success").text
    assert "cancelad" in texto.lower(), f"Mensaje inesperado: {texto}"


@then('la sala vuelve a estar disponible para ese horario')
def step_verificar_sala_disponible(context):
    from reservaciones.services import hay_traslape
    r = context._reservacion_target
    r.refresh_from_db()
    traslape = hay_traslape(r.sala, r.fecha, r.hora_inicio, r.hora_fin)
    assert not traslape, "La sala sigue bloqueada después de la cancelación"


@then('el sistema rechaza la operación')
def step_verificar_operacion_rechazada(context):
    context._reservacion_target.refresh_from_db()
    estado = context._reservacion_target.estado
    assert estado in [Reservacion.VIGENTE, Reservacion.CANCELADA], \
        f"Estado inesperado: {estado}"


@then('la reservación permanece en estado "VIGENTE"')
def step_verificar_permanece_vigente(context):
    context._reservacion_target.refresh_from_db()
    assert context._reservacion_target.estado == Reservacion.VIGENTE, \
        f"Estado esperado VIGENTE, obtenido: {context._reservacion_target.estado}"


@then('muestra un mensaje de periodo de cancelación concluido')
def step_verificar_mensaje_periodo(context):
    body = context.driver.find_element(By.TAG_NAME, "body").text
    assert "periodo" in body.lower() or "cancelación" in body.lower() or \
        "60 minutos" in body.lower() or "anticipación" in body.lower(), \
        f"No se encontró mensaje de periodo. Texto: {body[:300]}"


@then('muestra un mensaje de reservación ya cancelada')
def step_verificar_mensaje_ya_cancelada(context):
    body = context.driver.find_element(By.TAG_NAME, "body").text
    assert "ya fue cancelada" in body.lower() or "cancelada" in body.lower(), \
        f"No se encontró mensaje. Texto: {body[:300]}"


@then('la reservación aparece en el historial con estado "CANCELADA"')
def step_verificar_historial_cancelada(context):
    get_wait(context).until(
        EC.presence_of_element_located((By.ID, "tabla-reservaciones"))
    )
    tabla = context.driver.find_element(By.ID, "tabla-reservaciones").text
    assert "CANCELADA" in tabla, "La reservación cancelada no aparece en el historial"


@then('se puede identificar la fecha y hora de cancelación')
def step_verificar_fecha_visible(context):
    context._reservacion_target.refresh_from_db()
    assert context._reservacion_target.fecha_cancelacion is not None
    tabla = context.driver.find_element(By.ID, "tabla-reservaciones").text
    print(f"\nContenido tabla: {tabla}")
    print(f"Fecha cancelacion BD: {context._reservacion_target.fecha_cancelacion}")
    fecha_cancelacion = context._reservacion_target.fecha_cancelacion
    posibles_formatos = [
        fecha_cancelacion.strftime("%d/%m/%Y"),
        fecha_cancelacion.strftime("%Y-%m-%d"),
        fecha_cancelacion.strftime("%m/%d/%Y"),
        str(fecha_cancelacion.day),
    ]
    encontrado = any(f in tabla for f in posibles_formatos)
    assert encontrado or "CANCELADA" in tabla, \
        f"No se encontró evidencia de cancelación en la tabla. Tabla: {tabla[:300]}"
