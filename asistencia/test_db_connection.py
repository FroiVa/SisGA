import os
import sys
import django

# Configurar el entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AsistenciaProject.settings')
django.setup()

from django.db import connections
from asistencia.models import Area, Trabajador
from django.conf import settings

# Probar conexión a PostgreSQL
try:
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL conectado: {version[0]}")
except Exception as e:
    print(f"❌ Error PostgreSQL: {e}")

resultados = {
    'creados': 0,
    'actualizados': 0,
    'errores': []
}


# Probar conexión a SQL Server
def coneccion(sql):
    datos = []
    try:
        with connections['sqlserver'].cursor() as cursor:
            cursor.execute(sql)
            datos = cursor.fetchall()
            cursor.close()
            # connections.close()

    except Exception as e:
        print(f"❌ Error SQL Server: {e}")
    return datos

def get_areas():
    areas = coneccion("SELECT Id_Direccion, Desc_Direccion, GrupoNomina FROM RH_Unidades_Organizativas;")
    for area in areas:
        area, creado = Area.objects.update_or_create(
            cod_area=area[0],
            defaults={
                'nombre': area[1],
                'unidad_padre': area[2],
            }
        )
        if creado:
            resultados['creados'] += 1
            print(f"✅ CREADO: {area.cod_area} (Nombre: {area.nombre})")
        else:
            resultados['actualizados'] += 1
            print(f"🔄 ACTUALIZADO: {area.cod_area} (Nombre: {area.nombre})")

def get_trabajadores():

    trabajadores = coneccion("SELECT No_CI, Nombre, Apellido_1, Apellido_2, Id_Direccion, Baja FROM Empleados_Gral where Baja=0;")

    for trabajador in trabajadores:
        area = Area.objects.get(cod_area=trabajador[4])

        trabajador, creado = Trabajador.objects.update_or_create(
            ci=trabajador[0],
            defaults={
                'nombre': trabajador[1],
                'apellidos': trabajador[2] + " " + trabajador[3],
                'area': area,
                'es_baja': trabajador[5],
            }
        )
        if creado:
            resultados['creados'] += 1
            print(f"✅ CREADO: {area.cod_area} (Nombre: {area.nombre})")
        else:
            resultados['actualizados'] += 1
            print(f"🔄 ACTUALIZADO: {area.cod_area} (Nombre: {area.nombre})")

if __name__ == '__main__':
    get_trabajadores()