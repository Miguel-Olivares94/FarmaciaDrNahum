# farmacia/middleware.py
# Middleware para verificación de roles y seguridad

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from .models import RolPermiso, AuditoriaLog
import logging

logger = logging.getLogger('auditoria')


class VerificacionRolMiddleware:
    """
    Middleware que verifica el rol del usuario antes de permitir acceso a rutas protegidas.
    Bloquea acceso a rutas administrativas para usuarios sin permisos ADMIN.
    """
    
    # Rutas que requieren rol ADMIN
    RUTAS_ADMIN = [
        '/farmacia/admin/',
        '/farmacia/configuracion/',
        '/farmacia/usuarios/',
        '/farmacia/roles/',
        '/farmacia/auditoria/',
        '/farmacia/reportes/global/',
        '/farmacia/reportes/finanzas/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Validar acceso a rutas protegidas
        if self.es_ruta_admin(request.path):
            if request.user.is_authenticated:
                try:
                    rol_permiso = RolPermiso.objects.get(user=request.user)
                    if rol_permiso.rol != 'ADMIN':
                        self.registrar_acceso_denegado(request)
                        return HttpResponse('Acceso denegado - Solo administrador', status=403)
                except RolPermiso.DoesNotExist:
                    self.registrar_acceso_denegado(request)
                    return HttpResponse('Usuario sin rol asignado', status=403)
            else:
                return HttpResponse('No autenticado', status=401)
        
        response = self.get_response(request)
        return response
    
    def es_ruta_admin(self, path):
        """Verifica si la ruta es una ruta administrativa"""
        return any(path.startswith(ruta) for ruta in self.RUTAS_ADMIN)
    
    def registrar_acceso_denegado(self, request):
        """Registra intentos de acceso denegado en auditoría"""
        try:
            AuditoriaLog.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                accion='ACCESODENEGADO',
                objeto=request.path,
                objeto_id=0,
                detalles=f"Intento de acceder a ruta protegida: {request.path}",
                resultado=False,
                ip_address=self.get_client_ip(request),
            )
        except Exception as e:
            logger.error(f"Error registrando acceso denegado: {str(e)}")
        
        logger.warning(f"Acceso denegado: {request.user if request.user.is_authenticated else 'Anónimo'} - {request.path}")
    
    @staticmethod
    def get_client_ip(request):
        """Obtiene la IP del cliente"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
