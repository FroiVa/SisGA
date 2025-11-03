# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
import datetime

from django.db import models


class EmpleadosGral(models.Model):
    id_empleado = models.CharField(db_column='Id_Empleado', primary_key=True, max_length=15)  # Field name made lowercase.
    id_expediente = models.CharField(db_column='Id_Expediente', unique=True, max_length=15)  # Field name made lowercase.
    no_ci = models.CharField(db_column='No_CI', max_length=15)  # Field name made lowercase.
    nombre = models.CharField(db_column='Nombre', max_length=50)  # Field name made lowercase.
    apellido_1 = models.CharField(db_column='Apellido_1', max_length=50)  # Field name made lowercase.
    direccion = models.CharField(db_column='Direccion', max_length=255)  # Field name made lowercase.
    ciudad = models.CharField(db_column='Ciudad', max_length=50)  # Field name made lowercase.
    region = models.CharField(db_column='Region', max_length=50)  # Field name made lowercase.
    codigo_postal = models.CharField(db_column='Codigo_Postal', max_length=20)  # Field name made lowercase.
    pais = models.CharField(db_column='Pais', max_length=50)  # Field name made lowercase.
    exttelef = models.CharField(db_column='Exttelef', max_length=15)  # Field name made lowercase.
    telefono_particular = models.CharField(db_column='Telefono_Particular', max_length=30)  # Field name made lowercase.
    id_ccosto = models.CharField(db_column='Id_CCosto', max_length=10)  # Field name made lowercase.
    fecha_nacimiento = models.DateTimeField(db_column='Fecha_Nacimiento')  # Field name made lowercase.
    nota = models.CharField(db_column='Nota', max_length=255)  # Field name made lowercase.
    tipo_pago = models.SmallIntegerField(db_column='Tipo_Pago')  # Field name made lowercase.
    id_tipo_contrato = models.CharField(db_column='Id_Tipo_Contrato', max_length=3)  # Field name made lowercase.
    regimen_salarial = models.SmallIntegerField(db_column='Regimen_Salarial')  # Field name made lowercase.
    tarifa_horaria_con_reporte = models.BooleanField(db_column='Tarifa_Horaria_con_Reporte')  # Field name made lowercase.
    calendario = models.CharField(db_column='Calendario', max_length=3)  # Field name made lowercase.
    descontarsabado = models.BooleanField(db_column='DescontarSabado')  # Field name made lowercase.
    baja = models.BooleanField(db_column='Baja')  # Field name made lowercase.
    alta = models.BooleanField(db_column='Alta')  # Field name made lowercase.
    id_cargo = models.CharField(db_column='Id_Cargo', max_length=5)  # Field name made lowercase.
    id_categoria = models.CharField(db_column='Id_Categoria', max_length=5)  # Field name made lowercase.
    ngrupo = models.SmallIntegerField(db_column='NGrupo')  # Field name made lowercase.
    fecha_cargo = models.DateTimeField(db_column='Fecha_Cargo')  # Field name made lowercase.
    asignacion_por_cargo = models.BooleanField(db_column='Asignacion_por_Cargo')  # Field name made lowercase.
    nivel = models.SmallIntegerField(db_column='Nivel')  # Field name made lowercase.
    id_direccion = models.CharField(db_column='Id_Direccion', max_length=15)  # Field name made lowercase.
    plaza = models.BigIntegerField(db_column='Plaza')  # Field name made lowercase.
    id_causaalta = models.CharField(db_column='Id_CausaAlta', max_length=5)  # Field name made lowercase.
    id_fundamentacionalta = models.CharField(db_column='Id_FundamentacionAlta', max_length=5)  # Field name made lowercase.
    id_causabaja = models.CharField(db_column='Id_CausaBaja', max_length=5)  # Field name made lowercase.
    fecha_baja = models.DateTimeField(db_column='Fecha_Baja')  # Field name made lowercase.
    dias_descontar_alta = models.SmallIntegerField(db_column='Dias_Descontar_Alta')  # Field name made lowercase.
    dias_descontar_mov = models.SmallIntegerField(db_column='Dias_Descontar_Mov')  # Field name made lowercase.
    dias_descontar_baja = models.SmallIntegerField(db_column='Dias_Descontar_Baja')  # Field name made lowercase.
    saya = models.CharField(db_column='Saya', max_length=5)  # Field name made lowercase.
    pantalon = models.CharField(db_column='Pantalon', max_length=5)  # Field name made lowercase.
    camisa = models.CharField(db_column='Camisa', max_length=5)  # Field name made lowercase.
    zapato = models.CharField(db_column='Zapato', max_length=5)  # Field name made lowercase.
    sexo = models.CharField(db_column='Sexo', max_length=1)  # Field name made lowercase.
    color_piel = models.SmallIntegerField(db_column='Color_Piel')  # Field name made lowercase.
    color_pelo = models.SmallIntegerField(db_column='Color_Pelo')  # Field name made lowercase.
    estatura = models.DecimalField(db_column='Estatura', max_digits=7, decimal_places=2)  # Field name made lowercase.
    nombre_madre = models.CharField(db_column='Nombre_Madre', max_length=50)  # Field name made lowercase.
    nombre_padre = models.CharField(db_column='Nombre_Padre', max_length=50)  # Field name made lowercase.
    id_provincia = models.CharField(db_column='Id_Provincia', max_length=5)  # Field name made lowercase.
    id_municipio = models.CharField(db_column='Id_Municipio', max_length=5)  # Field name made lowercase.
    id_nivel_escolaridad = models.CharField(db_column='Id_Nivel_Escolaridad', max_length=3)  # Field name made lowercase.
    id_profesion = models.CharField(db_column='Id_Profesion', max_length=5)  # Field name made lowercase.
    fecha_contratacion = models.DateTimeField(db_column='Fecha_Contratacion')  # Field name made lowercase.
    fecha_terminacion_contrato = models.DateTimeField(db_column='Fecha_Terminacion_Contrato')  # Field name made lowercase.
    docente = models.BooleanField(db_column='Docente')  # Field name made lowercase.
    investigador = models.BooleanField(db_column='Investigador')  # Field name made lowercase.
    id_categoria_di = models.CharField(db_column='Id_Categoria_DI', max_length=5)  # Field name made lowercase.
    anoiniciodocencia = models.IntegerField(db_column='AnoInicioDocencia')  # Field name made lowercase.
    anointerruptodocencia = models.IntegerField(db_column='AnoInterruptoDocencia')  # Field name made lowercase.
    numero_radicacion_plaza = models.CharField(db_column='Numero_Radicacion_Plaza', max_length=50)  # Field name made lowercase.
    id_ubicacion_defensa = models.CharField(db_column='Id_Ubicacion_Defensa', max_length=5)  # Field name made lowercase.
    especificacion_defensa = models.CharField(db_column='Especificacion_Defensa', max_length=50)  # Field name made lowercase.
    imprescindible = models.BooleanField(db_column='Imprescindible')  # Field name made lowercase.
    fechamilitar = models.DateTimeField(db_column='FechaMilitar')  # Field name made lowercase.
    oc = models.BooleanField(db_column='OC')  # Field name made lowercase.
    militancia = models.SmallIntegerField(db_column='Militancia')  # Field name made lowercase.
    requisitoidiomatico = models.BooleanField(db_column='RequisitoIdiomatico')  # Field name made lowercase.
    requisitotecnico = models.BooleanField(db_column='RequisitoTecnico')  # Field name made lowercase.
    id_obra = models.CharField(db_column='Id_Obra', max_length=10)  # Field name made lowercase.
    tipo_vacuna = models.SmallIntegerField(db_column='Tipo_Vacuna')  # Field name made lowercase.
    fecha_vacuna = models.DateTimeField(db_column='Fecha_Vacuna')  # Field name made lowercase.
    nota_vacuna = models.CharField(db_column='Nota_Vacuna', max_length=100)  # Field name made lowercase.
    nivel_cp = models.SmallIntegerField(db_column='Nivel_CP')  # Field name made lowercase.
    id_direccion_cp = models.CharField(db_column='Id_Direccion_CP', max_length=15)  # Field name made lowercase.
    id_cargo_cp = models.CharField(db_column='Id_Cargo_CP', max_length=5)  # Field name made lowercase.
    id_categoria_cp = models.CharField(db_column='Id_Categoria_CP', max_length=5)  # Field name made lowercase.
    ngrupo_cp = models.SmallIntegerField(db_column='NGrupo_CP')  # Field name made lowercase.
    fecha_cargo_cp = models.DateTimeField(db_column='Fecha_Cargo_CP')  # Field name made lowercase.
    asignacion_por_cargo_cp = models.BooleanField(db_column='Asignacion_por_Cargo_CP')  # Field name made lowercase.
    id_grpevaluativo = models.CharField(db_column='Id_GrpEvaluativo', max_length=7)  # Field name made lowercase.
    id_grpsendrec = models.CharField(db_column='Id_GrpSendRec', max_length=7)  # Field name made lowercase.
    cuadroreserva = models.SmallIntegerField(db_column='CuadroReserva')  # Field name made lowercase.
    clasifcuadros = models.SmallIntegerField(db_column='ClasifCuadros')  # Field name made lowercase.
    situacionreserva = models.SmallIntegerField(db_column='SituacionReserva')  # Field name made lowercase.
    nivel_reserva = models.SmallIntegerField(db_column='Nivel_Reserva')  # Field name made lowercase.
    id_direccion_reserva = models.CharField(db_column='Id_Direccion_Reserva', max_length=15)  # Field name made lowercase.
    id_cargo_reserva = models.CharField(db_column='Id_Cargo_Reserva', max_length=5)  # Field name made lowercase.
    anosservicio = models.SmallIntegerField(db_column='AnosServicio')  # Field name made lowercase.
    antiguedaddispensa = models.SmallIntegerField(db_column='AntiguedadDispensa')  # Field name made lowercase.
    situacion = models.SmallIntegerField(db_column='Situacion')  # Field name made lowercase.
    id_actividad = models.CharField(db_column='Id_Actividad', max_length=3)  # Field name made lowercase.
    albergado = models.BooleanField(db_column='Albergado')  # Field name made lowercase.
    cubiculo = models.CharField(db_column='Cubiculo', max_length=5)  # Field name made lowercase.
    modulouniforme = models.CharField(db_column='ModuloUniforme', max_length=50)  # Field name made lowercase.
    fechasector = models.DateTimeField(db_column='FechaSector')  # Field name made lowercase.
    fechadireccion = models.DateTimeField(db_column='FechaDireccion')  # Field name made lowercase.
    mision_civil = models.BooleanField(db_column='Mision_Civil')  # Field name made lowercase.
    mision_militar = models.BooleanField(db_column='Mision_Militar')  # Field name made lowercase.
    ayuda_tecnica = models.BooleanField(db_column='Ayuda_Tecnica')  # Field name made lowercase.
    microbrigada = models.BooleanField(db_column='Microbrigada')  # Field name made lowercase.
    doble_expediente = models.BooleanField(db_column='Doble_Expediente')  # Field name made lowercase.
    disposicioncargo = models.BooleanField(db_column='DisposicionCargo')  # Field name made lowercase.
    prestacion_servicio = models.BooleanField(db_column='Prestacion_Servicio')  # Field name made lowercase.
    fecha_prestacion_servicio = models.DateTimeField(db_column='Fecha_Prestacion_Servicio')  # Field name made lowercase.
    mision = models.SmallIntegerField(db_column='Mision')  # Field name made lowercase.
    foto = models.BinaryField(db_column='Foto', blank=True, null=True)  # Field name made lowercase.
    id_user = models.CharField(db_column='Id_User', max_length=15)  # Field name made lowercase.
    fecha_op = models.DateTimeField(db_column='Fecha_Op')  # Field name made lowercase.
    id_subcategoria = models.CharField(db_column='Id_Subcategoria', max_length=5)  # Field name made lowercase.
    id_categoria_it = models.CharField(db_column='Id_Categoria_IT', max_length=5)  # Field name made lowercase.
    id_jornada = models.CharField(db_column='Id_Jornada', max_length=5)  # Field name made lowercase.
    id_tarjeta_reloj = models.CharField(db_column='Id_Tarjeta_Reloj', max_length=15)  # Field name made lowercase.
    tarjeta_reloj_on = models.BooleanField(db_column='Tarjeta_Reloj_On')  # Field name made lowercase.
    designacion = models.BooleanField(db_column='Designacion')  # Field name made lowercase.
    dias_dec_ley_91 = models.DecimalField(db_column='Dias_Dec_Ley_91', max_digits=10, decimal_places=4)  # Field name made lowercase.
    dias_dec_ley_91_saldo = models.DecimalField(db_column='Dias_Dec_Ley_91_Saldo', max_digits=10, decimal_places=4)  # Field name made lowercase.
    horario_regular = models.BooleanField(db_column='Horario_Regular')  # Field name made lowercase.
    apellido_2 = models.CharField(db_column='Apellido_2', max_length=50)  # Field name made lowercase.
    id_grado_cientifico = models.CharField(db_column='Id_Grado_Cientifico', max_length=5)  # Field name made lowercase.
    fecha_categoria_docente = models.DateTimeField(db_column='Fecha_Categoria_Docente')  # Field name made lowercase.
    pluriempleo = models.BooleanField(db_column='Pluriempleo')  # Field name made lowercase.
    horas_descontar_alta = models.DecimalField(db_column='Horas_Descontar_Alta', max_digits=7, decimal_places=4)  # Field name made lowercase.
    horas_descontar_mov = models.DecimalField(db_column='Horas_Descontar_Mov', max_digits=7, decimal_places=4)  # Field name made lowercase.
    horas_descontar_baja = models.DecimalField(db_column='Horas_Descontar_Baja', max_digits=7, decimal_places=4)  # Field name made lowercase.
    id_alta = models.IntegerField(db_column='Id_Alta')  # Field name made lowercase.
    agrupacion_alta = models.CharField(db_column='Agrupacion_Alta', max_length=5)  # Field name made lowercase.
    ano_alta = models.IntegerField(db_column='Ano_Alta')  # Field name made lowercase.
    id_baja = models.IntegerField(db_column='Id_Baja')  # Field name made lowercase.
    agrupacion_baja = models.CharField(db_column='Agrupacion_Baja', max_length=5)  # Field name made lowercase.
    ano_baja = models.IntegerField(db_column='Ano_Baja')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'Empleados_Gral'


class RhUnidadesOrganizativas(models.Model):
    pk = models.CompositePrimaryKey('Nivel', 'Id_Direccion')
    nivel = models.SmallIntegerField(db_column='Nivel')  # Field name made lowercase.
    id_direccion = models.CharField(db_column='Id_Direccion', max_length=15)  # Field name made lowercase.
    desc_direccion = models.CharField(db_column='Desc_Direccion', max_length=100)  # Field name made lowercase.
    clasificacion = models.CharField(db_column='Clasificacion', max_length=5)  # Field name made lowercase.
    gruponomina = models.CharField(db_column='GrupoNomina', max_length=15)  # Field name made lowercase.
    grupodisciplinalab = models.CharField(db_column='GrupoDisciplinaLab', max_length=15)  # Field name made lowercase.
    codgrpsendrec = models.CharField(db_column='CodGrpSendRec', max_length=7)  # Field name made lowercase.
    id_area = models.CharField(db_column='Id_Area', max_length=3)  # Field name made lowercase.
    nivelpadre = models.SmallIntegerField(db_column='NivelPadre')  # Field name made lowercase.
    id_direccionpadre = models.CharField(db_column='Id_DireccionPadre', max_length=15)  # Field name made lowercase.
    fecha_alta = models.DateTimeField(db_column='Fecha_Alta')  # Field name made lowercase.
    fecha_baja = models.DateTimeField(db_column='Fecha_Baja')  # Field name made lowercase.
    nota = models.CharField(db_column='Nota', max_length=255)  # Field name made lowercase.
    baja = models.BooleanField(db_column='Baja')  # Field name made lowercase.
    id_provincia = models.CharField(db_column='Id_Provincia', max_length=5)  # Field name made lowercase.
    id_municipio = models.CharField(db_column='Id_Municipio', max_length=5)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'RH_Unidades_Organizativas'

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
