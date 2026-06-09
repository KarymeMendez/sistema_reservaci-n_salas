from datetime import date, time, timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Reservacion, Sala
from .services import (
    ReservacionError,
    cancelar_reservacion,
    hay_traslape,
    registrar_reservacion,
)


def fecha_futura(dias=1):
    return timezone.localdate() + timedelta(days=dias)


def crear_sala(nombre="Sala Test", capacidad=10, activa=True):
    return Sala.objects.create(
        nombre=nombre,
        capacidad=capacidad,
        ubicacion="Edificio Test",
        activa=activa,
    )


def crear_usuario(username="testuser"):
    user, _ = User.objects.get_or_create(username=username)
    user.set_password("TestPass123!")
    user.save()
    return user


def crear_reservacion(usuario, sala, fecha=None, hora_inicio=None, hora_fin=None):
    return Reservacion.objects.create(
        usuario=usuario,
        sala=sala,
        fecha=fecha or fecha_futura(),
        hora_inicio=hora_inicio or time(10, 0),
        hora_fin=hora_fin or time(11, 0),
        asistentes=2,
        proposito="Reunión de estudio grupal",
        estado=Reservacion.VIGENTE,
    )


class TestModeloReservacion(TestCase):
    def test_ut01_crear_reservacion_valida(self):
        sala = crear_sala()
        usuario = crear_usuario()
        reservacion = registrar_reservacion(
            usuario=usuario,
            sala_id=sala.pk,
            fecha=fecha_futura(),
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Sesión de estudio grupal",
        )
        self.assertEqual(reservacion.estado, Reservacion.VIGENTE)
        self.assertIsNotNone(reservacion.pk)


class TestFormularioReservacion(TestCase):
    def setUp(self):
        self.sala = crear_sala(capacidad=4)
        self.usuario = crear_usuario()

    def test_ut02_rechazar_proposito_menor_10_caracteres(self):
        from .forms import ReservacionForm
        form = ReservacionForm(data={
            "sala": self.sala.pk,
            "fecha": fecha_futura(),
            "hora_inicio": "10:00",
            "hora_fin": "11:00",
            "asistentes": 2,
            "proposito": "Corto",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("proposito", form.errors)

    def test_ut03_rechazar_asistentes_cero(self):
        from .forms import ReservacionForm
        form = ReservacionForm(data={
            "sala": self.sala.pk,
            "fecha": fecha_futura(),
            "hora_inicio": "10:00",
            "hora_fin": "11:00",
            "asistentes": 0,
            "proposito": "Propósito válido para prueba",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("asistentes", form.errors)

    def test_ut03b_rechazar_asistentes_negativos(self):
        from .forms import ReservacionForm
        form = ReservacionForm(data={
            "sala": self.sala.pk,
            "fecha": fecha_futura(),
            "hora_inicio": "10:00",
            "hora_fin": "11:00",
            "asistentes": -1,
            "proposito": "Propósito válido para prueba",
        })
        self.assertFalse(form.is_valid())

    def test_ut04_rechazar_asistentes_superiores_a_capacidad(self):
        with self.assertRaises(ReservacionError) as ctx:
            registrar_reservacion(
                usuario=self.usuario,
                sala_id=self.sala.pk,
                fecha=fecha_futura(),
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                asistentes=5,
                proposito="Sesión de estudio grupal",
            )
        self.assertIn("capacidad", str(ctx.exception))

    def test_ut05_rechazar_fecha_pasada(self):
        from .forms import ReservacionForm
        form = ReservacionForm(data={
            "sala": self.sala.pk,
            "fecha": date.today() - timedelta(days=1),
            "hora_inicio": "10:00",
            "hora_fin": "11:00",
            "asistentes": 2,
            "proposito": "Propósito válido para prueba",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("fecha", form.errors)

    def test_ut06_rechazar_hora_fin_menor_igual_inicio(self):
        from .forms import ReservacionForm
        form = ReservacionForm(data={
            "sala": self.sala.pk,
            "fecha": fecha_futura(),
            "hora_inicio": "11:00",
            "hora_fin": "10:00",
            "asistentes": 2,
            "proposito": "Propósito válido para prueba",
        })
        self.assertFalse(form.is_valid())


class TestServicioReservacion(TestCase):
    def setUp(self):
        self.sala = crear_sala(capacidad=10)
        self.usuario = crear_usuario()

    def test_ut07_rechazar_duracion_menor_30_minutos(self):
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=self.usuario,
                sala_id=self.sala.pk,
                fecha=fecha_futura(),
                hora_inicio=time(10, 0),
                hora_fin=time(10, 20),
                asistentes=2,
                proposito="Sesión de estudio grupal",
            )

    def test_ut07b_rechazar_duracion_mayor_2_horas(self):
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=self.usuario,
                sala_id=self.sala.pk,
                fecha=fecha_futura(),
                hora_inicio=time(9, 0),
                hora_fin=time(12, 0),
                asistentes=2,
                proposito="Sesión de estudio grupal",
            )

    def test_ut08_detectar_traslape_parcial(self):
        fecha = fecha_futura()
        crear_reservacion(
            self.usuario, self.sala, fecha=fecha,
            hora_inicio=time(10, 0), hora_fin=time(11, 0)
        )
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=self.usuario,
                sala_id=self.sala.pk,
                fecha=fecha,
                hora_inicio=time(10, 30),
                hora_fin=time(11, 30),
                asistentes=2,
                proposito="Sesión de estudio grupal",
            )

    def test_ut08b_detectar_traslape_contenido(self):
        fecha = fecha_futura()
        crear_reservacion(
            self.usuario, self.sala, fecha=fecha,
            hora_inicio=time(9, 0), hora_fin=time(12, 0)
        )
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=self.usuario,
                sala_id=self.sala.pk,
                fecha=fecha,
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                asistentes=2,
                proposito="Sesión de estudio grupal",
            )

    def test_ut08c_detectar_traslape_total(self):
        fecha = fecha_futura()
        crear_reservacion(
            self.usuario, self.sala, fecha=fecha,
            hora_inicio=time(10, 0), hora_fin=time(11, 0)
        )
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=self.usuario,
                sala_id=self.sala.pk,
                fecha=fecha,
                hora_inicio=time(10, 0),
                hora_fin=time(11, 0),
                asistentes=2,
                proposito="Sesión de estudio grupal",
            )

    def test_ut09_permitir_horarios_adyacentes(self):
        fecha = fecha_futura()
        r1 = registrar_reservacion(
            usuario=self.usuario,
            sala_id=self.sala.pk,
            fecha=fecha,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Sesión de estudio grupal primera",
        )
        r2 = registrar_reservacion(
            usuario=self.usuario,
            sala_id=self.sala.pk,
            fecha=fecha,
            hora_inicio=time(11, 0),
            hora_fin=time(12, 0),
            asistentes=2,
            proposito="Sesión de estudio grupal segunda",
        )
        self.assertEqual(r1.estado, Reservacion.VIGENTE)
        self.assertEqual(r2.estado, Reservacion.VIGENTE)

    def test_ut10_ignorar_reservaciones_canceladas(self):
        fecha = fecha_futura()
        r = crear_reservacion(
            self.usuario, self.sala, fecha=fecha,
            hora_inicio=time(10, 0), hora_fin=time(11, 0)
        )
        r.estado = Reservacion.CANCELADA
        r.save()
        nueva = registrar_reservacion(
            usuario=self.usuario,
            sala_id=self.sala.pk,
            fecha=fecha,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Sesión de estudio grupal",
        )
        self.assertEqual(nueva.estado, Reservacion.VIGENTE)


class TestVistaReservacion(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = crear_usuario()
        self.sala = crear_sala(capacidad=10)

    def test_ut11_impedir_acceso_anonimo(self):
        response = self.client.get(reverse("nueva_reservacion"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('nueva_reservacion')}",
            fetch_redirect_response=False,
        )

    def test_ut12_crear_reservacion_post_valido(self):
        self.client.login(username="testuser", password="TestPass123!")
        response = self.client.post(
            reverse("nueva_reservacion"),
            {
                "sala": self.sala.pk,
                "fecha": fecha_futura(),
                "hora_inicio": "10:00",
                "hora_fin": "11:00",
                "asistentes": 2,
                "proposito": "Sesión de estudio grupal",
            },
        )
        self.assertRedirects(response, reverse("lista_reservaciones"))
        self.assertEqual(
            Reservacion.objects.filter(usuario=self.usuario).count(), 1
        )


class TestServicioCancelacion(TestCase):
    def setUp(self):
        self.sala = crear_sala()
        self.usuario = crear_usuario("propietario")
        self.otro_usuario = crear_usuario("otro")

    def _reservacion_futura(self, horas=2):
        ahora = timezone.localtime(timezone.now())
        inicio = (ahora + timedelta(hours=horas)).replace(second=0, microsecond=0)
        fin = (inicio + timedelta(hours=1)).replace(second=0, microsecond=0)
        return Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=inicio.date(),
            hora_inicio=inicio.time(),
            hora_fin=fin.time(),
            asistentes=2,
            proposito="Sesión de estudio grupal",
            estado=Reservacion.VIGENTE,
        )

    def test_ut13_cancelar_reservacion_propia_vigente(self):
        r = self._reservacion_futura(horas=3)
        cancelar_reservacion(self.usuario, r.pk)
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.CANCELADA)
        self.assertIsNotNone(r.fecha_cancelacion)

    def test_ut14_rechazar_cancelacion_ajena(self):
        r = self._reservacion_futura(horas=3)
        with self.assertRaises(ReservacionError):
            cancelar_reservacion(self.otro_usuario, r.pk)
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.VIGENTE)

    def test_ut15_rechazar_cancelacion_exactamente_60_minutos(self):
        ahora = timezone.localtime(timezone.now())
        inicio = ahora + timedelta(minutes=60)
        fin = inicio + timedelta(hours=1)
        r = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=inicio.date(),
            hora_inicio=inicio.time(),
            hora_fin=fin.time(),
            asistentes=2,
            proposito="Sesión de estudio grupal",
            estado=Reservacion.VIGENTE,
        )
        with self.assertRaises(ReservacionError):
            cancelar_reservacion(self.usuario, r.pk)

    def test_ut16_rechazar_cancelacion_menos_60_minutos(self):
        ahora = timezone.localtime(timezone.now())
        inicio = ahora + timedelta(minutes=30)
        fin = inicio + timedelta(hours=1)
        r = Reservacion.objects.create(
            usuario=self.usuario,
            sala=self.sala,
            fecha=inicio.date(),
            hora_inicio=inicio.time(),
            hora_fin=fin.time(),
            asistentes=2,
            proposito="Sesión de estudio grupal",
            estado=Reservacion.VIGENTE,
        )
        with self.assertRaises(ReservacionError):
            cancelar_reservacion(self.usuario, r.pk)

    def test_ut17_rechazar_segunda_cancelacion(self):
        r = self._reservacion_futura(horas=3)
        cancelar_reservacion(self.usuario, r.pk)
        r.refresh_from_db()
        primera_fecha = r.fecha_cancelacion
        with self.assertRaises(ReservacionError):
            cancelar_reservacion(self.usuario, r.pk)
        r.refresh_from_db()
        self.assertEqual(r.fecha_cancelacion, primera_fecha)

    def test_ut18_impedir_cancelacion_anonima(self):
        r = self._reservacion_futura(horas=3)
        client = Client()
        response = client.post(reverse("cancelar_reservacion", args=[r.pk]))
        self.assertIn(response.status_code, [302, 403])

    def test_ut19_impedir_cancelacion_registro_ajeno_via_vista(self):
        r = self._reservacion_futura(horas=3)
        client = Client()
        client.login(username="otro", password="TestPass123!")
        client.post(reverse("cancelar_reservacion", args=[r.pk]))
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.VIGENTE)


class TestCoberturaSalas(TestCase):
    def test_str_sala(self):
        sala = crear_sala(nombre="Sala X")
        self.assertEqual(str(sala), "Sala X")

    def test_str_reservacion(self):
        sala = crear_sala()
        usuario = crear_usuario("usr_str_res")
        r = crear_reservacion(usuario, sala, fecha=fecha_futura(),
                              hora_inicio=time(10, 0), hora_fin=time(11, 0))
        self.assertIn("10:00:00", str(r))

    def test_sala_inactiva_rechazada_en_servicio(self):
        sala = crear_sala(nombre="SalaInact", activa=False)
        usuario = crear_usuario("usr_inactiva")
        with self.assertRaises(ReservacionError) as ctx:
            registrar_reservacion(
                usuario=usuario, sala_id=sala.pk, fecha=fecha_futura(),
                hora_inicio=time(10, 0), hora_fin=time(11, 0),
                asistentes=1, proposito="Proposito de prueba valido completo",
            )
        self.assertIn("no se encuentra disponible", str(ctx.exception))

    def test_sala_inexistente_en_servicio(self):
        usuario = crear_usuario("usr_inexistente")
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=usuario, sala_id=9999, fecha=fecha_futura(),
                hora_inicio=time(10, 0), hora_fin=time(11, 0),
                asistentes=1, proposito="Proposito de prueba valido completo",
            )

    def test_reservacion_inexistente_cancelar(self):
        usuario = crear_usuario("usr_cancel_inv")
        with self.assertRaises(ReservacionError):
            cancelar_reservacion(usuario, 9999)

    def test_hora_inicio_antes_apertura_servicio(self):
        sala = crear_sala(nombre="SalaApert")
        usuario = crear_usuario("usr_apertura")
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=usuario, sala_id=sala.pk, fecha=fecha_futura(),
                hora_inicio=time(7, 0), hora_fin=time(8, 30),
                asistentes=1, proposito="Proposito de prueba valido completo",
            )

    def test_hora_inicio_desde_19_servicio(self):
        sala = crear_sala(nombre="SalaCierre")
        usuario = crear_usuario("usr_cierre")
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=usuario, sala_id=sala.pk, fecha=fecha_futura(),
                hora_inicio=time(19, 0), hora_fin=time(20, 0),
                asistentes=1, proposito="Proposito de prueba valido completo",
            )

    def test_hora_fin_excede_20_servicio(self):
        sala = crear_sala(nombre="SalaFin20")
        usuario = crear_usuario("usr_fin20")
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=usuario, sala_id=sala.pk, fecha=fecha_futura(),
                hora_inicio=time(18, 0), hora_fin=time(20, 30),
                asistentes=1, proposito="Proposito de prueba valido completo",
            )

    def test_asistentes_menos_de_uno_servicio(self):
        sala = crear_sala(nombre="SalaAsist0")
        usuario = crear_usuario("usr_asist0")
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=usuario, sala_id=sala.pk, fecha=fecha_futura(),
                hora_inicio=time(10, 0), hora_fin=time(11, 0),
                asistentes=0, proposito="Proposito de prueba valido completo",
            )

    def test_hay_traslape_con_excluir_id(self):
        sala = crear_sala(nombre="SalaExcluir")
        usuario = crear_usuario("usr_excluir")
        r = crear_reservacion(usuario, sala, fecha=fecha_futura(),
                              hora_inicio=time(10, 0), hora_fin=time(11, 0))
        resultado = hay_traslape(sala, fecha_futura(), time(10, 0), time(11, 0), excluir_id=r.pk)
        self.assertFalse(resultado)

    def test_hora_inicio_antes_apertura_formulario(self):
        from .forms import ReservacionForm
        sala = crear_sala(nombre="SalaFormApert")
        form = ReservacionForm(data={
            "sala": sala.pk, "fecha": fecha_futura(),
            "hora_inicio": "07:00", "hora_fin": "09:00",
            "asistentes": 1, "proposito": "Proposito valido para prueba ahora",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("hora_inicio", form.errors)

    def test_hora_inicio_desde_19_formulario(self):
        from .forms import ReservacionForm
        sala = crear_sala(nombre="SalaForm19")
        form = ReservacionForm(data={
            "sala": sala.pk, "fecha": fecha_futura(),
            "hora_inicio": "19:00", "hora_fin": "20:00",
            "asistentes": 1, "proposito": "Proposito valido para prueba ahora",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("hora_inicio", form.errors)

    def test_hora_fin_excede_20_formulario(self):
        from .forms import ReservacionForm
        sala = crear_sala(nombre="SalaFormFin20")
        form = ReservacionForm(data={
            "sala": sala.pk, "fecha": fecha_futura(),
            "hora_inicio": "18:00", "hora_fin": "20:30",
            "asistentes": 1, "proposito": "Proposito valido para prueba ahora",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("hora_fin", form.errors)


class TestVistasCobertura(TestCase):
    def setUp(self):
        self.client = Client()
        self.usuario = crear_usuario("vistas_usr")
        self.sala = crear_sala(nombre="SalaVistas", capacidad=10)
        self.client.login(username="vistas_usr", password="TestPass123!")

    def test_vista_nueva_reservacion_get(self):
        response = self.client.get(reverse("nueva_reservacion"))
        self.assertEqual(response.status_code, 200)

    def test_vista_nueva_reservacion_post_error_negocio(self):
        sala_inactiva = crear_sala(nombre="InactivaCob", activa=False)
        response = self.client.post(
            reverse("nueva_reservacion"),
            {
                "sala": sala_inactiva.pk, "fecha": fecha_futura(),
                "hora_inicio": "10:00", "hora_fin": "11:00",
                "asistentes": 1, "proposito": "Proposito valido para esta prueba hoy",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_vista_cancelar_get(self):
        r = Reservacion.objects.create(
            usuario=self.usuario, sala=self.sala,
            fecha=fecha_futura(5), hora_inicio=time(10, 0), hora_fin=time(11, 0),
            asistentes=1, proposito="Proposito valido para prueba",
            estado=Reservacion.VIGENTE,
        )
        response = self.client.get(reverse("cancelar_reservacion", args=[r.pk]))
        self.assertEqual(response.status_code, 200)

    def test_vista_cancelar_post_error_negocio(self):
        ahora = timezone.localtime(timezone.now())
        inicio = ahora + timedelta(minutes=30)
        fin = inicio + timedelta(hours=1)
        r = Reservacion.objects.create(
            usuario=self.usuario, sala=self.sala,
            fecha=inicio.date(), hora_inicio=inicio.time(), hora_fin=fin.time(),
            asistentes=1, proposito="Proposito valido para prueba",
            estado=Reservacion.VIGENTE,
        )
        response = self.client.post(reverse("cancelar_reservacion", args=[r.pk]))
        self.assertRedirects(response, reverse("lista_reservaciones"))

    def test_vista_lista_reservaciones(self):
        response = self.client.get(reverse("lista_reservaciones"))
        self.assertEqual(response.status_code, 200)

    def test_hora_fin_menor_inicio_en_servicio(self):
        sala = crear_sala(nombre="SalaFinMenor")
        usuario = crear_usuario("usr_fin_menor")
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=usuario, sala_id=sala.pk, fecha=fecha_futura(),
                hora_inicio=time(11, 0), hora_fin=time(10, 0),
                asistentes=1, proposito="Proposito de prueba valido completo",
            )

    def test_vista_nueva_post_form_invalido_muestra_errores(self):
        response = self.client.post(
            reverse("nueva_reservacion"),
            {
                "sala": self.sala.pk, "fecha": fecha_futura(),
                "hora_inicio": "10:00", "hora_fin": "10:00",
                "asistentes": 1, "proposito": "corto",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_hora_inicio_antes_apertura_directo_servicio(self):
        sala = crear_sala(nombre="SalaApDir")
        usuario = crear_usuario("usr_ap_dir")
        with self.assertRaises(ReservacionError):
            registrar_reservacion(
                usuario=usuario, sala_id=sala.pk, fecha=fecha_futura(),
                hora_inicio=time(7, 59), hora_fin=time(8, 59),
                asistentes=1, proposito="Proposito de prueba valido completo",
            )

    def test_vista_nueva_post_traslape_muestra_error(self):
        Reservacion.objects.create(
            usuario=self.usuario, sala=self.sala,
            fecha=fecha_futura(2), hora_inicio=time(10, 0), hora_fin=time(11, 0),
            asistentes=1, proposito="Reservacion previa de prueba valida",
            estado=Reservacion.VIGENTE,
        )
        response = self.client.post(
            reverse("nueva_reservacion"),
            {
                "sala": self.sala.pk, "fecha": fecha_futura(2),
                "hora_inicio": "10:00", "hora_fin": "11:00",
                "asistentes": 1, "proposito": "Intento de traslape en vista ahora",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_vista_cancelar_exitosa_redirige(self):
        ahora = timezone.localtime(timezone.now())
        inicio = ahora + timedelta(hours=3)
        fin = inicio + timedelta(hours=1)
        r = Reservacion.objects.create(
            usuario=self.usuario, sala=self.sala,
            fecha=inicio.date(), hora_inicio=inicio.time(), hora_fin=fin.time(),
            asistentes=1, proposito="Proposito valido para prueba cancelacion",
            estado=Reservacion.VIGENTE,
        )
        response = self.client.post(reverse("cancelar_reservacion", args=[r.pk]))
        self.assertRedirects(response, reverse("lista_reservaciones"))
        r.refresh_from_db()
        self.assertEqual(r.estado, Reservacion.CANCELADA)


class TestIntegracion(TestCase):
    def setUp(self):
        self.sala = crear_sala(capacidad=10)
        self.usuario = crear_usuario()

    def test_ut20_reservar_cancelar_volver_a_reservar(self):
        fecha = fecha_futura(3)
        r1 = registrar_reservacion(
            usuario=self.usuario,
            sala_id=self.sala.pk,
            fecha=fecha,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Primera sesión de estudio",
        )
        ahora = timezone.localtime(timezone.now())
        inicio_dt = timezone.make_aware(
            __import__("datetime").datetime.combine(fecha, time(10, 0)),
            timezone.get_current_timezone(),
        )
        with patch("reservaciones.services.timezone") as mock_tz:
            mock_tz.localdate.return_value = ahora.date()
            mock_tz.now.return_value = timezone.now()
            mock_tz.localtime.return_value = ahora - __import__("datetime").timedelta(hours=3)
            mock_tz.get_current_timezone.return_value = timezone.get_current_timezone()
            mock_tz.make_aware.return_value = inicio_dt
            cancelar_reservacion(self.usuario, r1.pk)

        r1.refresh_from_db()
        self.assertEqual(r1.estado, Reservacion.CANCELADA)

        r2 = registrar_reservacion(
            usuario=self.usuario,
            sala_id=self.sala.pk,
            fecha=fecha,
            hora_inicio=time(10, 0),
            hora_fin=time(11, 0),
            asistentes=2,
            proposito="Segunda sesión de estudio",
        )
        self.assertEqual(r2.estado, Reservacion.VIGENTE)

    def test_it01_concurrencia_solo_una_reservacion_vigente(self):
        from threading import Thread
        fecha = fecha_futura(5)
        resultados = []

        def intentar_reservar(idx):
            try:
                r = registrar_reservacion(
                    usuario=self.usuario,
                    sala_id=self.sala.pk,
                    fecha=fecha,
                    hora_inicio=time(14, 0),
                    hora_fin=time(15, 0),
                    asistentes=2,
                    proposito=f"Solicitud concurrente número {idx}",
                )
                resultados.append(("ok", r.pk))
            except ReservacionError as e:
                resultados.append(("bloqueado", str(e)))
            except Exception:
                resultados.append(("db_lock", "tabla bloqueada por concurrencia"))

        threads = [Thread(target=intentar_reservar, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        vigentes = Reservacion.objects.filter(
            sala=self.sala, fecha=fecha, estado=Reservacion.VIGENTE
        ).count()
        msg = "No deben existir dos reservaciones vigentes traslapadas para la misma sala."
        self.assertLessEqual(vigentes, 1, msg)
        exitosos = [r for r in resultados if r[0] == "ok"]
        self.assertLessEqual(len(exitosos), 1,
                             "Solo una solicitud debe tener éxito al mismo tiempo.")


class TestRamaServicioLine35(TestCase):
    def test_rechazar_hora_inicio_antes_08_en_servicio_directo(self):
        sala = Sala.objects.create(
            nombre="SalaLine35Unica", capacidad=5, ubicacion="Edificio Z", activa=True
        )
        usuario = User.objects.create_user("usr_line35_unico", password="TestPass123!")
        with self.assertRaises(ReservacionError) as ctx:
            registrar_reservacion(
                usuario=usuario,
                sala_id=sala.pk,
                fecha=fecha_futura(1),
                hora_inicio=time(7, 0),
                hora_fin=time(8, 30),
                asistentes=1,
                proposito="Proposito valido para prueba de rama directa",
            )
        self.assertIn("antes de las 08:00", str(ctx.exception))
