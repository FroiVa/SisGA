
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
    # assets = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['cod_area', 'nombre']
        db_table = 'area'

    def __str__(self):
        return self.nombre


class ResponsableArea(models.Model):
    """Modelo para asignar responsables a las áreas"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='areas_responsable')
    area = models.ForeignKey(Area, on_delete=models.CASCADE, db_column='Area')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Responsable de Área'
        verbose_name_plural = 'Responsables de Áreas'
        unique_together = ['usuario', 'area']
        ordering = ['area__cod_area', 'usuario__username']
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


class Trabajador(models.Model):
    ci = models.CharField(max_length=11, db_column='CI')
    nombre = models.CharField(max_length=100, db_column='Nombre')
    apellidos = models.CharField(max_length=150, db_column='Apellidos')
    es_baja = models.BooleanField(db_column='Baja')

    area = models.ForeignKey(Area, on_delete=models.CASCADE, db_column='Area')

    class Meta:
        verbose_name = 'Trabajador'
        verbose_name_plural = 'Trabajadores'
        db_table = 'trabajador'
        ordering = ['nombre',]

    def __str__(self):
        return f"{self.nombre}"


class Estado(models.Model):
    clave = models.CharField(max_length=100, db_column='Clave')
    clave_id = models.CharField(max_length=10, db_column='Clave_id')
    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'
        db_table = 'estado'
        ordering = ['clave',]
    def __str__(self):
        return f"{self.clave}"

class Incidencia(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE, db_column='Area')
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, db_column='Trabajador', default=None)
    estado = models.ForeignKey(Estado, on_delete=models.CASCADE, db_column='Estado', null=True, default=None)
    fecha_asistencia = models.DateField(db_column='Fecha_Asistencia', default=datetime.date.today)

    class Meta:
        verbose_name = 'Incidencia'
        verbose_name_plural = 'Incidencias'
        db_table = 'incidencia'
        unique_together = ['trabajador', 'fecha_asistencia']
        ordering = ['trabajador',]



