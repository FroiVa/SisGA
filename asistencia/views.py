# views.py
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from datetime import datetime, date, timedelta
from .models import ResponsableArea, Area, Incidencia
from .forms import (LDAPAuthenticationForm, ResponsableAreaForm, BuscarCrearUsuarioForm,
                    AsignacionRapidaForm, UserCreationFlexibleForm, IncidenciaTrabajadoresExistentesForm,
                    IncidenciaRangoDiasForm, IncidenciaForm, IncidenciaMasivaForm, IncidenciaImportarForm,
                    FiltroIncidenciasForm, IncidenciaEdicionMasivaForm
                    )
import calendar
import json
import csv
import io
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
    trabajadores_list = []
    for area in areas:
        trabajadores = obtener_usuarios_ldap3(area.area.cod_area)
        trabajadores_list.extend(trabajadores)
    return render(request, 'dashboard.html', {
        'user': request.user,
        'areas': areas,
        'trabajadores_list': trabajadores_list,
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
def incidencia_trabajadores_existentes(request):
    """Crea incidencias para trabajadores existentes en un rango de días"""
    if request.method == 'POST':
        form = IncidenciaTrabajadoresExistentesForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    area = form.cleaned_data['area']
                    trabajadores_responsables = form.cleaned_data['trabajadores']
                    estado_predeterminado = form.cleaned_data['estado_predeterminado']
                    comportamiento = form.cleaned_data['comportamiento_existentes']

                    # Obtener rango de fechas
                    fechas = form.obtener_rango_fechas()

                    if not fechas:
                        messages.error(request, "No hay fechas válidas en el rango seleccionado.")
                        return redirect('incidencia_trabajadores_existentes')

                    # Aplicar filtros de exclusión
                    fechas = aplicar_filtros_fechas(fechas, form.cleaned_data)

                    incidencias_creadas = 0
                    incidencias_actualizadas = 0
                    incidencias_omitidas = 0
                    errores = []

                    # Procesar cada trabajador y cada fecha
                    for responsable in trabajadores_responsables:
                        empleado_nombre = f"{responsable.usuario.first_name} {responsable.usuario.last_name}".strip()
                        if not empleado_nombre:
                            empleado_nombre = responsable.usuario.username

                        for fecha in fechas:
                            try:
                                # Buscar incidencia existente
                                incidencia_existente = Incidencia.objects.filter(
                                    empleado=empleado_nombre,
                                    fecha_asistencia=fecha,
                                    area=area.cod_area
                                ).first()

                                if incidencia_existente:
                                    if comportamiento == 'sobrescribir':
                                        # Sobrescribir incidencia existente
                                        incidencia_existente.estado = estado_predeterminado
                                        incidencia_existente.save()
                                        incidencias_actualizadas += 1
                                    elif comportamiento == 'omitir':
                                        # Omitir esta fecha
                                        incidencias_omitidas += 1
                                        continue
                                    elif comportamiento == 'preguntar':
                                        # En una implementación real, aquí manejarías la interacción del usuario
                                        # Por ahora, omitimos por simplicidad
                                        incidencias_omitidas += 1
                                        continue
                                else:
                                    # Crear nueva incidencia
                                    Incidencia.objects.create(
                                        area=area.cod_area,
                                        empleado=empleado_nombre,
                                        estado=estado_predeterminado,
                                        fecha_asistencia=fecha
                                    )
                                    incidencias_creadas += 1

                            except Exception as e:
                                errores.append(f"{empleado_nombre} - {fecha}: {str(e)}")

                    # Mostrar resultados
                    mensaje = f"Procesamiento completado: "
                    if incidencias_creadas > 0:
                        mensaje += f"{incidencias_creadas} creadas, "
                    if incidencias_actualizadas > 0:
                        mensaje += f"{incidencias_actualizadas} actualizadas, "
                    if incidencias_omitidas > 0:
                        mensaje += f"{incidencias_omitidas} omitidas, "
                    if errores:
                        mensaje += f"{len(errores)} errores"

                    messages.success(request, mensaje.rstrip(', '))

                    # Mostrar detalles si hay errores
                    if errores and len(errores) <= 5:
                        for error in errores:
                            messages.warning(request, f"Error: {error}")
                    elif errores:
                        messages.warning(request, f"Se produjeron {len(errores)} errores.")

                    return redirect('incidencia_list')

            except Exception as e:
                messages.error(request, f"Error al procesar el rango de días: {str(e)}")
    else:
        form = IncidenciaTrabajadoresExistentesForm()

    context = {
        'form': form,
        'title': 'Incidencias para Trabajadores Existentes'
    }
    return render(request, 'incidencias/trabajadores_existentes.html', context)


def aplicar_filtros_fechas(fechas, cleaned_data):
    """Aplica filtros de exclusión a la lista de fechas"""
    excluir_fines_semana = cleaned_data.get('excluir_fines_semana')
    dias_excluir = [int(dia) for dia in cleaned_data.get('dias_excluir', [])]

    if not excluir_fines_semana and not dias_excluir:
        return fechas

    fechas_filtradas = []
    for fecha in fechas:
        dia_semana = fecha.weekday()

        # Excluir fines de semana
        if excluir_fines_semana and dia_semana >= 5:
            continue

        # Excluir días específicos
        if dia_semana in dias_excluir:
            continue

        fechas_filtradas.append(fecha)

    return fechas_filtradas


@login_required
def obtener_trabajadores_area(request):
    """Obtiene los trabajadores de un área específica (AJAX)"""
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            area_id = request.GET.get('area_id')

            if not area_id:
                return JsonResponse({'success': False, 'error': 'ID de área no proporcionado'})

            trabajadores = ResponsableArea.objects.filter(
                area_id=area_id,
                activo=True
            ).select_related('usuario', 'area').order_by('usuario__first_name', 'usuario__last_name')

            trabajadores_data = []
            for responsable in trabajadores:
                nombre_completo = f"{responsable.usuario.first_name} {responsable.usuario.last_name}".strip()
                if not nombre_completo:
                    nombre_completo = responsable.usuario.username

                trabajadores_data.append({
                    'id': responsable.id,
                    'usuario_id': responsable.usuario.id,
                    'username': responsable.usuario.username,
                    'nombre_completo': nombre_completo,
                    'email': responsable.usuario.email,
                    'area_nombre': responsable.area.nombre,
                    'fecha_asignacion': responsable.fecha_asignacion.strftime('%d/%m/%Y')
                })

            data = {
                'success': True,
                'trabajadores': trabajadores_data,
                'total': len(trabajadores_data)
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def calcular_rango_trabajadores(request):
    """Calcula información del rango para trabajadores existentes (AJAX)"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = IncidenciaTrabajadoresExistentesForm(request.POST)
        if form.is_valid():
            try:
                trabajadores = form.cleaned_data.get('trabajadores', [])
                fechas = form.obtener_rango_fechas()
                fechas = aplicar_filtros_fechas(fechas, form.cleaned_data)

                total_trabajadores = len(trabajadores)
                total_dias = len(fechas)
                total_registros = total_trabajadores * total_dias

                # Información de las fechas
                primera_fecha = min(fechas) if fechas else None
                ultima_fecha = max(fechas) if fechas else None

                # Información de trabajadores (solo primeros 5 para preview)
                trabajadores_preview = []
                for responsable in trabajadores[:5]:
                    nombre_completo = f"{responsable.usuario.first_name} {responsable.usuario.last_name}".strip()
                    if not nombre_completo:
                        nombre_completo = responsable.usuario.username
                    trabajadores_preview.append(nombre_completo)

                data = {
                    'success': True,
                    'total_trabajadores': total_trabajadores,
                    'total_dias': total_dias,
                    'total_registros': total_registros,
                    'primera_fecha': primera_fecha.strftime('%d/%m/%Y') if primera_fecha else None,
                    'ultima_fecha': ultima_fecha.strftime('%d/%m/%Y') if ultima_fecha else None,
                    'fechas_ejemplo': [fecha.strftime('%d/%m/%Y') for fecha in fechas[:5]] if fechas else [],
                    'trabajadores_ejemplo': trabajadores_preview
                }

                return JsonResponse(data)

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })

        else:
            return JsonResponse({
                'success': False,
                'error': 'Formulario inválido',
                'errores': form.errors.get_json_data()
            })

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def verificar_incidencias_existentes(request):
    """Verifica incidencias existentes para el rango seleccionado (AJAX)"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            area_id = data.get('area_id')
            trabajadores_ids = data.get('trabajadores_ids', [])
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')

            if not all([area_id, trabajadores_ids, fecha_inicio, fecha_fin]):
                return JsonResponse({'success': False, 'error': 'Datos incompletos'})

            # Obtener área
            area = Area.objects.get(id=area_id)

            # Obtener trabajadores
            trabajadores = ResponsableArea.objects.filter(
                id__in=trabajadores_ids,
                activo=True
            ).select_related('usuario')

            # Convertir fechas
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

            # Contar incidencias existentes
            total_existentes = 0
            detalle_existentes = []

            for responsable in trabajadores:
                empleado_nombre = f"{responsable.usuario.first_name} {responsable.usuario.last_name}".strip()
                if not empleado_nombre:
                    empleado_nombre = responsable.usuario.username

                existentes = Incidencia.objects.filter(
                    empleado=empleado_nombre,
                    area=area.cod_area,
                    fecha_asistencia__range=[fecha_inicio, fecha_fin]
                ).count()

                if existentes > 0:
                    total_existentes += existentes
                    detalle_existentes.append({
                        'empleado': empleado_nombre,
                        'existentes': existentes
                    })

            data = {
                'success': True,
                'total_existentes': total_existentes,
                'detalle_existentes': detalle_existentes[:10]  # Limitar a 10 para preview
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# __________________________________________________________________________________________________________________

@login_required
def incidencia_rango_dias(request):
    """Crea incidencias para un listado de trabajadores en un rango de días"""
    if request.method == 'POST':
        form = IncidenciaRangoDiasForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    area = form.cleaned_data['area']
                    empleados = form.cleaned_data['empleados']
                    estado_predeterminado = form.cleaned_data['estado_predeterminado']
                    sobrescribir = form.cleaned_data['sobrescribir_existentes']

                    # Obtener rango de fechas
                    fechas = form.obtener_rango_fechas()

                    if not fechas:
                        messages.error(request, "No hay fechas válidas en el rango seleccionado.")
                        return redirect('incidencia_rango_dias')

                    incidencias_creadas = 0
                    incidencias_actualizadas = 0
                    errores = []

                    # Procesar cada empleado y cada fecha
                    for i, empleado in enumerate(empleados, 1):
                        for fecha in fechas:
                            try:
                                # Buscar incidencia existente
                                incidencia_existente = Incidencia.objects.filter(
                                    empleado=empleado,
                                    fecha_asistencia=fecha,
                                    area=area.cod_area
                                ).first()

                                if incidencia_existente:
                                    if sobrescribir:
                                        incidencia_existente.estado = estado_predeterminado
                                        incidencia_existente.save()
                                        incidencias_actualizadas += 1
                                else:
                                    # Crear nueva incidencia
                                    Incidencia.objects.create(
                                        area=area.cod_area,
                                        empleado=empleado,
                                        estado=estado_predeterminado,
                                        fecha_asistencia=fecha
                                    )
                                    incidencias_creadas += 1

                            except Exception as e:
                                errores.append(f"{empleado} - {fecha}: {str(e)}")

                    # Mostrar resultados
                    mensaje = f"Procesamiento completado: "
                    if incidencias_creadas > 0:
                        mensaje += f"{incidencias_creadas} creadas, "
                    if incidencias_actualizadas > 0:
                        mensaje += f"{incidencias_actualizadas} actualizadas, "
                    if errores:
                        mensaje += f"{len(errores)} errores"

                    messages.success(request, mensaje.rstrip(', '))

                    # Mostrar detalles si hay errores
                    if errores and len(errores) <= 10:
                        for error in errores:
                            messages.warning(request, f"Error: {error}")
                    elif errores:
                        messages.warning(request, f"Se produjeron {len(errores)} errores. Los primeros 5:")
                        for error in errores[:5]:
                            messages.warning(request, f"Error: {error}")

                    return redirect('incidencia_list')

            except Exception as e:
                messages.error(request, f"Error al procesar el rango de días: {str(e)}")
    else:
        form = IncidenciaRangoDiasForm()

    context = {
        'form': form,
        'title': 'Incidencias por Rango de Días'
    }
    return render(request, 'incidencias/rango_dias.html', context)


@login_required
def calcular_rango_dias(request):
    """Calcula y retorna información sobre el rango de días seleccionado (AJAX)"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        form = IncidenciaRangoDiasForm(request.POST)
        if form.is_valid():
            try:
                fechas = form.obtener_rango_fechas()
                empleados = form.cleaned_data.get('empleados', [])

                total_dias = len(fechas)
                total_empleados = len(empleados)
                total_registros = total_dias * total_empleados

                # Información de las fechas
                primera_fecha = min(fechas) if fechas else None
                ultima_fecha = max(fechas) if fechas else None

                data = {
                    'success': True,
                    'total_dias': total_dias,
                    'total_empleados': total_empleados,
                    'total_registros': total_registros,
                    'primera_fecha': primera_fecha.strftime('%d/%m/%Y') if primera_fecha else None,
                    'ultima_fecha': ultima_fecha.strftime('%d/%m/%Y') if ultima_fecha else None,
                    'fechas_ejemplo': [fecha.strftime('%d/%m/%Y') for fecha in fechas[:5]] if fechas else []
                }

                return JsonResponse(data)

            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })

        else:
            return JsonResponse({
                'success': False,
                'error': 'Formulario inválido',
                'errores': form.errors.get_json_data()
            })

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def obtener_dias_mes(request):
    """Obtiene los días de un mes específico (AJAX)"""
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            año = int(request.GET.get('año', datetime.now().year))
            mes = int(request.GET.get('mes', datetime.now().month))

            # Calcular días del mes
            _, dias_mes = calendar.monthrange(año, mes)

            # Generar lista de fechas
            fechas = []
            for dia in range(1, dias_mes + 1):
                fecha = date(año, mes, dia)
                fechas.append({
                    'dia': dia,
                    'fecha': fecha.strftime('%Y-%m-%d'),
                    'dia_semana': fecha.strftime('%A'),
                    'es_fin_semana': fecha.weekday() >= 5
                })

            data = {
                'success': True,
                'año': año,
                'mes': mes,
                'nombre_mes': calendar.month_name[mes],
                'total_dias': dias_mes,
                'fechas': fechas
            }

            return JsonResponse(data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def vista_previa_rango(request):
    """Genera una vista previa del rango seleccionado"""
    if request.method == 'POST':
        form = IncidenciaRangoDiasForm(request.POST)
        if form.is_valid():
            area = form.cleaned_data['area']
            empleados = form.cleaned_data['empleados']
            estado_predeterminado = form.cleaned_data['estado_predeterminado']
            fechas = form.obtener_rango_fechas()

            # Limitar para vista previa
            empleados_preview = empleados[:5]  # Mostrar solo 5 empleados
            fechas_preview = fechas[:7]  # Mostrar solo 7 días

            context = {
                'form': form,
                'area': area,
                'empleados': empleados,
                'empleados_preview': empleados_preview,
                'estado_predeterminado': estado_predeterminado,
                'fechas': fechas,
                'fechas_preview': fechas_preview,
                'total_empleados': len(empleados),
                'total_dias': len(fechas),
                'total_registros': len(empleados) * len(fechas),
                'title': 'Vista Previa - Incidencias por Rango'
            }

            return render(request, 'incidencias/vista_previa_rango.html', context)
        else:
            messages.error(request, "Por favor, corrija los errores en el formulario.")
            return redirect('incidencia_rango_dias')

    return redirect('incidencia_rango_dias')


# ____________________________________________________________________________________________________________________
@login_required
def incidencia_list(request):
    """Lista todas las incidencias con filtros"""
    incidencias = Incidencia.objects.all().order_by('-fecha_asistencia', 'empleado')

    # Formulario de filtros
    filter_form = FiltroIncidenciasForm(request.GET or None)
    if filter_form.is_valid():
        incidencias = filter_form.filtrar_queryset(incidencias)

    # Paginación
    paginator = Paginator(incidencias, 50)  # 50 items por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Estadísticas
    total_incidencias = incidencias.count()
    hoy = date.today()
    incidencias_hoy = Incidencia.objects.filter(fecha_asistencia=hoy).count()

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_incidencias': total_incidencias,
        'incidencias_hoy': incidencias_hoy,
        'estados': Incidencia.CHOICES
    }
    return render(request, 'incidencias/list.html', context)


@login_required
def incidencia_create_individual(request):
    """Crea una incidencia individual"""
    if request.method == 'POST':
        form = IncidenciaForm(request.POST)
        if form.is_valid():
            incidencia = form.save()
            messages.success(
                request,
                f'Incidencia creada para {incidencia.empleado}'
            )
            return redirect('incidencia_list')
    else:
        form = IncidenciaForm()

    context = {
        'form': form,
        'title': 'Registrar Incidencia Individual'
    }
    return render(request, 'incidencias/form_individual.html', context)


@login_required
def incidencia_create_masiva(request):
    """Crea incidencias de forma masiva desde lista"""
    if request.method == 'POST':
        form = IncidenciaMasivaForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    fecha_asistencia = form.cleaned_data['fecha_asistencia']
                    area = form.cleaned_data['area']
                    empleados = form.cleaned_data['empleados']
                    estado_predeterminado = form.cleaned_data['estado_predeterminado']

                    incidencias_creadas = 0
                    incidencias_actualizadas = 0
                    errores = []

                    for i, nombre_empleado in enumerate(empleados, 1):
                        try:
                            # Buscar si ya existe una incidencia para este empleado en esta fecha
                            incidencia_existente = Incidencia.objects.filter(
                                empleado=nombre_empleado,
                                fecha_asistencia=fecha_asistencia,
                                area=area.cod_area
                            ).first()

                            if incidencia_existente:
                                # Actualizar incidencia existente
                                incidencia_existente.estado = estado_predeterminado
                                incidencia_existente.save()
                                incidencias_actualizadas += 1
                            else:
                                # Crear nueva incidencia
                                Incidencia.objects.create(
                                    area=area.cod_area,
                                    empleado=nombre_empleado,
                                    estado=estado_predeterminado,
                                    fecha_asistencia=fecha_asistencia
                                )
                                incidencias_creadas += 1

                        except Exception as e:
                            errores.append(f"Línea {i}: {nombre_empleado} - {str(e)}")

                    # Mostrar resultados
                    if incidencias_creadas > 0:
                        messages.success(
                            request,
                            f'{incidencias_creadas} incidencias creadas exitosamente'
                        )
                    if incidencias_actualizadas > 0:
                        messages.info(
                            request,
                            f'{incidencias_actualizadas} incidencias actualizadas'
                        )
                    if errores:
                        messages.error(
                            request,
                            f'Errores en {len(errores)} empleados: {", ".join(errores[:5])}'
                        )

                    return redirect('incidencia_list')

            except Exception as e:
                messages.error(request, f'Error al procesar la lista: {str(e)}')
    else:
        form = IncidenciaMasivaForm()

    context = {
        'form': form,
        'title': 'Registro Masivo de Incidencias'
    }
    return render(request, 'incidencias/form_masiva.html', context)


@login_required
def incidencia_importar(request):
    """Importa incidencias desde archivo CSV"""
    if request.method == 'POST':
        form = IncidenciaImportarForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = form.cleaned_data['archivo']
            sobrescribir = form.cleaned_data['sobrescribir']

            try:
                with transaction.atomic():
                    # Leer archivo CSV
                    file = io.TextIOWrapper(archivo.file, encoding='utf-8')
                    reader = csv.DictReader(file)

                    required_fields = ['empleado', 'area_codigo', 'estado', 'fecha']
                    if not all(field in reader.fieldnames for field in required_fields):
                        messages.error(
                            request,
                            f'El archivo debe contener las columnas: {", ".join(required_fields)}'
                        )
                        return redirect('incidencia_importar')

                    incidencias_creadas = 0
                    incidencias_actualizadas = 0
                    errores = []

                    for linea_num, fila in enumerate(reader, 1):
                        try:
                            empleado = fila['empleado'].strip()
                            area_codigo = fila['area_codigo'].strip()
                            estado = fila['estado'].strip()
                            fecha_str = fila['fecha'].strip()

                            # Validar campos requeridos
                            if not all([empleado, area_codigo, estado, fecha_str]):
                                errores.append(f"Línea {linea_num}: Campos incompletos")
                                continue

                            # Validar área
                            if not Area.objects.filter(cod_area=area_codigo).exists():
                                errores.append(f"Línea {linea_num}: Área '{area_codigo}' no existe")
                                continue

                            # Validar estado
                            if estado not in dict(Incidencia.CHOICES):
                                errores.append(f"Línea {linea_num}: Estado '{estado}' no válido")
                                continue

                            # Parsear fecha
                            try:
                                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                            except ValueError:
                                errores.append(f"Línea {linea_num}: Formato de fecha inválido '{fecha_str}'")
                                continue

                            # Buscar incidencia existente
                            incidencia_existente = Incidencia.objects.filter(
                                empleado=empleado,
                                fecha_asistencia=fecha,
                                area=area_codigo
                            ).first()

                            if incidencia_existente:
                                if sobrescribir:
                                    incidencia_existente.estado = estado
                                    incidencia_existente.save()
                                    incidencias_actualizadas += 1
                            else:
                                Incidencia.objects.create(
                                    area=area_codigo,
                                    empleado=empleado,
                                    estado=estado,
                                    fecha_asistencia=fecha
                                )
                                incidencias_creadas += 1

                        except Exception as e:
                            errores.append(f"Línea {linea_num}: Error - {str(e)}")

                    # Mostrar resultados
                    if incidencias_creadas > 0:
                        messages.success(
                            request,
                            f'{incidencias_creadas} incidencias importadas exitosamente'
                        )
                    if incidencias_actualizadas > 0:
                        messages.info(
                            request,
                            f'{incidencias_actualizadas} incidencias actualizadas'
                        )
                    if errores:
                        messages.warning(
                            request,
                            f'{len(errores)} errores durante la importación'
                        )

                    return redirect('incidencia_list')

            except Exception as e:
                messages.error(request, f'Error al importar archivo: {str(e)}')
    else:
        form = IncidenciaImportarForm()

    context = {
        'form': form,
        'title': 'Importar Incidencias desde CSV'
    }
    return render(request, 'incidencias/importar.html', context)


@login_required
def incidencia_edicion_masiva(request):
    """Edición masiva de incidencias"""
    if request.method == 'POST':
        form = IncidenciaEdicionMasivaForm(request.POST)
        if form.is_valid():
            incidencias = form.cleaned_data['incidencias']
            nuevo_estado = form.cleaned_data['nuevo_estado']
            nueva_fecha = form.cleaned_data['nueva_fecha']

            try:
                with transaction.atomic():
                    incidencias_actualizadas = 0

                    for incidencia in incidencias:
                        incidencia.estado = nuevo_estado
                        if nueva_fecha:
                            incidencia.fecha_asistencia = nueva_fecha
                        incidencia.save()
                        incidencias_actualizadas += 1

                    messages.success(
                        request,
                        f'{incidencias_actualizadas} incidencias actualizadas exitosamente'
                    )
                    return redirect('incidencia_list')

            except Exception as e:
                messages.error(request, f'Error al actualizar incidencias: {str(e)}')
    else:
        # Obtener incidencias seleccionadas de la sesión o parámetros GET
        incidencias_ids = request.GET.getlist('incidencias') or request.session.get('incidencias_seleccionadas', [])
        incidencias = Incidencia.objects.filter(id__in=incidencias_ids)
        form = IncidenciaEdicionMasivaForm(initial={'incidencias': incidencias})

    context = {
        'form': form,
        'incidencias': incidencias,
        'title': 'Edición Masiva de Incidencias'
    }
    return render(request, 'incidencias/edicion_masiva.html', context)


@login_required
def incidencia_exportar(request):
    """Exporta incidencias a CSV"""
    incidencias = Incidencia.objects.all().order_by('-fecha_asistencia', 'empleado')

    # Aplicar filtros si existen
    filter_form = FiltroIncidenciasForm(request.GET or None)
    if filter_form.is_valid():
        incidencias = filter_form.filtrar_queryset(incidencias)

    # Crear respuesta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="incidencias_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['Empleado', 'Área', 'Estado', 'Fecha', 'Fecha_Registro'])

    for incidencia in incidencias:
        writer.writerow([
            incidencia.empleado,
            incidencia.area,
            incidencia.estado,
            incidencia.fecha_asistencia.strftime('%Y-%m-%d'),
            incidencia.fecha_asistencia.strftime('%d/%m/%Y')
        ])

    return response


@login_required
def incidencia_dashboard(request):
    """Dashboard con estadísticas de incidencias"""
    hoy = date.today()
    mes_actual = hoy.replace(day=1)

    # Estadísticas generales
    total_incidencias = Incidencia.objects.count()
    incidencias_hoy = Incidencia.objects.filter(fecha_asistencia=hoy).count()
    incidencias_mes = Incidencia.objects.filter(fecha_asistencia__month=hoy.month,
                                                fecha_asistencia__year=hoy.year).count()

    # Estadísticas por estado (hoy)
    estados_hoy = Incidencia.objects.filter(fecha_asistencia=hoy).values('estado').annotate(
        total=Count('id')
    ).order_by('estado')

    # Top áreas con más incidencias (mes actual)
    areas_top = Incidencia.objects.filter(
        fecha_asistencia__month=hoy.month,
        fecha_asistencia__year=hoy.year
    ).values('area').annotate(
        total=Count('id')
    ).order_by('-total')[:10]

    # Empleados con más incidencias (mes actual)
    empleados_top = Incidencia.objects.filter(
        fecha_asistencia__month=hoy.month,
        fecha_asistencia__year=hoy.year
    ).values('empleado').annotate(
        total=Count('id')
    ).order_by('-total')[:10]

    context = {
        'total_incidencias': total_incidencias,
        'incidencias_hoy': incidencias_hoy,
        'incidencias_mes': incidencias_mes,
        'estados_hoy': estados_hoy,
        'areas_top': areas_top,
        'empleados_top': empleados_top,
        'estados_choices': Incidencia.CHOICES
    }
    return render(request, 'incidencias/dashboard.html', context)


# Vistas API para AJAX
@login_required
def get_empleados_area(request, area_id):
    """Obtiene empleados frecuentes de un área (para autocompletar)"""
    try:
        area = Area.objects.get(pk=area_id)
        empleados = Incidencia.objects.filter(
            area=area.cod_area
        ).values_list('empleado', flat=True).distinct().order_by('empleado')[:20]

        data = {
            'empleados': list(empleados)
        }
        return JsonResponse(data)
    except Area.DoesNotExist:
        return JsonResponse({'empleados': []})


@login_required
def verificar_incidencia_existente(request):
    """Verifica si ya existe una incidencia para un empleado en una fecha"""
    empleado = request.GET.get('empleado', '')
    fecha_str = request.GET.get('fecha', '')
    area_id = request.GET.get('area', '')

    try:
        if empleado and fecha_str and area_id:
            area = Area.objects.get(pk=area_id)
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

            incidencia = Incidencia.objects.filter(
                empleado=empleado,
                fecha_asistencia=fecha,
                area=area.cod_area
            ).first()

            if incidencia:
                return JsonResponse({
                    'existe': True,
                    'estado_actual': incidencia.estado,
                    'fecha_actual': incidencia.fecha_asistencia.strftime('%d/%m/%Y')
                })

        return JsonResponse({'existe': False})
    except Exception as e:
        return JsonResponse({'error': str(e)})