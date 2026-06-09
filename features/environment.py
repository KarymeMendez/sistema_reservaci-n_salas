import os
import threading
import django
from datetime import timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "salas_estudio.settings")
os.environ.setdefault("BEHAVE_DJANGO_TEST", "1")

django.setup()

from django.test.utils import setup_test_environment
from django.test.runner import DiscoverRunner
from django.contrib.staticfiles.testing import LiveServerTestCase

setup_test_environment()

_runner = DiscoverRunner(verbosity=0)
_old_config = _runner.setup_databases()


def before_all(context):
    from django.test.testcases import LiveServerThread
    from django.db import connections

    context.test_runner = _runner
    context.server_thread = threading.Thread(target=_start_server, args=(context,))

    import django.test.testcases as tc
    context.live_server = _LiveServer()
    context.live_server.start()
    context.base_url = context.live_server.url

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    context.driver = webdriver.Chrome(options=opts)
    context.driver.implicitly_wait(5)


def after_all(context):
    context.driver.quit()
    context.live_server.stop()
    _runner.teardown_databases(_old_config)


def before_scenario(context, scenario):
    from django.contrib.auth.models import User
    from reservaciones.models import Sala, Reservacion
    Reservacion.objects.all().delete()
    Sala.objects.all().delete()
    User.objects.all().delete()


def after_scenario(context, scenario):
    pass


class _LiveServer:
    def __init__(self):
        from django.test.testcases import LiveServerTestCase
        self._thread = None
        self.url = None
        self._stop_event = threading.Event()

    def start(self):
        import socket
        from django.test.testcases import LiveServerThread
        from django.db import connections
        conn = connections["default"]
        self._thread = LiveServerThread("localhost", [8181], connections_override=None)
        self._thread.daemon = True
        self._thread.start()
        self._thread.is_ready.wait()
        if self._thread.error:
            raise self._thread.error
        self.url = f"http://localhost:{self._thread.port}"

    def stop(self):
        if self._thread:
            self._thread.terminate()
            self._thread.join()


def _start_server(context):
    pass
