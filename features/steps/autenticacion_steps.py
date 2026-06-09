from behave import given, when, then
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from django.contrib.auth.models import User


def login_usuario(context, username, password="TestPass123!"):
    driver = context.driver
    driver.get(f"{context.base_url}/login/")
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.NAME, "username")))
    driver.find_element(By.NAME, "username").clear()
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "password").clear()
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.execute_script(
        "arguments[0].click();",
        driver.find_element(By.ID, "btn-login")
    )
    wait.until(EC.url_contains("/reservaciones"))


@given('el usuario "{username}" ha iniciado sesión')
def step_usuario_logueado(context, username):
    User.objects.get_or_create(
        username=username,
        defaults={"email": f"{username}@test.com"}
    )
    user = User.objects.get(username=username)
    user.set_password("TestPass123!")
    user.save()
    login_usuario(context, username)


@given('el usuario "{username}" ha iniciado sesión')
def step_usuario_logueado_alt(context, username):
    step_usuario_logueado(context, username)
