
from django.urls import path

from .views import (
    ListaUsuariosAPIView,
    DetalleUsuarioAPIView,
    AdminEditarUsuarioAPIView,
    EliminarUsuarioAPIView,
    ActivarDesactivarUsuarioAPIView,
    AdminAsociarUsuarioEdificioAPIView,  
    ListaAsociacionesUsuarioEdificioAPIView, 
    EliminarAsociacionUsuarioEdificioAPIView, 
    UsuariosAsignadosAPIView,
    DetalleUsuarioAsignadoAPIView,
    ArrendadorActivarDesactivarArrendatarioAPIView,
    
    RegistroUsuarioAPIView,
    VerificarCorreoAPIView,
    EditarPerfilAPIView,
    PerfilUsuarioAPIView,
    SolicitarCambioCorreoAPIView,
    ConfirmarCambioCorreoAPIView
)    
from .views_solicitudes import (
    ListarSolicitudesPendientesAPIView,
    ValidarSolicitudAPIView,
    HistorialSolicitudesAPIView,
    SolicitudesEdificiosArrendadorAPIView,    

    SolicitarVinculacionAPIView    
)

urlpatterns = [
    path('admin/panel/', ListaUsuariosAPIView.as_view(), name='usuarios-lista'), #Lista de usuarios (superuser)    
    path('admin/detalle/<int:pk>/', DetalleUsuarioAPIView.as_view(), name='usuario-detalle'), #Vista de un usuario (superuser)
    path('admin/<int:pk>/editar/', AdminEditarUsuarioAPIView.as_view(), name='admin-editar-usuario'), #Vista para editar permisos usuario (superuser)
    path('admin/eliminar/<int:pk>/', EliminarUsuarioAPIView.as_view(), name='usuario-eliminar'), #Eliminar un usuario (superuser)  
    path('admin/<int:pk>/activar-desactivar/', ActivarDesactivarUsuarioAPIView.as_view(), name='activar-desactivar-usuario'), #Vista para activar/desactivar un usuario (superuser)
    path('admin/asociar-usuario-edificio/', AdminAsociarUsuarioEdificioAPIView.as_view(), name='admin-asociar-usuario-edificio'), #Vista para asociar usuario con edificio manualmente (superuser)
    path('admin/asociaciones/', ListaAsociacionesUsuarioEdificioAPIView.as_view(), name='admin-asociaciones'), #Lista de usuarios y sus edificios asociados (superuser)
    path('asociaciones/<int:pk>/eliminar/', EliminarAsociacionUsuarioEdificioAPIView.as_view(), name='eliminar-asociacion'), #Eliminar una asociacion entre usuario edificio (superuser)
    
    path('arrendador/asignados/', UsuariosAsignadosAPIView.as_view(), name='usuarios-asignados'), #Lista de usuarios del edificio (arrendador)
    path('arrendador/solicitudes/', SolicitudesEdificiosArrendadorAPIView.as_view(), name='solicitudes-arrendador'), #Historial de solicitudes de vinculacion de arrendatarios a edificio (arrendador) 
    path('arrendador/asignados/detalle/<int:pk>/', DetalleUsuarioAsignadoAPIView.as_view(), name='detalle-usuario-asignado'), #Vista detalle de perfil de arrendatarios asociados a edificio que se administra (arrendador)
    path('arrendador/<int:pk>/activar-desactivar/', ArrendadorActivarDesactivarArrendatarioAPIView.as_view(), name='arrendador-activar-desactivar-usuario'), #Vista que permite activar desactivar un arrendatario (arrendador)
    
    path('solicitudes/pendientes/', ListarSolicitudesPendientesAPIView.as_view(), name='solicitudes-pendientes'), #Lista de solicitudes de vinculacion pendientes
    path('solicitudes/<int:pk>/validar/', ValidarSolicitudAPIView.as_view(), name='validar-solicitud'), #Validacion o rechazo de solicitud de vinculacion
    path('solicitudes/historial/', HistorialSolicitudesAPIView.as_view(), name='historial-solicitudes'), #Historial de solicitudes de vinculacion (superuser) 
    path('arrendador/solicitudes/', SolicitudesEdificiosArrendadorAPIView.as_view(), name='solicitudes-arrendador'), #Lista de solicitudes de arrendatarios del edificio asociado (arrendador)

    path('registro/', RegistroUsuarioAPIView.as_view(), name='usuarios-registro'), #Registro general de usuarios
    path('verificar-email/<uidb64>/<token>/', VerificarCorreoAPIView.as_view(), name='verificar-correo'), #Vista para validar correo con token
    path('solicitar-vinculacion/', SolicitarVinculacionAPIView.as_view(), name='solicitar-vinculacion'), #Solicitud de vinculacion a edificio
    path('perfil/editar/', EditarPerfilAPIView.as_view(), name='editar-perfil'), #Editar perfil propio
    path('perfil/', PerfilUsuarioAPIView.as_view(), name='perfil-usuario'), #Ver perfil propio
    path('cambio-correo/solicitar/', SolicitarCambioCorreoAPIView.as_view(), name='solicitar-cambio-correo'), #Vista para solicitar cambio de correo
    path('cambio-correo/confirmar/<uidb64>/<token>/', ConfirmarCambioCorreoAPIView.as_view(), name='confirmar-cambio-correo'), #Vista para confirmar cambio correo
]