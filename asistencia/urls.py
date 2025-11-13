
from django.urls import path
from . import views

urlpatterns = [
    # Iniciar sesion.
    path('accounts/login/', views.login_view, name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # URLs existentes...
    path('responsables/crear/', views.responsable_area_create, name='responsable_area_create'),
    path('responsables/buscar-crear-usuario/', views.buscar_crear_usuario, name='buscar_crear_usuario'),
    path('responsables/asignacion-rapida/', views.asignacion_rapida, name='asignacion_rapida'),
    path('responsables/crear-usuario-ajax/', views.crear_usuario_ajax, name='crear_usuario_ajax'),
    path('responsables/buscar-usuario-ajax/', views.buscar_usuario_ajax, name='buscar_usuario_ajax'),
    path('usuarios/crear/', views.gestion_usuario_completa, name='crear_usuario'),
    path('usuarios/editar/<int:usuario_id>/', views.gestion_usuario_completa, name='editar_usuario'),

    # Incidencias
    path('incidencias/', views.incidencia_list, name='incidencia_list'),
    path('incidencias/crear/', views.incidencia_create_individual, name='incidencia_create_individual'),
    path('incidencias/crear-masiva/', views.incidencia_create_masiva, name='incidencia_create_masiva'),
    path('incidencias/importar/', views.incidencia_importar, name='incidencia_importar'),
    path('incidencias/edicion-masiva/', views.incidencia_edicion_masiva, name='incidencia_edicion_masiva'),
    path('incidencias/exportar/', views.incidencia_exportar, name='incidencia_exportar'),
    path('incidencias/dashboard/', views.incidencia_dashboard, name='incidencia_dashboard'),

    # API URLs
    path('api/empleados-area/<int:area_id>/', views.get_empleados_area, name='get_empleados_area'),
    path('api/verificar-incidencia/', views.verificar_incidencia_existente, name='verificar_incidencia_existente'),

    # Incidencias para trabajadores existentes
    path('incidencias/trabajadores-existentes/', views.incidencia_trabajadores_existentes, name='incidencia_trabajadores_existentes'),
    path('incidencias/obtener-trabajadores-area/', views.obtener_trabajadores_area, name='obtener_trabajadores_area'),
    path('incidencias/calcular-rango-trabajadores/', views.calcular_rango_trabajadores, name='calcular_rango_trabajadores'),
    path('incidencias/verificar-existencias/', views.verificar_incidencias_existentes, name='verificar_incidencias_existentes'),

    # Incidencias por rango de días
    path('incidencias/rango-dias/', views.incidencia_rango_dias, name='incidencia_rango_dias'),
    path('incidencias/calcular-rango/', views.calcular_rango_dias, name='calcular_rango_dias'),
    path('incidencias/obtener-dias-mes/', views.obtener_dias_mes, name='obtener_dias_mes'),
    path('incidencias/vista-previa-rango/', views.vista_previa_rango, name='vista_previa_rango'),


]