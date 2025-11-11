# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import datetime

from django.db import models

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q


class Area(models.Model):
    """Modelo para representar las áreas/departamentos de la organización"""
    cod_area = models.CharField(max_length=20)
    nombre = models.CharField(max_length=100, unique=True)
    unidad_padre = models.CharField(max_length=20)
    assets = models.IntegerField()

    class Meta:
        verbose_name = 'Área'
        verbose_name_plural = 'Áreas'
        ordering = ['nombre']

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

    def __str__(self):
        return f"{self.usuario.username} - {self.area.nombre}"


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

class Incidencias(models.Model):
    area = models.CharField(max_length=15, help_text='FK a RhUnidadesOrganizativas', db_column='Area')
    empleado = models.CharField(max_length=100, help_text='FK a EmpleadosGral', db_column='Empleado')
    estado = models.CharField(max_length=150, choices=CHOICES, db_column='Estado')
    fecha_asistencia = models.DateField(db_column='Fecha_Asistencia', default=datetime.date.today)
