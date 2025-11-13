# views.py
from django.contrib.auth import login, logout, authenticate
from .forms import LDAPAuthenticationForm
import asistencia.trabajadores
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator

from django.db import transaction

from django.db.models import Q, Count
from datetime import datetime, date

import json
import csv
import io
from .models import ResponsableArea, Area, Incidencia, User
from .forms import (
    ResponsableAreaForm,
    BuscarCrearUsuarioForm,
    AsignacionRapidaForm,
    UserCreationFlexibleForm,
    IncidenciaForm,
    IncidenciaMasivaForm,
    IncidenciaImportarForm,
    FiltroIncidenciasForm,
    IncidenciaEdicionMasivaForm
)
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
                    empleados = obtener_usuarios_ldap3()
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