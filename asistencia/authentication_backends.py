# authentication_backends.py
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException


class LDAPBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            # Configuración del servidor LDAP
            server = Server('ldap.uh.cu:389', get_info=ALL)

            # Intentar bind con las credenciales del usuario
            user_dn = f"uid={username},ou=Trabajadores,dc=ud,dc=cu"

            with Connection(server, user=user_dn, password=password) as conn:
                if conn.bind():
                    # Autenticación exitosa, obtener o crear usuario en Django
                    try:
                        user = User.objects.get(username=username)
                    except User.DoesNotExist:
                        # Crear nuevo usuario
                        user = User(username=username)
                        user.set_unusable_password()
                        user.is_staff = False
                        user.is_superuser = False
                        user.save()
                    return user

        except LDAPException:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None