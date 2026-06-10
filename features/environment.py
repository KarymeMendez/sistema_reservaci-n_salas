import os
import django
from django.test.utils import setup_test_environment

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "salas_estudio.settings")
django.setup()
setup_test_environment()


def before_all(context):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    from django.test.testcases import LiveServerThread
    from django.contrib.staticfiles.handlers import StaticFilesHandler

    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    service = Service(ChromeDriverManager().install())
    context.driver = webdriver.Chrome(service=service, options=opts)
    context.driver.implicitly_wait(8)

    context.server_thread = LiveServerThread(
        host="localhost",
        static_handler=StaticFilesHandler,
        connections_override=None,
        port=0,
    )
    context.server_thread.daemon = True
    context.server_thread.start()
    context.server_thread.is_ready.wait()
    if context.server_thread.error:
        raise context.server_thread.error
    context.base_url = f"http://localhost:{context.server_thread.port}"


def after_all(context):
    context.driver.quit()
    context.server_thread.terminate()
    context.server_thread.join()


def before_scenario(context, scenario):
    from django.contrib.auth.models import User
    from reservaciones.models import Sala, Reservacion
    Reservacion.objects.all().delete()
    Sala.objects.all().delete()
    User.objects.all().delete()


def after_scenario(context, scenario):
    pass