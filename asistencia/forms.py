# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import ResponsableArea, Area, Incidencia
from django.contrib.auth.models import User
import re
import calendar
import datetime


class LDAPAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=254,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuario LDAP',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )

    error_messages = {
        'invalid_login': "Credenciales incorrectas. Verifique su usuario y contraseña.",
        'inactive': "Esta cuenta está inactiva.",
    }


class UserCreationFlexibleForm(forms.ModelForm):
    """Formulario flexible para crear usuarios"""

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Validar formato del username
            if not re.match(r'^[a-zA-Z0-9_\.]+$', username):
                raise ValidationError(
                    "El nombre de usuario solo puede contener letras, números, puntos y guiones bajos."
                )
        return username

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 or password2:
            if password1 != password2:
                raise ValidationError("Las contraseñas no coinciden.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        # Si se proporcionó contraseña, usarla; sino, crear contraseña insegura
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # Para usuarios que solo usan LDAP

        if commit:
            user.save()
        return user


class ResponsableAreaForm(forms.ModelForm):
    """Formulario para asignar responsables con creación de usuarios"""

    # Campos para selección existente o creación nueva
    TIPO_SELECCION = [
        ('existente', 'Usuario Existente'),
        ('nuevo', 'Crear Nuevo Usuario'),
    ]

    tipo_usuario = forms.ChoiceField(
        choices=TIPO_SELECCION,
        initial='existente',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Tipo de Usuario"
    )

    # Campo para usuario existente
    usuario_existente = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        empty_label="Seleccionar usuario existente...",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Usuario Existente"
    )

    # Campos para nuevo usuario
    nuevo_username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre.usuario'
        }),
        label="Nombre de Usuario"
    )

    nuevo_first_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre'
        }),
        label="Nombre"
    )

    nuevo_last_name = forms.CharField(
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Apellido'
        }),
        label="Apellido"
    )

    nuevo_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@ejemplo.com'
        }),
        label="Email"
    )

    # Campos del modelo ResponsableArea
    areas = forms.ModelMultipleChoiceField(
        queryset=Area.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '6'
        }),
        label="Áreas a Asignar"
    )

    class Meta:
        model = ResponsableArea
        fields = ['activo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar querysets
        self.fields['usuario_existente'].queryset = User.objects.filter(
            is_active=True
        ).order_by('username')
        self.fields['areas'].queryset = Area.objects.all().order_by('nombre')

        # Si es edición, mostrar datos actuales
        if self.instance and self.instance.pk:
            self.fields['tipo_usuario'].initial = 'existente'
            self.fields['usuario_existente'].initial = self.instance.usuario
            self.fields['areas'].initial = [self.instance.area]

    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get('tipo_usuario')
        usuario_existente = cleaned_data.get('usuario_existente')
        nuevo_username = cleaned_data.get('nuevo_username')

        # Validaciones según el tipo de usuario
        if tipo_usuario == 'existente':
            if not usuario_existente:
                raise ValidationError("Debe seleccionar un usuario existente.")
        elif tipo_usuario == 'nuevo':
            if not nuevo_username:
                raise ValidationError("Debe ingresar un nombre de usuario para el nuevo usuario.")

            # Verificar si el nuevo username ya existe
            if User.objects.filter(username=nuevo_username).exists():
                raise ValidationError(f"El usuario '{nuevo_username}' ya existe.")

        # Validar que se hayan seleccionado áreas
        areas = cleaned_data.get('areas')
        if not areas:
            raise ValidationError("Debe seleccionar al menos un área.")

        return cleaned_data

    def save(self, commit=True):
        # Determinar el usuario
        tipo_usuario = self.cleaned_data.get('tipo_usuario')

        if tipo_usuario == 'existente':
            usuario = self.cleaned_data.get('usuario_existente')
        else:
            # Crear nuevo usuario
            usuario = User(
                username=self.cleaned_data.get('nuevo_username'),
                first_name=self.cleaned_data.get('nuevo_first_name', ''),
                last_name=self.cleaned_data.get('nuevo_last_name', ''),
                email=self.cleaned_data.get('nuevo_email', ''),
                is_active=True
            )
            usuario.set_unusable_password()  # Para autenticación LDAP
            usuario.save()

        # Crear asignaciones para cada área
        areas = self.cleaned_data.get('areas')
        activo = self.cleaned_data.get('activo', True)

        asignaciones_creadas = []
        for area in areas:
            # Usar get_or_create para evitar duplicados
            obj, created = ResponsableArea.objects.get_or_create(
                usuario=usuario,
                area=area,
                defaults={'activo': activo}
            )
            if created:
                asignaciones_creadas.append(obj)
            else:
                # Si ya existe, actualizar estado
                obj.activo = activo
                obj.save()
                asignaciones_creadas.append(obj)

        # Retornar la primera asignación para compatibilidad
        return asignaciones_creadas[0] if asignaciones_creadas else None


class BuscarCrearUsuarioForm(forms.Form):
    """Formulario para buscar o crear usuarios rápidamente"""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese nombre de usuario...'
        }),
        label="Usuario"
    )

    accion = forms.ChoiceField(
        choices=[
            ('buscar', 'Buscar Usuario Existente'),
            ('crear', 'Crear Usuario si no Existe')
        ],
        initial='crear',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Acción"
    )


class AsignacionRapidaForm(forms.Form):
    """Formulario para asignación rápida de responsables"""

    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'nombre.usuario'
        }),
        label="Usuario"
    )

    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Área"
    )

    crear_usuario = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Crear usuario si no existe"
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Validar formato básico
            if not re.match(r'^[a-zA-Z0-9_\.\-]+$', username):
                raise ValidationError(
                    "El nombre de usuario contiene caracteres no válidos."
                )
        return username


# _____________________________________________________________________________________________________________________
from django.utils import timezone


class IncidenciaForm(forms.ModelForm):
    """Formulario individual para una incidencia"""

    class Meta:
        model = Incidencia
        fields = ['area', 'empleado', 'estado', 'fecha_asistencia']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-select'}),
            'empleado': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del empleado'
            }),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'fecha_asistencia': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'area': 'Área',
            'empleado': 'Empleado',
            'estado': 'Estado de Asistencia',
            'fecha_asistencia': 'Fecha de Asistencia'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar áreas por nombre
        self.fields['area'].queryset = Area.objects.all().order_by('nombre')
        # Establecer fecha por defecto como hoy
        if not self.instance.pk:
            self.fields['fecha_asistencia'].initial = datetime.date.today()


class IncidenciaMasivaForm(forms.Form):
    """Formulario para creación masiva de incidencias"""

    fecha_asistencia = forms.DateField(
        label="Fecha de Asistencia",
        initial=datetime.date.today,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    area = forms.ModelChoiceField(
        queryset=Area.objects.all().order_by('nombre'),
        label="Área",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    empleados = forms.CharField(
        label="Lista de Empleados",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '10',
            'placeholder': 'Ingrese un empleado por línea\nEjemplo:\nJuan Pérez\nMaría García\nCarlos López'
        }),
        help_text="Un empleado por línea. Use el formato: Nombre Apellido"
    )

    estado_predeterminado = forms.ChoiceField(
        choices=[('', '-- Seleccionar Estado --')] + list(Incidencia.CHOICES.items()),
        label="Estado Predeterminado",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    def clean_empleados(self):
        empleados = self.cleaned_data.get('empleados', '')
        if empleados:
            # Dividir por líneas y limpiar
            lista_empleados = [emp.strip() for emp in empleados.split('\n') if emp.strip()]

            if not lista_empleados:
                raise ValidationError("Debe ingresar al menos un empleado.")

            # Validar que no haya nombres vacíos después de limpiar
            lista_empleados = [emp for emp in lista_empleados if emp]

            if len(lista_empleados) > 100:
                raise ValidationError("No puede ingresar más de 100 empleados a la vez.")

            return lista_empleados
        return []

    def clean_fecha_asistencia(self):
        fecha = self.cleaned_data.get('fecha_asistencia')
        if fecha:
            if fecha > datetime.date.today():
                raise ValidationError("La fecha no puede ser futura.")
        return fecha


class IncidenciaImportarForm(forms.Form):
    """Formulario para importar incidencias desde archivo"""

    archivo = forms.FileField(
        label="Archivo CSV",
        help_text="Formato: empleado,area_codigo,estado,fecha (YYYY-MM-DD)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.txt'
        })
    )

    sobrescribir = forms.BooleanField(
        required=False,
        initial=False,
        label="Sobrescribir incidencias existentes",
        help_text="Si está marcado, se eliminarán las incidencias existentes para las mismas fechas y empleados",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean_archivo(self):
        archivo = self.cleaned_data.get('archivo')
        if archivo:
            if not archivo.name.endswith('.csv'):
                raise ValidationError("Solo se permiten archivos CSV.")

            # Verificar tamaño (máximo 5MB)
            if archivo.size > 5 * 1024 * 1024:
                raise ValidationError("El archivo no puede ser mayor a 5MB.")
        return archivo


class FiltroIncidenciasForm(forms.Form):
    """Formulario para filtrar incidencias"""

    area = forms.ModelChoiceField(
        queryset=Area.objects.all().order_by('nombre'),
        required=False,
        empty_label="Todas las áreas",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    empleado = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por empleado...'
        })
    )

    estado = forms.ChoiceField(
        choices=[('', 'Todos los estados')] + list(Incidencia.CHOICES.items()),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Desde"
    )

    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label="Hasta"
    )

    def clean(self):
        cleaned_data = super().clean()
        fecha_desde = cleaned_data.get('fecha_desde')
        fecha_hasta = cleaned_data.get('fecha_hasta')

        if fecha_desde and fecha_hasta:
            if fecha_desde > fecha_hasta:
                raise ValidationError("La fecha 'Desde' no puede ser mayor que la fecha 'Hasta'.")

        return cleaned_data

    def filtrar_queryset(self, queryset):
        if self.is_valid():
            area = self.cleaned_data.get('area')
            empleado = self.cleaned_data.get('empleado')
            estado = self.cleaned_data.get('estado')
            fecha_desde = self.cleaned_data.get('fecha_desde')
            fecha_hasta = self.cleaned_data.get('fecha_hasta')

            if area:
                queryset = queryset.filter(area=area.cod_area)
            if empleado:
                queryset = queryset.filter(empleado__icontains=empleado)
            if estado:
                queryset = queryset.filter(estado=estado)
            if fecha_desde:
                queryset = queryset.filter(fecha_asistencia__gte=fecha_desde)
            if fecha_hasta:
                queryset = queryset.filter(fecha_asistencia__lte=fecha_hasta)

        return queryset


class IncidenciaEdicionMasivaForm(forms.Form):
    """Formulario para edición masiva de incidencias"""

    incidencias = forms.ModelMultipleChoiceField(
        queryset=Incidencia.objects.all(),
        widget=forms.MultipleHiddenInput()
    )

    nuevo_estado = forms.ChoiceField(
        choices=[('', '-- Seleccionar Nuevo Estado --')] + list(Incidencia.CHOICES.items()),
        label="Nuevo Estado",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    nueva_fecha = forms.DateField(
        required=False,
        label="Nueva Fecha (opcional)",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )

    def clean_incidencias(self):
        incidencias = self.cleaned_data.get('incidencias')
        if not incidencias:
            raise ValidationError("Debe seleccionar al menos una incidencia.")
        return incidencias


# ______________________________________________________________________________________________________________________
from datetime import datetime, date, timedelta

class IncidenciaRangoDiasForm(forms.Form):
    """Formulario para crear incidencias en un rango de días"""

    # Selección de área
    area = forms.ModelChoiceField(
        queryset=Area.objects.all().order_by('nombre'),
        label="Área",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    # Lista de empleados
    empleados = forms.CharField(
        label="Lista de Empleados",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': '8',
            'placeholder': 'Ingrese un empleado por línea\nEjemplo:\nJuan Pérez\nMaría García\nCarlos López'
        }),
        help_text="Un empleado por línea. Use el formato: Nombre Apellido"
    )

    # Estado predeterminado
    estado_predeterminado = forms.ChoiceField(
        choices=[('', '-- Seleccionar Estado --')] + list(Incidencia.CHOICES.items()),
        label="Estado de Asistencia",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    # Tipo de rango
    TIPO_RANGO = [
        ('rango_fechas', 'Rango de Fechas Específico'),
        ('mes_completo', 'Mes Completo'),
        ('rango_personalizado', 'Rango Personalizado'),
    ]

    tipo_rango = forms.ChoiceField(
        choices=TIPO_RANGO,
        initial='rango_fechas',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Tipo de Rango"
    )

    # Para rango de fechas específico
    fecha_inicio = forms.DateField(
        label="Fecha Inicio",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    fecha_fin = forms.DateField(
        label="Fecha Fin",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    # Para mes completo
    mes = forms.ChoiceField(
        choices=[],
        label="Mes",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    año = forms.IntegerField(
        label="Año",
        initial=datetime.now().year,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '2020',
            'max': '2030'
        }),
        required=False
    )

    # Días de la semana a excluir
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    excluir_fines_semana = forms.BooleanField(
        required=False,
        initial=True,
        label="Excluir fines de semana",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    dias_excluir = forms.MultipleChoiceField(
        choices=DIAS_SEMANA,
        required=False,
        label="Días específicos a excluir",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Seleccione los días que NO desea incluir"
    )

    # Días festivos
    excluir_festivos = forms.BooleanField(
        required=False,
        initial=False,
        label="Excluir días festivos",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Excluir días marcados como festivos en el sistema"
    )

    # Configuración avanzada
    sobrescribir_existentes = forms.BooleanField(
        required=False,
        initial=False,
        label="Sobrescribir incidencias existentes",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Si está marcado, se actualizarán las incidencias existentes"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Llenar choices de meses
        meses = [(i, calendar.month_name[i]) for i in range(1, 13)]
        self.fields['mes'].choices = [('', '-- Seleccionar Mes --')] + meses
        self.fields['mes'].initial = datetime.now().month

        # Establecer fechas por defecto
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        self.fields['fecha_inicio'].initial = inicio_mes
        self.fields['fecha_fin'].initial = hoy

    def clean_empleados(self):
        empleados = self.cleaned_data.get('empleados', '')
        if empleados:
            lista_empleados = [emp.strip() for emp in empleados.split('\n') if emp.strip()]
            lista_empleados = [emp for emp in lista_empleados if emp]

            if not lista_empleados:
                raise ValidationError("Debe ingresar al menos un empleado.")

            if len(lista_empleados) > 50:
                raise ValidationError("No puede ingresar más de 50 empleados a la vez.")

            return lista_empleados
        return []

    def clean(self):
        cleaned_data = super().clean()
        tipo_rango = cleaned_data.get('tipo_rango')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        mes = cleaned_data.get('mes')
        año = cleaned_data.get('año')

        # Validaciones según el tipo de rango
        if tipo_rango == 'rango_fechas':
            if not fecha_inicio or not fecha_fin:
                raise ValidationError("Para rango de fechas, debe especificar fecha inicio y fin.")

            if fecha_inicio > fecha_fin:
                raise ValidationError("La fecha inicio no puede ser mayor que la fecha fin.")

            if (fecha_fin - fecha_inicio).days > 365:
                raise ValidationError("El rango no puede ser mayor a 365 días.")

        elif tipo_rango == 'mes_completo':
            if not mes or not año:
                raise ValidationError("Para mes completo, debe especificar mes y año.")

        # Validar que no se generen demasiados registros
        empleados = cleaned_data.get('empleados', [])
        total_dias = self._calcular_total_dias(cleaned_data)
        total_registros = len(empleados) * total_dias

        if total_registros > 1000:
            raise ValidationError(
                f"La operación generaría {total_registros} registros. "
                f"El máximo permitido es 1000. Reduzca la cantidad de empleados o días."
            )

        return cleaned_data

    def _calcular_total_dias(self, cleaned_data):
        """Calcula el total de días en el rango seleccionado"""
        tipo_rango = cleaned_data.get('tipo_rango')

        if tipo_rango == 'rango_fechas':
            fecha_inicio = cleaned_data.get('fecha_inicio')
            fecha_fin = cleaned_data.get('fecha_fin')
            if fecha_inicio and fecha_fin:
                return (fecha_fin - fecha_inicio).days + 1

        elif tipo_rango == 'mes_completo':
            mes = int(cleaned_data.get('mes', 1))
            año = cleaned_data.get('año', datetime.now().year)
            return calendar.monthrange(año, mes)[1]

        return 0

    def obtener_rango_fechas(self):
        """Retorna la lista de fechas en el rango seleccionado"""
        tipo_rango = self.cleaned_data.get('tipo_rango')
        excluir_fines_semana = self.cleaned_data.get('excluir_fines_semana')
        dias_excluir = [int(dia) for dia in self.cleaned_data.get('dias_excluir', [])]

        fechas = []

        if tipo_rango == 'rango_fechas':
            fecha_inicio = self.cleaned_data.get('fecha_inicio')
            fecha_fin = self.cleaned_data.get('fecha_fin')

            if fecha_inicio and fecha_fin:
                current_date = fecha_inicio
                while current_date <= fecha_fin:
                    fechas.append(current_date)
                    current_date += timedelta(days=1)

        elif tipo_rango == 'mes_completo':
            mes = int(self.cleaned_data.get('mes', 1))
            año = self.cleaned_data.get('año', datetime.now().year)

            # Obtener primer y último día del mes
            _, ultimo_dia = calendar.monthrange(año, mes)

            for dia in range(1, ultimo_dia + 1):
                fecha = date(año, mes, dia)
                fechas.append(fecha)

        # Filtrar fechas según exclusiones
        if excluir_fines_semana or dias_excluir:
            fechas_filtradas = []
            for fecha in fechas:
                dia_semana = fecha.weekday()

                # Excluir fines de semana (sábado=5, domingo=6)
                if excluir_fines_semana and dia_semana >= 5:
                    continue

                # Excluir días específicos
                if dia_semana in dias_excluir:
                    continue

                fechas_filtradas.append(fecha)

            fechas = fechas_filtradas

        # Aquí podrías agregar lógica para excluir días festivos
        if self.cleaned_data.get('excluir_festivos'):
            # Implementar lógica de días festivos si es necesario
            pass

        return fechas


# ______________________________________________________________________________________________________________________
class IncidenciaTrabajadoresExistentesForm(forms.Form):
    """Formulario para crear incidencias desde trabajadores existentes"""

    # Selección de área
    area = forms.ModelChoiceField(
        queryset=Area.objects.all().order_by('nombre'),
        label="Área",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_area_trabajadores'
        }),
        required=True,
        help_text="Seleccione el área para filtrar trabajadores"
    )

    # Selección de trabajadores (se llena dinámicamente)
    trabajadores = forms.ModelMultipleChoiceField(
        queryset=ResponsableArea.objects.none(),
        label="Trabajadores",
        widget=forms.SelectMultiple(attrs={
            'class': 'form-select',
            'size': '10',
            'id': 'id_trabajadores'
        }),
        required=True,
        help_text="Seleccione los trabajadores. Use Ctrl+Click para selección múltiple"
    )

    # Estado predeterminado
    estado_predeterminado = forms.ChoiceField(
        choices=[('', '-- Seleccionar Estado --')] + list(Incidencia.CHOICES.items()),
        label="Estado de Asistencia",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    # Tipo de rango
    TIPO_RANGO = [
        ('rango_fechas', 'Rango de Fechas Específico'),
        ('mes_completo', 'Mes Completo'),
        ('semana_actual', 'Semana Actual'),
        ('semana_siguiente', 'Semana Siguiente'),
    ]

    tipo_rango = forms.ChoiceField(
        choices=TIPO_RANGO,
        initial='rango_fechas',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Tipo de Rango"
    )

    # Para rango de fechas específico
    fecha_inicio = forms.DateField(
        label="Fecha Inicio",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    fecha_fin = forms.DateField(
        label="Fecha Fin",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )

    # Para mes completo
    mes = forms.ChoiceField(
        choices=[],
        label="Mes",
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    año = forms.IntegerField(
        label="Año",
        initial=datetime.now().year,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '2020',
            'max': '2030'
        }),
        required=False
    )

    # Configuración de días
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    excluir_fines_semana = forms.BooleanField(
        required=False,
        initial=True,
        label="Excluir fines de semana",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    dias_excluir = forms.MultipleChoiceField(
        choices=DIAS_SEMANA,
        required=False,
        label="Días específicos a excluir",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        help_text="Seleccione los días que NO desea incluir"
    )

    # Comportamiento con incidencias existentes
    COMPORTAMIENTO_EXISTENTES = [
        ('sobrescribir', 'Sobrescribir incidencias existentes'),
        ('omitir', 'Omitir fechas con incidencias existentes'),
        ('preguntar', 'Preguntar por cada conflicto'),
    ]

    comportamiento_existentes = forms.ChoiceField(
        choices=COMPORTAMIENTO_EXISTENTES,
        initial='sobrescribir',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Comportamiento con incidencias existentes"
    )

    # Opción para incluir todos los trabajadores del área
    incluir_todos = forms.BooleanField(
        required=False,
        initial=False,
        label="Incluir todos los trabajadores del área",
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_incluir_todos'
        }),
        help_text="Si está marcado, se seleccionarán automáticamente todos los trabajadores del área"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Llenar choices de meses
        meses = [(i, calendar.month_name[i]) for i in range(1, 13)]
        self.fields['mes'].choices = [('', '-- Seleccionar Mes --')] + meses
        self.fields['mes'].initial = datetime.now().month

        # Establecer fechas por defecto
        hoy = date.today()
        inicio_mes = hoy.replace(day=1)
        self.fields['fecha_inicio'].initial = inicio_mes
        self.fields['fecha_fin'].initial = hoy

        # Si hay un área seleccionada en los datos, actualizar el queryset de trabajadores
        if 'area' in self.data:
            try:
                area_id = int(self.data.get('area'))
                self.fields['trabajadores'].queryset = self._get_trabajadores_queryset(area_id)
            except (ValueError, TypeError):
                pass

    def _get_trabajadores_queryset(self, area_id):
        """Obtiene el queryset de trabajadores para un área específica"""
        return ResponsableArea.objects.filter(
            area_id=area_id,
            activo=True
        ).select_related('usuario').order_by('usuario__first_name', 'usuario__last_name')

    def clean(self):
        cleaned_data = super().clean()
        tipo_rango = cleaned_data.get('tipo_rango')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        mes = cleaned_data.get('mes')
        año = cleaned_data.get('año')
        area = cleaned_data.get('area')
        trabajadores = cleaned_data.get('trabajadores')
        incluir_todos = cleaned_data.get('incluir_todos')

        # Validar área
        if not area:
            raise ValidationError("Debe seleccionar un área.")

        # Actualizar queryset de trabajadores basado en el área
        if area:
            self.fields['trabajadores'].queryset = self._get_trabajadores_queryset(area.id)

        # Si "incluir todos" está marcado, seleccionar todos los trabajadores del área
        if incluir_todos and area:
            todos_trabajadores = self._get_trabajadores_queryset(area.id)
            cleaned_data['trabajadores'] = list(todos_trabajadores)

        # Validar que se hayan seleccionado trabajadores
        if not cleaned_data.get('trabajadores'):
            raise ValidationError("Debe seleccionar al menos un trabajador.")

        # Validaciones según el tipo de rango
        if tipo_rango == 'rango_fechas':
            if not fecha_inicio or not fecha_fin:
                raise ValidationError("Para rango de fechas, debe especificar fecha inicio y fin.")

            if fecha_inicio > fecha_fin:
                raise ValidationError("La fecha inicio no puede ser mayor que la fecha fin.")

            if (fecha_fin - fecha_inicio).days > 365:
                raise ValidationError("El rango no puede ser mayor a 365 días.")

        elif tipo_rango == 'mes_completo':
            if not mes or not año:
                raise ValidationError("Para mes completo, debe especificar mes y año.")

        # Validar que no se generen demasiados registros
        total_trabajadores = len(cleaned_data.get('trabajadores', []))
        total_dias = self._calcular_total_dias(cleaned_data)
        total_registros = total_trabajadores * total_dias

        if total_registros > 2000:
            raise ValidationError(
                f"La operación generaría {total_registros} registros. "
                f"El máximo permitido es 2000. Reduzca la cantidad de trabajadores o días."
            )

        return cleaned_data

    def _calcular_total_dias(self, cleaned_data):
        """Calcula el total de días en el rango seleccionado"""
        tipo_rango = cleaned_data.get('tipo_rango')
        excluir_fines_semana = cleaned_data.get('excluir_fines_semana')
        dias_excluir = [int(dia) for dia in cleaned_data.get('dias_excluir', [])]

        fechas = self.obtener_rango_fechas()

        # Filtrar fechas según exclusiones
        if excluir_fines_semana or dias_excluir:
            fechas_filtradas = []
            for fecha in fechas:
                dia_semana = fecha.weekday()

                # Excluir fines de semana (sábado=5, domingo=6)
                if excluir_fines_semana and dia_semana >= 5:
                    continue

                # Excluir días específicos
                if dia_semana in dias_excluir:
                    continue

                fechas_filtradas.append(fecha)

            fechas = fechas_filtradas

        return len(fechas)

    def obtener_rango_fechas(self):
        """Retorna la lista de fechas en el rango seleccionado"""
        tipo_rango = self.cleaned_data.get('tipo_rango')
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        fecha_fin = self.cleaned_data.get('fecha_fin')
        mes = self.cleaned_data.get('mes')
        año = self.cleaned_data.get('año')

        fechas = []

        if tipo_rango == 'rango_fechas' and fecha_inicio and fecha_fin:
            current_date = fecha_inicio
            while current_date <= fecha_fin:
                fechas.append(current_date)
                current_date += timedelta(days=1)

        elif tipo_rango == 'mes_completo' and mes and año:
            mes = int(mes)
            _, ultimo_dia = calendar.monthrange(año, mes)
            for dia in range(1, ultimo_dia + 1):
                fecha = date(año, mes, dia)
                fechas.append(fecha)

        elif tipo_rango == 'semana_actual':
            hoy = date.today()
            inicio_semana = hoy - timedelta(days=hoy.weekday())
            fin_semana = inicio_semana + timedelta(days=6)
            current_date = inicio_semana
            while current_date <= fin_semana:
                fechas.append(current_date)
                current_date += timedelta(days=1)

        elif tipo_rango == 'semana_siguiente':
            hoy = date.today()
            inicio_semana_siguiente = hoy + timedelta(days=(7 - hoy.weekday()))
            fin_semana_siguiente = inicio_semana_siguiente + timedelta(days=6)
            current_date = inicio_semana_siguiente
            while current_date <= fin_semana_siguiente:
                fechas.append(current_date)
                current_date += timedelta(days=1)

        return fechas

    def obtener_trabajadores_seleccionados(self):
        """Retorna la lista de trabajadores seleccionados con información completa"""
        trabajadores = self.cleaned_data.get('trabajadores', [])
        resultado = []

        for responsable in trabajadores:
            resultado.append({
                'id': responsable.id,
                'usuario_id': responsable.usuario.id,
                'username': responsable.usuario.username,
                'nombre_completo': f"{responsable.usuario.first_name} {responsable.usuario.last_name}".strip(),
                'email': responsable.usuario.email,
                'area_nombre': responsable.area.nombre,
                'area_codigo': responsable.area.cod_area
            })

        return resultado