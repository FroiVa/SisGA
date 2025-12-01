import django
from django.conf import settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AsistenciaProject.settings')
django.setup()

from django.db import connections

# Probar conexión a PostgreSQL
try:
    with connections['default'].cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL conectado: {version[0]}")
except Exception as e:
    print(f"❌ Error PostgreSQL: {e}")

# Probar conexión a SQL Server
try:
    with connections['sqlserver'].cursor() as cursor:
        cursor.execute("SELECT * FROM Empleados_Gral;")
        empleados = cursor.fetchall()
        for empleado in empleados[:10]:
            print(empleado)

except Exception as e:
    print(f"❌ Error SQL Server: {e}")