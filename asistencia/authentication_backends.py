# backends.py
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import LDAPException
import logging

logger = logging.getLogger(__name__)


class LDAP3Backend(BaseBackend):
    """
    Backend de autenticación personalizado usando ldap3
    Solo permite login a usuarios que existan en la base de datos Django
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None

        # PRIMERO: Verificar si el usuario existe en la base de datos Django
        try:
            UserModel = get_user_model()
            user = UserModel.objects.get(username=username)

            # Verificar si el usuario está activo
            if not user.is_active:
                logger.warning(f"Usuario {username} intentó login pero está inactivo")
                return None

        except UserModel.DoesNotExist:
            # Usuario no existe en la base de datos
            logger.warning(f"Usuario {username} no encontrado")
            return None

        # SEGUNDO: Autenticar contra LDAP
        ldap_authenticated = self._authenticate_ldap(username, password)

        if ldap_authenticated:
            # Actualizar información del usuario desde LDAP
            self._update_user_from_ldap(user, username)
            logger.info(f"Login exitoso para usuario {username}")
            return user
        else:
            logger.warning(f"Falló autenticación LDAP para usuario {username}")
            return None

    def _authenticate_ldap(self, username, password):
        """
        Autentica al usuario contra el servidor LDAP
        """
        try:
            # Configuración del servidor LDAP - AJUSTA ESTOS VALORES
            server = Server(
                'ldap.uh.cu',
                port=389,
                get_info=ALL,
                use_ssl=False  # Cambia a True si usas LDAPS
            )

            # Construir el DN del usuario - AJUSTA ESTO SEGÚN TU ESTRUCTURA LDAP
            user_dn = f"uid={username},ou=Trabajadores,dc=uh,dc=cu"

            # Intentar autenticación
            conn = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True  # Se autobindea para autenticar
            )

            # Si llegamos aquí, la autenticación fue exitosa
            conn.unbind()
            return True

        except LDAPException as e:
            logger.error(f"Error LDAP para usuario {username}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en LDAP para {username}: {str(e)}")
            return False

    def _update_user_from_ldap(self, user, username):
        """
        Actualiza la información del usuario desde LDAP
        """
        try:
            server = Server('ldap.uh.cu', get_info=ALL)

            # Conexión con credenciales de administrador para buscar - AJUSTA ESTO
            admin_conn = Connection(
                server,
                'cn=admin,dc=uh,dc=cu',
                'killdirectory',
                auto_bind=True
            )

            # Buscar información del usuario
            search_base = 'ou=Trabajadores,dc=uh,dc=cu'
            search_filter = f'(uid={username})'
            attributes = ['cn', 'sn', 'mail', 'displayName']

            admin_conn.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=attributes
            )

            if admin_conn.entries:
                entry = admin_conn.entries[0]

                # Actualizar campos del usuario
                if 'cn' in entry and entry.cn.value:
                    user.first_name = entry.cn.value

                if 'sn' in entry and entry.sn.value:
                    user.last_name = entry.sn.value

                if 'Correo' in entry and entry.Correo.value:
                    user.email = entry.Correo.value

                user.save()
                logger.info(f"Información actualizada desde LDAP para {username}")

            admin_conn.unbind()

        except Exception as e:
            logger.warning(f"No se pudo actualizar información LDAP para {username}: {str(e)}")

    def get_user(self, user_id):
        """
        Obtiene un usuario por su ID
        """
        try:
            UserModel = get_user_model()
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None