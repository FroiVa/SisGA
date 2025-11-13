import os
import sys
import django


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AsistenciaProject.settings')
django.setup()
from ldap3 import Server, Connection, ALL


def obtener_usuarios_ldap3(codigo_area):
    from django.conf import settings

    ldap_config = settings.LDAP_CONFIG

    try:
        server = Server(ldap_config['SERVER_URI'], get_info=ALL)
        conn = Connection(server,
                          user=ldap_config['BIND_DN'],
                          password=ldap_config['BIND_PASSWORD'],
                          auto_bind=True)

        base_dn = ldap_config['USER_BASE']
        filtro = f"(&(objectClass=Trabajador)(CodigoDeDependencia={codigo_area}))"

        atributos = ['uid', 'cn', 'sn', 'Correo', 'Area', 'CI', 'CodigoDeDependencia', 'CodigoDelArea', 'Assets']


        conn.search(base_dn, filtro, attributes=atributos)

        usuarios = []
        for entry in conn.entries:
            usuario = {
                'uid': str(entry.uid) if entry.uid else '',
                'cn': str(entry.cn) if entry.cn else '',
                'sn': str(entry.sn) if entry.sn else '',
                'email': str(entry.Correo) if entry.Correo else '',
                'area': str(entry.Area) if entry.Area else '',
                'ci': str(entry.CI) if entry.CI else '',
                'dependencia': str(entry.CodigoDeDependencia) if entry.CodigoDeDependencia else '',
                'codarea': str(entry.CodigoDelArea) if entry.CodigoDelArea else '',
                'assets': str(entry.Assets) if entry.Assets else '',
            }
            usuarios.append(usuario)

        return usuarios

    except Exception as e:
        print(f"Error: {e}")
        return []


if __name__ == "__main__":
    users = obtener_usuarios_ldap3('A3000-1')
    for user in users:
        print(user)