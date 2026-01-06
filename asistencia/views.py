# views.py
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.db.models import F
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import datetime, date, timedelta
from .models import ResponsableArea, Area, Incidencia, Trabajador, Estado
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
def responsable_area_list(request):
    """
    Vista para listar todos los responsables de áreas con opciones de gestión
    """
    # Obtener todos los responsables activos
    responsables = ResponsableArea.objects.filter(activo=True).select_related(
        'usuario', 'area'
    ).order_by('area__nombre', 'usuario__username')

    # Si se recibe un filtro por área
    area_id = request.GET.get('area')
    if area_id:
        try:
            area = Area.objects.get(pk=area_id)
            responsables = responsables.filter(area=area)
        except (Area.DoesNotExist, ValueError):
            pass

    # Si se recibe un filtro por usuario
    usuario_id = request.GET.get('usuario')
    if usuario_id:
        try:
            usuario = User.objects.get(pk=usuario_id)
            responsables = responsables.filter(usuario=usuario)
        except (User.DoesNotExist, ValueError):
            pass

    # Obtener todas las áreas para el filtro
    areas = Area.objects.all().order_by('nombre')

    # Obtener todos los usuarios que son responsables
    usuarios_responsables = User.objects.filter(
        areas_responsable__activo=True
    ).distinct().order_by('username')

    # Estadísticas
    total_responsables = responsables.count()
    areas_con_responsable = Area.objects.filter(
        responsablearea__activo=True
    ).distinct().count()
    usuarios_con_asignaciones = User.objects.filter(
        areas_responsable__activo=True
    ).distinct().count()

    # Paginación
    page = request.GET.get('page', 1)
    paginator = Paginator(responsables, 20)  # 20 elementos por página

    try:
        responsables_paginados = paginator.page(page)
    except PageNotAnInteger:
        responsables_paginados = paginator.page(1)
    except EmptyPage:
        responsables_paginados = paginator.page(paginator.num_pages)

    context = {
        'responsables': responsables_paginados,
        'areas': areas,
        'usuarios_responsables': usuarios_responsables,
        'total_responsables': total_responsables,
        'areas_con_responsable': areas_con_responsable,
        'usuarios_con_asignaciones': usuarios_con_asignaciones,
        'title': 'Gestión de Responsables de Áreas',
        'filter_area': request.GET.get('area', ''),
        'filter_usuario': request.GET.get('usuario', ''),
    }

    return render(request, 'responsable_area/responsable_area_list.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def responsable_area_delete(request, pk):
    """
    Vista para desactivar una asignación de responsable (borrado lógico)
    """
    responsable = get_object_or_404(ResponsableArea, pk=pk)

    if request.method == 'POST':
        try:
            # Borrado lógico (desactivar)
            responsable.activo = False
            responsable.save()

            messages.success(
                request,
                f'Se ha desactivado la asignación de {responsable.usuario.username} '
                f'para el área {responsable.area.nombre}'
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            return redirect('responsable_area_list')

        except Exception as e:
            messages.error(request, f'Error al desactivar la asignación: {str(e)}')

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})

            return redirect('responsable_area_list')

    # Si es GET, mostrar confirmación
    context = {
        'responsable': responsable,
        'title': 'Confirmar Desactivación'
    }

    # Si es AJAX, retornar HTML parcial
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'responsable_area/_confirm_delete.html', context)

    return render(request, 'responsable_area/confirm_delete.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def responsable_area_reactivate(request, pk):
    """
    Vista para reactivar una asignación desactivada
    """
    responsable = get_object_or_404(ResponsableArea, pk=pk)

    if request.method == 'POST':
        try:
            responsable.activo = True
            responsable.save()

            messages.success(
                request,
                f'Se ha reactivado la asignación de {responsable.usuario.username} '
                f'para el área {responsable.area.nombre}'
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

        except Exception as e:
            messages.error(request, f'Error al reactivar la asignación: {str(e)}')

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': str(e)})

    return redirect('responsable_area_list')


@login_required
@user_passes_test(is_admin_or_staff)
def responsable_area_edit(request, pk):
    """
    Vista para editar una asignación existente
    """
    responsable = get_object_or_404(ResponsableArea, pk=pk)

    if request.method == 'POST':
        form = ResponsableAreaForm(request.POST, instance=responsable)
        if form.is_valid():
            try:
                form.save()
                messages.success(
                    request,
                    f'Asignación actualizada exitosamente para '
                    f'{responsable.usuario.username}'
                )
                return redirect('responsable_area_list')
            except Exception as e:
                messages.error(request, f'Error al actualizar la asignación: {str(e)}')
    else:
        form = ResponsableAreaForm(instance=responsable)

    context = {
        'form': form,
        'title': f'Editar Asignación: {responsable.usuario.username} - {responsable.area.nombre}',
        'responsable': responsable
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
    areas_hijas = Area.objects.filter(unidad_padre=area_responsable.area.cod_area)

    if not area_responsable and not request.user.is_superuser:
        return render(request, 'error.html', {
            'mensaje': 'No tienes permisos para ver esta página'
        })

    # Formulario de filtro de fechas
    form_filtro = FiltroFechaForm(request.GET or None)

    # Determinar rango de fechas
    meses_es = [
        "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    ]
    hoy = timezone.now().date()
    mes = meses_es[hoy.month - 1]

    if form_filtro.is_valid() and form_filtro.cleaned_data.get('fecha_inicio') and form_filtro.cleaned_data.get(
            'fecha_fin'):
        fecha_inicio = form_filtro.cleaned_data['fecha_inicio']
        fecha_fin = form_filtro.cleaned_data['fecha_fin']
    else:
        # Por defecto: desde el 20 del mes anterior hasta hoy
        fecha_inicio = hoy.replace(day=1)
        fecha_fin = hoy

    # Generar lista de días en el rango
    dias = []
    current_date = fecha_inicio
    while current_date <= fecha_fin:
        dias.append(current_date)
        current_date += timedelta(days=1)
        # Obteniendo todas las áreas que pertenecen a una misma área padre.

    # Obtener incidencias según permisos

    incidencias_qs = Incidencia.objects.filter(
        area=area_responsable.area,
        fecha_asistencia__range=[fecha_inicio, fecha_fin])
    trabajadores = Trabajador.objects.filter(area=area_responsable.area)
    for area in areas_hijas:
        incidencias_qs = incidencias_qs.union(Incidencia.objects.filter(
            area=area,
            fecha_asistencia__range=[fecha_inicio, fecha_fin]
        ))
        trabajadores = trabajadores.union(Trabajador.objects.filter(area=area))

    for trabajador in trabajadores:
        for dia in dias:
            # Verificar si es sábado o domingo
            if dia.weekday() == 5:
                estado = Estado.objects.get(id=110)
            elif dia.weekday() == 6:
                estado = Estado.objects.get(id=111)
            else:
                estado = Estado.objects.get(id=109)

            incidencia, created = Incidencia.objects.get_or_create(
                trabajador=trabajador,
                fecha_asistencia=dia,
                defaults={
                    'area': trabajador.area,
                    'estado': estado,
                }
            )

    # Agrupar por empleado
    empleados_data = {}
    for incidencia in incidencias_qs:
        empleado_key = f"{incidencia.trabajador.nombre} {incidencia.trabajador.apellidos}"
        if empleado_key not in empleados_data:
            empleados_data[empleado_key] = {
                'trabajador': incidencia.trabajador.nombre + ' ' + incidencia.trabajador.apellidos,
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
            'empleado': datos['trabajador'],
            'area': datos['area'],
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
        'areas': areas_hijas,
        'incidencias': incidencias_qs,
        'area_responsable': area_responsable,
        'trabajadores': trabajadores,
        'tabla_datos': tabla_datos,
        'dias': dias,
        'form_filtro': form_filtro,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'es_responsable': area_responsable or request.user.is_superuser,
        'opciones_estado': Estado.objects.all(),
        'mes': mes,

    }

    return render(request, 'incidencias/tabla_incidencias.html', context)


@login_required
def editar_incidencia(request, incidencia_id):
    incidencia = get_object_or_404(Incidencia, id=incidencia_id)

    # Verificar permisos

    es_responsable = ResponsableArea.es_responsable_area(request.user, incidencia.area)
    if not es_responsable:
        return render(request, 'error.html', {
            'mensaje': 'No tienes permisos para editar esta incidencia'
        })

    if request.method == 'POST':
        form = IncidenciaForm(request.POST, instance=incidencia)
        if form.is_valid():
            form.save()
            return redirect('tabla_incidencias', area_id=incidencia.area.pk)

    return redirect('tabla_incidencias', area_id=incidencia.area.pk)
