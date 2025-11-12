from django.contrib.auth.models import User
from ldap3 import Server, Connection, ALL


def get_user(username):

    try:
        server = Server('ldap.uh.cu', 389, get_info=ALL)
        conn = Connection(server, 'cn=admin,dc=uh,dc=cu', 'killdirectory')

        if conn.bind():
            conn.search(
                'ou=Trabajadores,dc=uh,dc=cu',
                f'(uid={username})',
                attributes=['cn', 'sn', 'Correo']
            )

            if conn.entries:
                entry = conn.entries[0]
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'first_name': getattr(entry, 'cn', [''])[0],
                        'last_name': getattr(entry, 'sn', [''])[0],
                        'email': getattr(entry, 'Correo', [''])[0],
                        'is_active': True
                    }
                )
                if created:
                    return user

            else:
                return  None

            conn.unbind()

        return None

    except Exception as e:
        return f'Erro de consulta: {e}'


