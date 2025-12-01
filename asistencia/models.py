
import datetime

from django.db import models

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q


class Area(models.Model):
    """Modelo para representar las áreas/departamentos de la organización"""
    cod_area = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100)
    unidad_padre = models.CharField(max_length=20)
    assets = models.IntegerField()

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['assets', 'cod_area', 'nombre']
        db_table = 'area'

    def __str__(self):
        return self.nombre


class ResponsableArea(models.Model):
    """Modelo para asignar responsables a las áreas"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='areas_responsable')
    area = models.ForeignKey(Area, on_delete=models.CASCADE, related_name='responsables')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Responsable de Área'
        verbose_name_plural = 'Responsables de Áreas'
        unique_together = ['usuario', 'area']
        ordering = ['area__nombre', 'usuario__username']
        db_table = 'responsable_area'

    def __str__(self):
        return f"{self.usuario.username} - {self.area.nombre}"

    @classmethod
    def get_responsables_activos_area(cls, area):
        """Obtiene todos los responsables activos de un área"""
        return cls.objects.filter(area=area, activo=True).select_related('usuario')

    @classmethod
    def get_areas_responsable_usuario(cls, usuario):
        """Obtiene todas las áreas de las que un usuario es responsable"""
        return cls.objects.filter(usuario=usuario, activo=True).select_related('area')

    @classmethod
    def es_responsable_area(cls, usuario, area):
        """Verifica si un usuario es responsable de un área específica"""
        return cls.objects.filter(usuario=usuario, area=area, activo=True).exists()



class Incidencia(models.Model):
    CHOICES = {
        'Asistió puntual': 'Asistió puntual',
        'Asistió con retardo': 'Asistió con retardo',
        'Falta justificada': 'Falta justificada',
        'Falta injustificada': 'Falta injustificada',
        'Vacaciones': 'Vacaciones',
        'Incapacidad médica': 'Incapacidad',
        'Permiso con goce de sueldo': 'Permiso con goce de sueldo',
        'Permiso sin goce de sueldo': 'Permiso sin goce de sueldo',
        'Teletrabajo': 'Teletrabajo',
        'Licencia especial': 'Licencia especial',
    }
    area = models.ForeignKey(Area, on_delete=models.CASCADE, db_column='Area')
    uid = models.CharField(max_length=100, help_text='Usuario LDAP', db_column='UID', default=None)
    empleado = models.CharField(max_length=100, help_text='FK a EmpleadosGral', db_column='Empleado')
    estado = models.CharField(max_length=150, choices=CHOICES, db_column='Estado', default=CHOICES['Asistió puntual'], null=True, blank=True)
    fecha_asistencia = models.DateField(db_column='Fecha_Asistencia', default=datetime.date.today)

    class Meta:
        verbose_name = 'Incidencia'
        verbose_name_plural = 'Incidencias'
        db_table = 'incidencia'
        unique_together = ['uid', 'fecha_asistencia']
