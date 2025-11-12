import os
import sys
import django


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AsistenciaProject.settings')
django.setup()
from ldap3 import Server, Connection, ALL
from asistencia.models import Area

def obtener_areas():
    from django.conf import settings

    ldap_config = settings.LDAP_CONFIG

    try:
        server = Server(ldap_config['SERVER_URI'], get_info=ALL)
        conn = Connection(server,
                          user=ldap_config['BIND_DN'],
                          password=ldap_config['BIND_PASSWORD'],
                          auto_bind=True)

        base_dn = ldap_config['USER_BASE']
        filtro = f"(&(objectClass=Trabajador))"

        atributos = ['Area', 'CodigoDeDependencia', 'CodigoDelArea', 'Assets']
        #

        conn.search(base_dn, filtro, attributes=atributos)

        areas = []
        for entry in conn.entries:
            area_entry = {
                'codarea': str(entry.CodigoDelArea) if entry.CodigoDelArea else '',
                'nombre': str(entry.Area) if entry.Area else '',
                'dependencia': str(entry.CodigoDeDependencia) if entry.CodigoDeDependencia else '',
                'assets': str(entry.Assets) if entry.Assets else '',
            }

            if area_entry not in areas:
                areas.append(area_entry)

        return areas

    except Exception as e:
        print(f"Error: {e}")
        return []



if __name__ == "__main__":
    areas = obtener_areas()
    for a in areas:
        area = Area()
        area.cod_area = a['codarea']
        area.nombre = a['nombre']
        area.unidad_padre = a['dependencia']
        area.assets = a['assets']
        area.save()
        print(a)