from rest_framework.permissions import BasePermission

class EsArrendatario(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.tipo_usuario == 'arrendatario'
    
class EsArrendador(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_superuser or request.user.tipo_usuario == 'arrendador'
    
    