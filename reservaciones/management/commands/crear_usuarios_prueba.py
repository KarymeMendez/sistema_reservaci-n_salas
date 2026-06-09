from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea usuarios de prueba reproducibles"

    def handle(self, *args, **options):
        usuarios = [
            ("alumno1", "alumno1@test.com", "TestPass123!"),
            ("alumno2", "alumno2@test.com", "TestPass123!"),
        ]
        for username, email, password in usuarios:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": email},
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Usuario '{username}' creado."))
            else:
                self.stdout.write(f"Usuario '{username}' ya existe.")
