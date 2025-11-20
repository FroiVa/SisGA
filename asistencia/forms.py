# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import ResponsableArea, Area, Incidencia
from django.contrib.auth.models import User
import re


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


class IncidenciaForm(forms.ModelForm):
    class Meta:
        model = Incidencia
        fields = ['estado']
        widgets = {
            'estado': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'this.form.submit()'
            }),
        }

class FiltroFechaForm(forms.Form):
    fecha_inicio = forms.DateField(
        label='Fecha inicio',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        label='Fecha fin',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )