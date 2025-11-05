#!/usr/bin/env python
import os
import sys
import django

# Agregar el directorio del proyecto al path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AsistenciaProject.settings')
django.setup()

from ldap3 import Server, Connection, ALL


def test_ldap_connection():
    from django.conf import settings

    ldap_config = settings.LDAP_CONFIG

    try:
        server = Server(ldap_config['SERVER_URI'], get_info=ALL)
        conn = Connection(server,
                          user=ldap_config['BIND_DN'],
                          password=ldap_config['BIND_PASSWORD'])

        if conn.bind():
            print("✅ Conexión LDAP exitosa!")

            # Buscar usuarios
            conn.search(ldap_config['USER_BASE'], '(objectclass=*)', attributes=['cn', 'Correo', 'Area', 'CI', 'CodigoDeDependencia', 'CodigoDelArea'])
            print(f"📊 Usuarios encontrados: {len(conn.entries)}")


            for entry in conn.entries[:3]:  # Mostrar primeros 3
                print(entry)


        else:
            print("❌ Error en la conexión LDAP")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_ldap_connection()