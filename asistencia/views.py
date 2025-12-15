# views.py
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime, date, timedelta
from .models import ResponsableArea, Area, Incidencia, Trabajador
from dateutil.relativedelta import relativedelta
from .forms import (LDAPAuthenticationForm, ResponsableAreaForm, BuscarCrearUsuarioForm,
                    AsignacionRapidaForm, UserCreationFlexibleForm, IncidenciaForm, FiltroFechaForm
                    )
import json
from .trabajadores import obtener_usuarios_ldap3


def login_view(request):
    """
    Vista personalizada para login con LDAP
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LDAPAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # Autenticar usuario
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)

                # Redirigir a la página solicitada o al dashboard
                next_url = request.GET.get('next', 'dashboard')
                messages.success(request, f'Bienvenido, {user.get_full_name() or user.username}')
                return redirect(next_url)
            else:
                messages.error(request, 'Credenciales incorrectas o usuario no autorizado')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario')
    else:
        form = LDAPAuthenticationForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def logout_view(request):
    """
    Vista para cerrar sesión
    """
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('login')


@login_required
def dashboard_view(request):
    """
    Vista del dashboard después del login
    """
    usuario = request.user
    areas = ResponsableArea.objects.filter(usuario=usuario, activo=True).select_related('area').order_by('area__nombre')


    return render(request, 'dashboard.html', {
        'user': request.user,
        'areas': areas,
        'areas_responsable': request.user.areas_responsable.all() if hasattr(request.user, 'areas_responsable') else []
    })


def is_admin_or_staff(user):
    """Verifica si el usuario es admin o staff"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin_or_staff)
def responsable_area_create(request):
    """Crea asignaciones con posibilidad de crear usuarios"""
    if request.method == 'POST':
        form = ResponsableAreaForm(request.POST)
        if form.is_valid():
            try:
                responsable = form.save()
                if responsable:
                    messages.success(
                        request,
                        f'Asignación creada exitosamente para {responsable.usuario.username}'
                    )
                return redirect('responsable_area_list')
            except Exception as e:
                messages.error(request, f'Error al crear la asignación: {str(e)}')
    else:
        form = ResponsableAreaForm()

    context = {
        'form': form,
        'title': 'Asignar Responsable - Crear Usuario si no Existe'
    }
    return render(request, 'responsable_area/form_con_creacion.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def buscar_crear_usuario(request):
    """Busca un usuario o lo crea si no existe"""
    usuario = None
    form = BuscarCrearUsuarioForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        accion = form.cleaned_data['accion']

        try:
            # Buscar usuario existente
            usuario = User.objects.get(username=username, is_active=True)
            messages.info(request, f'Usuario encontrado: {usuario.username}')

        except User.DoesNotExist:
            if accion == 'crear':
                # Crear nuevo usuario
                usuario = User.objects.create(
                    username=username,
                    is_active=True
                )
                usuario.set_unusable_password()  # Para LDAP
                usuario.save()
                messages.success(request, f'Usuario creado: {username}')
            else:
                messages.error(request, f'Usuario {username} no encontrado')

    context = {
        'form': form,
        'usuario': usuario,
        'areas': Area.objects.all().order_by('nombre')
    }
    return render(request, 'responsable_area/buscar_crear_usuario.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def asignacion_rapida(request):
    """Asignación rápida de responsable con creación de usuario"""
    if request.method == 'POST':
        form = AsignacionRapidaForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            area = form.cleaned_data['area']
            crear_usuario = form.cleaned_data['crear_usuario']

            try:
                # Buscar o crear usuario
                try:
                    usuario = User.objects.get(username=username, is_active=True)
                    usuario_existente = True
                except User.DoesNotExist:
                    if crear_usuario:
                        usuario = User.objects.create(
                            username=username,
                            is_active=True
                        )
                        usuario.set_unusable_password()
                        usuario.save()
                        usuario_existente = False
                    else:
                        messages.error(request, f'Usuario {username} no encontrado')
                        return redirect('asignacion_rapida')

                # Crear asignación
                obj, created = ResponsableArea.objects.get_or_create(
                    usuario=usuario,
                    area=area,
                    defaults={'activo': True}
                )

                if created:
                    if usuario_existente:
                        messages.success(
                            request,
                            f'Usuario {username} asignado al área {area.nombre}'
                        )
                    else:
                        messages.success(
                            request,
                            f'Usuario {username} creado y asignado al área {area.nombre}'
                        )
                else:
                    messages.info(
                        request,
                        f'El usuario ya era responsable de esta área'
                    )

                return redirect('responsable_area_list')

            except Exception as e:
                messages.error(request, f'Error en la asignación: {str(e)}')
    else:
        form = AsignacionRapidaForm()

    context = {
        'form': form,
        'title': 'Asignación Rápida de Responsable'
    }
    return render(request, 'responsable_area/asignacion_rapida.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def crear_usuario_ajax(request):
    """Crea un usuario via AJAX"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = json.loads(request.body)
        username = data.get('username')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        email = data.get('email', '')

        try:
            # Verificar si ya existe
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'success': False,
                    'message': f'El usuario {username} ya existe'
                })

            # Crear nuevo usuario
            usuario = User.objects.create(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                is_active=True
            )
            usuario.set_unusable_password()
            usuario.save()

            return JsonResponse({
                'success': True,
                'message': f'Usuario {username} creado exitosamente',
                'usuario': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'email': usuario.email
                }
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error al crear usuario: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@user_passes_test(is_admin_or_staff)
def buscar_usuario_ajax(request):
    """Busca usuario via AJAX"""
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        username = request.GET.get('username', '')

        try:
            usuario = User.objects.get(username=username, is_active=True)
            return JsonResponse({
                'success': True,
                'encontrado': True,
                'usuario': {
                    'id': usuario.id,
                    'username': usuario.username,
                    'first_name': usuario.first_name,
                    'last_name': usuario.last_name,
                    'email': usuario.email
                }
            })
        except User.DoesNotExist:
            return JsonResponse({
                'success': True,
                'encontrado': False,
                'message': f'Usuario {username} no encontrado'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error en la búsqueda: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Método no permitido'})


@login_required
@user_passes_test(is_admin_or_staff)
def gestion_usuario_completa(request, usuario_id=None):
    """Gestion completa de usuario (crear/editar) y sus áreas"""
    usuario = None
    if usuario_id:
        usuario = get_object_or_404(User, pk=usuario_id, is_active=True)

    if request.method == 'POST':
        user_form = UserCreationFlexibleForm(request.POST, instance=usuario)

        if user_form.is_valid():
            usuario = user_form.save()

            # Procesar asignaciones de áreas
            areas_seleccionadas = request.POST.getlist('areas')
            for area_id in areas_seleccionadas:
                try:
                    area = Area.objects.get(pk=area_id)
                    ResponsableArea.objects.get_or_create(
                        usuario=usuario,
                        area=area,
                        defaults={'activo': True}
                    )
                except Area.DoesNotExist:
                    pass

            if usuario_id:
                messages.success(request, f'Usuario {usuario.username} actualizado')
            else:
                messages.success(request, f'Usuario {usuario.username} creado')

            return redirect('responsable_area_list')
    else:
        user_form = UserCreationFlexibleForm(instance=usuario)

    # Obtener áreas actuales del usuario
    areas_actuales = []
    if usuario:
        areas_actuales = ResponsableArea.objects.filter(
            usuario=usuario, activo=True
        ).values_list('area_id', flat=True)

    context = {
        'user_form': user_form,
        'usuario': usuario,
        'areas': Area.objects.all().order_by('nombre'),
        'areas_actuales': areas_actuales,
        'title': 'Editar Usuario' if usuario else 'Crear Usuario'
    }
    return render(request, 'responsable_area/gestion_usuario_completa.html', context)


# _____________________________________________________________________________________________________________________
@login_required
def responsables_listar(request):
    responsables = ResponsableArea.objects.all().order_by('usuario__first_name')
    context = {
        'responsables': responsables,
    }
    return render(request, 'responsable_area/responsables_area.html', context)


@login_required
def tabla_incidencias(request, area_id):
    # Verificar si el usuario es responsable de algún área
    area_responsable = ResponsableArea.objects.get(area=(Area.objects.get(pk=area_id)))

    if not area_responsable and not request.user.is_superuser:
        return render(request, 'error.html', {
            'mensaje': 'No tienes permisos para ver esta página'
        })

    # Formulario de filtro de fechas
    form_filtro = FiltroFechaForm(request.GET or None)

    # Determinar rango de fechas
    hoy = timezone.now().date()
    if form_filtro.is_valid() and form_filtro.cleaned_data.get('fecha_inicio') and form_filtro.cleaned_data.get(
            'fecha_fin'):
        fecha_inicio = form_filtro.cleaned_data['fecha_inicio']
        fecha_fin = form_filtro.cleaned_data['fecha_fin']
    else:
        # Por defecto: desde el 20 del mes anterior hasta hoy
        primer_dia_mes_actual = hoy.replace(day=1)
        ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
        fecha_inicio = ultimo_dia_mes_anterior.replace(day=20)
        fecha_fin = hoy

    # Generar lista de días en el rango
    dias = []
    current_date = fecha_inicio
    while current_date <= fecha_fin:
        dias.append(current_date)
        current_date += timedelta(days=1)

    # Obtener incidencias según permisos
    if request.user.is_superuser:
        incidencias_qs = Incidencia.objects.filter(
            fecha_asistencia__range=[fecha_inicio, fecha_fin]
        )
    else:
        areas_ids = [ra.area.id for ra in area_responsable]
        incidencias_qs = Incidencia.objects.filter(
            area_id__in=areas_ids,
            fecha_asistencia__range=[fecha_inicio, fecha_fin]
        )

    trabajadores = Trabajador.objects.filter(area=area_responsable.area)
    trabajadores_list = list(trabajadores)

    for trabajador in trabajadores_list:

        for dia in dias:
            incidencia, created = Incidencia.objects.get_or_create(
                fecha_asistencia=dia,
                defaults={
                    'area': trabajador.area,
                    'trabajador': trabajador,
                }
            )

    # Agrupar por empleado
    empleados_data = {}
    for incidencia in incidencias_qs.select_related('area'):
        empleado_key = f"{incidencia.uid}_{incidencia.empleado}"
        if empleado_key not in empleados_data:
            empleados_data[empleado_key] = {
                'uid': incidencia.uid,
                'empleado': incidencia.empleado,
                'area': incidencia.area.nombre,
                'incidencias': {}
            }
        empleados_data[empleado_key]['incidencias'][incidencia.fecha_asistencia] = {
            'id': incidencia.id,
            'estado': incidencia.estado
        }

    # Preparar datos para la tabla
    tabla_datos = []
    for empleado_key, datos in empleados_data.items():
        fila = {
            'empleado': datos['empleado'],
            'area': datos['area'],
            'uid': datos['uid'],
            'dias': []
        }

        for dia in dias:
            incidencia_dia = datos['incidencias'].get(dia)
            if incidencia_dia:
                fila['dias'].append({
                    'fecha': dia,
                    'incidencia_id': incidencia_dia['id'],
                    'estado': incidencia_dia['estado'],
                    'tiene_incidencia': True
                })
            else:
                fila['dias'].append({
                    'fecha': dia,
                    'incidencia_id': None,
                    'estado': 'No registrado',
                    'tiene_incidencia': False
                })

        tabla_datos.append(fila)
    context = {
        'areas_responsable': area_responsable,
        'trabajadores_list': trabajadores_list,
        'tabla_datos': tabla_datos,
        'dias': dias,
        'form_filtro': form_filtro,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'es_responsable': area_responsable.exists() or request.user.is_superuser,
        'opciones_estado': Incidencia.CHOICES.items()
    }

    return render(request, 'incidencias/tabla_incidencias.html', context)


@login_required
def editar_incidencia(request, incidencia_id):
    incidencia = get_object_or_404(Incidencia, id=incidencia_id)

    # Verificar permisos
    if not request.user.is_superuser:
        es_responsable = ResponsableArea.es_responsable_area(request.user, incidencia.area)
        if not es_responsable:
            return render(request, 'error.html', {
                'mensaje': 'No tienes permisos para editar esta incidencia'
            })

    if request.method == 'POST':
        form = IncidenciaForm(request.POST, instance=incidencia)
        if form.is_valid():
            form.save()
            return redirect('tabla_incidencias')

    return redirect('tabla_incidencias')