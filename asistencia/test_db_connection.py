import os
import sys
import django

# Configurar el entorno Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AsistenciaProject.settings')
django.setup()

from django.db import connections
from asistencia.models import Area
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
try:
    with connections['sqlserver'].cursor() as cursor:

        cursor.execute("SELECT Id_Direccion, Desc_Direccion, GrupoNomina FROM RH_Unidades_Organizativas;")
        areas = cursor.fetchall()
        for area in areas:
            area, creado = Area.objects.update_or_create(
                cod_area = area[0],
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

except Exception as e:
    print(f"❌ Error SQL Server: {e}")