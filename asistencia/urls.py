
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
]